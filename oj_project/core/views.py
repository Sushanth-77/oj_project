# core/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Problem, Submission, TestCase
from collections import defaultdict

def problems_list(request):
    """Display list of all problems with user progress"""
    problems = Problem.objects.all().order_by('difficulty', 'name')
    
    # Initialize context data
    context = {
        'problems': problems,
        'easy_count': problems.filter(difficulty='E').count(),
        'medium_count': problems.filter(difficulty='M').count(),
        'hard_count': problems.filter(difficulty='H').count(),
    }
    
    # If user is authenticated, calculate their progress
    if request.user.is_authenticated:
        # Get all accepted submissions for this user
        accepted_submissions = Submission.objects.filter(
            user=request.user,
            verdict='AC'
        ).values_list('problem__short_code', flat=True).distinct()
        
        solved_problems = set(accepted_submissions)
        
        # Count solved problems by difficulty
        easy_solved = 0
        medium_solved = 0
        hard_solved = 0
        
        for problem in problems:
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

def problem_detail(request, short_code):
    """Display problem details and handle submission"""
    problem = get_object_or_404(Problem, short_code=short_code)
    
    # Get visible test cases (not hidden)
    visible_testcases = problem.testcases.filter(is_hidden=False)
    
    context = {
        'problem': problem,
        'testcases': visible_testcases,
    }
    
    # Handle code submission
    if request.method == 'POST' and request.user.is_authenticated:
        code_text = request.POST.get('code', '').strip()
        language = request.POST.get('language', 'py')
        
        if not code_text:
            messages.error(request, 'Code cannot be empty')
            return render(request, 'problem_detail.html', context)
        
        # For now, we'll create a simple submission without actual code execution
        # In a real system, you'd run the code against test cases here
        
        # Simple mock evaluation - just check if code is not empty
        verdict = 'AC' if len(code_text) > 10 else 'WA'  # Very basic check
        
        # Create submission record
        submission = Submission.objects.create(
            problem=problem,
            user=request.user,
            code_text=code_text,
            language=language,
            verdict=verdict
        )
        
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