# oj_project/core/views.py - Updated with multiple test cases support
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
import shutil

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
    """
    Evaluate submission against both database test cases and file-based test cases
    """
    problem = submission.problem
    
    try:
        # Phase 1: Evaluate visible test cases from database (if any)
        visible_test_cases = problem.testcases.filter(is_hidden=False) if hasattr(problem.testcases.first(), 'is_hidden') else problem.testcases.all()
        
        if visible_test_cases.exists():
            print(f"Phase 1: Evaluating {visible_test_cases.count()} visible test cases from database...")
            for i, test_case in enumerate(visible_test_cases, 1):
                print(f"\n=== Testing visible test case {i} ===")
                print(f"Input: {repr(test_case.input)}")
                print(f"Expected: {repr(test_case.output)}")
                
                output = run_code(language, submission.code_text, test_case.input)
                print(f"Raw output: {repr(output)}")
                
                if output is None:
                    print("Runtime error in visible test case")
                    return 'RE'
                
                # Enhanced output comparison
                expected_output = test_case.output.strip().replace('\r\n', '\n').replace('\r', '\n')
                actual_output = output.strip().replace('\r\n', '\n').replace('\r', '\n')
                
                if expected_output != actual_output:
                    print(f"\n!!! MISMATCH in visible test case {i} !!!")
                    return 'WA'
                else:
                    print(f"✓ Test case {i} PASSED")
        
        # Phase 2: Evaluate file-based test cases
        file_verdict = evaluate_file_based_test_cases(submission, language)
        if file_verdict != 'AC':
            return file_verdict
            
        print("✓ All test cases passed!")
        return 'AC'
        
    except Exception as e:
        print(f"Exception during evaluation: {str(e)}")
        import traceback
        traceback.print_exc()
        return 'RE'

def evaluate_file_based_test_cases(submission, language):
    """
    Evaluate test cases from input/output files with support for multiple test cases
    """
    problem = submission.problem
    
    try:
        from django.conf import settings
        base_path = Path(settings.BASE_DIR)
    except:
        base_path = Path(".")
    
    input_path = base_path / "inputs" / f"{problem.short_code}.txt"
    output_path = base_path / "outputs" / f"{problem.short_code}.txt"
    
    if not input_path.exists() or not output_path.exists():
        print(f"No test files found for {problem.short_code}")
        print(f"Looking for: {input_path} and {output_path}")
        return 'AC'  # No file tests, consider passed
    
    try:
        # Read all inputs and outputs
        with open(input_path, 'r', encoding='utf-8') as f:
            input_content = f.read().strip()
        
        with open(output_path, 'r', encoding='utf-8') as f:
            output_content = f.read().strip()
        
        print(f"Input file content: {repr(input_content)}")
        print(f"Output file content: {repr(output_content)}")
        
        # Parse test cases - each line in input corresponds to one test case
        input_lines = input_content.split('\n')
        expected_output_lines = output_content.split('\n')
        
        print(f"Found {len(input_lines)} input lines")
        print(f"Found {len(expected_output_lines)} expected output lines")
        
        if len(input_lines) != len(expected_output_lines):
            print(f"ERROR: Mismatch in number of test cases!")
            print(f"Input lines: {len(input_lines)}, Output lines: {len(expected_output_lines)}")
            return 'RE'
        
        # Test each case individually
        for i, (test_input, expected_output) in enumerate(zip(input_lines, expected_output_lines)):
            print(f"\n=== Testing file-based test case {i+1} ===")
            print(f"Input: {repr(test_input.strip())}")
            print(f"Expected: {repr(expected_output.strip())}")
            
            # Run code with this specific input
            actual_output = run_code(language, submission.code_text, test_input.strip())
            
            if actual_output is None:
                print(f"Runtime error in test case {i+1}")
                return 'RE'
            
            # Clean and compare outputs
            expected_clean = expected_output.strip()
            actual_clean = actual_output.strip()
            
            print(f"Actual: {repr(actual_clean)}")
            
            if expected_clean != actual_clean:
                print(f"!!! MISMATCH in test case {i+1} !!!")
                print(f"Expected: '{expected_clean}' (len: {len(expected_clean)})")
                print(f"Actual: '{actual_clean}' (len: {len(actual_clean)})")
                
                # Character-by-character comparison for debugging
                max_len = max(len(expected_clean), len(actual_clean))
                for j in range(max_len):
                    exp_char = expected_clean[j] if j < len(expected_clean) else '<END>'
                    act_char = actual_clean[j] if j < len(actual_clean) else '<END>'
                    if exp_char != act_char:
                        print(f"  First difference at position {j}: Expected {repr(exp_char)}, Got {repr(act_char)}")
                        break
                return 'WA'
            else:
                print(f"✓ Test case {i+1} PASSED")
        
        return 'AC'
        
    except Exception as e:
        print(f"Error evaluating file-based test cases: {str(e)}")
        import traceback
        traceback.print_exc()
        return 'RE'

def run_code(language, code, input_data):
    """Execute code with improved error handling and cleanup"""
    unique = str(uuid.uuid4())
    temp_dir = None
    
    try:
        # Create a temporary directory for this execution
        temp_dir = tempfile.mkdtemp(prefix=f"oj_exec_{unique}_")
        temp_path = Path(temp_dir)
        
        # Create file paths
        if language == 'py':
            code_file_path = temp_path / f"{unique}.py"
        elif language == 'cpp':
            code_file_path = temp_path / f"{unique}.cpp"
        elif language == 'c':
            code_file_path = temp_path / f"{unique}.c"
        
        input_file_path = temp_path / f"{unique}_input.txt"
        output_file_path = temp_path / f"{unique}_output.txt"

        # Write code to file
        with open(code_file_path, "w", encoding='utf-8') as code_file:
            code_file.write(code)

        # Write input data to file
        with open(input_file_path, "w", encoding='utf-8') as input_file:
            input_file.write(input_data if input_data is not None else '')

        # Execute based on language
        if language == "cpp":
            result = execute_cpp_improved(code_file_path, input_file_path, output_file_path, temp_path, unique)
        elif language == "c":
            result = execute_c_improved(code_file_path, input_file_path, output_file_path, temp_path, unique)
        elif language == "py":
            result = execute_python_improved(code_file_path, input_file_path, output_file_path)
        else:
            return None
            
        return result

    except Exception as e:
        print(f"Error in run_code: {str(e)}")
        return None
    finally:
        # Cleanup temporary directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception as cleanup_error:
                print(f"Cleanup error: {cleanup_error}")
                pass

def execute_python_improved(code_file_path, input_file_path, output_file_path):
    """Execute Python code with better error handling"""
    try:
        python_cmd = None
        for cmd in ['python3', 'python']:
            try:
                result = subprocess.run([cmd, '--version'], capture_output=True, timeout=5)
                if result.returncode == 0:
                    python_cmd = cmd
                    break
            except:
                continue
        
        if not python_cmd:
            print("No Python interpreter found")
            return None
        
        print(f"Using Python command: {python_cmd}")
        
        try:
            with open(input_file_path, "r", encoding='utf-8') as input_file:
                with open(output_file_path, "w", encoding='utf-8') as output_file:
                    result = subprocess.run(
                        [python_cmd, str(code_file_path)],
                        stdin=input_file,
                        stdout=output_file,
                        stderr=subprocess.PIPE,
                        timeout=10,
                        text=True,
                        cwd=str(code_file_path.parent)
                    )
                    
                    print(f"Python process return code: {result.returncode}")
                    if result.stderr:
                        print(f"Python stderr: {result.stderr}")
                    
                    if result.returncode != 0:
                        print(f"Python runtime error: {result.stderr}")
                        return None

            # Read output
            with open(output_file_path, "r", encoding='utf-8') as output_file:
                output = output_file.read()
                print(f"Python execution successful, output: '{output}' (length: {len(output)})")
                return output
                
        except subprocess.TimeoutExpired:
            print("Python execution timed out")
            return None
            
    except Exception as e:
        print(f"Python execution error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def execute_cpp_improved(code_file_path, input_file_path, output_file_path, temp_path, unique):
    """Execute C++ code with improved error handling"""
    try:
        executable_path = temp_path / unique
        
        try:
            subprocess.run(["g++", "--version"], capture_output=True, timeout=5)
        except FileNotFoundError:
            print("g++ compiler not found")
            return None
        
        # Compile with g++
        compile_result = subprocess.run(
            ["g++", "-o", str(executable_path), str(code_file_path), "-std=c++17"],
            capture_output=True,
            timeout=15,
            text=True
        )
        
        if compile_result.returncode != 0:
            print(f"C++ compilation error: {compile_result.stderr}")
            return None

        # Execute
        with open(input_file_path, "r", encoding='utf-8') as input_file:
            with open(output_file_path, "w", encoding='utf-8') as output_file:
                result = subprocess.run(
                    [str(executable_path)],
                    stdin=input_file,
                    stdout=output_file,
                    stderr=subprocess.PIPE,
                    timeout=10,
                    text=True
                )
                
                if result.returncode != 0:
                    print(f"C++ runtime error: {result.stderr}")
                    return None

        # Read output
        with open(output_file_path, "r", encoding='utf-8') as output_file:
            return output_file.read()
            
    except subprocess.TimeoutExpired:
        print("C++ execution timed out")
        return None
    except Exception as e:
        print(f"C++ execution error: {str(e)}")
        return None

def execute_c_improved(code_file_path, input_file_path, output_file_path, temp_path, unique):
    """Execute C code with improved error handling"""
    try:
        executable_path = temp_path / unique
        
        try:
            subprocess.run(["gcc", "--version"], capture_output=True, timeout=5)
        except FileNotFoundError:
            print("gcc compiler not found")
            return None
        
        # Compile with gcc
        compile_result = subprocess.run(
            ["gcc", "-o", str(executable_path), str(code_file_path), "-std=c99"],
            capture_output=True,
            timeout=15,
            text=True
        )
        
        if compile_result.returncode == 0:
            # Execute
            with open(input_file_path, "r", encoding='utf-8') as input_file:
                with open(output_file_path, "w", encoding='utf-8') as output_file:
                    result = subprocess.run(
                        [str(executable_path)],
                        stdin=input_file,
                        stdout=output_file,
                        stderr=subprocess.PIPE,
                        timeout=10,
                        text=True
                    )
                    
                    if result.returncode != 0:
                        print(f"C runtime error: {result.stderr}")
                        return None

            # Read output
            with open(output_file_path, "r", encoding='utf-8') as output_file:
                return output_file.read()
        else:
            print(f"C compilation error: {compile_result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        print("C execution timed out")
        return None
    except Exception as e:
        print(f"C execution error: {str(e)}")
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
        'submissions': user_submissions[:50],
        'verdict_filter': verdict_filter,
    }
    return render(request, 'submissions.html', context)