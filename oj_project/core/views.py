# core/views.py - Updated with proper compiler integration
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

# Import the evaluation function from compiler app
from compiler.views import evaluate_submission

from .admin_utils import check_admin_access

# Replace your existing problems_list function with this updated version:
# Add these imports at the top of your views.py
from django.contrib.auth.models import User
from django.db.models import Count, Q
from datetime import datetime, timedelta
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Helper function for admin check
def is_admin(user):
    """Check if user is admin/superuser"""
    return user.is_superuser or user.is_staff

# Update your admin_dashboard view

# Add these new views for Users and Analytics
@login_required
@user_passes_test(is_admin)
def admin_users_list(request):
    """Admin page to view and manage all users"""
    search_query = request.GET.get('search', '').strip()
    
    users = User.objects.all()
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    users = users.order_by('-date_joined')
    
    # Calculate user statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(last_login__gte=datetime.now() - timedelta(days=30)).count()
    admin_users = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True)).count()
    
    # Get users with submission counts
    users_with_stats = users.annotate(
        submission_count=Count('submission'),
        accepted_count=Count('submission', filter=Q(submission__verdict='AC'))
    )
    
    context = {
        'users': users_with_stats[:50],  # Limit to 50 for performance
        'search_query': search_query,
        'total_users': total_users,
        'active_users': active_users,
        'admin_users': admin_users,
    }
    
    return render(request, 'admin/users_list.html', context)

@login_required
@user_passes_test(is_admin)
def admin_analytics(request):
    """Admin page showing platform analytics"""
    # Time-based analytics
    now = datetime.now()
    last_week = now - timedelta(days=7)
    last_month = now - timedelta(days=30)
    
    # Submission analytics
    total_submissions = Submission.objects.count()
    weekly_submissions = Submission.objects.filter(submitted__gte=last_week).count()
    monthly_submissions = Submission.objects.filter(submitted__gte=last_month).count()
    
    # Problem analytics
    total_problems = Problem.objects.count()
    easy_problems = Problem.objects.filter(difficulty='E').count()
    medium_problems = Problem.objects.filter(difficulty='M').count()
    hard_problems = Problem.objects.filter(difficulty='H').count()
    
    # User analytics
    total_users = User.objects.count()
    active_users = User.objects.filter(last_login__gte=last_week).count()
    new_users_this_month = User.objects.filter(date_joined__gte=last_month).count()
    
    # Verdict distribution
    verdict_stats = Submission.objects.values('verdict').annotate(count=Count('verdict'))
    
    # Popular problems (most submitted)
    popular_problems = Problem.objects.annotate(
        submission_count=Count('submission')
    ).order_by('-submission_count')[:10]
    
    # Daily submission trend (last 7 days)
    daily_submissions = []
    for i in range(7):
        day = now - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        count = Submission.objects.filter(
            submitted__gte=day_start,
            submitted__lt=day_end
        ).count()
        
        daily_submissions.append({
            'date': day.strftime('%Y-%m-%d'),
            'count': count
        })
    
    context = {
        'total_submissions': total_submissions,
        'weekly_submissions': weekly_submissions,
        'monthly_submissions': monthly_submissions,
        'total_problems': total_problems,
        'easy_problems': easy_problems,
        'medium_problems': medium_problems,
        'hard_problems': hard_problems,
        'total_users': total_users,
        'active_users': active_users,
        'new_users_this_month': new_users_this_month,
        'verdict_stats': verdict_stats,
        'popular_problems': popular_problems,
        'daily_submissions': daily_submissions,
    }
    
    return render(request, 'admin/analytics.html', context)

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
    
    # Calculate difficulty counts from ALL problems (not just filtered ones)
    all_problems = Problem.objects.all()
    easy_count = all_problems.filter(difficulty='E').count()
    medium_count = all_problems.filter(difficulty='M').count()
    hard_count = all_problems.filter(difficulty='H').count()
    total_problems = all_problems.count()
    
    context = {
        'problems': problems,
        'search_query': search_query,
        'total_problems': total_problems,
        'easy_count': easy_count,
        'medium_count': medium_count,
        'hard_count': hard_count,
    }
    
    return render(request, 'admin/problems_list.html', context)

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
        
        # Validate code input
        if not code_text:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Code cannot be empty'
                })
            messages.error(request, 'Code cannot be empty')
            return render(request, 'problem_detail.html', context)
        
        # Basic validation - check for meaningful code
        if len(code_text.strip()) < 10:
            messages.error(request, 'Please provide a meaningful solution')
            return render(request, 'problem_detail.html', context)
        
        # Map language values from form to database choices
        language_mapping = {
            'python': 'py',
            'cpp': 'cpp',
            'java': 'py',  # Fallback to Python for now
            'c': 'c'
        }
        db_language = language_mapping.get(language, 'py')
        
        # Create submission record first (with pending status)
        submission = Submission.objects.create(
            problem=problem,
            user=request.user,
            code_text=code_text,
            language=db_language,
            verdict='PE'  # Pending evaluation
        )
        
        logger.info(f"Created submission {submission.id} for user {request.user.username} on problem {problem.short_code}")
        
        try:
            # For AI review only, just set a basic verdict and return
            if action == 'ai_review_only':
                submission.verdict = 'AC'  # Assume AC for AI review
                submission.save()
                
                return JsonResponse({
                    'success': True,
                    'submission_id': submission.id,
                    'message': 'Submission created for AI review'
                })
            
            # Use the actual compiler evaluation function
            logger.info(f"Starting evaluation for submission {submission.id}")
            verdict = evaluate_submission(submission, db_language)
            
            # Update submission with the verdict
            submission.verdict = verdict
            submission.save()
            
            logger.info(f"Evaluation completed for submission {submission.id} with verdict: {verdict}")
            
            # Provide feedback based on action and verdict
            if action == 'test':
                if verdict == 'AC':
                    messages.success(request, '✅ Test passed! Your code works correctly on the sample test cases.')
                elif verdict == 'WA':
                    messages.error(request, '❌ Wrong Answer. Your output doesn\'t match the expected results.')
                elif verdict == 'RE':
                    messages.error(request, '💥 Runtime Error. There\'s an error in your code execution.')
                elif verdict == 'TLE':
                    messages.error(request, '⏰ Time Limit Exceeded. Your code is taking too long to execute.')
                elif verdict == 'CE':
                    messages.error(request, '⚠️ Compilation Error. There\'s a syntax error in your code.')
                else:
                    messages.warning(request, f'Test completed with status: {submission.get_verdict_display()}')
            else:  # submit
                if verdict == 'AC':
                    messages.success(request, '🎉 Congratulations! Your solution was accepted!')
                elif verdict == 'WA':
                    messages.error(request, '❌ Wrong Answer. Please check your logic and try again.')
                elif verdict == 'RE':
                    messages.error(request, '💥 Runtime Error. Please fix the errors in your code.')
                elif verdict == 'TLE':
                    messages.error(request, '⏰ Time Limit Exceeded. Try optimizing your solution.')
                elif verdict == 'CE':
                    messages.error(request, '⚠️ Compilation Error. Please fix the syntax errors.')
                else:
                    messages.warning(request, f'Submission completed with status: {submission.get_verdict_display()}')
        
        except Exception as e:
            logger.error(f"Error during evaluation of submission {submission.id}: {str(e)}", exc_info=True)
            submission.verdict = 'RE'  # Runtime error
            submission.save()
            
            if action == 'test':
                messages.error(request, '💥 Error occurred during testing. Please check your code.')
            else:
                messages.error(request, '💥 Error occurred during submission evaluation. Please try again.')
        
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
    """Admin dashboard showing real platform statistics"""
    # Get recent problems (latest 10)
    problems = Problem.objects.all().order_by('-id')[:10]
    
    # Calculate real statistics
    total_problems = Problem.objects.count()
    total_submissions = Submission.objects.count()
    total_users = User.objects.count()
    
    # Calculate success rate
    if total_submissions > 0:
        accepted_submissions = Submission.objects.filter(verdict='AC').count()
        success_rate = round((accepted_submissions / total_submissions) * 100)
    else:
        success_rate = 0
    
    # Get recent submissions for activity feed (latest 10)
    recent_submissions = Submission.objects.select_related('user', 'problem').order_by('-submitted')[:10]
    
    context = {
        'problems': problems,
        'total_problems': total_problems,
        'total_submissions': total_submissions,
        'total_users': total_users,
        'success_rate': success_rate,
        'recent_submissions': recent_submissions,
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
                
                # Split by double newlines OR single newlines based on content
                # First try double newlines (preferred format)
                if '\n\n' in input_content:
                    inputs = [inp.strip() for inp in input_content.strip().split('\n\n') if inp.strip()]
                else:
                    # If no double newlines, split by single newlines (each line is a test case)
                    inputs = [inp.strip() for inp in input_content.strip().split('\n') if inp.strip()]
                
                if '\n\n' in output_content:
                    outputs = [out.strip() for out in output_content.strip().split('\n\n') if out.strip()]
                else:
                    outputs = [out.strip() for out in output_content.strip().split('\n') if out.strip()]
                
                if len(inputs) != len(outputs):
                    messages.warning(request, f'File mismatch: {len(inputs)} inputs vs {len(outputs)} outputs. Manual test cases will be used.')
                else:
                    # Create test cases from files
                    for i, (inp, out) in enumerate(zip(inputs, outputs)):
                        TestCase.objects.create(
                            problem=problem,
                            input=inp,
                            output=out,
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

@login_required
@user_passes_test(is_admin)
def admin_submissions_list(request):
    """Admin page to view and manage all submissions"""
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')
    language_filter = request.GET.get('language', '')
    
    # Base queryset
    submissions = Submission.objects.select_related('user', 'problem').all()
    
    # Apply filters
    if search_query:
        submissions = submissions.filter(
            Q(user__username__icontains=search_query) |
            Q(problem__name__icontains=search_query) |
            Q(problem__short_code__icontains=search_query) |
            Q(id__icontains=search_query)
        )
    
    if status_filter:
        submissions = submissions.filter(verdict=status_filter)
    
    if language_filter:
        submissions = submissions.filter(language=language_filter)
    
    # Order by latest first
    submissions = submissions.order_by('-submitted')
    
    # Pagination could be added here
    submissions = submissions[:100]  # Limit to 100 for now
    
    # Calculate statistics
    total_submissions = Submission.objects.count()
    accepted_count = Submission.objects.filter(verdict='AC').count()
    wrong_answer_count = Submission.objects.filter(verdict='WA').count()
    success_rate = round((accepted_count / total_submissions * 100) if total_submissions > 0 else 0)
    
    context = {
        'submissions': submissions,
        'search_query': search_query,
        'status_filter': status_filter,
        'language_filter': language_filter,
        'total_submissions': total_submissions,
        'accepted_count': accepted_count,
        'wrong_answer_count': wrong_answer_count,
        'success_rate': success_rate,
    }
    
    return render(request, 'admin/submissions_list.html', context)

@login_required
@user_passes_test(is_admin)
def admin_submission_detail(request, submission_id):
    """Admin page to view detailed submission information"""
    submission = get_object_or_404(Submission, id=submission_id)
    
    context = {
        'submission': submission,
    }
    
    return render(request, 'admin/submission_detail.html', context)