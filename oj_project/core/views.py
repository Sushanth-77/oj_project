# oj_project/core/views.py - Fixed version with runtime error issues resolved
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
import shutil  # THIS WAS MISSING - CRITICAL FOR CLEANUP

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
    Two-phase evaluation: 
    1. First evaluate visible test cases
    2. Only if all visible pass, evaluate hidden test cases
    """
    problem = submission.problem
    
    # Get visible test cases from database
    visible_test_cases = problem.testcases.filter(is_hidden=False) if hasattr(problem.testcases.first(), 'is_hidden') else problem.testcases.all()
    
    try:
        # Phase 1: Evaluate visible test cases
        print(f"Phase 1: Evaluating {visible_test_cases.count()} visible test cases...")
        for i, test_case in enumerate(visible_test_cases, 1):
            print(f"Testing visible test case {i}")
            print(f"Input: {repr(test_case.input)}")
            print(f"Expected: {repr(test_case.output)}")
            
            output = run_code(language, submission.code_text, test_case.input)
            print(f"Actual: {repr(output)}")
            
            if output is None:
                print("Runtime error in visible test case")
                return 'RE'
            
            # Compare output - FIXED: More robust comparison
            expected_output = test_case.output.strip().replace('\r\n', '\n').replace('\r', '\n')
            actual_output = output.strip().replace('\r\n', '\n').replace('\r', '\n')
            
            if expected_output != actual_output:
                print(f"Wrong answer in visible test case {i}")
                print(f"Expected (repr): {repr(expected_output)}")
                print(f"Actual (repr): {repr(actual_output)}")
                return 'WA'
        
        print("All visible test cases passed!")
        
        # Phase 2: Evaluate hidden test cases from file
        hidden_verdict = evaluate_hidden_test_cases(submission, language)
        if hidden_verdict != 'AC':
            return hidden_verdict
            
        print("All hidden test cases passed!")
        return 'AC'
        
    except Exception as e:
        print(f"Exception during evaluation: {str(e)}")
        return 'RE'

def evaluate_hidden_test_cases(submission, language):
    """
    Evaluate hidden test cases from input file
    """
    problem = submission.problem
    
    # FIXED: Better path handling
    try:
        # Use Django's BASE_DIR or settings to get proper paths
        from django.conf import settings
        base_path = Path(settings.BASE_DIR)
    except:
        base_path = Path(".")
    
    input_path = base_path / "inputs" / f"{problem.short_code}.txt"
    output_path = base_path / "outputs" / f"{problem.short_code}.txt"
    
    if not input_path.exists() or not output_path.exists():
        print(f"No hidden test files found for {problem.short_code}")
        print(f"Looking for: {input_path} and {output_path}")
        return 'AC'  # No hidden tests, consider passed
    
    try:
        # Read expected outputs
        with open(output_path, 'r', encoding='utf-8') as f:
            expected_outputs = f.read().strip().split('\n')
        
        # Read inputs and process them
        with open(input_path, 'r', encoding='utf-8') as f:
            input_lines = f.read().strip().split('\n')
        
        # FIXED: Better handling of multiple test cases
        test_case_count = len([line for line in input_lines if line.strip()])
        expected_count = len([out for out in expected_outputs if out.strip()])
        
        print(f"Found {test_case_count} hidden test cases")
        print(f"Expected {expected_count} outputs")
        
        # Run the code with all hidden inputs at once
        all_hidden_input = '\n'.join(input_lines)
        output = run_code(language, submission.code_text, all_hidden_input)
        
        if output is None:
            print("Runtime error in hidden test cases")
            return 'RE'
        
        # FIXED: Better output comparison
        actual_outputs = [line.strip() for line in output.strip().split('\n') if line.strip()]
        expected_clean = [line.strip() for line in expected_outputs if line.strip()]
        
        print(f"Expected outputs: {expected_clean}")
        print(f"Actual outputs: {actual_outputs}")
        
        # Compare each output
        if len(actual_outputs) != len(expected_clean):
            print(f"Output count mismatch: expected {len(expected_clean)}, got {len(actual_outputs)}")
            return 'WA'
        
        for i, (expected, actual) in enumerate(zip(expected_clean, actual_outputs)):
            if expected != actual:
                print(f"Hidden test case {i+1} failed: expected '{expected}', got '{actual}'")
                return 'WA'
        
        return 'AC'
        
    except Exception as e:
        print(f"Error evaluating hidden test cases: {str(e)}")
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

        # Write input data to file - FIXED: Handle None input
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
                pass  # Ignore cleanup errors

def execute_python_improved(code_file_path, input_file_path, output_file_path):
    """Execute Python code with better error handling"""
    try:
        # FIXED: Better Python executable detection
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
        
        # First, try to run the code and capture any compilation errors
        syntax_check = subprocess.run(
            [python_cmd, "-m", "py_compile", str(code_file_path)],
            capture_output=True,
            timeout=5,
            text=True
        )
        
        if syntax_check.returncode != 0:
            print(f"Python syntax error: {syntax_check.stderr}")
            return None  # Compilation error
        
        # Now execute the code
        with open(input_file_path, "r", encoding='utf-8') as input_file:
            with open(output_file_path, "w", encoding='utf-8') as output_file:
                result = subprocess.run(
                    [python_cmd, str(code_file_path)],
                    stdin=input_file,
                    stdout=output_file,
                    stderr=subprocess.PIPE,
                    timeout=10,  # FIXED: Increased timeout
                    text=True
                )
                
                if result.returncode != 0:
                    print(f"Python runtime error: {result.stderr}")
                    return None

        # Read output
        with open(output_file_path, "r", encoding='utf-8') as output_file:
            output = output_file.read()
            print(f"Python execution successful, output length: {len(output)}")
            return output
            
    except subprocess.TimeoutExpired:
        print("Python execution timed out")
        return None
    except Exception as e:
        print(f"Python execution error: {str(e)}")
        return None

def execute_cpp_improved(code_file_path, input_file_path, output_file_path, temp_path, unique):
    """Execute C++ code with improved error handling"""
    try:
        executable_path = temp_path / unique
        
        # FIXED: Check if g++ is available
        try:
            subprocess.run(["g++", "--version"], capture_output=True, timeout=5)
        except FileNotFoundError:
            print("g++ compiler not found")
            return None
        
        # Compile with g++
        compile_result = subprocess.run(
            ["g++", "-o", str(executable_path), str(code_file_path), "-std=c++17"],  # FIXED: Added C++ standard
            capture_output=True,
            timeout=15,  # FIXED: Increased timeout
            text=True
        )
        
        if compile_result.returncode != 0:
            print(f"C++ compilation error: {compile_result.stderr}")
            return None  # Compilation failed

        # Execute
        with open(input_file_path, "r", encoding='utf-8') as input_file:
            with open(output_file_path, "w", encoding='utf-8') as output_file:
                result = subprocess.run(
                    [str(executable_path)],
                    stdin=input_file,
                    stdout=output_file,
                    stderr=subprocess.PIPE,
                    timeout=10,  # FIXED: Increased timeout
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
        
        # FIXED: Check if gcc is available
        try:
            subprocess.run(["gcc", "--version"], capture_output=True, timeout=5)
        except FileNotFoundError:
            print("gcc compiler not found")
            return None
        
        # Compile with gcc
        compile_result = subprocess.run(
            ["gcc", "-o", str(executable_path), str(code_file_path), "-std=c99"],  # FIXED: Added C standard
            capture_output=True,
            timeout=15,  # FIXED: Increased timeout
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
                        timeout=10,  # FIXED: Increased timeout
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
            return None  # Compilation failed
            
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
        'submissions': user_submissions[:50],  # Limit to 50 recent submissions
        'verdict_filter': verdict_filter,
    }
    return render(request, 'submissions.html', context)