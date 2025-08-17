# core/views.py - RENDER-OPTIMIZED VERSION with async submission handling
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
import threading
from concurrent.futures import ThreadPoolExecutor
import logging

# Import the evaluation function from compiler app
from compiler.views import evaluate_submission

from .admin_utils import check_admin_access

# Add these imports at the top of your views.py
from django.contrib.auth.models import User
from django.db.models import Count, Q
from datetime import datetime, timedelta

# Set up logging
logger = logging.getLogger(__name__)

# Global thread pool for async submission handling
submission_executor = ThreadPoolExecutor(max_workers=2)

# Helper function for admin check
def is_admin(user):
    """Check if user is admin/superuser"""
    return user.is_superuser or user.is_staff

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

def problems_list(request):
    """Display list of all problems with search and filtering"""
    search_query = request.GET.get('search', '').strip()
    difficulty_filter = request.GET.get('difficulty', '')
    
    # Base queryset
    problems = Problem.objects.all()
    
    # Apply search filter
    if search_query:
        problems = problems.filter(
            Q(name__icontains=search_query) |
            Q(short_code__icontains=search_query) |
            Q(statement__icontains=search_query)
        )
    
    # Apply difficulty filter
    if difficulty_filter:
        problems = problems.filter(difficulty=difficulty_filter)
    
    # Order by difficulty and name
    problems = problems.order_by('difficulty', 'name')
    
    # Get user progress for authenticated users
    user_progress = get_user_progress(request.user)
    
    # Count problems by difficulty
    all_problems = Problem.objects.all()
    easy_count = all_problems.filter(difficulty='E').count()
    medium_count = all_problems.filter(difficulty='M').count()
    hard_count = all_problems.filter(difficulty='H').count()
    total_count = all_problems.count()
    
    context = {
        'problems': problems,
        'search_query': search_query,
        'difficulty_filter': difficulty_filter,
        'user_progress': user_progress,
        'easy_count': easy_count,
        'medium_count': medium_count,
        'hard_count': hard_count,
        'total_problems_count': total_count,
    }
    
    return render(request, 'problem_list.html', context)

def async_evaluate_submission(submission_id, language):
    """Async evaluation function that runs in background"""
    try:
        submission = Submission.objects.get(id=submission_id)
        logger.info(f"🔄 Background evaluation started for submission {submission_id}")
        
        # Run evaluation
        verdict = evaluate_submission(submission, language)
        
        # Update submission
        submission.verdict = verdict
        submission.save()
        
        logger.info(f"✅ Background evaluation completed for submission {submission_id}: {verdict}")
        
    except Exception as e:
        logger.error(f"💥 Background evaluation failed for submission {submission_id}: {str(e)}")
        try:
            submission = Submission.objects.get(id=submission_id)
            submission.verdict = 'RE'
            submission.save()
        except:
            pass

def problem_detail(request, short_code):
    """Display problem details and handle submission with ASYNC processing"""
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
        'problems': all_problems,
        'easy_count': Problem.objects.filter(difficulty='E').count(),
        'medium_count': Problem.objects.filter(difficulty='M').count(),
        'hard_count': Problem.objects.filter(difficulty='H').count(),
    }
    
    # Handle code submission with ASYNC processing
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
        
        # Basic validation
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
        
        # Create submission record immediately
        submission = Submission.objects.create(
            problem=problem,
            user=request.user,
            code_text=code_text,
            language=db_language,
            verdict='PE'  # Pending evaluation
        )
        
        logger.info(f"🆕 Created submission {submission.id} for user {request.user.username}")
        
        # Handle different actions
        if action == 'ai_review_only':
            # For AI review, just set AC and return immediately
            submission.verdict = 'AC'
            submission.save()
            
            return JsonResponse({
                'success': True,
                'submission_id': submission.id,
                'message': 'Submission ready for AI review'
            })
        
        elif action == 'test':
            # For testing, provide immediate feedback but run async evaluation
            messages.info(request, '⏳ Your code is being tested... This may take a moment.')
            
            # Submit for async evaluation
            submission_executor.submit(async_evaluate_submission, submission.id, db_language)
            
            # Redirect immediately - user can check submission status later
            return redirect('core:problem_detail', short_code=short_code)
        
        else:  # submit action
            # For submission, provide immediate feedback and run async evaluation
            messages.info(request, '🚀 Your solution has been submitted and is being evaluated... Check your submissions page for results.')
            
            # Submit for async evaluation
            submission_executor.submit(async_evaluate_submission, submission.id, db_language)
            
            # Redirect immediately
            return redirect('core:problem_detail', short_code=short_code)
    
    return render(request, 'problem_detail.html', context)

@login_required
def submissions_list(request):
    """Display user's submissions with real-time status"""
    submissions = Submission.objects.filter(user=request.user).order_by('-submitted')
    
    context = {
        'submissions': submissions,
    }
    
    return render(request, 'submissions.html', context)

@login_required
def submit_solution(request, short_code):
    """Handle solution submission - redirect to problem detail for processing"""
    return redirect('core:problem_detail', short_code=short_code)

@login_required
def submission_status(request, submission_id):
    """AJAX endpoint to check submission status"""
    try:
        submission = get_object_or_404(Submission, id=submission_id, user=request.user)
        
        return JsonResponse({
            'success': True,
            'status': submission.verdict,
            'status_display': submission.get_verdict_display(),
            'is_pending': submission.verdict == 'PE'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

# ============================
# ADMIN VIEWS
# ============================

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
    """Admin page to add new problems with SMART TEST CASE PARSING from files"""
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
            
            # Handle manual test cases (visible examples)
            test_case_count = 0
            created_visible_test_cases = 0
            
            # Count manual test cases
            for key in request.POST.keys():
                if key.startswith('testcase_input_'):
                    test_case_count += 1
            
            # Create manual test cases
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
                    if not is_hidden:
                        created_visible_test_cases += 1
            
            # Handle file uploads with SMART PARSING
            input_file = request.FILES.get('input_file')
            output_file = request.FILES.get('output_file')
            
            file_test_cases_created = 0
            
            if input_file and output_file:
                try:
                    # Save files to inputs/ and outputs/ directories first
                    from django.conf import settings
                    from pathlib import Path
                    
                    base_dir = Path(settings.BASE_DIR)
                    inputs_dir = base_dir / "inputs"
                    outputs_dir = base_dir / "outputs"
                    
                    # Create directories if they don't exist
                    inputs_dir.mkdir(exist_ok=True)
                    outputs_dir.mkdir(exist_ok=True)
                    
                    # Read file contents for parsing
                    input_content = input_file.read().decode('utf-8', errors='replace')
                    output_content = output_file.read().decode('utf-8', errors='replace')
                    
                    # Reset file pointers and save files
                    input_file.seek(0)
                    output_file.seek(0)
                    
                    # Save input file
                    input_path = inputs_dir / f"{short_code}.txt"
                    with open(input_path, 'wb') as f:
                        for chunk in input_file.chunks():
                            f.write(chunk)
                    
                    # Save output file
                    output_path = outputs_dir / f"{short_code}.txt"
                    with open(output_path, 'wb') as f:
                        for chunk in output_file.chunks():
                            f.write(chunk)
                    
                    # Use Smart Parser to parse the test cases from files
                    from compiler.views import SmartTestCaseParser
                    parser = SmartTestCaseParser()
                    
                    logger.info(f"📁 Parsing test cases from uploaded files for {short_code}")
                    logger.info(f"Input content length: {len(input_content)}")
                    logger.info(f"Output content length: {len(output_content)}")
                    
                    parsed_test_cases = parser.parse_test_cases(input_content, output_content)
                    
                    if parsed_test_cases:
                        logger.info(f"🎯 Smart Parser found {len(parsed_test_cases)} test cases")
                        
                        # Create hidden test cases from parsed data
                        for i, test_case in enumerate(parsed_test_cases, 1):
                            TestCase.objects.create(
                                problem=problem,
                                input=test_case['input'],
                                output=test_case['output'],
                                is_hidden=True,  # File-based test cases are hidden by default
                                order=created_visible_test_cases + i  # Order after manual test cases
                            )
                            file_test_cases_created += 1
                        
                        logger.info(f"✅ Created {file_test_cases_created} hidden test cases from files")
                        
                        messages.success(request, 
                            f'Problem "{name}" created successfully! '
                            f'📁 Files saved and parsed: {len(parsed_test_cases)} hidden test cases created. '
                            f'📝 Manual test cases: {created_visible_test_cases} visible. '
                            f'🎯 Total: {created_visible_test_cases + file_test_cases_created} test cases.')
                    else:
                        logger.warning(f"⚠️ Smart Parser could not parse test cases from files")
                        messages.warning(request, 
                            f'Problem created and files saved, but no test cases could be parsed from files. '
                            f'Created {created_visible_test_cases} visible test cases from manual input. '
                            f'You may need to check the file format.')
                    
                except Exception as e:
                    logger.error(f"💥 Error processing files: {str(e)}")
                    messages.warning(request, 
                        f'Problem created with {created_visible_test_cases} manual test cases, '
                        f'but file processing failed: {str(e)}')
            else:
                messages.success(request, 
                    f'Problem "{name}" created successfully with {created_visible_test_cases} visible test cases!')
            
            return redirect('core:admin_problems_list')
            
        except Exception as e:
            logger.error(f"💥 Error creating problem: {str(e)}")
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
    
    problems = problems.order_by('-id')
    
    # Calculate difficulty counts
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
            
            # Check if short code conflicts
            if Problem.objects.filter(short_code=problem.short_code).exclude(id=problem.id).exists():
                messages.error(request, f'Another problem with short code "{problem.short_code}" already exists!')
                return render(request, 'admin/edit_problem.html', {'problem': problem})
            
            problem.save()
            
            # Update test cases
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
    
    # Limit for performance
    submissions = submissions[:100]
    
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
        'users': users_with_stats[:50],
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
    
    # Popular problems
    popular_problems = Problem.objects.annotate(
        submission_count=Count('submission')
    ).order_by('-submission_count')[:10]
    
    # Daily submission trend
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