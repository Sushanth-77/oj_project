# Create your views here.
# compiler/views.py
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from core.models import Submission
import subprocess
import os
import uuid
from pathlib import Path
import tempfile
import shutil
import requests
import json
import time
import random
import logging

# Set up logging
logger = logging.getLogger(__name__)

@login_required
def ai_review_submission(request, submission_id):
    """Get AI review for a submission using Gemini LLM with retry logic"""
    submission = get_object_or_404(Submission, id=submission_id, user=request.user)
    
    try:
        # Get Gemini API key from settings
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            return JsonResponse({
                'success': False,
                'error': 'AI review service is not configured. Please contact administrator.'
            })
        
        # Try multiple models with fallback
        models_to_try = [
            'gemini-1.5-flash-latest',
            'gemini-1.5-flash',
            'gemini-pro'
        ]
        
        for model_name in models_to_try:
            result = try_ai_review_with_model(submission, api_key, model_name)
            if result['success']:
                return JsonResponse(result)
            elif result.get('should_retry', False):
                continue  # Try next model
            else:
                return JsonResponse(result)  # Non-retryable error
        
        # If all models failed
        return JsonResponse({
            'success': False,
            'error': 'All AI models are currently unavailable. Please try again in a few minutes.'
        })
            
    except Exception as e:
        logger.error(f"Unexpected error in AI review: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred. Please try again later.'
        })

def try_ai_review_with_model(submission, api_key, model_name, max_retries=3):
    """Try AI review with a specific model and retry logic"""
    
    # Prepare the prompt for Gemini
    prompt = f"""
    You are a coding mentor reviewing a programming solution. Please analyze the following code and provide constructive feedback.

    Problem: {submission.problem.name}
    Programming Language: {get_language_display(submission)}
    Submission Status: {submission.get_verdict_display()}

    Code:
    ```
    {submission.code_text}
    ```

    Please provide a concise review covering:
    1. Code quality assessment (⭐⭐⭐⭐⭐)
    2. Time complexity: O(?)
    3. Space complexity: O(?)
    4. Key suggestions for improvement
    5. Alternative approaches (if applicable)

    Keep the review constructive and educational. Focus on helping the programmer improve.
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    
    headers = {
        'Content-Type': 'application/json',
    }
    
    data = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 1024,
        },
        "safetySettings": [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH", 
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
    }
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting AI review with {model_name}, attempt {attempt + 1}")
            
            # Add exponential backoff with jitter
            if attempt > 0:
                delay = (2 ** attempt) + random.uniform(0, 1)
                logger.info(f"Waiting {delay:.2f} seconds before retry...")
                time.sleep(delay)
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            logger.info(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if 'candidates' in result and len(result['candidates']) > 0:
                        candidate = result['candidates'][0]
                        if 'content' in candidate and 'parts' in candidate['content']:
                            ai_review = candidate['content']['parts'][0]['text']
                            return {
                                'success': True,
                                'review': ai_review,
                                'model_used': model_name
                            }
                        else:
                            # Check finish reason
                            finish_reason = candidate.get('finishReason', 'UNKNOWN')
                            if finish_reason == 'SAFETY':
                                return {
                                    'success': False,
                                    'error': 'AI review was blocked by safety filters. Please try with different code.',
                                    'should_retry': False
                                }
                            elif finish_reason == 'MAX_TOKENS':
                                return {
                                    'success': False,
                                    'error': 'Code is too long for AI review. Please try with shorter code.',
                                    'should_retry': False
                                }
                    
                    return {
                        'success': False,
                        'error': 'No review generated. Please try again.',
                        'should_retry': True
                    }
                    
                except json.JSONDecodeError as e:
                    return {
                        'success': False,
                        'error': 'Invalid response from AI service.',
                        'should_retry': True
                    }
            
            elif response.status_code == 503:
                logger.warning(f"Model {model_name} is overloaded, attempt {attempt + 1}")
                if attempt == max_retries - 1:
                    return {
                        'success': False,
                        'error': f'AI model {model_name} is currently overloaded.',
                        'should_retry': True
                    }
                continue
                
            elif response.status_code == 429:
                logger.warning(f"Rate limit hit for {model_name}, attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep(5 + random.uniform(1, 3))
                    continue
                return {
                    'success': False,
                    'error': 'Rate limit exceeded. Please try again in a few minutes.',
                    'should_retry': True
                }
                
            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    error_message = error_data.get('error', {}).get('message', 'Bad request')
                    return {
                        'success': False,
                        'error': f'API Error: {error_message}',
                        'should_retry': False
                    }
                except:
                    return {
                        'success': False,
                        'error': 'Invalid request to AI service.',
                        'should_retry': False
                    }
                    
            elif response.status_code == 403:
                return {
                    'success': False,
                    'error': 'API key is invalid or has insufficient permissions.',
                    'should_retry': False
                }
                
            elif response.status_code == 404:
                return {
                    'success': False,
                    'error': f'AI model {model_name} not found.',
                    'should_retry': True
                }
                
            else:
                logger.error(f"Unexpected status code {response.status_code}: {response.text[:200]}")
                return {
                    'success': False,
                    'error': f'AI service error: {response.status_code}',
                    'should_retry': True if attempt < max_retries - 1 else False
                }
                
        except requests.exceptions.Timeout:
            logger.warning(f"Request timeout for {model_name}, attempt {attempt + 1}")
            if attempt == max_retries - 1:
                return {
                    'success': False,
                    'error': 'AI review request timed out.',
                    'should_retry': True
                }
            continue
            
        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection error for {model_name}, attempt {attempt + 1}")
            if attempt == max_retries - 1:
                return {
                    'success': False,
                    'error': 'Could not connect to AI service.',
                    'should_retry': True
                }
            continue
            
        except Exception as e:
            logger.error(f"Unexpected error with {model_name}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'should_retry': False
            }
    
    return {
        'success': False,
        'error': f'AI model {model_name} failed after {max_retries} attempts.',
        'should_retry': True
    }

def get_language_display(submission):
    """Helper function to get language display name"""
    if hasattr(submission, 'language') and submission.language:
        language_map = {
            'py': 'Python 3',
            'cpp': 'C++',
            'c': 'C'
        }
        return language_map.get(submission.language, 'Unknown')
    
    # Fallback to code detection
    code = submission.code_text.lower()
    if 'print(' in code or 'def ' in code or 'import ' in code:
        return 'Python 3'
    elif '#include' in code and ('cout' in code or 'printf' in code):
        if 'cout' in code:
            return 'C++'
        else:
            return 'C'
    else:
        return 'Unknown'

def get_docker_safe_base_path():
    """Get base path that works in Docker environment"""
    try:
        from django.conf import settings
        base_path = Path(settings.BASE_DIR)
    except:
        base_path = Path("/app")  # Default Docker working directory
    
    # Ensure the path exists
    if not base_path.exists():
        base_path = Path.cwd()
    
    return base_path

def evaluate_submission(submission, language):
    """
    Evaluate submission against both database test cases and file-based test cases
    Fixed for Docker environment
    """
    problem = submission.problem
    
    try:
        # Phase 1: Evaluate visible test cases from database (if any)
        visible_test_cases = problem.testcases.filter(is_hidden=False) if hasattr(problem.testcases.first(), 'is_hidden') else problem.testcases.all()
        
        if visible_test_cases.exists():
            logger.info(f"Phase 1: Evaluating {visible_test_cases.count()} visible test cases from database...")
            for i, test_case in enumerate(visible_test_cases, 1):
                logger.info(f"Testing visible test case {i}")
                logger.debug(f"Input: {repr(test_case.input)}")
                logger.debug(f"Expected: {repr(test_case.output)}")
                
                output = run_code(language, submission.code_text, test_case.input)
                logger.debug(f"Raw output: {repr(output)}")
                
                if output is None:
                    logger.error("Runtime error in visible test case")
                    return 'RE'
                
                # Enhanced output comparison
                expected_output = test_case.output.strip().replace('\r\n', '\n').replace('\r', '\n')
                actual_output = output.strip().replace('\r\n', '\n').replace('\r', '\n')
                
                if expected_output != actual_output:
                    logger.error(f"MISMATCH in visible test case {i}")
                    return 'WA'
                else:
                    logger.info(f"Test case {i} PASSED")
        
        # Phase 2: Evaluate file-based test cases
        file_verdict = evaluate_file_based_test_cases(submission, language)
        if file_verdict != 'AC':
            return file_verdict
            
        logger.info("All test cases passed!")
        return 'AC'
        
    except Exception as e:
        logger.error(f"Exception during evaluation: {str(e)}", exc_info=True)
        return 'RE'

def detect_test_case_format(input_content, output_content):
    """
    Intelligently detect the format of test cases and return parsing strategy
    """
    input_lines = input_content.strip().split('\n')
    output_lines = output_content.strip().split('\n')
    
    # Strategy 1: Single line inputs/outputs (like NQ.txt)
    if len(input_lines) == len(output_lines) and len(input_lines) > 1:
        # Check if each input line looks like a single value
        single_value_pattern = True
        for line in input_lines[:5]:  # Check first 5 lines
            if len(line.strip().split()) > 1:
                single_value_pattern = False
                break
        
        if single_value_pattern:
            return {
                'format': 'single_line',
                'description': 'Each line is one test case'
            }
    
    # Strategy 2: Multi-line test cases separated by empty lines
    input_sections = input_content.strip().split('\n\n')
    output_sections = output_content.strip().split('\n\n')
    
    if len(input_sections) > 1 and len(input_sections) == len(output_sections):
        return {
            'format': 'empty_line_separated',
            'description': 'Multi-line test cases separated by empty lines',
            'sections': list(zip(input_sections, output_sections))
        }
    
    # Strategy 3: First line indicates number of test cases
    first_input_line = input_lines[0].strip()
    if first_input_line.isdigit():
        num_cases = int(first_input_line)
        if num_cases > 0 and num_cases <= 1000:
            return {
                'format': 'count_prefixed',
                'description': 'First line contains number of test cases',
                'count': num_cases,
                'remaining_input': '\n'.join(input_lines[1:])
            }
    
    # Strategy 4: Fixed number of lines per test case
    if len(input_lines) % len(output_lines) == 0 and len(output_lines) > 0:
        lines_per_case = len(input_lines) // len(output_lines)
        if lines_per_case > 1 and lines_per_case <= 10:
            return {
                'format': 'fixed_lines',
                'description': f'{lines_per_case} input lines per test case',
                'lines_per_case': lines_per_case
            }
    
    # Fallback: Single test case
    return {
        'format': 'single_test',
        'description': 'Entire content is one test case'
    }

def parse_test_cases_smart(input_content, output_content):
    """Smart test case parser that handles multiple formats"""
    format_info = detect_test_case_format(input_content, output_content)
    
    logger.info(f"Detected format: {format_info['format']} - {format_info['description']}")
    
    test_cases = []
    
    if format_info['format'] == 'single_line':
        # Each line is one test case (like NQ.txt)
        input_lines = input_content.strip().split('\n')
        output_lines = output_content.strip().split('\n')
        
        for i, (inp_line, out_line) in enumerate(zip(input_lines, output_lines)):
            test_cases.append({
                'input': inp_line.strip(),
                'output': out_line.strip(),
                'case_number': i + 1,
                'is_multiline': False
            })
    
    elif format_info['format'] == 'empty_line_separated':
        # Multi-line test cases separated by empty lines
        for i, (inp_section, out_section) in enumerate(format_info['sections']):
            test_cases.append({
                'input': inp_section.strip(),
                'output': out_section.strip(),
                'case_number': i + 1,
                'is_multiline': True
            })
    
    elif format_info['format'] == 'count_prefixed':
        # First line contains number of test cases
        remaining_input = format_info['remaining_input']
        output_lines = output_content.strip().split('\n')
        input_lines = remaining_input.split('\n')
        num_cases = format_info['count']
        
        if len(input_lines) == num_cases and len(output_lines) == num_cases:
            # Simple: one line input, one line output per case
            for i in range(num_cases):
                test_cases.append({
                    'input': input_lines[i].strip(),
                    'output': output_lines[i].strip(),
                    'case_number': i + 1,
                    'is_multiline': False
                })
        else:
            # Complex: multiple lines per test case
            lines_per_case = len(input_lines) // num_cases
            for i in range(num_cases):
                start_idx = i * lines_per_case
                end_idx = start_idx + lines_per_case
                case_input = '\n'.join(input_lines[start_idx:end_idx])
                case_output = output_lines[i] if i < len(output_lines) else ""
                
                test_cases.append({
                    'input': case_input.strip(),
                    'output': case_output.strip(),
                    'case_number': i + 1,
                    'is_multiline': True
                })
    
    elif format_info['format'] == 'fixed_lines':
        # Fixed number of lines per test case
        input_lines = input_content.strip().split('\n')
        output_lines = output_content.strip().split('\n')
        lines_per_case = format_info['lines_per_case']
        
        case_num = 1
        for i in range(0, len(input_lines), lines_per_case):
            if i + lines_per_case <= len(input_lines):
                input_case = '\n'.join(input_lines[i:i + lines_per_case])
                output_case = output_lines[case_num - 1] if case_num - 1 < len(output_lines) else ""
                
                test_cases.append({
                    'input': input_case.strip(),
                    'output': output_case.strip(),
                    'case_number': case_num,
                    'is_multiline': True
                })
                case_num += 1
    
    else:  # single_test
        # Entire content is one test case
        test_cases.append({
            'input': input_content.strip(),
            'output': output_content.strip(),
            'case_number': 1,
            'is_multiline': True
        })
    
    return test_cases

def evaluate_file_based_test_cases(submission, language):
    """
    Evaluate test cases from input/output files with smart format detection
    Handles both single-line (NQ.txt) and multi-line formats
    """
    problem = submission.problem
    base_path = get_docker_safe_base_path()
    
    input_path = base_path / "inputs" / f"{problem.short_code}.txt"
    output_path = base_path / "outputs" / f"{problem.short_code}.txt"
    
    if not input_path.exists() or not output_path.exists():
        logger.info(f"No test files found for {problem.short_code}")
        return 'AC'
    
    try:
        # Read all inputs and outputs
        with open(input_path, 'r', encoding='utf-8') as f:
            input_content = f.read()
        
        with open(output_path, 'r', encoding='utf-8') as f:
            output_content = f.read()
        
        logger.debug(f"Input file content (first 200 chars): {repr(input_content[:200])}")
        logger.debug(f"Output file content (first 200 chars): {repr(output_content[:200])}")
        
        # Use smart parsing to detect format and parse test cases
        test_cases = parse_test_cases_smart(input_content, output_content)
        
        logger.info(f"Smart parser found {len(test_cases)} test cases")
        
        # Test each case
        for test_case in test_cases:
            case_num = test_case['case_number']
            test_input = test_case['input']
            expected_output = test_case['output']
            is_multiline = test_case['is_multiline']
            
            logger.info(f"=== Testing case {case_num} ({'multi-line' if is_multiline else 'single-line'}) ===")
            logger.debug(f"Input: {repr(test_input)}")
            logger.debug(f"Expected: {repr(expected_output)}")
            
            # Run code with the input
            actual_output = run_code(language, submission.code_text, test_input)
            
            if actual_output is None:
                logger.error(f"Runtime error in test case {case_num}")
                return 'RE'
            
            # Clean and compare outputs
            expected_clean = expected_output.strip()
            actual_clean = actual_output.strip()
            
            logger.debug(f"Actual: {repr(actual_clean)}")
            
            if expected_clean != actual_clean:
                logger.error(f"MISMATCH in test case {case_num}")
                logger.error(f"Expected: '{expected_clean}' (len: {len(expected_clean)})")
                logger.error(f"Actual: '{actual_clean}' (len: {len(actual_clean)})")
                
                # Show first difference for debugging
                min_len = min(len(expected_clean), len(actual_clean))
                for j in range(min_len):
                    if expected_clean[j] != actual_clean[j]:
                        logger.error(f"First diff at pos {j}: expected {repr(expected_clean[j])}, got {repr(actual_clean[j])}")
                        break
                
                return 'WA'
            else:
                logger.info(f"✓ Test case {case_num} PASSED")
        
        return 'AC'
        
    except Exception as e:
        logger.error(f"Error in smart test case evaluation: {str(e)}", exc_info=True)
        return 'RE'

def run_code(language, code, input_data):
    """Execute code with Docker-safe temporary directory handling"""
    unique = str(uuid.uuid4())[:8]  # Shorter UUID for Docker
    temp_dir = None
    
    try:
        # Create Docker-safe temporary directory
        if os.path.exists('/tmp'):
            temp_base = '/tmp'
        else:
            temp_base = get_docker_safe_base_path() / 'temp'
            temp_base.mkdir(exist_ok=True)
        
        temp_dir = tempfile.mkdtemp(prefix=f"oj_exec_{unique}_", dir=temp_base)
        temp_path = Path(temp_dir)
        
        logger.debug(f"Created temp directory: {temp_dir}")
        
        # Create file paths
        if language == 'py':
            code_file_path = temp_path / f"{unique}.py"
        elif language == 'cpp':
            code_file_path = temp_path / f"{unique}.cpp"
        elif language == 'c':
            code_file_path = temp_path / f"{unique}.c"
        else:
            logger.error(f"Unsupported language: {language}")
            return None
        
        input_file_path = temp_path / f"{unique}_input.txt"
        output_file_path = temp_path / f"{unique}_output.txt"

        # Write code to file with error handling
        try:
            with open(code_file_path, "w", encoding='utf-8') as code_file:
                code_file.write(code)
        except Exception as e:
            logger.error(f"Failed to write code file: {e}")
            return None

        # Write input data to file
        try:
            with open(input_file_path, "w", encoding='utf-8') as input_file:
                input_file.write(input_data if input_data is not None else '')
        except Exception as e:
            logger.error(f"Failed to write input file: {e}")
            return None

        # Execute based on language
        if language == "cpp":
            result = execute_cpp_docker_safe(code_file_path, input_file_path, output_file_path, temp_path, unique)
        elif language == "c":
            result = execute_c_docker_safe(code_file_path, input_file_path, output_file_path, temp_path, unique)
        elif language == "py":
            result = execute_python_docker_safe(code_file_path, input_file_path, output_file_path)
        else:
            return None
            
        return result

    except Exception as e:
        logger.error(f"Error in run_code: {str(e)}", exc_info=True)
        return None
    finally:
        # Cleanup temporary directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception as cleanup_error:
                logger.warning(f"Cleanup error: {cleanup_error}")
                pass

def execute_python_docker_safe(code_file_path, input_file_path, output_file_path):
    """Execute Python code with Docker-safe settings"""
    try:
        # Check for Python in Docker environment
        python_commands = [
            '/usr/local/bin/python3',  # Docker Python location
            '/usr/bin/python3',
            'python3',
            'python'
        ]
        
        python_cmd = None
        for cmd in python_commands:
            try:
                result = subprocess.run([cmd, '--version'], 
                                      capture_output=True, 
                                      timeout=5, 
                                      text=True)
                if result.returncode == 0:
                    python_cmd = cmd
                    logger.debug(f"Found Python at: {cmd}")
                    break
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        if not python_cmd:
            logger.error("No Python interpreter found")
            return None
        
        try:
            with open(input_file_path, "r", encoding='utf-8') as input_file:
                with open(output_file_path, "w", encoding='utf-8') as output_file:
                    result = subprocess.run(
                        [python_cmd, str(code_file_path)],
                        stdin=input_file,
                        stdout=output_file,
                        stderr=subprocess.PIPE,
                        timeout=10,  # 10 second timeout
                        text=True,
                        cwd=str(code_file_path.parent),
                        # Add resource limits for Docker
                        preexec_fn=None if os.name == 'nt' else os.setsid
                    )
                    
                    logger.debug(f"Python process return code: {result.returncode}")
                    if result.stderr:
                        logger.debug(f"Python stderr: {result.stderr}")
                    
                    if result.returncode != 0:
                        logger.error(f"Python runtime error: {result.stderr}")
                        return None

            # Read output
            try:
                with open(output_file_path, "r", encoding='utf-8') as output_file:
                    output = output_file.read()
                    logger.debug(f"Python execution successful, output length: {len(output)}")
                    return output
            except FileNotFoundError:
                logger.error("Output file not created")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("Python execution timed out")
            return None
            
    except Exception as e:
        logger.error(f"Python execution error: {str(e)}", exc_info=True)
        return None

def execute_cpp_docker_safe(code_file_path, input_file_path, output_file_path, temp_path, unique):
    """Execute C++ code with Docker-safe compiler paths"""
    try:
        executable_path = temp_path / unique
        
        # Check for g++ in Docker environment
        gcc_commands = ['/usr/bin/g++', 'g++']
        gcc_cmd = None
        
        for cmd in gcc_commands:
            try:
                result = subprocess.run([cmd, '--version'], 
                                      capture_output=True, 
                                      timeout=5, 
                                      text=True)
                if result.returncode == 0:
                    gcc_cmd = cmd
                    logger.debug(f"Found g++ at: {cmd}")
                    break
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        if not gcc_cmd:
            logger.error("g++ compiler not found")
            return None
        
        # Compile with g++
        compile_result = subprocess.run(
            [gcc_cmd, "-o", str(executable_path), str(code_file_path), 
             "-std=c++17", "-O2", "-Wall"],
            capture_output=True,
            timeout=15,
            text=True
        )
        
        if compile_result.returncode != 0:
            logger.error(f"C++ compilation error: {compile_result.stderr}")
            return None

        # Execute with resource limits
        with open(input_file_path, "r", encoding='utf-8') as input_file:
            with open(output_file_path, "w", encoding='utf-8') as output_file:
                result = subprocess.run(
                    [str(executable_path)],
                    stdin=input_file,
                    stdout=output_file,
                    stderr=subprocess.PIPE,
                    timeout=10,
                    text=True,
                    preexec_fn=None if os.name == 'nt' else os.setsid
                )
                
                if result.returncode != 0:
                    logger.error(f"C++ runtime error: {result.stderr}")
                    return None

        # Read output
        try:
            with open(output_file_path, "r", encoding='utf-8') as output_file:
                return output_file.read()
        except FileNotFoundError:
            logger.error("C++ output file not created")
            return None
            
    except subprocess.TimeoutExpired:
        logger.error("C++ execution timed out")
        return None
    except Exception as e:
        logger.error(f"C++ execution error: {str(e)}", exc_info=True)
        return None

def execute_c_docker_safe(code_file_path, input_file_path, output_file_path, temp_path, unique):
    """Execute C code with Docker-safe compiler paths"""
    try:
        executable_path = temp_path / unique
        
        # Check for gcc in Docker environment
        gcc_commands = ['/usr/bin/gcc', 'gcc']
        gcc_cmd = None
        
        for cmd in gcc_commands:
            try:
                result = subprocess.run([cmd, '--version'], 
                                      capture_output=True, 
                                      timeout=5, 
                                      text=True)
                if result.returncode == 0:
                    gcc_cmd = cmd
                    logger.debug(f"Found gcc at: {cmd}")
                    break
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        if not gcc_cmd:
            logger.error("gcc compiler not found")
            return None
        
        # Compile with gcc
        compile_result = subprocess.run(
            [gcc_cmd, "-o", str(executable_path), str(code_file_path), 
             "-std=c99", "-O2", "-Wall"],
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
                        text=True,
                        preexec_fn=None if os.name == 'nt' else os.setsid
                    )
                    
                    if result.returncode != 0:
                        logger.error(f"C runtime error: {result.stderr}")
                        return None

            # Read output
            try:
                with open(output_file_path, "r", encoding='utf-8') as output_file:
                    return output_file.read()
            except FileNotFoundError:
                logger.error("C output file not created")
                return None
        else:
            logger.error(f"C compilation error: {compile_result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        logger.error("C execution timed out")
        return None
    except Exception as e:
        logger.error(f"C execution error: {str(e)}", exc_info=True)
        return None