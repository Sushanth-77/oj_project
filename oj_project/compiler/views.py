# compiler/views.py - FIXED VERSION
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
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import stat

# Set up logging
logger = logging.getLogger(__name__)

# Global thread pool for background tasks
executor = ThreadPoolExecutor(max_workers=2)

@login_required
def ai_review_submission(request, submission_id):
    """Get AI review for a submission using Gemini LLM with optimized retry logic"""
    submission = get_object_or_404(Submission, id=submission_id, user=request.user)
    
    try:
        # Get Gemini API key from settings
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            return JsonResponse({
                'success': False,
                'error': 'AI review service is not configured.'
            })
        
        # Use only the most reliable model for faster response
        model_name = 'gemini-1.5-flash-latest'
        
        # Run AI review with timeout
        try:
            future = executor.submit(try_ai_review_with_model, submission, api_key, model_name)
            result = future.result(timeout=15)  # 15 second timeout
            return JsonResponse(result)
        except TimeoutError:
            return JsonResponse({
                'success': False,
                'error': 'AI review timed out. Please try again.'
            })
            
    except Exception as e:
        logger.error(f"AI review error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'AI service temporarily unavailable.'
        })

def try_ai_review_with_model(submission, api_key, model_name, max_retries=2):
    """Optimized AI review with minimal retries"""
    
    # Shorter, focused prompt for faster processing
    prompt = f"""
    Review this {get_language_display(submission)} solution for problem: {submission.problem.name}
    Status: {submission.get_verdict_display()}

    Code:
    ```
    {submission.code_text[:2000]}  # Limit code length
    ```

    Provide brief feedback on:
    1. Rating: ⭐⭐⭐⭐⭐
    2. Time complexity: O(?)  
    3. Space complexity: O(?)
    4. Main improvement suggestion

    Be concise and constructive.
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 512,  # Reduced for faster response
        }
    }
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                time.sleep(1)  # Minimal backoff
            
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and result['candidates']:
                    candidate = result['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        return {
                            'success': True,
                            'review': candidate['content']['parts'][0]['text']
                        }
            
            elif response.status_code in [503, 429]:
                if attempt < max_retries - 1:
                    continue
                    
        except Exception as e:
            logger.error(f"AI review attempt {attempt + 1} failed: {str(e)}")
            if attempt == max_retries - 1:
                break
    
    return {
        'success': False,
        'error': 'AI review temporarily unavailable.'
    }

def get_language_display(submission):
    """Optimized language detection"""
    if hasattr(submission, 'language') and submission.language:
        return {
            'py': 'Python', 'python': 'Python',
            'cpp': 'C++', 'c': 'C',
            'java': 'Java', 'js': 'JavaScript'
        }.get(submission.language, submission.language)
    
    # Quick code detection
    code = submission.code_text[:200].lower()
    if 'def ' in code or 'print(' in code: return 'Python'
    elif '#include' in code: return 'C++' if 'cout' in code else 'C'
    elif 'public class' in code: return 'Java'
    elif 'function' in code or 'console.log' in code: return 'JavaScript'
    return 'Unknown'

# ============================
# FIXED CODE EXECUTION
# ============================

class RenderOptimizedRunner:
    """Fixed code runner with proper error handling"""
    
    def __init__(self):
        # Use /tmp which is fastest on most cloud platforms
        self.temp_base = Path('/tmp')
        self.timeout_limits = {
            'py': 10, 'python': 10,
            'cpp': 15, 'c': 15,  # Increased timeout for C++
            'java': 12, 'js': 8
        }
        self.compile_timeout = 15  # Increased compile timeout
        
    def run_code(self, language, code, input_data="", timeout_override=None):
        """Fixed code execution with proper timeout handling"""
        unique_id = uuid.uuid4().hex[:8]
        temp_dir = self.temp_base / f"oj_{unique_id}"
        
        try:
            temp_dir.mkdir(exist_ok=True)
            
            # Use timeout override if provided
            if timeout_override:
                original_timeout = self.timeout_limits.get(language, 10)
                self.timeout_limits[language] = timeout_override
            
            # Route to optimized runners
            result = None
            if language in ['py', 'python']:
                result = self._run_python_fast(code, input_data, temp_dir, unique_id)
            elif language == 'cpp':
                result = self._run_cpp_fast(code, input_data, temp_dir, unique_id)
            elif language == 'c':
                result = self._run_c_fast(code, input_data, temp_dir, unique_id)
            elif language == 'java':
                result = self._run_java_fast(code, input_data, temp_dir, unique_id)
            elif language in ['js', 'javascript']:
                result = self._run_js_fast(code, input_data, temp_dir, unique_id)
            
            # Restore original timeout
            if timeout_override:
                self.timeout_limits[language] = original_timeout
                
            return result
                
        except Exception as e:
            logger.error(f"Execution error: {str(e)}")
            return None
        finally:
            # Fast cleanup
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass
    
    def _run_python_fast(self, code, input_data, temp_dir, unique_id):
        """Fixed Python execution"""
        try:
            code_file = temp_dir / f"{unique_id}.py"
            code_file.write_text(code, encoding='utf-8')
            
            try:
                result = subprocess.run(
                    ['python3', str(code_file)],
                    input=input_data,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_limits['py'],
                    cwd=str(temp_dir)
                )
                
                if result.returncode == 0:
                    return result.stdout
                else:
                    logger.error(f"Python error: {result.stderr[:200]}")
                    return None
                    
            except subprocess.TimeoutExpired:
                logger.error("Python execution timeout")
                return None
            except FileNotFoundError:
                logger.error("Python3 not found")
                return None
                
        except Exception as e:
            logger.error(f"Python execution error: {str(e)}")
            return None
    
    def _run_cpp_fast(self, code, input_data, temp_dir, unique_id):
        """Fixed C++ execution with better error handling"""
        try:
            code_file = temp_dir / f"{unique_id}.cpp"
            executable = temp_dir / f"{unique_id}_exe"
            
            # Write code file
            try:
                code_file.write_text(code, encoding='utf-8')
            except Exception as e:
                logger.error(f"Error writing C++ file: {str(e)}")
                return None
            
            # Compilation with better flags
            try:
                compile_result = subprocess.run(
                    ['g++', '-std=c++17', str(code_file), '-o', str(executable), '-O2'],
                    capture_output=True,
                    text=True,
                    timeout=self.compile_timeout,
                    cwd=str(temp_dir)
                )
                
                if compile_result.returncode != 0:
                    logger.error(f"C++ compile error: {compile_result.stderr[:200]}")
                    return None
                    
            except subprocess.TimeoutExpired:
                logger.error("C++ compilation timeout")
                return None
            except FileNotFoundError:
                logger.error("g++ compiler not found")
                return None
            
            # Make executable
            try:
                os.chmod(str(executable), stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
            except:
                pass  # Ignore chmod errors
            
            # Execute
            try:
                result = subprocess.run(
                    [str(executable)],
                    input=input_data,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_limits['cpp'],
                    cwd=str(temp_dir)
                )
                
                if result.returncode == 0:
                    return result.stdout
                else:
                    logger.error(f"C++ runtime error: {result.stderr[:200]}")
                    return None
                
            except subprocess.TimeoutExpired:
                logger.error("C++ execution timeout")
                return None
                
        except Exception as e:
            logger.error(f"C++ execution error: {str(e)}")
            return None
    
    def _run_c_fast(self, code, input_data, temp_dir, unique_id):
        """Fixed C execution"""
        try:
            code_file = temp_dir / f"{unique_id}.c"
            executable = temp_dir / f"{unique_id}_exe"
            
            code_file.write_text(code, encoding='utf-8')
            
            # Compile
            try:
                compile_result = subprocess.run(
                    ['gcc', '-std=c11', str(code_file), '-o', str(executable), '-O2'],
                    capture_output=True,
                    text=True,
                    timeout=self.compile_timeout,
                    cwd=str(temp_dir)
                )
                
                if compile_result.returncode != 0:
                    logger.error(f"C compile error: {compile_result.stderr[:200]}")
                    return None
                    
            except subprocess.TimeoutExpired:
                return None
            except FileNotFoundError:
                logger.error("gcc compiler not found")
                return None
            
            # Make executable
            try:
                os.chmod(str(executable), stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
            except:
                pass
            
            # Execute
            try:
                result = subprocess.run(
                    [str(executable)],
                    input=input_data,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_limits['c'],
                    cwd=str(temp_dir)
                )
                
                return result.stdout if result.returncode == 0 else None
                
            except subprocess.TimeoutExpired:
                return None
                
        except Exception as e:
            logger.error(f"C execution error: {str(e)}")
            return None
    
    def _run_java_fast(self, code, input_data, temp_dir, unique_id):
        """Fixed Java execution"""
        try:
            class_name = self._extract_java_class_name(code)
            if not class_name:
                class_name = "Main"  # Default class name
                # Wrap code in Main class if needed
                if "class" not in code:
                    code = f"public class Main {{\n{code}\n}}"
                
            code_file = temp_dir / f"{class_name}.java"
            code_file.write_text(code, encoding='utf-8')
            
            # Compile
            try:
                compile_result = subprocess.run(
                    ['javac', str(code_file)],
                    capture_output=True,
                    text=True,
                    timeout=self.compile_timeout,
                    cwd=str(temp_dir)
                )
                
                if compile_result.returncode != 0:
                    logger.error(f"Java compile error: {compile_result.stderr[:200]}")
                    return None
                    
            except subprocess.TimeoutExpired:
                return None
            except FileNotFoundError:
                logger.error("javac not found")
                return None
            
            # Execute
            try:
                result = subprocess.run(
                    ['java', class_name],
                    input=input_data,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_limits['java'],
                    cwd=str(temp_dir)
                )
                
                return result.stdout if result.returncode == 0 else None
                
            except subprocess.TimeoutExpired:
                return None
                
        except Exception as e:
            logger.error(f"Java execution error: {str(e)}")
            return None
    
    def _run_js_fast(self, code, input_data, temp_dir, unique_id):
        """Fixed JavaScript execution"""
        try:
            # Simple input wrapper for Node.js
            wrapped_code = f"""
const input = `{input_data}`;
const lines = input.trim().split('\\n');
let lineIndex = 0;
function readline() {{ return lines[lineIndex++] || ''; }}

{code}
"""
            
            code_file = temp_dir / f"{unique_id}.js"
            code_file.write_text(wrapped_code, encoding='utf-8')
            
            try:
                result = subprocess.run(
                    ['node', str(code_file)],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_limits['js'],
                    cwd=str(temp_dir)
                )
                
                return result.stdout if result.returncode == 0 else None
                
            except subprocess.TimeoutExpired:
                return None
            except FileNotFoundError:
                logger.error("node not found")
                return None
                
        except Exception as e:
            logger.error(f"JavaScript execution error: {str(e)}")
            return None
    
    def _extract_java_class_name(self, code):
        """Extract Java class name"""
        match = re.search(r'public\s+class\s+(\w+)', code, re.IGNORECASE)
        if match:
            return match.group(1)
        
        match = re.search(r'class\s+(\w+)', code, re.IGNORECASE)
        return match.group(1) if match else None


# ============================
# FIXED TEST CASE HANDLING
# ============================

class FastTestParser:
    """Fixed test case parser with better spacing handling"""
    
    @staticmethod
    def normalize_output(text):
        """Fixed output normalization"""
        if not text:
            return ""
        # Replace different line endings but preserve internal newlines
        normalized = text.replace('\r\n', '\n').replace('\r', '\n')
        # Only strip trailing whitespace, preserve leading/internal whitespace
        return normalized.rstrip()
    
    @staticmethod
    def parse_test_cases(input_content, output_content):
        """Enhanced test case parsing with multiple strategies"""
        if not input_content.strip() or not output_content.strip():
            logger.warning("Empty input or output content")
            return []
        
        logger.info("Starting enhanced test case parsing...")
        
        # Strategy 1: Multiple empty lines (2 or more newlines)
        input_sections = FastTestParser._split_by_multiple_newlines(input_content)
        output_sections = FastTestParser._split_by_multiple_newlines(output_content)
        
        logger.info(f"Multiple newlines strategy: {len(input_sections)} inputs, {len(output_sections)} outputs")
        
        if len(input_sections) > 1 and len(input_sections) == len(output_sections):
            return FastTestParser._create_test_cases(input_sections, output_sections, "multiple newlines")
        
        # Strategy 2: Double newline separation
        input_sections = FastTestParser._split_by_double_newlines(input_content)
        output_sections = FastTestParser._split_by_double_newlines(output_content)
        
        logger.info(f"Double newlines strategy: {len(input_sections)} inputs, {len(output_sections)} outputs")
        
        if len(input_sections) > 1 and len(input_sections) == len(output_sections):
            return FastTestParser._create_test_cases(input_sections, output_sections, "double newlines")
        
        # Strategy 3: Blank line separation (single empty line)
        input_sections = FastTestParser._split_by_blank_lines(input_content)
        output_sections = FastTestParser._split_by_blank_lines(output_content)
        
        logger.info(f"Blank lines strategy: {len(input_sections)} inputs, {len(output_sections)} outputs")
        
        if len(input_sections) > 1 and len(input_sections) == len(output_sections):
            return FastTestParser._create_test_cases(input_sections, output_sections, "blank lines")
        
        # Strategy 4: Line-by-line matching (each non-empty line is a test case)
        input_lines = [line.strip() for line in input_content.strip().split('\n') if line.strip()]
        output_lines = [line.strip() for line in output_content.strip().split('\n') if line.strip()]
        
        logger.info(f"Line-by-line strategy: {len(input_lines)} inputs, {len(output_lines)} outputs")
        
        if len(input_lines) == len(output_lines) and len(input_lines) > 0:
            logger.info(f"Using line-by-line mapping: {len(input_lines)} cases")
            return [
                {'input': inp, 'output': out, 'case_number': i + 1}
                for i, (inp, out) in enumerate(zip(input_lines, output_lines))
            ]
        
        # Final fallback: Single test case
        logger.info("Using single test case fallback")
        return [{
            'input': input_content.strip(), 
            'output': output_content.strip(), 
            'case_number': 1
        }]
    
    @staticmethod
    def _split_by_multiple_newlines(content):
        """Split content by multiple consecutive newlines (2 or more)"""
        if not content.strip():
            return []
        
        import re
        normalized = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # Split on 2 or more consecutive newlines
        raw_sections = re.split(r'\n{2,}', normalized)
        
        sections = []
        for section in raw_sections:
            section = section.strip()
            if section:
                sections.append(section)
        
        return sections
    
    @staticmethod
    def _split_by_double_newlines(content):
        """Split content by exactly double newlines"""
        if not content.strip():
            return []
        
        normalized = content.replace('\r\n', '\n').replace('\r', '\n')
        raw_sections = normalized.split('\n\n')
        
        sections = []
        for section in raw_sections:
            section = section.strip()
            if section:
                sections.append(section)
        
        return sections
    
    @staticmethod
    def _split_by_blank_lines(content):
        """Split content by single blank lines"""
        if not content.strip():
            return []
        
        normalized = content.replace('\r\n', '\n').replace('\r', '\n')
        lines = normalized.split('\n')
        
        sections = []
        current_section = []
        
        for line in lines:
            if line.strip() == '':  # Empty line
                if current_section:
                    sections.append('\n'.join(current_section).strip())
                    current_section = []
            else:
                current_section.append(line)
        
        # Add last section if it exists
        if current_section:
            sections.append('\n'.join(current_section).strip())
        
        return [s for s in sections if s]  # Filter out empty sections
    
    @staticmethod
    def _create_test_cases(input_sections, output_sections, strategy_name):
        """Create test cases from sections"""
        test_cases = []
        for i, (inp, out) in enumerate(zip(input_sections, output_sections)):
            test_cases.append({
                'input': inp.strip(),
                'output': out.strip(), 
                'case_number': i + 1
            })
            logger.debug(f"Test case {i+1}: Input={repr(inp[:50])}, Output={repr(out[:50])}")
        
        logger.info(f"Successfully parsed {len(test_cases)} test cases using {strategy_name} method")
        return test_cases


# ============================
# FIXED EVALUATION SYSTEM
# ============================

# Global instances
code_runner = RenderOptimizedRunner()
test_parser = FastTestParser()

def evaluate_submission(submission, language):
    """Fixed submission evaluation"""
    try:
        problem = submission.problem
        logger.info(f"🚀 Starting evaluation for problem {problem.short_code}")
        
        # Phase 1: Database test cases (visible test cases)
        if hasattr(problem, 'testcases'):
            db_test_cases = problem.testcases.all()
            
            if db_test_cases.exists():
                logger.info(f"📝 Phase 1: Testing {db_test_cases.count()} visible database test cases")
                
                for i, test_case in enumerate(db_test_cases, 1):
                    logger.info(f"🧪 Testing visible case {i}/{db_test_cases.count()}")
                    
                    # Execute code
                    output = code_runner.run_code(
                        language, 
                        submission.code_text, 
                        test_case.input,
                        timeout_override=15
                    )
                    
                    if output is None:
                        logger.error(f"❌ Runtime error/timeout in visible test case {i}")
                        return 'RE'
                    
                    expected = test_parser.normalize_output(test_case.output)
                    actual = test_parser.normalize_output(output)
                    
                    if expected != actual:
                        logger.error(f"❌ Wrong answer in visible test case {i}")
                        logger.error(f"Expected: {repr(expected)}")
                        logger.error(f"Actual: {repr(actual)}")
                        return 'WA'
                    
                    logger.info(f"✅ Visible test case {i} passed")
        
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
    """Fixed file-based test case evaluation"""
    try:
        problem = submission.problem
        
        # Use BASE_DIR from settings
        base_dir = Path(settings.BASE_DIR)
        input_file = base_dir / "inputs" / f"{problem.short_code}.txt"
        output_file = base_dir / "outputs" / f"{problem.short_code}.txt"
        
        if not input_file.exists() or not output_file.exists():
            logger.info(f"No test files found for problem {problem.short_code}")
            return 'AC'  # No test files = accepted
        
        # Read files
        try:
            input_content = input_file.read_text(encoding='utf-8', errors='replace')
            output_content = output_file.read_text(encoding='utf-8', errors='replace')
            logger.info(f"Read test files: input={len(input_content)} chars, output={len(output_content)} chars")
        except Exception as e:
            logger.error(f"Error reading test files: {str(e)}")
            return 'RE'
        
        # Parse test cases
        test_cases = test_parser.parse_test_cases(input_content, output_content)
        
        if not test_cases:
            logger.error("Failed to parse any test cases from files")
            return 'RE'
        
        logger.info(f"Successfully parsed {len(test_cases)} hidden test cases")
        
        # Run test cases
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"Executing hidden test case {i}/{len(test_cases)}")
            
            # Use longer timeout for hidden tests
            timeout = 20 if language == 'cpp' else 15
            
            actual_output = code_runner.run_code(
                language, 
                submission.code_text, 
                test_case['input'],
                timeout_override=timeout
            )
            
            if actual_output is None:
                logger.error(f"Runtime error/timeout in hidden test case {i}")
                return 'RE'
            
            # Normalize outputs
            expected = test_parser.normalize_output(test_case['output'])
            actual = test_parser.normalize_output(actual_output)
            
            # Compare
            if not test_parser.detailed_comparison(expected, actual, i):
                return 'WA'
            
            logger.info(f"✅ Hidden test case {i} passed")
        
        logger.info(f"🎉 All {len(test_cases)} hidden test cases passed!")
        return 'AC'
        
    except Exception as e:
        logger.error(f"File test evaluation error: {str(e)}", exc_info=True)
        return 'RE'

# Legacy compatibility functions
def run_code_safe(language, code, input_data):
    """Legacy compatibility"""
    return code_runner.run_code(language, code, input_data)

def run_code(language, code, input_data):
    """Legacy compatibility"""
    return code_runner.run_code(language, code, input_data)

def normalize_output(output):
    """Legacy compatibility"""
    return test_parser.normalize_output(output)