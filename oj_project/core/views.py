# oj_project/core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from .models import Problem, TestCase, Submission
import subprocess
import os
import uuid
from pathlib import Path
from django.conf import settings
import tempfile
import logging

# Set up logging
logger = logging.getLogger(__name__)

def register_user(request):
    """User registration view with improved validation"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        # Improved validation
        if not username or not password:
            messages.error(request, 'Username and password are required')
            return redirect("/auth/register/")

        if len(username) < 3:
            messages.error(request, 'Username must be at least 3 characters long')
            return redirect("/auth/register/")
            
        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long')
            return redirect("/auth/register/")

        if User.objects.filter(username=username).exists():
            messages.error(request, 'User with this username already exists')
            return redirect("/auth/register/")
        
        try:
            User.objects.create_user(username=username, password=password)
            messages.success(request, 'User created successfully. Please login.')
            return redirect('/auth/login/')
        except Exception as e:
            messages.error(request, f'Error creating user: {str(e)}')
            return redirect("/auth/register/")

    return render(request, 'register.html')

def login_user(request):
    """Improved login view with better error handling"""
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            messages.error(request, 'Username and password are required')
            return redirect('/auth/login/')

        if not User.objects.filter(username=username).exists():
            messages.error(request, 'User with this username does not exist')
            return redirect('/auth/login/')
        
        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, 'Invalid password')
            return redirect('/auth/login/')
        
        login(request, user)
        messages.success(request, f'Welcome back, {user.username}!')
        return redirect('/problems/')
    
    return render(request, 'login.html')

def logout_user(request):
    """Logout user and redirect"""
    logout(request)
    messages.success(request, 'Logged out successfully')
    return redirect('/auth/login/')

def problems_list(request):
    """Display list of all problems with statistics"""
    problems = Problem.objects.all().order_by('id')
    
    # Calculate statistics
    stats = {
        'total': problems.count(),
        'easy': problems.filter(difficulty='E').count(),
        'medium': problems.filter(difficulty='M').count(),
        'hard': problems.filter(difficulty='H').count(),
    }
    
    context = {
        'problems': problems,
        'easy_count': stats['easy'],
        'medium_count': stats['medium'],
        'hard_count': stats['hard'],
    }
    return render(request, 'problem_list.html', context)  # Using the better template

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
        ).order_by('-submitted')[:5]  # Show last 5 submissions
    
    context = {
        'problem': problem,
        'user_submissions': user_submissions,
    }
    return render(request, 'problem_detail.html', context)

@login_required
def handle_submission(request, problem):
    """Handle code submission and evaluation with better error handling"""
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
        # Create submission record
        submission = Submission.objects.create(
            problem=problem,
            user=request.user,
            code_text=code,
            verdict='CE'  # Default to compilation error
        )
        
        # Test the code against test cases
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
        logger.error(f"Submission error for user {request.user.id}: {str(e)}")
        messages.error(request, 'An error occurred while processing your submission.')
    
    return redirect('core:problem_detail', short_code=problem.short_code)

def evaluate_submission(submission, language):
    """Evaluate submission against test cases with improved error handling"""
    problem = submission.problem
    test_cases = problem.testcases.all()
    
    if not test_cases.exists():
        logger.warning(f"No test cases found for problem {problem.short_code}")
        return 'AC'  # No test cases, accept by default
    
    try:
        for test_case in test_cases:
            result = run_code(language, submission.code_text, test_case.input)
            
            if result['status'] != 'success':
                error_msg = result.get('error', '').lower()
                if 'timeout' in error_msg:
                    return 'TLE'
                elif 'compilation' in error_msg or 'syntax' in error_msg:
                    return 'CE'
                else:
                    return 'RE'
            
            # Compare output (strip whitespace and normalize line endings)
            expected_output = test_case.output.strip().replace('\r\n', '\n')
            actual_output = result['output'].strip().replace('\r\n', '\n')
            
            if expected_output != actual_output:
                return 'WA'
        
        return 'AC'
        
    except Exception as e:
        logger.error(f"Evaluation error: {str(e)}")
        return 'RE'

def run_code(language, code, input_data):
    """Execute code with given input and return result - improved security and error handling"""
    try:
        # Create temporary directory for this execution
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            unique_id = str(uuid.uuid4())
            
            # File extensions for different languages
            extensions = {
                'py': 'py',
                'cpp': 'cpp',
                'c': 'c'
            }
            
            if language not in extensions:
                return {'status': 'error', 'error': 'Unsupported language'}
            
            code_file = temp_path / f"{unique_id}.{extensions[language]}"
            input_file = temp_path / f"{unique_id}_input.txt"
            
            # Write code and input files
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            with open(input_file, 'w', encoding='utf-8') as f:
                f.write(input_data or '')
            
            # Execute based on language
            if language == 'py':
                return run_python(code_file, input_file)
            elif language in ['cpp', 'c']:
                return run_cpp_c(code_file, input_file, language)
            
    except Exception as e:
        logger.error(f"Code execution error: {str(e)}")
        return {'status': 'error', 'error': f'Execution error: {str(e)}'}

def run_python(code_file, input_file):
    """Execute Python code with improved security"""
    try:
        with open(input_file, 'r', encoding='utf-8') as input_f:
            # Use python3 explicitly and add security restrictions
            result = subprocess.run(
                ['python3', '-S', str(code_file)],  # -S disables site module
                stdin=input_f,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5,  # 5 second timeout
                text=True,
                env={'PATH': '/usr/bin:/bin'}  # Restrict PATH
            )
        
        if result.returncode != 0:
            return {'status': 'error', 'error': f'Runtime error: {result.stderr}'}
        
        return {'status': 'success', 'output': result.stdout}
    
    except subprocess.TimeoutExpired:
        return {'status': 'error', 'error': 'Time limit exceeded'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def run_cpp_c(code_file, input_file, language):
    """Execute C/C++ code with improved compilation and security"""
    try:
        compiler = 'g++' if language == 'cpp' else 'gcc'
        executable = code_file.with_suffix('')
        
        # Improved compilation flags
        compile_flags = [
            compiler, str(code_file), '-o', str(executable),
            '-Wall',  # Enable warnings
            '-O2',    # Optimization
            '-std=c++17' if language == 'cpp' else '-std=c11',
        ]
        
        # Compile
        compile_result = subprocess.run(
            compile_flags,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            text=True
        )
        
        if compile_result.returncode != 0:
            return {'status': 'error', 'error': f'Compilation failed: {compile_result.stderr}'}
        
        # Execute
        with open(input_file, 'r', encoding='utf-8') as input_f:
            exec_result = subprocess.run(
                [str(executable)],
                stdin=input_f,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5,
                text=True
            )
        
        if exec_result.returncode != 0:
            return {'status': 'error', 'error': f'Runtime error: {exec_result.stderr}'}
        
        return {'status': 'success', 'output': exec_result.stdout}
    
    except subprocess.TimeoutExpired:
        return {'status': 'error', 'error': 'Time limit exceeded'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

@login_required
def submissions_list(request):
    """Display user's submissions with filtering and pagination"""
    user_submissions = Submission.objects.filter(
        user=request.user
    ).select_related('problem').order_by('-submitted')
    
    # Add filtering by verdict if requested
    verdict_filter = request.GET.get('verdict')
    if verdict_filter:
        user_submissions = user_submissions.filter(verdict=verdict_filter)
    
    context = {
        'submissions': user_submissions[:50],  # Limit to 50 recent submissions
        'verdict_filter': verdict_filter,
    }
    return render(request, 'submissions.html', context)