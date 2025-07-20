# oj_project/core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Problem, TestCase, Submission
import subprocess
import os
import uuid
from pathlib import Path
from django.conf import settings
import tempfile

def register_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            messages.info(request, 'Username and password are required')
            return redirect("/auth/register/")

        if User.objects.filter(username=username).exists():
            messages.info(request, 'User with this username already exists')
            return redirect("/auth/register/")
        
        User.objects.create_user(username=username, password=password)
        messages.info(request, 'User created successfully. Please login.')
        return redirect('/auth/login/')

    return render(request, 'register.html')

def login_user(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            messages.info(request, 'Username and password are required')
            return redirect('/auth/login/')

        if not User.objects.filter(username=username).exists():
            messages.info(request, 'User with this username does not exist')
            return redirect('/auth/login/')
        
        user = authenticate(username=username, password=password)

        if user is None:
            messages.info(request, 'Invalid password')
            return redirect('/auth/login/')
        
        login(request, user)
        messages.info(request, 'Login successful')
        return redirect('/problems/')  # Redirect to problems list after login
    
    return render(request, 'login.html')

def logout_user(request):
    logout(request)
    messages.info(request,'logout successful')
    return redirect('/auth/login/')

# Problem related views
def problems_list(request):
    """Display list of all problems"""
    problems = Problem.objects.all().order_by('id')
    return render(request, 'problem_list.html', {'problems': problems})

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
        )[:5]  # Show last 5 submissions
    
    context = {
        'problem': problem,
        'user_submissions': user_submissions,
    }
    return render(request, 'problem_detail.html', context)

@login_required
def handle_submission(request, problem):
    """Handle code submission and evaluation"""
    code = request.POST.get('code', '').strip()
    language = request.POST.get('language', 'py')
    
    if not code:
        messages.error(request, 'Code cannot be empty')
        return redirect('problem_detail', short_code=problem.short_code)
    
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
        'AC': 'Accepted! Great job!',
        'WA': 'Wrong Answer. Please check your logic.',
        'TLE': 'Time Limit Exceeded. Optimize your solution.',
        'RE': 'Runtime Error. Check for array bounds, division by zero, etc.',
        'CE': 'Compilation Error. Please check your syntax.',
    }
    
    if verdict == 'AC':
        messages.success(request, verdict_messages[verdict])
    else:
        messages.error(request, verdict_messages[verdict])
    
    return redirect('problem_detail', short_code=problem.short_code)

def evaluate_submission(submission, language):
    """Evaluate submission against test cases"""
    problem = submission.problem
    test_cases = problem.testcases.all()
    
    if not test_cases:
        return 'AC'  # No test cases, accept by default
    
    for test_case in test_cases:
        result = run_code(language, submission.code_text, test_case.input)
        
        if result['status'] != 'success':
            if 'timeout' in result.get('error', '').lower():
                return 'TLE'
            else:
                return 'RE'
        
        # Compare output (strip whitespace for comparison)
        expected_output = test_case.output.strip()
        actual_output = result['output'].strip()
        
        if expected_output != actual_output:
            return 'WA'
    
    return 'AC'

def run_code(language, code, input_data):
    """Execute code with given input and return result"""
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
            with open(code_file, 'w') as f:
                f.write(code)
            
            with open(input_file, 'w') as f:
                f.write(input_data or '')
            
            # Execute based on language
            if language == 'py':
                return run_python(code_file, input_file)
            elif language in ['cpp', 'c']:
                return run_cpp_c(code_file, input_file, language)
            
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def run_python(code_file, input_file):
    """Execute Python code"""
    try:
        with open(input_file, 'r') as input_f:
            result = subprocess.run(
                ['python3', str(code_file)],
                stdin=input_f,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5,  # 5 second timeout
                text=True
            )
        
        if result.returncode != 0:
            return {'status': 'error', 'error': result.stderr}
        
        return {'status': 'success', 'output': result.stdout}
    
    except subprocess.TimeoutExpired:
        return {'status': 'error', 'error': 'timeout'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def run_cpp_c(code_file, input_file, language):
    """Execute C/C++ code"""
    try:
        compiler = 'g++' if language == 'cpp' else 'gcc'
        executable = code_file.with_suffix('')
        
        # Compile
        compile_result = subprocess.run(
            [compiler, str(code_file), '-o', str(executable)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            text=True
        )
        
        if compile_result.returncode != 0:
            return {'status': 'error', 'error': f'Compilation failed: {compile_result.stderr}'}
        
        # Execute
        with open(input_file, 'r') as input_f:
            exec_result = subprocess.run(
                [str(executable)],
                stdin=input_f,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5,
                text=True
            )
        
        if exec_result.returncode != 0:
            return {'status': 'error', 'error': exec_result.stderr}
        
        return {'status': 'success', 'output': exec_result.stdout}
    
    except subprocess.TimeoutExpired:
        return {'status': 'error', 'error': 'timeout'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

@login_required
def submissions_list(request):
    """Display user's submissions"""
    user_submissions = Submission.objects.filter(user=request.user).select_related('problem')
    return render(request, 'submissions_list.html', {'submissions': user_submissions})