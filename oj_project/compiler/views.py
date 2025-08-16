# compiler/views.py - Improved version with flexible test case handling
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
import re

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

def normalize_output(output):
    """Normalize output for comparison - handles different line endings and whitespace"""
    if output is None:
        return ""
    
    # Remove all types of line endings and normalize to \n
    normalized = output.replace('\r\n', '\n').replace('\r', '\n')
    
    # Split into lines, strip each line, and rejoin
    lines = [line.rstrip() for line in normalized.split('\n')]
    
    # Remove empty lines from the end
    while lines and not lines[-1]:
        lines.pop()
    
    return '\n'.join(lines)

def evaluate_submission(submission, language):
    """
    Main evaluation function that handles both database and file-based test cases
    """
    problem = submission.problem
    
    try:
        logger.info(f"Starting evaluation for problem {problem.short_code}")
        
        # Phase 1: Evaluate visible test cases from database (if any)
        visible_test_cases = problem.testcases.filter(is_hidden=False) if hasattr(problem.testcases.first(), 'is_hidden') else problem.testcases.all()
        
        if visible_test_cases.exists():
            logger.info(f"Phase 1: Evaluating {visible_test_cases.count()} visible test cases from database...")
            for i, test_case in enumerate(visible_test_cases, 1):
                logger.info(f"Testing database test case {i}")
                
                output = run_code_safe(language, submission.code_text, test_case.input)
                if output is None:
                    logger.error(f"Runtime error in database test case {i}")
                    return 'RE'
                
                expected = normalize_output(test_case.output)
                actual = normalize_output(output)
                
                if expected != actual:
                    logger.error(f"MISMATCH in database test case {i}")
                    logger.error(f"Expected: {repr(expected)}")
                    logger.error(f"Actual: {repr(actual)}")
                    return 'WA'
                else:
                    logger.info(f"✓ Database test case {i} PASSED")
        
        # Phase 2: Evaluate file-based test cases
        file_verdict = evaluate_file_based_test_cases(submission, language)
        if file_verdict != 'AC':
            return file_verdict
            
        logger.info("All test cases passed!")
        return 'AC'
        
    except Exception as e:
        logger.error(f"Exception during evaluation: {str(e)}", exc_info=True)
        return 'RE'

class TestCaseFormatDetector:
    """Advanced test case format detector and parser with improved logic"""
    
    @staticmethod
    def detect_format(input_content, output_content):
        """
        Detect the format of test cases with improved logic for FIFO-style problems
        Returns format information and parsing strategy
        """
        input_lines = [line.strip() for line in input_content.strip().split('\n') if line.strip()]
        output_lines = [line.strip() for line in output_content.strip().split('\n') if line.strip()]
        
        logger.info(f"Format detection: {len(input_lines)} input lines, {len(output_lines)} output lines")
        logger.debug(f"First 3 input lines: {input_lines[:3]}")
        logger.debug(f"First 3 output lines: {output_lines[:3]}")
        
        # Strategy 1: Check for empty line separated input sections with single line outputs
        input_sections = input_content.strip().split('\n\n')
        input_sections = [section.strip() for section in input_sections if section.strip()]
        
        if len(input_sections) > 1 and len(input_sections) == len(output_lines):
            # This handles the FIFO case: input sections separated by empty lines, single line outputs
            pairs = []
            for inp_section, out_line in zip(input_sections, output_lines):
                pairs.append((inp_section.strip(), out_line.strip()))
            
            return {
                'type': 'sections_to_lines',
                'description': f'Input sections separated by empty lines, single line outputs ({len(pairs)} cases)',
                'pairs': pairs
            }
        
        # Strategy 2: Equal number of lines - likely one test case per line
        if len(input_lines) == len(output_lines) and len(input_lines) > 1:
            # Check if inputs look like single values or simple expressions
            simple_inputs = 0
            for line in input_lines[:min(5, len(input_lines))]:
                # Count lines that look like single numbers, simple expressions, or short strings
                if (line.replace('-', '').replace('.', '').replace(' ', '').isdigit() or
                    len(line.split()) <= 3 or
                    re.match(r'^[a-zA-Z0-9\s\-+*/]+$', line)):
                    simple_inputs += 1
            
            if simple_inputs >= len(input_lines[:5]) * 0.8:  # 80% are simple
                return {
                    'type': 'line_by_line',
                    'description': f'Each line is one test case ({len(input_lines)} total)',
                    'pairs': list(zip(input_lines, output_lines))
                }
        
        # Strategy 3: Check if first line is a count
        if len(input_lines) > 1 and input_lines[0].strip().isdigit():
            test_count = int(input_lines[0])
            remaining_input_lines = input_lines[1:]
            
            logger.info(f"First line indicates {test_count} test cases")
            
            if 0 < test_count <= 1000:  # Reasonable test count
                if len(remaining_input_lines) == test_count and len(output_lines) == test_count:
                    # Simple: one line per test case after count
                    return {
                        'type': 'count_then_lines',
                        'description': f'Count ({test_count}) followed by one line per test case',
                        'count': test_count,
                        'pairs': list(zip(remaining_input_lines, output_lines))
                    }
                elif len(remaining_input_lines) % test_count == 0:
                    # Multiple lines per test case
                    lines_per_case = len(remaining_input_lines) // test_count
                    pairs = []
                    for i in range(test_count):
                        start = i * lines_per_case
                        end = start + lines_per_case
                        case_input = '\n'.join(remaining_input_lines[start:end])
                        case_output = output_lines[i] if i < len(output_lines) else ""
                        pairs.append((case_input, case_output))
                    
                    return {
                        'type': 'count_then_multiline',
                        'description': f'Count ({test_count}) followed by {lines_per_case} lines per test case',
                        'count': test_count,
                        'lines_per_case': lines_per_case,
                        'pairs': pairs
                    }
        
        # Strategy 4: Multi-line test cases separated by empty lines (both input and output)
        output_sections = output_content.strip().split('\n\n')
        output_sections = [section.strip() for section in output_sections if section.strip()]
        
        if len(input_sections) > 1 and len(input_sections) == len(output_sections):
            pairs = []
            for inp_section, out_section in zip(input_sections, output_sections):
                pairs.append((inp_section.strip(), out_section.strip()))
            
            return {
                'type': 'empty_line_separated',
                'description': f'Multi-line test cases separated by empty lines ({len(pairs)} cases)',
                'pairs': pairs
            }
        
        # Strategy 5: Single large test case with multiple outputs
        if len(output_lines) > 1 and len(input_lines) != len(output_lines):
            # Could be one input producing multiple outputs
            return {
                'type': 'single_input_multi_output',
                'description': 'Single input case producing multiple output lines',
                'pairs': [(input_content.strip(), output_content.strip())]
            }
        
        # Fallback: Treat as single test case
        return {
            'type': 'single_case',
            'description': 'Single test case (entire content)',
            'pairs': [(input_content.strip(), output_content.strip())]
        }

def evaluate_file_based_test_cases(submission, language):
    """
    Improved file-based test case evaluation with better format detection
    """
    problem = submission.problem
    base_path = get_docker_safe_base_path()
    
    input_path = base_path / "inputs" / f"{problem.short_code}.txt"
    output_path = base_path / "outputs" / f"{problem.short_code}.txt"
    
    if not input_path.exists() or not output_path.exists():
        logger.info(f"No test files found for {problem.short_code}")
        return 'AC'
    
    try:
        # Read test files
        with open(input_path, 'r', encoding='utf-8') as f:
            input_content = f.read()
        
        with open(output_path, 'r', encoding='utf-8') as f:
            output_content = f.read()
        
        logger.info(f"Read {len(input_content)} chars input, {len(output_content)} chars output")
        
        # Detect format and get test case pairs
        format_info = TestCaseFormatDetector.detect_format(input_content, output_content)
        logger.info(f"Detected format: {format_info['type']} - {format_info['description']}")
        
        test_pairs = format_info['pairs']
        logger.info(f"Found {len(test_pairs)} test case pairs")
        
        # Execute each test case
        for i, (test_input, expected_output) in enumerate(test_pairs, 1):
            logger.info(f"=== Testing case {i}/{len(test_pairs)} ===")
            logger.debug(f"Input: {repr(test_input[:100])}{'...' if len(test_input) > 100 else ''}")
            logger.debug(f"Expected: {repr(expected_output[:100])}{'...' if len(expected_output) > 100 else ''}")
            
            # Run the code
            actual_output = run_code_safe(language, submission.code_text, test_input)
            
            if actual_output is None:
                logger.error(f"Runtime error in test case {i}")
                return 'RE'
            
            # Normalize and compare outputs
            expected_clean = normalize_output(expected_output)
            actual_clean = normalize_output(actual_output)
            
            logger.debug(f"Actual: {repr(actual_clean[:100])}{'...' if len(actual_clean) > 100 else ''}")
            
            if expected_clean != actual_clean:
                logger.error(f"MISMATCH in test case {i}")
                logger.error(f"Expected ({len(expected_clean)} chars): {repr(expected_clean[:200])}")
                logger.error(f"Actual ({len(actual_clean)} chars): {repr(actual_clean[:200])}")
                
                # Show character-by-character diff for debugging
                min_len = min(len(expected_clean), len(actual_clean))
                for j in range(min_len):
                    if expected_clean[j] != actual_clean[j]:
                        logger.error(f"First difference at position {j}:")
                        logger.error(f"  Expected: {repr(expected_clean[j])} (ord {ord(expected_clean[j])})")
                        logger.error(f"  Actual: {repr(actual_clean[j])} (ord {ord(actual_clean[j])})")
                        break
                
                if len(expected_clean) != len(actual_clean):
                    logger.error(f"Length mismatch: expected {len(expected_clean)}, got {len(actual_clean)}")
                
                return 'WA'
            else:
                logger.info(f"✓ Test case {i} PASSED")
        
        return 'AC'
        
    except Exception as e:
        logger.error(f"Error in file-based test case evaluation: {str(e)}", exc_info=True)
        return 'RE'

def run_code_safe(language, code, input_data):
    """
    Safe code execution with improved error handling and resource management
    """
    unique = str(uuid.uuid4())[:8]
    temp_dir = None
    
    try:
        # Create secure temporary directory
        if os.path.exists('/tmp'):
            temp_base = '/tmp'
        else:
            temp_base = get_docker_safe_base_path() / 'temp'
            temp_base.mkdir(exist_ok=True)
        
        temp_dir = tempfile.mkdtemp(prefix=f"oj_exec_{unique}_", dir=temp_base)
        temp_path = Path(temp_dir)
        
        logger.debug(f"Created temp directory: {temp_dir}")
        
        # Set up file paths
        extensions = {'py': '.py', 'cpp': '.cpp', 'c': '.c'}
        if language not in extensions:
            logger.error(f"Unsupported language: {language}")
            return None
        
        code_file_path = temp_path / f"{unique}{extensions[language]}"
        input_file_path = temp_path / f"{unique}_input.txt"
        output_file_path = temp_path / f"{unique}_output.txt"
        
        # Write files
        try:
            with open(code_file_path, "w", encoding='utf-8') as f:
                f.write(code)
            
            with open(input_file_path, "w", encoding='utf-8') as f:
                f.write(input_data if input_data is not None else '')
        except Exception as e:
            logger.error(f"Failed to write files: {e}")
            return None
        
        # Execute based on language
        if language == 'py':
            return execute_python_improved(code_file_path, input_file_path, output_file_path)
        elif language == 'cpp':
            return execute_cpp_improved(code_file_path, input_file_path, output_file_path, temp_path, unique)
        elif language == 'c':
            return execute_c_improved(code_file_path, input_file_path, output_file_path, temp_path, unique)
        
        return None
        
    except Exception as e:
        logger.error(f"Error in run_code_safe: {str(e)}", exc_info=True)
        return None
    finally:
        # Cleanup
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception as cleanup_error:
                logger.warning(f"Cleanup error: {cleanup_error}")

def execute_python_improved(code_file_path, input_file_path, output_file_path):
    """Improved Python execution with better error handling"""
    try:
        # Find Python interpreter
        python_commands = ['/usr/local/bin/python3', '/usr/bin/python3', 'python3', 'python']
        python_cmd = None
        
        for cmd in python_commands:
            try:
                result = subprocess.run([cmd, '--version'], capture_output=True, timeout=3, text=True)
                if result.returncode == 0:
                    python_cmd = cmd
                    logger.debug(f"Found Python: {cmd}")
                    break
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        if not python_cmd:
            logger.error("No Python interpreter found")
            return None
        
        # Execute with proper resource limits
        try:
            with open(input_file_path, "r", encoding='utf-8') as stdin_file:
                with open(output_file_path, "w", encoding='utf-8') as stdout_file:
                    process = subprocess.run(
                        [python_cmd, str(code_file_path)],
                        stdin=stdin_file,
                        stdout=stdout_file,
                        stderr=subprocess.PIPE,
                        timeout=15,  # Increased timeout
                        text=True,
                        cwd=str(code_file_path.parent)
                    )
                    
                    if process.returncode != 0:
                        logger.error(f"Python execution failed with code {process.returncode}")
                        if process.stderr:
                            logger.error(f"Python stderr: {process.stderr}")
                        return None
            
            # Read output
            if output_file_path.exists():
                with open(output_file_path, "r", encoding='utf-8') as f:
                    output = f.read()
                    logger.debug(f"Python execution successful, output: {len(output)} chars")
                    return output
            else:
                logger.error("Python output file not created")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("Python execution timed out")
            return None
            
    except Exception as e:
        logger.error(f"Python execution error: {str(e)}", exc_info=True)
        return None

def execute_cpp_improved(code_file_path, input_file_path, output_file_path, temp_path, unique):
    """Improved C++ execution"""
    try:
        executable_path = temp_path / unique
        
        # Find g++ compiler
        compilers = ['/usr/bin/g++', 'g++']
        compiler = None
        
        for cmd in compilers:
            try:
                result = subprocess.run([cmd, '--version'], capture_output=True, timeout=3, text=True)
                if result.returncode == 0:
                    compiler = cmd
                    logger.debug(f"Found g++: {cmd}")
                    break
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        if not compiler:
            logger.error("g++ compiler not found")
            return None
        
        # Compile
        compile_process = subprocess.run(
            [compiler, "-o", str(executable_path), str(code_file_path), 
             "-std=c++17", "-O2", "-Wall", "-Wextra"],
            capture_output=True,
            timeout=20,
            text=True
        )
        
        if compile_process.returncode != 0:
            logger.error(f"C++ compilation failed: {compile_process.stderr}")
            return None
        
        # Execute
        try:
            with open(input_file_path, "r", encoding='utf-8') as stdin_file:
                with open(output_file_path, "w", encoding='utf-8') as stdout_file:
                    process = subprocess.run(
                        [str(executable_path)],
                        stdin=stdin_file,
                        stdout=stdout_file,
                        stderr=subprocess.PIPE,
                        timeout=15,
                        text=True
                    )
                    
                    if process.returncode != 0:
                        logger.error(f"C++ execution failed: {process.stderr}")
                        return None
            
            # Read output
            if output_file_path.exists():
                with open(output_file_path, "r", encoding='utf-8') as f:
                    return f.read()
            else:
                logger.error("C++ output file not created")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("C++ execution timed out")
            return None
            
    except Exception as e:
        logger.error(f"C++ execution error: {str(e)}", exc_info=True)
        return None

def execute_c_improved(code_file_path, input_file_path, output_file_path, temp_path, unique):
    """Improved C execution"""
    try:
        executable_path = temp_path / unique
        
        # Find gcc compiler
        compilers = ['/usr/bin/gcc', 'gcc']
        compiler = None
        
        for cmd in compilers:
            try:
                result = subprocess.run([cmd, '--version'], capture_output=True, timeout=3, text=True)
                if result.returncode == 0:
                    compiler = cmd
                    logger.debug(f"Found gcc: {cmd}")
                    break
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        if not compiler:
            logger.error("gcc compiler not found")
            return None
        
        # Compile
        compile_process = subprocess.run(
            [compiler, "-o", str(executable_path), str(code_file_path), 
             "-std=c99", "-O2", "-Wall", "-Wextra", "-lm"],
            capture_output=True,
            timeout=20,
            text=True
        )
        
        if compile_process.returncode != 0:
            logger.error(f"C compilation failed: {compile_process.stderr}")
            return None
        
        # Execute
        try:
            with open(input_file_path, "r", encoding='utf-8') as stdin_file:
                with open(output_file_path, "w", encoding='utf-8') as stdout_file:
                    process = subprocess.run(
                        [str(executable_path)],
                        stdin=stdin_file,
                        stdout=stdout_file,
                        stderr=subprocess.PIPE,
                        timeout=15,
                        text=True
                    )
                    
                    if process.returncode != 0:
                        logger.error(f"C execution failed: {process.stderr}")
                        return None
            
            # Read output
            if output_file_path.exists():
                with open(output_file_path, "r", encoding='utf-8') as f:
                    return f.read()
            else:
                logger.error("C output file not created")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("C execution timed out")
            return None
            
    except Exception as e:
        logger.error(f"C execution error: {str(e)}", exc_info=True)
        return None


# Legacy functions for backward compatibility
def run_code(language, code, input_data):
    """Legacy function - redirects to improved version"""
    return run_code_safe(language, code, input_data)

def detect_test_case_format(input_content, output_content):
    """Legacy function - redirects to improved detector"""
    return TestCaseFormatDetector.detect_format(input_content, output_content)

def parse_test_cases_smart(input_content, output_content):
    """Legacy function - redirects to improved parser"""
    format_info = TestCaseFormatDetector.detect_format(input_content, output_content)
    test_cases = []
    
    for i, (test_input, expected_output) in enumerate(format_info['pairs'], 1):
        test_cases.append({
            'input': test_input,
            'output': expected_output,
            'case_number': i,
            'is_multiline': '\n' in test_input
        })
    
    return test_cases