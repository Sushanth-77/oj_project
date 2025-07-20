# oj_project/core/views.py - Enhanced version with better debugging
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
import shutil

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
    """Handle code submission and evaluation with enhanced debugging"""
    code = request.POST.get('code', '').strip()
    language = request.POST.get('language', 'py')
    
    print(f"DEBUG: Received submission - Language: {language}, Code length: {len(code)}")
    
    if not code:
        messages.error(request, 'Code cannot be empty')
        return redirect('core:problem_detail', short_code=problem.short_code)
    
    # Validate language
    valid_languages = ['py', 'cpp', 'c']
    if language not in valid_languages:
        messages.error(request, 'Invalid language selected')
        return redirect('core:problem_detail', short_code=problem.short_code)
    
    try:
        # Check system prerequisites first
        prereq_check = check_system_prerequisites(language)
        if not prereq_check['success']:
            messages.error(request, f'System Error: {prereq_check["error"]}')
            return redirect('core:problem_detail', short_code=problem.short_code)
        
        # Create submission record
        submission = Submission.objects.create(
            problem=problem,
            user=request.user,
            code_text=code,
            verdict='CE'  # Default to compilation error
        )
        
        print(f"DEBUG: Created submission ID: {submission.id}")
        
        # Test the code against test cases
        verdict = evaluate_submission(submission, language)
        submission.verdict = verdict
        submission.save()
        
        print(f"DEBUG: Final verdict: {verdict}")
        
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
        print(f"DEBUG: Exception in handle_submission: {str(e)}")
        logger.error(f"Submission error for user {request.user.id}: {str(e)}")
        messages.error(request, f'An error occurred while processing your submission: {str(e)}')
    
    return redirect('core:problem_detail', short_code=problem.short_code)

def check_system_prerequisites(language):
    """Check if required compilers/interpreters are available"""
    try:
        if language == 'py':
            # Check for Python
            result = subprocess.run(['python3', '--version'], 
                                 capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                # Try python as fallback
                result = subprocess.run(['python', '--version'], 
                                     capture_output=True, text=True, timeout=5)
                if result.returncode != 0:
                    return {'success': False, 'error': 'Python interpreter not found'}
            return {'success': True, 'version': result.stdout.strip()}
            
        elif language == 'cpp':
            # Check for g++
            result = subprocess.run(['g++', '--version'], 
                                 capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                return {'success': False, 'error': 'g++ compiler not found'}
            return {'success': True, 'version': result.stdout.split('\n')[0]}
            
        elif language == 'c':
            # Check for gcc
            result = subprocess.run(['gcc', '--version'], 
                                 capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                return {'success': False, 'error': 'gcc compiler not found'}
            return {'success': True, 'version': result.stdout.split('\n')[0]}
            
    except subprocess.TimeoutExpired:
        return {'success': False, 'error': 'Compiler check timed out'}
    except Exception as e:
        return {'success': False, 'error': f'System check failed: {str(e)}'}
    
    return {'success': False, 'error': 'Unknown language'}

def evaluate_submission(submission, language):
    """Evaluate submission against test cases with enhanced debugging"""
    problem = submission.problem
    test_cases = problem.testcases.all()
    
    print(f"DEBUG: Evaluating submission for problem {problem.short_code}")
    print(f"DEBUG: Found {test_cases.count()} test cases")
    
    if not test_cases.exists():
        print("DEBUG: No test cases found, accepting by default")
        return 'AC'  # No test cases, accept by default
    
    try:
        for i, test_case in enumerate(test_cases):
            print(f"DEBUG: Running test case {i+1}")
            print(f"DEBUG: Input: {repr(test_case.input[:50])}...")  # Show first 50 chars
            print(f"DEBUG: Expected: {repr(test_case.output[:50])}...")
            
            result = run_code(language, submission.code_text, test_case.input)
            
            print(f"DEBUG: Execution result: {result}")
            
            if result['status'] != 'success':
                error_msg = result.get('error', '').lower()
                print(f"DEBUG: Error occurred: {error_msg}")
                
                if 'timeout' in error_msg or 'time limit exceeded' in error_msg:
                    return 'TLE'
                elif any(keyword in error_msg for keyword in ['compilation', 'syntax', 'compile']):
                    return 'CE'
                else:
                    return 'RE'
            
            # Compare output (strip whitespace and normalize line endings)
            expected_output = test_case.output.strip().replace('\r\n', '\n')
            actual_output = result['output'].strip().replace('\r\n', '\n')
            
            print(f"DEBUG: Expected output: {repr(expected_output)}")
            print(f"DEBUG: Actual output: {repr(actual_output)}")
            
            if expected_output != actual_output:
                print(f"DEBUG: Output mismatch on test case {i+1}")
                return 'WA'
        
        print("DEBUG: All test cases passed")
        return 'AC'
        
    except Exception as e:
        print(f"DEBUG: Exception in evaluate_submission: {str(e)}")
        logger.error(f"Evaluation error: {str(e)}")
        return 'RE'

def run_code(language, code, input_data):
    """Execute code with enhanced debugging and error handling"""
    print(f"DEBUG: Running code in {language}")
    print(f"DEBUG: Code preview: {code[:100]}...")  # First 100 chars
    print(f"DEBUG: Input data: {repr(input_data)}")
    
    try:
        # Create temporary directory for this execution
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            unique_id = str(uuid.uuid4())[:8]  # Shorter ID for debugging
            
            print(f"DEBUG: Using temp directory: {temp_path}")
            print(f"DEBUG: Unique ID: {unique_id}")
            
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
            
            print(f"DEBUG: Code file: {code_file}")
            print(f"DEBUG: Input file: {input_file}")
            
            # Write code and input files
            try:
                with open(code_file, 'w', encoding='utf-8') as f:
                    f.write(code)
                print(f"DEBUG: Successfully wrote code file")
                
                with open(input_file, 'w', encoding='utf-8') as f:
                    f.write(input_data or '')
                print(f"DEBUG: Successfully wrote input file")
            except Exception as e:
                print(f"DEBUG: File write error: {str(e)}")
                return {'status': 'error', 'error': f'File write error: {str(e)}'}
            
            # Execute based on language
            if language == 'py':
                return run_python(code_file, input_file)
            elif language in ['cpp', 'c']:
                return run_cpp_c(code_file, input_file, language)
            
    except Exception as e:
        print(f"DEBUG: Exception in run_code: {str(e)}")
        logger.error(f"Code execution error: {str(e)}")
        return {'status': 'error', 'error': f'Execution error: {str(e)}'}

def run_python(code_file, input_file):
    """Execute Python code with enhanced debugging"""
    print(f"DEBUG: Executing Python file: {code_file}")
    
    try:
        # Try python3 first, then python
        python_cmd = 'python3'
        
        # Test if python3 is available
        test_result = subprocess.run([python_cmd, '--version'], 
                                   capture_output=True, timeout=2)
        if test_result.returncode != 0:
            python_cmd = 'python'
            print(f"DEBUG: python3 not found, trying python")
        
        print(f"DEBUG: Using Python command: {python_cmd}")
        
        with open(input_file, 'r', encoding='utf-8') as input_f:
            print(f"DEBUG: Starting Python execution...")
            
            result = subprocess.run(
                [python_cmd, str(code_file)],
                stdin=input_f,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5,  # 5 second timeout
                text=True,
                cwd=code_file.parent  # Set working directory
            )
        
        print(f"DEBUG: Python execution completed. Return code: {result.returncode}")
        print(f"DEBUG: stdout: {repr(result.stdout)}")
        print(f"DEBUG: stderr: {repr(result.stderr)}")
        
        if result.returncode != 0:
            return {'status': 'error', 'error': f'Runtime error: {result.stderr}'}
        
        return {'status': 'success', 'output': result.stdout}
    
    except subprocess.TimeoutExpired:
        print(f"DEBUG: Python execution timed out")
        return {'status': 'error', 'error': 'Time limit exceeded'}
    except FileNotFoundError as e:
        print(f"DEBUG: Python interpreter not found: {str(e)}")
        return {'status': 'error', 'error': f'Python interpreter not found: {str(e)}'}
    except Exception as e:
        print(f"DEBUG: Exception in run_python: {str(e)}")
        return {'status': 'error', 'error': str(e)}

def run_cpp_c(code_file, input_file, language):
    """Execute C/C++ code with enhanced debugging"""
    print(f"DEBUG: Compiling and executing {language.upper()} file: {code_file}")
    
    try:
        compiler = 'g++' if language == 'cpp' else 'gcc'
        executable = code_file.with_suffix('')
        
        print(f"DEBUG: Using compiler: {compiler}")
        print(f"DEBUG: Output executable: {executable}")
        
        # Check if compiler exists
        compiler_check = subprocess.run([compiler, '--version'], 
                                      capture_output=True, timeout=2)
        if compiler_check.returncode != 0:
            return {'status': 'error', 'error': f'{compiler} compiler not found'}
        
        # Compilation flags
        compile_flags = [
            compiler, str(code_file), '-o', str(executable),
            '-Wall',  # Enable warnings
            '-O1',    # Basic optimization (changed from O2 for compatibility)
        ]
        
        # Add language standard
        if language == 'cpp':
            compile_flags.append('-std=c++14')  # Changed from c++17 for better compatibility
        else:
            compile_flags.append('-std=c99')   # Changed from c11 for better compatibility
        
        print(f"DEBUG: Compile command: {' '.join(compile_flags)}")
        
        # Compile
        compile_result = subprocess.run(
            compile_flags,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            text=True,
            cwd=code_file.parent
        )
        
        print(f"DEBUG: Compilation completed. Return code: {compile_result.returncode}")
        print(f"DEBUG: Compile stdout: {repr(compile_result.stdout)}")
        print(f"DEBUG: Compile stderr: {repr(compile_result.stderr)}")
        
        if compile_result.returncode != 0:
            return {'status': 'error', 'error': f'Compilation failed: {compile_result.stderr}'}
        
        # Check if executable was created
        if not executable.exists():
            return {'status': 'error', 'error': 'Executable not created after compilation'}
        
        print(f"DEBUG: Executable created successfully: {executable}")
        
        # Execute
        with open(input_file, 'r', encoding='utf-8') as input_f:
            print(f"DEBUG: Starting execution...")
            
            exec_result = subprocess.run(
                [str(executable)],
                stdin=input_f,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5,
                text=True,
                cwd=code_file.parent
            )
        
        print(f"DEBUG: Execution completed. Return code: {exec_result.returncode}")
        print(f"DEBUG: Exec stdout: {repr(exec_result.stdout)}")
        print(f"DEBUG: Exec stderr: {repr(exec_result.stderr)}")
        
        if exec_result.returncode != 0:
            return {'status': 'error', 'error': f'Runtime error: {exec_result.stderr}'}
        
        return {'status': 'success', 'output': exec_result.stdout}
    
    except subprocess.TimeoutExpired:
        print(f"DEBUG: {language.upper()} execution timed out")
        return {'status': 'error', 'error': 'Time limit exceeded'}
    except FileNotFoundError as e:
        print(f"DEBUG: Compiler not found: {str(e)}")
        return {'status': 'error', 'error': f'{compiler} compiler not found: {str(e)}'}
    except Exception as e:
        print(f"DEBUG: Exception in run_cpp_c: {str(e)}")
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