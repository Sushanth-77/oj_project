# oj_project/core/views.py - Simplified version using online-compiler approach
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import Problem, TestCase, Submission
import subprocess
import os
import uuid
from pathlib import Path
import tempfile

def register_user(request):
    """User registration view"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

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
    """User login view"""
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
    """Handle code submission and evaluation"""
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
        messages.error(request, f'An error occurred while processing your submission: {str(e)}')
    
    return redirect('core:problem_detail', short_code=problem.short_code)

def evaluate_submission(submission, language):
    """Evaluate submission against test cases"""
    problem = submission.problem
    test_cases = problem.testcases.all()
    
    if not test_cases.exists():
        return 'AC'  # No test cases, accept by default
    
    try:
        for test_case in test_cases:
            output = run_code(language, submission.code_text, test_case.input)
            
            if output is None:
                return 'RE'  # Runtime error
            
            # Compare output (strip whitespace and normalize line endings)
            expected_output = test_case.output.strip().replace('\r\n', '\n')
            actual_output = output.strip().replace('\r\n', '\n')
            
            if expected_output != actual_output:
                return 'WA'  # Wrong answer
        
        return 'AC'  # All test cases passed
        
    except Exception:
        return 'RE'  # Runtime error

def run_code(language, code, input_data):
    """Execute code using online-compiler approach with temporary directories"""
    try:
        # Create directory structure similar to online-compiler
        project_path = Path(settings.BASE_DIR)
        directories = ["codes", "inputs", "outputs"]

        for directory in directories:
            dir_path = project_path / directory
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)

        codes_dir = project_path / "codes"
        inputs_dir = project_path / "inputs"
        outputs_dir = project_path / "outputs"

        # Generate unique identifier
        unique = str(uuid.uuid4())

        # Create file paths
        code_file_name = f"{unique}.{language}"
        input_file_name = f"{unique}.txt"
        output_file_name = f"{unique}.txt"

        code_file_path = codes_dir / code_file_name
        input_file_path = inputs_dir / input_file_name
        output_file_path = outputs_dir / output_file_name

        # Write code to file
        with open(code_file_path, "w") as code_file:
            code_file.write(code)

        # Write input data to file
        with open(input_file_path, "w") as input_file:
            input_file.write(input_data or '')

        # Create empty output file
        with open(output_file_path, "w") as output_file:
            pass

        # Execute based on language
        if language == "cpp":
            return execute_cpp(code_file_path, input_file_path, output_file_path, codes_dir, unique)
        elif language == "c":
            return execute_c(code_file_path, input_file_path, output_file_path, codes_dir, unique)
        elif language == "py":
            return execute_python(code_file_path, input_file_path, output_file_path)

    except Exception as e:
        print(f"Error in run_code: {str(e)}")
        return None

def execute_cpp(code_file_path, input_file_path, output_file_path, codes_dir, unique):
    """Execute C++ code"""
    try:
        executable_path = codes_dir / unique
        
        # Compile with g++ (fallback to clang++)
        compile_cmd = ["g++", str(code_file_path), "-o", str(executable_path)]
        compile_result = subprocess.run(compile_cmd, capture_output=True, timeout=10)
        
        if compile_result.returncode != 0:
            # Try clang++ as fallback
            compile_cmd = ["clang++", str(code_file_path), "-o", str(executable_path)]
            compile_result = subprocess.run(compile_cmd, capture_output=True, timeout=10)
            
        if compile_result.returncode == 0:
            with open(input_file_path, "r") as input_file:
                with open(output_file_path, "w") as output_file:
                    subprocess.run(
                        [str(executable_path)],
                        stdin=input_file,
                        stdout=output_file,
                        timeout=5
                    )
        else:
            return None  # Compilation failed

        # Read output
        with open(output_file_path, "r") as output_file:
            return output_file.read()
            
    except subprocess.TimeoutExpired:
        return None  # Time limit exceeded
    except Exception:
        return None

def execute_c(code_file_path, input_file_path, output_file_path, codes_dir, unique):
    """Execute C code"""
    try:
        executable_path = codes_dir / unique
        
        # Compile with gcc
        compile_cmd = ["gcc", str(code_file_path), "-o", str(executable_path)]
        compile_result = subprocess.run(compile_cmd, capture_output=True, timeout=10)
        
        if compile_result.returncode == 0:
            with open(input_file_path, "r") as input_file:
                with open(output_file_path, "w") as output_file:
                    subprocess.run(
                        [str(executable_path)],
                        stdin=input_file,
                        stdout=output_file,
                        timeout=5
                    )
        else:
            return None  # Compilation failed

        # Read output
        with open(output_file_path, "r") as output_file:
            return output_file.read()
            
    except subprocess.TimeoutExpired:
        return None  # Time limit exceeded
    except Exception:
        return None

def execute_python(code_file_path, input_file_path, output_file_path):
    """Execute Python code"""
    try:
        with open(input_file_path, "r") as input_file:
            with open(output_file_path, "w") as output_file:
                # Try python3 first, then python
                try:
                    subprocess.run(
                        ["python3", str(code_file_path)],
                        stdin=input_file,
                        stdout=output_file,
                        timeout=5
                    )
                except FileNotFoundError:
                    # Fallback to python
                    subprocess.run(
                        ["python", str(code_file_path)],
                        stdin=input_file,
                        stdout=output_file,
                        timeout=5
                    )

        # Read output
        with open(output_file_path, "r") as output_file:
            return output_file.read()
            
    except subprocess.TimeoutExpired:
        return None  # Time limit exceeded
    except Exception:
        return None

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
        'submissions': user_submissions[:50],  # Limit to 50 recent submissions
        'verdict_filter': verdict_filter,
    }
    return render(request, 'submissions.html', context)