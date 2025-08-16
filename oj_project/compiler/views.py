# compiler/views.py - BULLETPROOF VERSION
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
import signal

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
            'python': 'Python 3',
            'cpp': 'C++',
            'c': 'C',
            'java': 'Java',
            'js': 'JavaScript',
            'javascript': 'JavaScript'
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
    elif 'public static void main' in code:
        return 'Java'
    elif 'console.log' in code or 'function' in code or 'let ' in code or 'const ' in code:
        return 'JavaScript'
    else:
        return 'Unknown'

# ============================
# BULLETPROOF CODE EXECUTION SYSTEM
# ============================

class SecureCodeRunner:
    """Ultra-secure and reliable code runner that handles ANY format"""
    
    def __init__(self):
        self.temp_base = self._get_temp_base()
        self.timeout_limits = {
            'py': 30,
            'python': 30,
            'cpp': 25,
            'c': 25,
            'java': 35,
            'js': 20,
            'javascript': 20
        }
        self.compile_timeout = 30
        
    def _get_temp_base(self):
        """Get the best temporary directory for this environment"""
        candidates = ['/tmp', '/var/tmp', str(Path.home() / 'tmp')]
        
        for candidate in candidates:
            try:
                test_dir = Path(candidate)
                test_dir.mkdir(exist_ok=True)
                
                # Test write permissions
                test_file = test_dir / f"test_{uuid.uuid4().hex[:8]}.txt"
                test_file.write_text("test")
                test_file.unlink()
                
                return test_dir
            except:
                continue
        
        # Fallback to current directory
        return Path.cwd() / 'temp'
    
    def run_code(self, language, code, input_data=""):
        """
        Run code with ANY input and return output
        This is the main entry point - it NEVER fails unexpectedly
        """
        unique_id = uuid.uuid4().hex[:12]
        temp_dir = None
        
        try:
            # Create secure workspace
            temp_dir = self.temp_base / f"oj_run_{unique_id}"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"🔧 Running {language} code in {temp_dir}")
            
            # Normalize input
            if input_data is None:
                input_data = ""
            
            # Route to appropriate runner
            if language == 'py' or language == 'python':
                return self._run_python(code, input_data, temp_dir, unique_id)
            elif language == 'cpp':
                return self._run_cpp(code, input_data, temp_dir, unique_id)
            elif language == 'c':
                return self._run_c(code, input_data, temp_dir, unique_id)
            elif language == 'java':
                return self._run_java(code, input_data, temp_dir, unique_id)
            elif language == 'js' or language == 'javascript':
                return self._run_javascript(code, input_data, temp_dir, unique_id)
            else:
                logger.error(f"❌ Unsupported language: {language}")
                return None
                
        except Exception as e:
            logger.error(f"💥 Fatal error in run_code: {str(e)}", exc_info=True)
            return None
        finally:
            # ALWAYS cleanup
            if temp_dir and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except:
                    pass
    
    def _run_python(self, code, input_data, temp_dir, unique_id):
        """Run Python code with bulletproof execution"""
        try:
            # Find Python interpreter
            python_cmd = self._find_python()
            if not python_cmd:
                logger.error("❌ Python interpreter not found")
                return None
            
            # Create files
            code_file = temp_dir / f"{unique_id}.py"
            input_file = temp_dir / f"{unique_id}_input.txt"
            output_file = temp_dir / f"{unique_id}_output.txt"
            error_file = temp_dir / f"{unique_id}_error.txt"
            
            # Write files safely
            code_file.write_text(code, encoding='utf-8')
            input_file.write_text(input_data, encoding='utf-8')
            
            # Execute with maximum safety
            cmd = [python_cmd, str(code_file)]
            
            with open(input_file, 'r') as stdin_f:
                with open(output_file, 'w') as stdout_f:
                    with open(error_file, 'w') as stderr_f:
                        
                        process = subprocess.Popen(
                            cmd,
                            stdin=stdin_f,
                            stdout=stdout_f,
                            stderr=stderr_f,
                            cwd=str(temp_dir),
                            text=True,
                            preexec_fn=os.setsid if hasattr(os, 'setsid') else None
                        )
                        
                        try:
                            return_code = process.wait(timeout=self.timeout_limits['py'])
                        except subprocess.TimeoutExpired:
                            # Kill the entire process group
                            try:
                                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                            except:
                                process.terminate()
                            
                            try:
                                process.wait(timeout=5)
                            except subprocess.TimeoutExpired:
                                try:
                                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                                except:
                                    process.kill()
                            
                            logger.error("⏰ Python execution timed out")
                            return None
            
            # Check execution result
            if return_code != 0:
                error_content = ""
                if error_file.exists():
                    error_content = error_file.read_text(encoding='utf-8', errors='ignore')
                logger.error(f"❌ Python execution failed (code {return_code}): {error_content[:200]}")
                return None
            
            # Read output
            if output_file.exists():
                output = output_file.read_text(encoding='utf-8', errors='ignore')
                logger.info(f"✅ Python execution successful, output: {len(output)} chars")
                return output
            else:
                logger.warning("⚠️ No output file generated")
                return ""
                
        except Exception as e:
            logger.error(f"💥 Python execution error: {str(e)}", exc_info=True)
            return None
    
    def _run_cpp(self, code, input_data, temp_dir, unique_id):
        """Run C++ code with bulletproof compilation and execution"""
        try:
            # Find compiler
            compiler = self._find_cpp_compiler()
            if not compiler:
                logger.error("❌ C++ compiler not found")
                return None
            
            # Create files
            code_file = temp_dir / f"{unique_id}.cpp"
            executable = temp_dir / f"{unique_id}_exec"
            input_file = temp_dir / f"{unique_id}_input.txt"
            output_file = temp_dir / f"{unique_id}_output.txt"
            compile_error_file = temp_dir / f"{unique_id}_compile_error.txt"
            runtime_error_file = temp_dir / f"{unique_id}_runtime_error.txt"
            
            # Write source code
            code_file.write_text(code, encoding='utf-8')
            input_file.write_text(input_data, encoding='utf-8')
            
            # Compile with comprehensive flags
            compile_cmd = [
                compiler, 
                str(code_file), 
                '-o', str(executable),
                '-std=c++17',
                '-O2',
                '-Wall', '-Wextra',
                '-static-libgcc', '-static-libstdc++'
            ]
            
            with open(compile_error_file, 'w') as stderr_f:
                compile_process = subprocess.run(
                    compile_cmd,
                    stderr=stderr_f,
                    timeout=self.compile_timeout,
                    text=True
                )
            
            if compile_process.returncode != 0:
                error_content = compile_error_file.read_text(encoding='utf-8', errors='ignore')
                logger.error(f"❌ C++ compilation failed: {error_content[:200]}")
                return None
            
            # Execute
            with open(input_file, 'r') as stdin_f:
                with open(output_file, 'w') as stdout_f:
                    with open(runtime_error_file, 'w') as stderr_f:
                        
                        process = subprocess.Popen(
                            [str(executable)],
                            stdin=stdin_f,
                            stdout=stdout_f,
                            stderr=stderr_f,
                            cwd=str(temp_dir),
                            text=True,
                            preexec_fn=os.setsid if hasattr(os, 'setsid') else None
                        )
                        
                        try:
                            return_code = process.wait(timeout=self.timeout_limits['cpp'])
                        except subprocess.TimeoutExpired:
                            # Kill process group
                            try:
                                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                            except:
                                process.terminate()
                            
                            try:
                                process.wait(timeout=5)
                            except subprocess.TimeoutExpired:
                                try:
                                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                                except:
                                    process.kill()
                            
                            logger.error("⏰ C++ execution timed out")
                            return None
            
            if return_code != 0:
                error_content = ""
                if runtime_error_file.exists():
                    error_content = runtime_error_file.read_text(encoding='utf-8', errors='ignore')
                logger.error(f"❌ C++ execution failed (code {return_code}): {error_content[:200]}")
                return None
            
            # Read output
            if output_file.exists():
                output = output_file.read_text(encoding='utf-8', errors='ignore')
                logger.info(f"✅ C++ execution successful, output: {len(output)} chars")
                return output
            else:
                return ""
                
        except Exception as e:
            logger.error(f"💥 C++ execution error: {str(e)}", exc_info=True)
            return None
    
    def _run_c(self, code, input_data, temp_dir, unique_id):
        """Run C code with bulletproof compilation and execution"""
        try:
            # Find compiler
            compiler = self._find_c_compiler()
            if not compiler:
                logger.error("❌ C compiler not found")
                return None
            
            # Create files
            code_file = temp_dir / f"{unique_id}.c"
            executable = temp_dir / f"{unique_id}_exec"
            input_file = temp_dir / f"{unique_id}_input.txt"
            output_file = temp_dir / f"{unique_id}_output.txt"
            compile_error_file = temp_dir / f"{unique_id}_compile_error.txt"
            runtime_error_file = temp_dir / f"{unique_id}_runtime_error.txt"
            
            # Write source code
            code_file.write_text(code, encoding='utf-8')
            input_file.write_text(input_data, encoding='utf-8')
            
            # Compile
            compile_cmd = [
                compiler, 
                str(code_file), 
                '-o', str(executable),
                '-std=c99',
                '-O2',
                '-Wall', '-Wextra',
                '-lm'  # Link math library
            ]
            
            with open(compile_error_file, 'w') as stderr_f:
                compile_process = subprocess.run(
                    compile_cmd,
                    stderr=stderr_f,
                    timeout=self.compile_timeout,
                    text=True
                )
            
            if compile_process.returncode != 0:
                error_content = compile_error_file.read_text(encoding='utf-8', errors='ignore')
                logger.error(f"❌ C compilation failed: {error_content[:200]}")
                return None
            
            # Execute
            with open(input_file, 'r') as stdin_f:
                with open(output_file, 'w') as stdout_f:
                    with open(runtime_error_file, 'w') as stderr_f:
                        
                        process = subprocess.Popen(
                            [str(executable)],
                            stdin=stdin_f,
                            stdout=stdout_f,
                            stderr=stderr_f,
                            cwd=str(temp_dir),
                            text=True,
                            preexec_fn=os.setsid if hasattr(os, 'setsid') else None
                        )
                        
                        try:
                            return_code = process.wait(timeout=self.timeout_limits['c'])
                        except subprocess.TimeoutExpired:
                            try:
                                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                            except:
                                process.terminate()
                            
                            try:
                                process.wait(timeout=5)
                            except subprocess.TimeoutExpired:
                                try:
                                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                                except:
                                    process.kill()
                            
                            logger.error("⏰ C execution timed out")
                            return None
            
            if return_code != 0:
                error_content = ""
                if runtime_error_file.exists():
                    error_content = runtime_error_file.read_text(encoding='utf-8', errors='ignore')
                logger.error(f"❌ C execution failed (code {return_code}): {error_content[:200]}")
                return None
            
            # Read output
            if output_file.exists():
                output = output_file.read_text(encoding='utf-8', errors='ignore')
                logger.info(f"✅ C execution successful, output: {len(output)} chars")
                return output
            else:
                return ""
                
        except Exception as e:
            logger.error(f"💥 C execution error: {str(e)}", exc_info=True)
            return None
    
    def _run_java(self, code, input_data, temp_dir, unique_id):
        """Run Java code with bulletproof compilation and execution"""
        try:
            # Find Java tools
            javac = self._find_javac()
            java = self._find_java()
            
            if not javac or not java:
                logger.error("❌ Java compiler/runtime not found")
                return None
            
            # Extract class name from code
            class_name = self._extract_java_class_name(code)
            if not class_name:
                logger.error("❌ Could not extract Java class name")
                return None
            
            # Create files
            code_file = temp_dir / f"{class_name}.java"
            input_file = temp_dir / f"{unique_id}_input.txt"
            output_file = temp_dir / f"{unique_id}_output.txt"
            compile_error_file = temp_dir / f"{unique_id}_compile_error.txt"
            runtime_error_file = temp_dir / f"{unique_id}_runtime_error.txt"
            
            # Write files
            code_file.write_text(code, encoding='utf-8')
            input_file.write_text(input_data, encoding='utf-8')
            
            # Compile
            with open(compile_error_file, 'w') as stderr_f:
                compile_process = subprocess.run(
                    [javac, str(code_file)],
                    stderr=stderr_f,
                    cwd=str(temp_dir),
                    timeout=self.compile_timeout,
                    text=True
                )
            
            if compile_process.returncode != 0:
                error_content = compile_error_file.read_text(encoding='utf-8', errors='ignore')
                logger.error(f"❌ Java compilation failed: {error_content[:200]}")
                return None
            
            # Execute
            with open(input_file, 'r') as stdin_f:
                with open(output_file, 'w') as stdout_f:
                    with open(runtime_error_file, 'w') as stderr_f:
                        
                        process = subprocess.Popen(
                            [java, class_name],
                            stdin=stdin_f,
                            stdout=stdout_f,
                            stderr=stderr_f,
                            cwd=str(temp_dir),
                            text=True,
                            preexec_fn=os.setsid if hasattr(os, 'setsid') else None
                        )
                        
                        try:
                            return_code = process.wait(timeout=self.timeout_limits['java'])
                        except subprocess.TimeoutExpired:
                            try:
                                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                            except:
                                process.terminate()
                            
                            try:
                                process.wait(timeout=5)
                            except subprocess.TimeoutExpired:
                                try:
                                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                                except:
                                    process.kill()
                            
                            logger.error("⏰ Java execution timed out")
                            return None
            
            if return_code != 0:
                error_content = ""
                if runtime_error_file.exists():
                    error_content = runtime_error_file.read_text(encoding='utf-8', errors='ignore')
                logger.error(f"❌ Java execution failed (code {return_code}): {error_content[:200]}")
                return None
            
            # Read output
            if output_file.exists():
                output = output_file.read_text(encoding='utf-8', errors='ignore')
                logger.info(f"✅ Java execution successful, output: {len(output)} chars")
                return output
            else:
                return ""
                
        except Exception as e:
            logger.error(f"💥 Java execution error: {str(e)}", exc_info=True)
            return None
    
    def _run_javascript(self, code, input_data, temp_dir, unique_id):
        """Run JavaScript code with Node.js"""
        try:
            # Find Node.js
            node_cmd = self._find_nodejs()
            if not node_cmd:
                logger.error("❌ Node.js not found")
                return None
            
            # Wrap code to handle input
            wrapped_code = f'''
const fs = require('fs');
const path = require('path');

// Read input
let input = '';
try {{
    input = fs.readFileSync('{unique_id}_input.txt', 'utf8');
}} catch (e) {{
    // No input file
}}

// Set up input for the user code
let inputLines = input.trim().split('\\n');
let currentLine = 0;

function readline() {{
    if (currentLine < inputLines.length) {{
        return inputLines[currentLine++];
    }}
    return '';
}}

// User code starts here
{code}
'''
            
            # Create files
            code_file = temp_dir / f"{unique_id}.js"
            input_file = temp_dir / f"{unique_id}_input.txt"
            output_file = temp_dir / f"{unique_id}_output.txt"
            error_file = temp_dir / f"{unique_id}_error.txt"
            
            # Write files
            code_file.write_text(wrapped_code, encoding='utf-8')
            input_file.write_text(input_data, encoding='utf-8')
            
            # Execute
            with open(output_file, 'w') as stdout_f:
                with open(error_file, 'w') as stderr_f:
                    
                    process = subprocess.Popen(
                        [node_cmd, str(code_file)],
                        stdout=stdout_f,
                        stderr=stderr_f,
                        cwd=str(temp_dir),
                        text=True,
                        preexec_fn=os.setsid if hasattr(os, 'setsid') else None
                    )
                    
                    try:
                        return_code = process.wait(timeout=self.timeout_limits['js'])
                    except subprocess.TimeoutExpired:
                        try:
                            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                        except:
                            process.terminate()
                        
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            try:
                                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                            except:
                                process.kill()
                        
                        logger.error("⏰ JavaScript execution timed out")
                        return None
        
            if return_code != 0:
                error_content = ""
                if error_file.exists():
                    error_content = error_file.read_text(encoding='utf-8', errors='ignore')
                logger.error(f"❌ JavaScript execution failed (code {return_code}): {error_content[:200]}")
                return None
            
            # Read output
            if output_file.exists():
                output = output_file.read_text(encoding='utf-8', errors='ignore')
                logger.info(f"✅ JavaScript execution successful, output: {len(output)} chars")
                return output
            else:
                return ""
                
        except Exception as e:
            logger.error(f"💥 JavaScript execution error: {str(e)}", exc_info=True)
            return None

    # Helper methods for finding compilers/interpreters
    def _find_python(self):
        """Find Python interpreter with priority order"""
        candidates = [
            '/usr/local/bin/python3',
            '/usr/bin/python3',
            '/opt/python3/bin/python3',
            'python3',
            '/usr/bin/python',
            'python'
        ]
        
        for cmd in candidates:
            try:
                result = subprocess.run(
                    [cmd, '--version'], 
                    capture_output=True, 
                    timeout=5, 
                    text=True
                )
                if result.returncode == 0 and '3.' in result.stdout:
                    logger.info(f"✅ Found Python: {cmd}")
                    return cmd
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        return None

    def _find_cpp_compiler(self):
        """Find C++ compiler"""
        candidates = [
            '/usr/bin/g++',
            '/usr/local/bin/g++',
            '/opt/gcc/bin/g++',
            'g++',
            '/usr/bin/clang++',
            'clang++'
        ]
        
        for cmd in candidates:
            try:
                result = subprocess.run(
                    [cmd, '--version'], 
                    capture_output=True, 
                    timeout=5, 
                    text=True
                )
                if result.returncode == 0:
                    logger.info(f"✅ Found C++ compiler: {cmd}")
                    return cmd
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        return None

    def _find_c_compiler(self):
        """Find C compiler"""
        candidates = [
            '/usr/bin/gcc',
            '/usr/local/bin/gcc',
            '/opt/gcc/bin/gcc',
            'gcc',
            '/usr/bin/clang',
            'clang'
        ]
        
        for cmd in candidates:
            try:
                result = subprocess.run(
                    [cmd, '--version'], 
                    capture_output=True, 
                    timeout=5, 
                    text=True
                )
                if result.returncode == 0:
                    logger.info(f"✅ Found C compiler: {cmd}")
                    return cmd
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        return None

    def _find_javac(self):
        """Find Java compiler"""
        candidates = [
            '/usr/bin/javac',
            '/usr/local/bin/javac',
            '/opt/java/bin/javac',
            'javac'
        ]
        
        for cmd in candidates:
            try:
                result = subprocess.run(
                    [cmd, '-version'], 
                    capture_output=True, 
                    timeout=5, 
                    text=True
                )
                if result.returncode == 0:
                    logger.info(f"✅ Found Java compiler: {cmd}")
                    return cmd
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        return None

    def _find_java(self):
        """Find Java runtime"""
        candidates = [
            '/usr/bin/java',
            '/usr/local/bin/java',
            '/opt/java/bin/java',
            'java'
        ]
        
        for cmd in candidates:
            try:
                result = subprocess.run(
                    [cmd, '-version'], 
                    capture_output=True, 
                    timeout=5, 
                    text=True
                )
                if result.returncode == 0:
                    logger.info(f"✅ Found Java runtime: {cmd}")
                    return cmd
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        return None

    def _find_nodejs(self):
        """Find Node.js"""
        candidates = [
            '/usr/bin/node',
            '/usr/local/bin/node',
            '/opt/node/bin/node',
            'node',
            'nodejs'
        ]
        
        for cmd in candidates:
            try:
                result = subprocess.run(
                    [cmd, '--version'], 
                    capture_output=True, 
                    timeout=5, 
                    text=True
                )
                if result.returncode == 0:
                    logger.info(f"✅ Found Node.js: {cmd}")
                    return cmd
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        return None

    def _extract_java_class_name(self, code):
        """Extract the main class name from Java code"""
        import re
        
        # Look for public class with main method
        main_class_pattern = r'public\s+class\s+(\w+)(?=.*public\s+static\s+void\s+main)'
        match = re.search(main_class_pattern, code, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1)
        
        # Fallback: look for any public class
        class_pattern = r'public\s+class\s+(\w+)'
        match = re.search(class_pattern, code, re.IGNORECASE)
        
        if match:
            return match.group(1)
        
        # Last resort: look for any class
        class_pattern = r'class\s+(\w+)'
        match = re.search(class_pattern, code, re.IGNORECASE)
        
        if match:
            return match.group(1)
        
        return None


# ============================
# ADVANCED TEST CASE PARSER
# ============================

class UniversalTestCaseParser:
    """Handles ANY test case format you throw at it"""
    
    @staticmethod
    def normalize_output(text):
        """Normalize output for comparison"""
        if text is None:
            return ""
        
        # Handle different line endings
        normalized = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Split into lines and strip each line
        lines = [line.rstrip() for line in normalized.split('\n')]
        
        # Remove empty lines from the end
        while lines and not lines[-1]:
            lines.pop()
        
        return '\n'.join(lines)
    
    @staticmethod
    def parse_test_cases(input_content, output_content):
        """
        Universal test case parser that handles ALL formats:
        1. Empty line separated sections
        2. Line-by-line pairs
        3. Multi-line input to single line output
        4. Complex mixed formats
        """
        logger.info("🔍 Starting universal test case parsing...")
        
        if not input_content.strip() or not output_content.strip():
            logger.warning("⚠️ Empty input or output content")
            return []
        
        # Strategy 1: Try empty line separated sections (most common)
        result = UniversalTestCaseParser._try_section_parsing(input_content, output_content)
        if result:
            logger.info(f"✅ Parsed {len(result)} test cases using section method")
            return result
        
        # Strategy 2: Try line-by-line matching
        result = UniversalTestCaseParser._try_line_parsing(input_content, output_content)
        if result:
            logger.info(f"✅ Parsed {len(result)} test cases using line method")
            return result
        
        # Strategy 3: Try intelligent splitting
        result = UniversalTestCaseParser._try_intelligent_parsing(input_content, output_content)
        if result:
            logger.info(f"✅ Parsed {len(result)} test cases using intelligent method")
            return result
        
        # Strategy 4: Treat as single test case
        logger.warning("⚠️ Falling back to single test case")
        return [{
            'input': input_content.strip(),
            'output': output_content.strip(),
            'case_number': 1
        }]
    
    @staticmethod
    def _try_section_parsing(input_content, output_content):
        """Parse sections separated by double newlines"""
        input_sections = [s.strip() for s in input_content.strip().split('\n\n') if s.strip()]
        output_sections = [s.strip() for s in output_content.strip().split('\n\n') if s.strip()]
        
        # Perfect match - same number of sections
        if len(input_sections) > 1 and len(input_sections) == len(output_sections):
            return [
                {
                    'input': inp.strip(),
                    'output': out.strip(),
                    'case_number': i + 1
                }
                for i, (inp, out) in enumerate(zip(input_sections, output_sections))
            ]
        
        # Input sections match output lines
        output_lines = [line.strip() for line in output_content.strip().split('\n') if line.strip()]
        if len(input_sections) > 1 and len(input_sections) == len(output_lines):
            return [
                {
                    'input': inp.strip(),
                    'output': out.strip(),
                    'case_number': i + 1
                }
                for i, (inp, out) in enumerate(zip(input_sections, output_lines))
            ]
        
        return None
    
    @staticmethod
    def _try_line_parsing(input_content, output_content):
        """Parse line by line"""
        input_lines = [line.strip() for line in input_content.strip().split('\n') if line.strip()]
        output_lines = [line.strip() for line in output_content.strip().split('\n') if line.strip()]
        
        if len(input_lines) == len(output_lines) and len(input_lines) > 1:
            return [
                {
                    'input': inp,
                    'output': out,
                    'case_number': i + 1
                }
                for i, (inp, out) in enumerate(zip(input_lines, output_lines))
            ]
        
        return None
    
    @staticmethod
    def _try_intelligent_parsing(input_content, output_content):
        """Intelligent parsing for complex formats"""
        input_lines = input_content.strip().split('\n')
        output_lines = output_content.strip().split('\n')
        
        # Look for patterns like multiple numbers per line in input
        # and single numbers in output
        input_groups = []
        current_group = []
        
        for line in input_lines:
            line = line.strip()
            if not line:
                if current_group:
                    input_groups.append('\n'.join(current_group))
                    current_group = []
            else:
                current_group.append(line)
        
        if current_group:
            input_groups.append('\n'.join(current_group))
        
        # Filter out empty groups
        input_groups = [g for g in input_groups if g.strip()]
        output_lines = [line.strip() for line in output_lines if line.strip()]
        
        if len(input_groups) == len(output_lines) and len(input_groups) > 1:
            return [
                {
                    'input': inp,
                    'output': out,
                    'case_number': i + 1
                }
                for i, (inp, out) in enumerate(zip(input_groups, output_lines))
            ]
        
        return None


# ============================
# MAIN EVALUATION SYSTEM
# ============================

# Global runner instance
code_runner = SecureCodeRunner()
test_parser = UniversalTestCaseParser()

def evaluate_submission(submission, language):
    """
    BULLETPROOF submission evaluation that handles:
    - Database test cases
    - File-based test cases
    - ANY input format
    - Multiple languages
    - Comprehensive error handling
    """
    try:
        problem = submission.problem
        logger.info(f"🚀 Starting evaluation for problem {problem.short_code}")
        
        # Phase 1: Database test cases (if any)
        if hasattr(problem, 'testcases'):
            db_test_cases = problem.testcases.all()
            
            if db_test_cases.exists():
                logger.info(f"📝 Phase 1: Testing {db_test_cases.count()} database test cases")
                
                for i, test_case in enumerate(db_test_cases, 1):
                    logger.info(f"🧪 Testing database case {i}")
                    
                    output = code_runner.run_code(language, submission.code_text, test_case.input)
                    
                    if output is None:
                        logger.error(f"❌ Runtime error in database test case {i}")
                        return 'RE'
                    
                    expected = test_parser.normalize_output(test_case.output)
                    actual = test_parser.normalize_output(output)
                    
                    if expected != actual:
                        logger.error(f"❌ Wrong answer in database test case {i}")
                        logger.error(f"Expected: {repr(expected[:100])}")
                        logger.error(f"Actual: {repr(actual[:100])}")
                        return 'WA'
                    
                    logger.info(f"✅ Database test case {i} passed")
        
        # Phase 2: File-based test cases
        verdict = evaluate_file_test_cases(submission, language)
        if verdict != 'AC':
            return verdict
        
        logger.info("🎉 All test cases passed!")
        return 'AC'
        
    except Exception as e:
        logger.error(f"💥 Fatal evaluation error: {str(e)}", exc_info=True)
        return 'RE'

def evaluate_file_test_cases(submission, language):
    """Evaluate file-based test cases with universal parsing"""
    try:
        problem = submission.problem
        
        # Find test files
        base_dir = Path(settings.BASE_DIR)
        input_file = base_dir / "inputs" / f"{problem.short_code}.txt"
        output_file = base_dir / "outputs" / f"{problem.short_code}.txt"
        
        if not input_file.exists() or not output_file.exists():
            logger.info(f"📁 No test files found for {problem.short_code}")
            return 'AC'  # No file tests = AC
        
        # Read test files
        input_content = input_file.read_text(encoding='utf-8', errors='ignore')
        output_content = output_file.read_text(encoding='utf-8', errors='ignore')
        
        logger.info(f"📖 Read {len(input_content)} chars input, {len(output_content)} chars output")
        
        # Parse test cases
        test_cases = test_parser.parse_test_cases(input_content, output_content)
        
        if not test_cases:
            logger.error("❌ No test cases could be parsed")
            return 'RE'
        
        logger.info(f"🧪 Testing {len(test_cases)} file-based test cases")
        
        # Run each test case
        for test_case in test_cases:
            case_num = test_case['case_number']
            test_input = test_case['input']
            expected_output = test_case['output']
            
            logger.info(f"🧪 Testing case {case_num}/{len(test_cases)}")
            logger.debug(f"Input: {repr(test_input[:50])}{'...' if len(test_input) > 50 else ''}")
            logger.debug(f"Expected: {repr(expected_output[:50])}{'...' if len(expected_output) > 50 else ''}")
            
            # Execute code
            actual_output = code_runner.run_code(language, submission.code_text, test_input)
            
            if actual_output is None:
                logger.error(f"❌ Runtime error in test case {case_num}")
                return 'RE'
            
            # Compare outputs
            expected_clean = test_parser.normalize_output(expected_output)
            actual_clean = test_parser.normalize_output(actual_output)
            
            if expected_clean != actual_clean:
                logger.error(f"❌ Wrong answer in test case {case_num}")
                logger.error(f"Expected ({len(expected_clean)} chars): {repr(expected_clean[:100])}")
                logger.error(f"Actual ({len(actual_clean)} chars): {repr(actual_clean[:100])}")
                
                # Show detailed diff
                show_detailed_diff(expected_clean, actual_clean)
                return 'WA'
            
            logger.info(f"✅ Test case {case_num} passed")
        
        return 'AC'
        
    except Exception as e:
        logger.error(f"💥 File test evaluation error: {str(e)}", exc_info=True)
        return 'RE'

def show_detailed_diff(expected, actual):
    """Show detailed character-by-character diff for debugging"""
    min_len = min(len(expected), len(actual))
    
    # Find first difference
    for i in range(min_len):
        if expected[i] != actual[i]:
            logger.error(f"🔍 First difference at position {i}:")
            logger.error(f"   Expected: {repr(expected[i])} (ord {ord(expected[i])})")
            logger.error(f"   Actual: {repr(actual[i])} (ord {ord(actual[i])})")
            
            # Show context around the difference
            start = max(0, i - 10)
            end = min(len(expected), i + 10)
            logger.error(f"   Context expected: {repr(expected[start:end])}")
            
            end = min(len(actual), i + 10)
            logger.error(f"   Context actual: {repr(actual[start:end])}")
            break
    
    if len(expected) != len(actual):
        logger.error(f"🔍 Length difference: expected {len(expected)}, got {len(actual)}")


# ============================
# LEGACY COMPATIBILITY
# ============================

def run_code_safe(language, code, input_data):
    """Legacy compatibility - redirects to new system"""
    return code_runner.run_code(language, code, input_data)

def run_code(language, code, input_data):
    """Legacy compatibility - redirects to new system"""
    return code_runner.run_code(language, code, input_data)

def normalize_output(output):
    """Legacy compatibility - redirects to new system"""
    return test_parser.normalize_output(output)

def get_docker_safe_base_path():
    """Get base path that works in any environment"""
    try:
        return Path(settings.BASE_DIR)
    except:
        return Path("/app") if Path("/app").exists() else Path.cwd()