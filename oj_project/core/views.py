# core/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from .models import Problem, Submission, TestCase
from collections import defaultdict
import json
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from .admin_utils import check_admin_access

# Replace your existing problems_list function with this updated version:
def problems_list(request):
    """Display list of all problems with user progress and search functionality"""
    # Check if admin user should be redirected to admin dashboard
    if request.user.is_authenticated and (request.user.is_superuser or request.user.is_staff):
        # If admin user came directly to problems list, show a message with admin options
        if not request.GET.get('from_admin'):
            messages.info(request, 'Welcome Admin! You can manage problems from the admin panel above.')
    
    # Get search query
    search_query = request.GET.get('search', '').strip()
    
    # Base queryset
    problems = Problem.objects.all()
    
    # Apply search filter if query exists
    if search_query:
        problems = problems.filter(
            Q(name__icontains=search_query) |
            Q(short_code__icontains=search_query) |
            Q(statement__icontains=search_query)
        )
    
    # Order problems
    problems = problems.order_by('difficulty', 'name')
    
    # Get counts for all problems (not just filtered ones)
    all_problems = Problem.objects.all()
    easy_count = all_problems.filter(difficulty='E').count()
    medium_count = all_problems.filter(difficulty='M').count()
    hard_count = all_problems.filter(difficulty='H').count()
    total_problems_count = all_problems.count()
    
    # Initialize context data
    context = {
        'problems': problems,
        'search_query': search_query,
        'easy_count': easy_count,
        'medium_count': medium_count,
        'hard_count': hard_count,
        'total_problems_count': total_problems_count,
        'is_admin': check_admin_access(request.user),
    }
    
    # If user is authenticated, calculate their progress
    if request.user.is_authenticated:
        # Get all accepted submissions for this user
        accepted_submissions = Submission.objects.filter(
            user=request.user,
            verdict='AC'
        ).values_list('problem__short_code', flat=True).distinct()
        
        solved_problems = set(accepted_submissions)
        
        # Count solved problems by difficulty (from all problems, not just filtered)
        easy_solved = 0
        medium_solved = 0
        hard_solved = 0
        
        for problem in all_problems:
            if problem.short_code in solved_problems:
                if problem.difficulty == 'E':
                    easy_solved += 1
                elif problem.difficulty == 'M':
                    medium_solved += 1
                elif problem.difficulty == 'H':
                    hard_solved += 1
        
        total_solved = len(solved_problems)
        remaining_problems = total_problems_count - total_solved
        
        user_progress = {
            'solved_problems': solved_problems,
            'easy_completed': easy_solved,
            'medium_completed': medium_solved,
            'hard_completed': hard_solved,
            'total_solved': total_solved,
            'remaining_problems': remaining_problems,
        }
        
        context['user_progress'] = user_progress
    else:
        # Default progress for non-authenticated users
        context['user_progress'] = {
            'solved_problems': set(),
            'easy_completed': 0,
            'medium_completed': 0,
            'hard_completed': 0,
            'total_solved': 0,
            'remaining_problems': total_problems_count,
        }
    
    return render(request, 'problem_list.html', context)

def get_user_progress(user):
    """Helper function to calculate user progress"""
    all_problems = Problem.objects.all()
    total_problems_count = all_problems.count()
    
    if user.is_authenticated:
        # Get all accepted submissions for this user
        accepted_submissions = Submission.objects.filter(
            user=user,
            verdict='AC'
        ).values_list('problem__short_code', flat=True).distinct()
        
        solved_problems = set(accepted_submissions)
        
        # Count solved problems by difficulty
        easy_solved = 0
        medium_solved = 0
        hard_solved = 0
        
        for problem in all_problems:
            if problem.short_code in solved_problems:
                if problem.difficulty == 'E':
                    easy_solved += 1
                elif problem.difficulty == 'M':
                    medium_solved += 1
                elif problem.difficulty == 'H':
                    hard_solved += 1
        
        total_solved = len(solved_problems)
        remaining_problems = total_problems_count - total_solved
        
        return {
            'solved_problems': solved_problems,
            'easy_completed': easy_solved,
            'medium_completed': medium_solved,
            'hard_completed': hard_solved,
            'total_solved': total_solved,
            'remaining_problems': remaining_problems,
        }
    else:
        # Default progress for non-authenticated users
        return {
            'solved_problems': set(),
            'easy_completed': 0,
            'medium_completed': 0,
            'hard_completed': 0,
            'total_solved': 0,
            'remaining_problems': total_problems_count,
        }

def problem_detail(request, short_code):
    """Display problem details and handle submission"""
    try:
        problem = get_object_or_404(Problem, short_code=short_code)
    except Problem.DoesNotExist:
        messages.error(request, f'Problem with code "{short_code}" not found.')
        return redirect('core:problems_list')
    
    # Get visible test cases (not hidden)
    visible_testcases = problem.testcases.filter(is_hidden=False)
    
    # Get user's submissions for this problem if authenticated
    user_submissions = []
    if request.user.is_authenticated:
        user_submissions = Submission.objects.filter(
            problem=problem,
            user=request.user
        ).order_by('-submitted')[:10]  # Last 10 submissions
    
    # Get user progress and problem counts for the template
    user_progress = get_user_progress(request.user)
    all_problems = Problem.objects.all()
    
    context = {
        'problem': problem,
        'testcases': visible_testcases,
        'user_submissions': user_submissions,
        'user_progress': user_progress,
        'problems': all_problems,  # For the dashboard section
        'easy_count': Problem.objects.filter(difficulty='E').count(),
        'medium_count': Problem.objects.filter(difficulty='M').count(),
        'hard_count': Problem.objects.filter(difficulty='H').count(),
    }
    
    # Handle code submission
    if request.method == 'POST' and request.user.is_authenticated:
        code_text = request.POST.get('solution_code', '').strip()
        language = request.POST.get('language', 'python')
        action = request.POST.get('action', 'submit')
        
        if not code_text:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Code cannot be empty'
                })
            messages.error(request, 'Code cannot be empty')
            return render(request, 'problem_detail.html', context)
        
        # Map language values from form to database choices
        language_mapping = {
            'python': 'py',
            'cpp': 'cpp',
            'java': 'py',  # Fallback to Python for now
            'c': 'c'
        }
        db_language = language_mapping.get(language, 'py')
        
        # For AI review only, create submission but don't show regular messages
        if action == 'ai_review_only':
            # Simple mock evaluation for AI review
            verdict = 'AC' if len(code_text.strip()) > 20 else 'WA'
            
            submission = Submission.objects.create(
                problem=problem,
                user=request.user,
                code_text=code_text,
                language=db_language,
                verdict=verdict
            )
            
            return JsonResponse({
                'success': True,
                'submission_id': submission.id,
                'message': 'Submission created for AI review'
            })
        
        # For regular submission or testing
        # Simple mock evaluation - just check if code is not empty and has some content
        verdict = 'AC' if len(code_text.strip()) > 20 else 'WA'  # Very basic check
        
        # Create submission record
        submission = Submission.objects.create(
            problem=problem,
            user=request.user,
            code_text=code_text,
            language=db_language,
            verdict=verdict
        )
        
        if action == 'test':
            if verdict == 'AC':
                messages.success(request, 'Test passed! Your code looks good.')
            else:
                messages.warning(request, 'Test failed. Please review your code.')
        else:  # submit
            if verdict == 'AC':
                messages.success(request, 'Congratulations! Your solution was accepted.')
            else:
                messages.error(request, 'Wrong Answer. Please try again.')
        
        return redirect('core:problem_detail', short_code=short_code)
    
    return render(request, 'problem_detail.html', context)

@login_required
def submissions_list(request):
    """Display user's submissions"""
    submissions = Submission.objects.filter(user=request.user).order_by('-submitted')
    
    context = {
        'submissions': submissions,
    }
    
    return render(request, 'submissions.html', context)

@login_required
def submit_solution(request, short_code):
    """Handle solution submission - redirect to problem detail for processing"""
    return redirect('core:problem_detail', short_code=short_code)

# Admin Views
def is_admin(user):
    """Check if user is admin/superuser"""
    return user.is_superuser or user.is_staff

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Admin dashboard showing problems overview"""
    problems = Problem.objects.all().order_by('-id')[:10]  # Latest 10 problems
    total_problems = Problem.objects.count()
    total_submissions = Submission.objects.count()
    
    # Count by difficulty
    easy_count = Problem.objects.filter(difficulty='E').count()
    medium_count = Problem.objects.filter(difficulty='M').count()
    hard_count = Problem.objects.filter(difficulty='H').count()
    
    context = {
        'problems': problems,
        'total_problems': total_problems,
        'total_submissions': total_submissions,
        'easy_count': easy_count,
        'medium_count': medium_count,
        'hard_count': hard_count,
    }
    
    return render(request, 'admin/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_add_problem(request):
    """Admin page to add new problems"""
    if request.method == 'POST':
        try:
            # Get basic problem data
            name = request.POST.get('name', '').strip()
            short_code = request.POST.get('short_code', '').strip()
            statement = request.POST.get('statement', '').strip()
            difficulty = request.POST.get('difficulty', '')
            
            # Validate required fields
            if not all([name, short_code, statement, difficulty]):
                messages.error(request, 'All fields are required!')
                return render(request, 'admin/add_problem.html')
            
            # Check if short code already exists
            if Problem.objects.filter(short_code=short_code).exists():
                messages.error(request, f'Problem with short code "{short_code}" already exists!')
                return render(request, 'admin/add_problem.html')
            
            # Create the problem
            problem = Problem.objects.create(
                name=name,
                short_code=short_code,
                statement=statement,
                difficulty=difficulty
            )
            
            # Handle file uploads for test cases
            input_file = request.FILES.get('input_file')
            output_file = request.FILES.get('output_file')
            
            if input_file and output_file:
                # Read file contents
                input_content = input_file.read().decode('utf-8')
                output_content = output_file.read().decode('utf-8')
                
                # Split by double newlines for multiple test cases
                inputs = input_content.strip().split('\n\n')
                outputs = output_content.strip().split('\n\n')
                
                if len(inputs) != len(outputs):
                    messages.warning(request, f'File mismatch: {len(inputs)} inputs vs {len(outputs)} outputs. Manual test cases will be used.')
                else:
                    # Create test cases from files
                    for i, (inp, out) in enumerate(zip(inputs, outputs)):
                        TestCase.objects.create(
                            problem=problem,
                            input=inp.strip(),
                            output=out.strip(),
                            is_hidden=False,  # File-based test cases are visible by default
                            order=i + 1
                        )
                    
                    messages.success(request, f'Problem "{name}" created successfully with {len(inputs)} test cases from files!')
                    return redirect('core:admin_problems_list')
            
            # Handle manual test cases
            test_case_count = 0
            created_test_cases = 0
            
            # Count how many test cases were submitted
            for key in request.POST.keys():
                if key.startswith('testcase_input_'):
                    test_case_count += 1
            
            # Create test cases
            for i in range(1, test_case_count + 1):
                input_key = f'testcase_input_{i}'
                output_key = f'testcase_output_{i}'
                hidden_key = f'testcase_hidden_{i}'
                order_key = f'testcase_order_{i}'
                
                test_input = request.POST.get(input_key, '').strip()
                test_output = request.POST.get(output_key, '').strip()
                is_hidden = request.POST.get(hidden_key) == 'on'
                order = request.POST.get(order_key, i)
                
                if test_input and test_output:
                    TestCase.objects.create(
                        problem=problem,
                        input=test_input,
                        output=test_output,
                        is_hidden=is_hidden,
                        order=int(order)
                    )
                    created_test_cases += 1
            
            if created_test_cases == 0:
                messages.warning(request, 'Problem created but no test cases were added!')
            else:
                messages.success(request, f'Problem "{name}" created successfully with {created_test_cases} test cases!')
            
            return redirect('core:admin_problems_list')
            
        except Exception as e:
            messages.error(request, f'Error creating problem: {str(e)}')
            return render(request, 'admin/add_problem.html')
    
    return render(request, 'admin/add_problem.html')

@login_required
@user_passes_test(is_admin)
def admin_problems_list(request):
    """Admin page to view and manage all problems"""
    search_query = request.GET.get('search', '').strip()
    
    problems = Problem.objects.all()
    
    if search_query:
        problems = problems.filter(
            Q(name__icontains=search_query) |
            Q(short_code__icontains=search_query) |
            Q(statement__icontains=search_query)
        )
    
    problems = problems.order_by('-id')  # Latest first
    
    context = {
        'problems': problems,
        'search_query': search_query,
        'total_problems': Problem.objects.count(),
    }
    
    return render(request, 'admin/problems_list.html', context)

@login_required
@user_passes_test(is_admin)
def admin_edit_problem(request, short_code):
    """Admin page to edit existing problem"""
    problem = get_object_or_404(Problem, short_code=short_code)
    
    if request.method == 'POST':
        try:
            # Update basic problem data
            problem.name = request.POST.get('name', '').strip()
            problem.short_code = request.POST.get('short_code', '').strip()
            problem.statement = request.POST.get('statement', '').strip()
            problem.difficulty = request.POST.get('difficulty', '')
            
            # Check if short code conflicts with another problem
            if Problem.objects.filter(short_code=problem.short_code).exclude(id=problem.id).exists():
                messages.error(request, f'Another problem with short code "{problem.short_code}" already exists!')
                return render(request, 'admin/edit_problem.html', {'problem': problem})
            
            problem.save()
            
            # Update test cases - delete existing and recreate
            problem.testcases.all().delete()
            
            test_case_count = 0
            created_test_cases = 0
            
            # Count test cases
            for key in request.POST.keys():
                if key.startswith('testcase_input_'):
                    test_case_count += 1
            
            # Create new test cases
            for i in range(1, test_case_count + 1):
                input_key = f'testcase_input_{i}'
                output_key = f'testcase_output_{i}'
                hidden_key = f'testcase_hidden_{i}'
                order_key = f'testcase_order_{i}'
                
                test_input = request.POST.get(input_key, '').strip()
                test_output = request.POST.get(output_key, '').strip()
                is_hidden = request.POST.get(hidden_key) == 'on'
                order = request.POST.get(order_key, i)
                
                if test_input and test_output:
                    TestCase.objects.create(
                        problem=problem,
                        input=test_input,
                        output=test_output,
                        is_hidden=is_hidden,
                        order=int(order)
                    )
                    created_test_cases += 1
            
            messages.success(request, f'Problem "{problem.name}" updated successfully with {created_test_cases} test cases!')
            return redirect('core:admin_problems_list')
            
        except Exception as e:
            messages.error(request, f'Error updating problem: {str(e)}')
    
    # Get existing test cases for editing
    test_cases = problem.testcases.all().order_by('order')
    
    context = {
        'problem': problem,
        'test_cases': test_cases,
    }
    
    return render(request, 'admin/edit_problem.html', context)

@login_required
@user_passes_test(is_admin)
def admin_delete_problem(request, short_code):
    """Admin page to delete a problem"""
    problem = get_object_or_404(Problem, short_code=short_code)
    
    if request.method == 'POST':
        problem_name = problem.name
        problem.delete()
        messages.success(request, f'Problem "{problem_name}" deleted successfully!')
        return redirect('core:admin_problems_list')
    
    context = {
        'problem': problem,
        'submission_count': problem.submission_set.count(),
    }
    
    return render(request, 'admin/delete_problem.html', context)