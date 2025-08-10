# core/views.py - Fixed version with error handling
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Problem, Submission
from compiler.views import evaluate_submission

def problems_list(request):
    """Display list of all problems with statistics and user progress"""
    try:
        problems = Problem.objects.all().order_by('id')
        
        # Basic problem counts with error handling
        easy_count = problems.filter(difficulty='E').count()
        medium_count = problems.filter(difficulty='M').count()
        hard_count = problems.filter(difficulty='H').count()
        
        # Initialize user progress
        user_progress = {
            'easy_completed': 0,
            'medium_completed': 0,
            'hard_completed': 0,
            'solved_problems': set()
        }
        
        # Calculate user progress if authenticated
        if request.user.is_authenticated:
            try:
                # Get all problems the user has solved (AC verdict)
                solved_submissions = Submission.objects.filter(
                    user=request.user,
                    verdict='AC'
                ).values_list('problem__short_code', 'problem__difficulty').distinct()
                
                solved_problems = set()
                for short_code, difficulty in solved_submissions:
                    if short_code:  # Check for None values
                        solved_problems.add(short_code)
                        if difficulty == 'E':
                            user_progress['easy_completed'] += 1
                        elif difficulty == 'M':
                            user_progress['medium_completed'] += 1
                        elif difficulty == 'H':
                            user_progress['hard_completed'] += 1
                
                user_progress['solved_problems'] = solved_problems
            except Exception as e:
                # Log error but don't break the page
                print(f"Error calculating user progress: {e}")
        
        context = {
            'problems': problems,
            'easy_count': easy_count,
            'medium_count': medium_count,
            'hard_count': hard_count,
            'user_progress': user_progress,
        }
        return render(request, 'core/problem_list.html', context)
    
    except Exception as e:
        messages.error(request, 'An error occurred while loading problems.')
        print(f"Error in problems_list view: {e}")
        return render(request, 'core/problem_list.html', {
            'problems': [],
            'easy_count': 0,
            'medium_count': 0,
            'hard_count': 0,
            'user_progress': {
                'easy_completed': 0,
                'medium_completed': 0,
                'hard_completed': 0,
                'solved_problems': set()
            },
        })

def problem_detail(request, short_code):
    """Display problem details and handle code submission"""
    try:
        problem = get_object_or_404(Problem, short_code=short_code)
        
        if request.method == 'POST' and request.user.is_authenticated:
            return handle_submission(request, problem)
        
        # Get user's previous submissions for this problem
        user_submissions = []
        user_solved = False
        
        if request.user.is_authenticated:
            try:
                user_submissions = Submission.objects.filter(
                    problem=problem, 
                    user=request.user
                ).order_by('-submitted')[:5]
                
                # Check if user has solved this problem
                user_solved = Submission.objects.filter(
                    problem=problem,
                    user=request.user,
                    verdict='AC'
                ).exists()
            except Exception as e:
                print(f"Error fetching user submissions: {e}")
        
        context = {
            'problem': problem,
            'user_submissions': user_submissions,
            'user_solved': user_solved,
        }
        return render(request, 'core/problem_detail.html', context)
    
    except Problem.DoesNotExist:
        messages.error(request, 'Problem not found.')
        return redirect('core:problems_list')
    except Exception as e:
        messages.error(request, 'An error occurred while loading the problem.')
        print(f"Error in problem_detail view: {e}")
        return redirect('core:problems_list')

@login_required
def handle_submission(request, problem):
    """Handle code submission and evaluation"""
    try:
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
        
        # Create submission record with language info
        submission = Submission.objects.create(
            problem=problem,
            user=request.user,
            code_text=code,
            language=language,  # Make sure this field exists in your Submission model
            verdict='CE'  # Default to compilation error
        )
        
        # Test the code against test cases using compiler app
        try:
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
            
            message = verdict_messages.get(verdict, f'Submission processed with verdict: {verdict}')
            
            if verdict == 'AC':
                messages.success(request, message)
            else:
                messages.error(request, message)
        
        except Exception as eval_error:
            submission.verdict = 'CE'
            submission.save()
            messages.error(request, f'Error evaluating submission: {str(eval_error)}')
            print(f"Evaluation error: {eval_error}")
            
    except Exception as e:
        messages.error(request, 'An error occurred while processing your submission.')
        print(f"Error in handle_submission: {e}")
    
    return redirect('core:problem_detail', short_code=problem.short_code)

@login_required
def submissions_list(request):
    """Display user's submissions with filtering and statistics"""
    try:
        user_submissions = Submission.objects.filter(
            user=request.user
        ).select_related('problem').order_by('-submitted')
        
        # Add filtering by verdict if requested
        verdict_filter = request.GET.get('verdict')
        if verdict_filter and verdict_filter in ['AC', 'WA', 'TLE', 'RE', 'CE']:
            user_submissions = user_submissions.filter(verdict=verdict_filter)
        
        # Calculate user statistics
        stats = {
            'total_submissions': user_submissions.count(),
            'accepted': user_submissions.filter(verdict='AC').count(),
            'wrong_answer': user_submissions.filter(verdict='WA').count(),
            'time_limit': user_submissions.filter(verdict='TLE').count(),
            'runtime_error': user_submissions.filter(verdict='RE').count(),
            'compilation_error': user_submissions.filter(verdict='CE').count(),
        }
        
        # Calculate solved problems count by difficulty
        solved_problems = Submission.objects.filter(
            user=request.user,
            verdict='AC'
        ).values('problem__difficulty').annotate(
            count=Count('problem', distinct=True)
        )
        
        difficulty_stats = {'E': 0, 'M': 0, 'H': 0}
        for item in solved_problems:
            difficulty = item.get('problem__difficulty')
            if difficulty in difficulty_stats:
                difficulty_stats[difficulty] = item['count']
        
        context = {
            'submissions': user_submissions[:50],  # Limit to 50 for performance
            'verdict_filter': verdict_filter,
            'stats': stats,
            'difficulty_stats': difficulty_stats,
        }
        return render(request, 'core/submissions.html', context)
    
    except Exception as e:
        messages.error(request, 'An error occurred while loading submissions.')
        print(f"Error in submissions_list view: {e}")
        return render(request, 'core/submissions.html', {
            'submissions': [],
            'verdict_filter': None,
            'stats': {
                'total_submissions': 0,
                'accepted': 0,
                'wrong_answer': 0,
                'time_limit': 0,
                'runtime_error': 0,
                'compilation_error': 0,
            },
            'difficulty_stats': {'E': 0, 'M': 0, 'H': 0},
        })