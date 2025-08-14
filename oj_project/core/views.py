# core/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from .models import Problem, Submission, TestCase
from collections import defaultdict
import json

def problems_list(request):
    """Display list of all problems with user progress and search functionality"""
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
    
    # Initialize context data
    context = {
        'problems': problems,
        'search_query': search_query,
        'easy_count': Problem.objects.filter(difficulty='E').count(),
        'medium_count': Problem.objects.filter(difficulty='M').count(),
        'hard_count': Problem.objects.filter(difficulty='H').count(),
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
        all_problems = Problem.objects.all()
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
        
        user_progress = {
            'solved_problems': solved_problems,
            'easy_completed': easy_solved,
            'medium_completed': medium_solved,
            'hard_completed': hard_solved,
        }
        
        context['user_progress'] = user_progress
    else:
        # Default progress for non-authenticated users
        context['user_progress'] = {
            'solved_problems': set(),
            'easy_completed': 0,
            'medium_completed': 0,
            'hard_completed': 0,
        }
    
    return render(request, 'problem_list.html', context)

def get_user_progress(user):
    """Helper function to calculate user progress"""
    if user.is_authenticated:
        # Get all accepted submissions for this user
        accepted_submissions = Submission.objects.filter(
            user=user,
            verdict='AC'
        ).values_list('problem__short_code', flat=True).distinct()
        
        solved_problems = set(accepted_submissions)
        
        # Count solved problems by difficulty
        all_problems = Problem.objects.all()
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
        
        return {
            'solved_problems': solved_problems,
            'easy_completed': easy_solved,
            'medium_completed': medium_solved,
            'hard_completed': hard_solved,
        }
    else:
        # Default progress for non-authenticated users
        return {
            'solved_problems': set(),
            'easy_completed': 0,
            'medium_completed': 0,
            'hard_completed': 0,
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