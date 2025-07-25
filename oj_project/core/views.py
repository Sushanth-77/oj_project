# oj_project/core/views.py - Updated with multi-line test cases support
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

def parse_test_cases_from_files(input_content, output_content, problem=None):
    """
    Parse test cases from input and output files.
    Supports multiple formats:
    1. Single-line test cases (each line is one test case)
    2. Multi-line test cases separated by empty lines
    3. Multi-line test cases with specific separators
    4. Fixed number of lines per test case (if problem config available)
    """
    
    # Method 1: Try to detect if we have multi-line test cases separated by empty lines
    input_sections = input_content.strip().split('\n\n')
    output_sections = output_content.strip().split('\n\n')
    
    print(f"Detected {len(input_sections)} input sections and {len(output_sections)} output sections")
    
    # Check if problem has specific parsing configuration
    if problem and hasattr(problem, 'test_case_format'):
        format_type = getattr(problem, 'test_case_format', 'auto')
        lines_per_case = getattr(problem, 'lines_per_test_case', None)
        
        if format_type == 'fixed_lines' and lines_per_case:
            print(f"Using fixed lines format: {lines_per_case} lines per test case")
            return parse_fixed_lines_format(input_content, output_content, lines_per_case)
    
    # If we have multiple sections separated by empty lines, use them
    if len(input_sections) > 1 and len(input_sections) == len(output_sections):
        print("Using multi-line test cases separated by empty lines")
        test_cases = []
        for i, (inp_section, out_section) in enumerate(zip(input_sections, output_sections)):
            test_cases.append({
                'input': inp_section.strip(),
                'output': out_section.strip(),
                'case_number': i + 1
            })
        return test_cases
    
    # Method 2: Check if input/output have same number of lines (single-line test cases)
    input_lines = input_content.strip().split('\n')
    output_lines = output_content.strip().split('\n')
    
    if len(input_lines) == len(output_lines) and len(input_lines) > 1:
        print("Using single-line test cases (each line is one test case)")
        test_cases = []
        for i, (inp_line, out_line) in enumerate(zip(input_lines, output_lines)):
            test_cases.append({
                'input': inp_line.strip(),
                'output': out_line.strip(),
                'case_number': i + 1
            })
        return test_cases
    
    # Method 3: Try to detect pattern-based separation
    # Look for common patterns like "Case 1:", "Test 1:", etc.
    import re
    case_pattern = re.compile(r'^(Case|Test|Input)\s*\d+', re.MULTILINE | re.IGNORECASE)
    
    input_matches = list(case_pattern.finditer(input_content))
    output_matches = list(case_pattern.finditer(output_content))
    
    if len(input_matches) > 1 and len(input_matches) == len(output_matches):
        print("Using pattern-based test case separation")
        test_cases = []
        
        for i in range(len(input_matches)):
            # Extract input for this test case
            start_pos = input_matches[i].end()
            end_pos = input_matches[i + 1].start() if i + 1 < len(input_matches) else len(input_content)
            inp_text = input_content[start_pos:end_pos].strip()
            
            # Extract output for this test case
            start_pos = output_matches[i].end()
            end_pos = output_matches[i + 1].start() if i + 1 < len(output_matches) else len(output_content)
            out_text = output_content[start_pos:end_pos].strip()
            
            test_cases.append({
                'input': inp_text,
                'output': out_text,
                'case_number': i + 1
            })
        return test_cases
    
    # Method 4: Fallback - treat entire content as single test case
    print("Using entire content as single test case")
    return [{
        'input': input_content.strip(),
        'output': output_content.strip(),
        'case_number': 1
    }]

def parse_fixed_lines_format(input_content, output_content, lines_per_case):
    """
    Parse test cases when each test case has a fixed number of lines
    """
    input_lines = input_content.strip().split('\n')
    output_lines = output_content.strip().split('\n')
    
    test_cases = []
    case_num = 1
    
    # Parse input
    for i in range(0, len(input_lines), lines_per_case):
        if i + lines_per_case <= len(input_lines):
            input_case = '\n'.join(input_lines[i:i + lines_per_case])
            
            # Find corresponding output (assuming same structure)
            output_start = (case_num - 1) * lines_per_case
            if output_start < len(output_lines):
                # Try to determine output lines dynamically or use same count
                output_case = output_lines[output_start] if output_start < len(output_lines) else ""
                
                test_cases.append({
                    'input': input_case,
                    'output': output_case,
                    'case_number': case_num
                })
                case_num += 1
    
    return test_cases

def evaluate_file_based_test_cases(submission, language):
    """
    Evaluate test cases from input/output files with support for multi-line test cases
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
            input_content = f.read()
        
        with open(output_path, 'r', encoding='utf-8') as f:
            output_content = f.read()
        
        print(f"Input file content: {repr(input_content)}")
        print(f"Output file content: {repr(output_content)}")
        
        # Parse test cases using the new method
        test_cases = parse_test_cases_from_files(input_content, output_content, problem)
        
        print(f"Parsed {len(test_cases)} test cases")
        
        # Test each case individually
        for test_case in test_cases:
            case_num = test_case['case_number']
            test_input = test_case['input']
            expected_output = test_case['output']
            
            print(f"\n=== Testing file-based test case {case_num} ===")
            print(f"Input: {repr(test_input)}")
            print(f"Expected: {repr(expected_output)}")
            
            # Run code with this specific input
            actual_output = run_code(language, submission.code_text, test_input)
            
            if actual_output is None:
                print(f"Runtime error in test case {case_num}")
                return 'RE'
            
            # Clean and compare outputs
            expected_clean = expected_output.strip()
            actual_clean = actual_output.strip()
            
            print(f"Actual: {repr(actual_clean)}")
            
            if expected_clean != actual_clean:
                print(f"!!! MISMATCH in test case {case_num} !!!")
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
                print(f"✓ Test case {case_num} PASSED")
        
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