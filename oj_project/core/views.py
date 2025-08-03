# core/views.py - Updated with separated concerns
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Problem, Submission
from compiler.views import evaluate_submission

def problems_list(request):
    """Display list of all problems with statistics"""
    problems = Problem.objects.all().order_by('id')
    
    context = {
        'problems': problems,
        'easy_count': problems.filter(difficulty='E').count(),
        'medium_count': problems.filter(difficulty='M').count(),
        'hard_count': problems.filter(difficulty='H').count(),
    }
    return render(request, 'problem_list.html', context)

def problem_detail(request, short_code):
    """Display problem details and handle code submission"""
    problem = get_object_or_404(Problem, short_code=short_code)
    
    if request.method == 'POST' and request.user.is_authenticated:
        return handle_submission(request, problem)
    
    # Get user's previous submissions for this problem
    user_submissions = []
    if request.user.is_authenticated:
        user_submissions = Submission.objects.filter(
            problem=problem, 
            user=request.user
        ).order_by('-submitted')[:5]
    
    context = {
        'problem': problem,
        'user_submissions': user_submissions,
    }
    return render(request, 'problem_detail.html', context)

@login_required
def handle_submission(request, problem):
    """Handle code submission and evaluation - UPDATED"""
    code = request.POST.get('code', '').strip()
    language = request.POST.get('language', 'py')
    
    if not code:
        messages.error(request, 'Code cannot be empty')
        return redirect('core:problem_detail', short_code=problem.short_code)
    
    # Validate language
    valid_languages = ['py', 'cpp', 'c']
    if language not in valid_languages:
        messages.error(request, 'Invalid language selected')
        return redirect('core:problem_detail', short_code=problem.short_code)
    
    try:
        # Create submission record with language info
        submission = Submission.objects.create(
            problem=problem,
            user=request.user,
            code_text=code,
            language=language,  # Store language in the model
            verdict='CE'  # Default to compilation error
        )
        
        # Test the code against test cases using compiler app
        verdict = evaluate_submission(submission, language)
        submission.verdict = verdict
        submission.save()
        
        # Add message based on verdict
        verdict_messages = {
            'AC': 'Accepted! Great job! 🎉',
            'WA': 'Wrong Answer. Please check your logic and try again.',
            'TLE': 'Time Limit Exceeded. Your solution is too slow.',
            'RE': 'Runtime Error. Check for array bounds, division by zero, etc.',
            'CE': 'Compilation Error. Please check your syntax.',
        }
        
        if verdict == 'AC':
            messages.success(request, verdict_messages[verdict])
        else:
            messages.error(request, verdict_messages[verdict])
            
    except Exception as e:
        messages.error(request, f'An error occurred while processing your submission: {str(e)}')
    
    return redirect('core:problem_detail', short_code=problem.short_code)

@login_required
def submissions_list(request):
    """Display user's submissions with filtering"""
    user_submissions = Submission.objects.filter(
        user=request.user
    ).select_related('problem').order_by('-submitted')
    
    # Add filtering by verdict if requested
    verdict_filter = request.GET.get('verdict')
    if verdict_filter:
        user_submissions = user_submissions.filter(verdict=verdict_filter)
    
    context = {
        'submissions': user_submissions[:50],
        'verdict_filter': verdict_filter,
    }
    return render(request, 'submissions.html', context)