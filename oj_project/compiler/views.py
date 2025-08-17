# compiler/views.py - UPDATED with Smart Test Case Parser
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
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
import stat
import asyncio
from asgiref.sync import sync_to_async
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View

# Set up logging
logger = logging.getLogger(__name__)

# Global thread pool for background tasks - optimized for Render
executor = ThreadPoolExecutor(max_workers=3)

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
            result = future.result(timeout=12)  # Reduced timeout for Render
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

def try_ai_review_with_model(submission, api_key, model_name, max_retries=1):
    """Ultra-optimized AI review for Render"""
    
    # Ultra-short prompt for fastest processing
    prompt = f"""
    Quick review for {get_language_display(submission)} solution:
    Problem: {submission.problem.name}
    Status: {submission.get_verdict_display()}

    Code:
    ```
    {submission.code_text[:1500]}
    ```

    Brief feedback:
    Rating: ⭐⭐⭐⭐⭐
    Time: O(?)
    Space: O(?)
    Tip: (one sentence)
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 300,  # Minimal tokens for speed
        }
    }
    
    try:
        response = requests.post(url, json=data, timeout=8)
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and result['candidates']:
                candidate = result['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    return {
                        'success': True,
                        'review': candidate['content']['parts'][0]['text']
                    }
        
    except Exception as e:
        logger.error(f"AI review failed: {str(e)}")
    
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
# SMART TEST CASE PARSER
# ============================

class SmartTestCaseParser:
    """
    Intelligent test case parser that automatically detects and handles:
    - Single line inputs with double newline separation
    - Multi-line inputs with double newline separation  
    - Mixed single/multi-line inputs
    - Various edge cases and formats
    """
    
    def __init__(self):
        # Use Django DEBUG setting and environment variables
        from django.conf import settings
        import os
        
        # Check multiple sources for debug mode
        self.debug_mode = (
            getattr(settings, 'DEBUG', False) or  # Django DEBUG setting
            os.environ.get('DEBUG', 'False').lower() == 'true' or  # ENV variable
            os.environ.get('PARSER_DEBUG', 'False').lower() == 'true'  # Specific parser debug
        )
    
    def parse_test_cases(self, input_content, output_content):
        """Main parsing function that intelligently detects format and parses accordingly"""
        if not input_content.strip() or not output_content.strip():
            self._error_log("❌ Empty input or output content")
            return []
        
        # Normalize line endings
        input_content = self._normalize_content(input_content)
        output_content = self._normalize_content(output_content)
        
        self._debug_log(f"📊 Content lengths: input={len(input_content)}, output={len(output_content)}")
        
        # Detect the format and parse accordingly
        format_type = self._detect_format(input_content, output_content)
        self._info_log(f"🔍 Detected format: {format_type}")
        
        if format_type == "double_newline_separated":
            return self._parse_double_newline_format(input_content, output_content)
        elif format_type == "single_line_per_case":
            return self._parse_single_line_format(input_content, output_content)
        elif format_type == "structured_multi_line":
            return self._parse_structured_format(input_content, output_content)
        elif format_type == "mixed_format":
            return self._parse_mixed_format(input_content, output_content)
        else:
            # Fallback: try all methods and return the best result
            return self._parse_with_fallback(input_content, output_content)
    
    def _normalize_content(self, content):
        """Normalize line endings and clean content"""
        return content.replace('\r\n', '\n').replace('\r', '\n').strip()
    
    def _detect_format(self, input_content, output_content):
        """Intelligently detect the test case format based on content analysis"""
        input_lines = input_content.split('\n')
        output_lines = output_content.split('\n')
        
        # Remove empty lines for analysis
        non_empty_input_lines = [line for line in input_lines if line.strip()]
        non_empty_output_lines = [line for line in output_lines if line.strip()]
        
        self._debug_log(f"📊 Lines: input={len(input_lines)}, output={len(output_lines)}")
        self._debug_log(f"📊 Non-empty lines: input={len(non_empty_input_lines)}, output={len(non_empty_output_lines)}")
        
        # Check for double newlines (indicating separated test cases)
        double_newlines_in_input = input_content.count('\n\n')
        double_newlines_in_output = output_content.count('\n\n')
        
        self._debug_log(f"🔍 Double newlines: input={double_newlines_in_input}, output={double_newlines_in_output}")
        
        # Pattern 1: Clear double newline separation
        if (double_newlines_in_input >= 1 and double_newlines_in_output >= 1 and 
            double_newlines_in_input == double_newlines_in_output):
            return "double_newline_separated"
        
        # Pattern 2: Equal number of non-empty lines (single line per case)
        if (len(non_empty_input_lines) == len(non_empty_output_lines) and 
            len(non_empty_input_lines) > 1):
            return "single_line_per_case"
        
        # Pattern 3: Structured format (like your MAXDPS problem)
        if self._is_structured_format(input_content):
            return "structured_multi_line"
        
        # Pattern 4: Mixed format detection
        if double_newlines_in_input > 0 or double_newlines_in_output > 0:
            return "mixed_format"
        
        return "unknown"
    
    def _is_structured_format(self, input_content):
        """Detect if input follows a structured pattern"""
        lines = [line.strip() for line in input_content.split('\n') if line.strip()]
        
        if len(lines) < 2:
            return False
        
        # Check if first few lines are numbers (indicating structure)
        numeric_starts = 0
        for i, line in enumerate(lines[:min(5, len(lines))]):
            if re.match(r'^\d+(\s+\d+)*$', line):
                numeric_starts += 1
        
        # If more than 60% of first few lines are numeric, likely structured
        return numeric_starts / min(5, len(lines)) > 0.6
    
    def _parse_double_newline_format(self, input_content, output_content):
        """Parse test cases separated by double newlines"""
        self._info_log("🔧 Using double newline parsing")
        
        # Split by double newlines and filter empty sections
        input_sections = [s.strip() for s in input_content.split('\n\n') if s.strip()]
        output_sections = [s.strip() for s in output_content.split('\n\n') if s.strip()]
        
        self._info_log(f"📊 Sections found: input={len(input_sections)}, output={len(output_sections)}")
        
        if len(input_sections) != len(output_sections):
            self._error_log(f"❌ Section count mismatch")
            return []
        
        test_cases = []
        for i, (inp, out) in enumerate(zip(input_sections, output_sections)):
            test_cases.append({
                'input': inp,
                'output': out,
                'case_number': i + 1
            })
            self._debug_log(f"✅ Case {i+1}: '{inp[:50]}...' -> '{out[:50]}...'")
        
        return test_cases
    
    def _parse_single_line_format(self, input_content, output_content):
        """Parse when each line is a separate test case"""
        self._debug_log("🔧 Using single line parsing")
        
        input_lines = [line.strip() for line in input_content.split('\n') if line.strip()]
        output_lines = [line.strip() for line in output_content.split('\n') if line.strip()]
        
        if len(input_lines) != len(output_lines):
            self._debug_log(f"❌ Line count mismatch: {len(input_lines)} vs {len(output_lines)}")
            return []
        
        test_cases = []
        for i, (inp, out) in enumerate(zip(input_lines, output_lines)):
            test_cases.append({
                'input': inp,
                'output': out,
                'case_number': i + 1
            })
            self._debug_log(f"✅ Case {i+1}: '{inp}' -> '{out}'")
        
        return test_cases
    
    def _parse_structured_format(self, input_content, output_content):
        """Parse structured format where test cases have variable lengths"""
        self._debug_log("🔧 Using structured parsing")
        
        input_lines = [line.strip() for line in input_content.split('\n') if line.strip()]
        output_lines = [line.strip() for line in output_content.split('\n') if line.strip()]
        
        test_cases = []
        input_idx = 0
        output_idx = 0
        case_num = 1
        
        while input_idx < len(input_lines) and output_idx < len(output_lines):
            try:
                # Try to determine case size from first line
                first_line = input_lines[input_idx]
                case_input_lines = [first_line]
                input_idx += 1
                
                # Parse numbers in first line to determine structure
                nums = [int(x) for x in first_line.split() if x.isdigit()]
                
                if len(nums) >= 1:
                    # Use first number as indicator of following lines
                    expected_lines = nums[0]
                    
                    # Read the expected number of lines
                    for _ in range(min(expected_lines, len(input_lines) - input_idx)):
                        if input_idx < len(input_lines):
                            case_input_lines.append(input_lines[input_idx])
                            input_idx += 1
                
                # Get corresponding output
                if output_idx < len(output_lines):
                    case_output = output_lines[output_idx]
                    output_idx += 1
                    
                    test_cases.append({
                        'input': '\n'.join(case_input_lines),
                        'output': case_output,
                        'case_number': case_num
                    })
                    
                    self._debug_log(f"✅ Structured case {case_num}: {len(case_input_lines)} input lines")
                    case_num += 1
                else:
                    break
                    
            except (ValueError, IndexError) as e:
                self._debug_log(f"❌ Error in structured parsing: {e}")
                break
        
        return test_cases
    
    def _parse_mixed_format(self, input_content, output_content):
        """Handle mixed format with some double newlines and some single lines"""
        self._debug_log("🔧 Using mixed format parsing")
        
        # Try double newline first, fall back if needed
        result = self._parse_double_newline_format(input_content, output_content)
        
        if not result:
            # Fallback to single line if double newline fails
            result = self._parse_single_line_format(input_content, output_content)
        
        return result
    
    def _parse_with_fallback(self, input_content, output_content):
        """Try all parsing methods and return the one with most reasonable results"""
        self._debug_log("🔧 Using fallback parsing - trying all methods")
        
        methods = [
            ("double_newline", self._parse_double_newline_format),
            ("single_line", self._parse_single_line_format),  
            ("structured", self._parse_structured_format),
        ]
        
        best_result = []
        best_score = 0
        
        for name, method in methods:
            try:
                result = method(input_content, output_content)
                score = self._score_parsing_result(result, input_content, output_content)
                
                self._debug_log(f"🔍 Method {name}: {len(result)} cases, score={score}")
                
                if score > best_score:
                    best_result = result
                    best_score = score
                    
            except Exception as e:
                self._debug_log(f"❌ Method {name} failed: {e}")
                continue
        
        self._debug_log(f"🎯 Best method produced {len(best_result)} test cases")
        return best_result
    
    def _score_parsing_result(self, test_cases, input_content, output_content):
        """Score a parsing result based on various quality metrics"""
        if not test_cases:
            return 0
        
        score = len(test_cases)  # Base score: number of test cases
        
        # Bonus points for reasonable case distribution
        total_chars = len(input_content) + len(output_content)
        avg_case_size = total_chars / len(test_cases) if test_cases else 0
        
        # Prefer results where cases have reasonable sizes (not too small/large)
        if 10 <= avg_case_size <= 1000:
            score += 10
        
        # Bonus for consistent case structure
        input_lengths = [len(case['input']) for case in test_cases]
        if len(set(input_lengths)) <= len(input_lengths) * 0.5:  # Less than 50% unique lengths
            score += 5
        
        return score
    
    def _debug_log(self, message):
        """Smart logging that adapts to environment"""
        if self.debug_mode:
            # In debug mode, log as INFO for visibility
            logger.info(f"[PARSER] {message}")
        else:
            # In production, log as DEBUG (won't show unless DEBUG level is set)
            logger.debug(f"[PARSER] {message}")
    
    def _error_log(self, message):
        """Always log errors regardless of debug mode"""
        logger.error(f"[PARSER] {message}")
    
    def _info_log(self, message):
        """Log important info regardless of debug mode"""
        logger.info(f"[PARSER] {message}")
    
    @staticmethod
    def normalize_output(text):
        """Normalize output for comparison"""
        if not text:
            return ""
        return text.replace('\r\n', '\n').replace('\r', '\n').rstrip()
    
    def detailed_comparison(self, expected, actual, case_number):
        """Detailed output comparison with extensive logging"""
        expected_clean = expected.strip()
        actual_clean = actual.strip()
        
        self._debug_log(f"🔍 Comparing test case {case_number}:")
        self._debug_log(f"  Expected: '{expected_clean}' (len={len(expected_clean)})")
        self._debug_log(f"  Actual:   '{actual_clean}' (len={len(actual_clean)})")
        
        if expected_clean == actual_clean:
            self._debug_log(f"✅ Test case {case_number}: PASS")
            return True
        
        self._error_log(f"❌ Test case {case_number}: FAIL")
        self._debug_log(f"Expected bytes: {expected_clean.encode()}")
        self._debug_log(f"Actual bytes:   {actual_clean.encode()}")
        
        # Character-by-character comparison for debugging
        min_len = min(len(expected_clean), len(actual_clean))
        for i in range(min_len):
            if expected_clean[i] != actual_clean[i]:
                self._debug_log(f"First difference at position {i}: expected '{expected_clean[i]}' (ord={ord(expected_clean[i])}), got '{actual_clean[i]}' (ord={ord(actual_clean[i])})")
                break
        
        if len(expected_clean) != len(actual_clean):
            self._debug_log(f"Length difference: expected {len(expected_clean)}, got {len(actual_clean)}")
        
        return False


# ============================
# RENDER-OPTIMIZED CODE EXECUTION
# ============================

class RenderOptimizedRunner:
    """Ultra-fast code runner optimized for Render platform"""
    
    def __init__(self):
        # Use /tmp for fastest I/O on Render
        self.temp_base = Path('/tmp')
        # Aggressive timeouts for Render
        self.timeout_limits = {
            'py': 8, 'python': 8,
            'cpp': 12, 'c': 10,
            'java': 10, 'js': 6
        }
        self.compile_timeout = 10
        
    def run_code(self, language, code, input_data="", timeout_override=None):
        """Render-optimized code execution with minimal overhead"""
        unique_id = uuid.uuid4().hex[:6]  # Shorter ID
        temp_dir = self.temp_base / f"oj_{unique_id}"
        
        try:
            temp_dir.mkdir(exist_ok=True)
            
            # Use timeout override if provided
            if timeout_override:
                original_timeout = self.timeout_limits.get(language, 8)
                self.timeout_limits[language] = min(timeout_override, 15)  # Cap at 15s for Render
            
            # Route to optimized runners
            result = None
            if language in ['py', 'python']:
                result = self._run_python_render(code, input_data, temp_dir, unique_id)
            elif language == 'cpp':
                result = self._run_cpp_render(code, input_data, temp_dir, unique_id)
            elif language == 'c':
                result = self._run_c_render(code, input_data, temp_dir, unique_id)
            elif language == 'java':
                result = self._run_java_render(code, input_data, temp_dir, unique_id)
            elif language in ['js', 'javascript']:
                result = self._run_js_render(code, input_data, temp_dir, unique_id)
            
            # Restore original timeout
            if timeout_override:
                self.timeout_limits[language] = original_timeout
                
            return result
                
        except Exception as e:
            logger.error(f"Execution error: {str(e)}")
            return None
        finally:
            # Ultra-fast cleanup
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass
    
    def _run_python_render(self, code, input_data, temp_dir, unique_id):
        """Render-optimized Python execution"""
        try:
            code_file = temp_dir / f"{unique_id}.py"
            
            # Write with minimal error handling for speed
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            # Execute with optimized settings
            result = subprocess.run(
                ['python3', str(code_file)],
                input=input_data,
                capture_output=True,
                text=True,
                timeout=self.timeout_limits['py'],
                cwd=str(temp_dir),
                env={'PYTHONUNBUFFERED': '1'}  # Faster output
            )
            
            return result.stdout if result.returncode == 0 else None
                
        except subprocess.TimeoutExpired:
            return None
        except Exception:
            return None
    
    def _run_cpp_render(self, code, input_data, temp_dir, unique_id):
        """Render-optimized C++ execution"""
        try:
            code_file = temp_dir / f"{unique_id}.cpp"
            executable = temp_dir / f"{unique_id}"
            
            # Write code file
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            # Fast compilation
            compile_result = subprocess.run(
                ['g++', '-std=c++17', '-O2', '-static', str(code_file), '-o', str(executable)],
                capture_output=True,
                text=True,
                timeout=self.compile_timeout,
                cwd=str(temp_dir)
            )
            
            if compile_result.returncode != 0:
                return None
            
            # Execute
            result = subprocess.run(
                [str(executable)],
                input=input_data,
                capture_output=True,
                text=True,
                timeout=self.timeout_limits['cpp'],
                cwd=str(temp_dir)
            )
            
            return result.stdout if result.returncode == 0 else None
                
        except subprocess.TimeoutExpired:
            return None
        except Exception:
            return None
    
    def _run_c_render(self, code, input_data, temp_dir, unique_id):
        """Render-optimized C execution"""
        try:
            code_file = temp_dir / f"{unique_id}.c"
            executable = temp_dir / f"{unique_id}"
            
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            # Compile
            compile_result = subprocess.run(
                ['gcc', '-std=c11', '-O2', '-static', str(code_file), '-o', str(executable)],
                capture_output=True,
                text=True,
                timeout=self.compile_timeout,
                cwd=str(temp_dir)
            )
            
            if compile_result.returncode != 0:
                return None
            
            # Execute
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
        except Exception:
            return None
    
    def _run_java_render(self, code, input_data, temp_dir, unique_id):
        """Render-optimized Java execution"""
        try:
            class_name = self._extract_java_class_name(code) or "Main"
            
            # Wrap in Main class if needed
            if "class" not in code.lower():
                code = f"public class Main {{\n{code}\n}}"
                class_name = "Main"
                
            code_file = temp_dir / f"{class_name}.java"
            
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            # Compile
            compile_result = subprocess.run(
                ['javac', str(code_file)],
                capture_output=True,
                text=True,
                timeout=self.compile_timeout,
                cwd=str(temp_dir)
            )
            
            if compile_result.returncode != 0:
                return None
            
            # Execute
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
        except Exception:
            return None
    
    def _run_js_render(self, code, input_data, temp_dir, unique_id):
        """Render-optimized JavaScript execution"""
        try:
            # Minimal input wrapper
            wrapped_code = f"""
const input = `{input_data}`;
const lines = input.trim().split('\\n');
let lineIndex = 0;
function readline() {{ return lines[lineIndex++] || ''; }}
{code}
"""
            
            code_file = temp_dir / f"{unique_id}.js"
            
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(wrapped_code)
            
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
        except Exception:
            return None
    
    def _extract_java_class_name(self, code):
        """Extract Java class name"""
        match = re.search(r'public\s+class\s+(\w+)', code, re.IGNORECASE)
        if match:
            return match.group(1)
        
        match = re.search(r'class\s+(\w+)', code, re.IGNORECASE)
        return match.group(1) if match else None


# ============================
# RENDER-OPTIMIZED EVALUATION WITH SMART PARSER
# ============================

# Global instances
code_runner = RenderOptimizedRunner()
smart_parser = SmartTestCaseParser()

def evaluate_submission(submission, language):
    """Render-optimized submission evaluation with smart test case parsing"""
    try:
        problem = submission.problem
        logger.info(f"🚀 Evaluating submission {submission.id} for problem {problem.short_code}")
        
        # Phase 1: Database test cases (visible)
        if hasattr(problem, 'testcases'):
            db_test_cases = problem.testcases.all()
            
            if db_test_cases.exists():
                logger.info(f"📝 Testing {db_test_cases.count()} visible test cases")
                
                for i, test_case in enumerate(db_test_cases, 1):
                    logger.info(f"🧪 Testing visible case {i}")
                    
                    # Execute with timeout
                    output = code_runner.run_code(
                        language, 
                        submission.code_text, 
                        test_case.input,
                        timeout_override=12  # Render-optimized timeout
                    )
                    
                    if output is None:
                        logger.error(f"❌ Execution failed in visible test case {i}")
                        return 'RE'
                    
                    expected = smart_parser.normalize_output(test_case.output)
                    actual = smart_parser.normalize_output(output)
                    
                    if not smart_parser.detailed_comparison(expected, actual, i):
                        return 'WA'
        
        # Phase 2: File-based test cases (hidden) with SMART PARSING
        verdict = evaluate_file_test_cases_smart(submission, language)
        if verdict != 'AC':
            return verdict
        
        logger.info("🎉 All test cases passed!")
        return 'AC'
        
    except Exception as e:
        logger.error(f"💥 Evaluation error: {str(e)}", exc_info=True)
        return 'RE'

def evaluate_file_test_cases_smart(submission, language):
    """Render-optimized file test case evaluation with INDIVIDUAL test case execution"""
    try:
        problem = submission.problem
        
        # Use correct file paths
        base_dir = Path(settings.BASE_DIR)
        input_file = base_dir / "inputs" / f"{problem.short_code}.txt"
        output_file = base_dir / "outputs" / f"{problem.short_code}.txt"
        
        logger.info(f"🔍 Looking for test files:")
        logger.info(f"   Input: {input_file} (exists: {input_file.exists()})")
        logger.info(f"   Output: {output_file} (exists: {output_file.exists()})")
        
        if not input_file.exists() or not output_file.exists():
            logger.info(f"No test files found for problem {problem.short_code} - accepting")
            return 'AC'
        
        # Read files with detailed logging
        try:
            input_content = input_file.read_text(encoding='utf-8', errors='replace')
            output_content = output_file.read_text(encoding='utf-8', errors='replace')
            logger.info(f"📖 Read files successfully:")
            logger.info(f"   Input: {len(input_content)} characters")
            logger.info(f"   Output: {len(output_content)} characters")
            logger.debug(f"   Input preview: {repr(input_content[:100])}")
            logger.debug(f"   Output preview: {repr(output_content[:100])}")
        except Exception as e:
            logger.error(f"Error reading test files: {str(e)}")
            return 'RE'
        
        # Parse test cases using SMART PARSER
        test_cases = smart_parser.parse_test_cases(input_content, output_content)
        
        if not test_cases:
            logger.error("❌ Failed to parse any test cases")
            return 'RE'
        
        logger.info(f"🎯 Successfully parsed {len(test_cases)} test cases, now executing individually...")
        
        # Execute each test case INDIVIDUALLY
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"🚀 Executing test case {i}/{len(test_cases)} individually")
            
            # Render-optimized timeout
            timeout = 15 if language == 'cpp' else 12
            
            # Run the code with ONLY this test case's input
            actual_output = code_runner.run_code(
                language, 
                submission.code_text, 
                test_case['input'],  # Only this test case's input
                timeout_override=timeout
            )
            
            if actual_output is None:
                logger.error(f"💥 Execution failed in test case {i}")
                return 'RE'
            
            # Compare outputs using detailed comparison
            expected = smart_parser.normalize_output(test_case['output'])
            actual = smart_parser.normalize_output(actual_output)
            
            if not smart_parser.detailed_comparison(expected, actual, i):
                logger.error(f"❌ Test case {i} failed comparison")
                logger.error(f"   Input: {test_case['input']}")
                logger.error(f"   Expected: {repr(expected)}")
                logger.error(f"   Got: {repr(actual)}")
                return 'WA'
            
            logger.info(f"✅ Test case {i} passed")
        
        logger.info(f"🎉 All {len(test_cases)} test cases passed!")
        return 'AC'
        
    except Exception as e:
        logger.error(f"💥 File test evaluation error: {str(e)}", exc_info=True)
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
    return smart_parser.normalize_output(output)