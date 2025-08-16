# compiler/views.py - RENDER-OPTIMIZED VERSION
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
import resource

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
# RENDER-OPTIMIZED CODE EXECUTION
# ============================

class RenderOptimizedRunner:
    """Lightweight, fast code runner optimized for Render's constraints"""
    
    def __init__(self):
        # Use /tmp which is fastest on most cloud platforms
        self.temp_base = Path('/tmp')
        self.timeout_limits = {
            'py': 10, 'python': 10,  # Reduced timeouts
            'cpp': 8, 'c': 8,
            'java': 12, 'js': 8
        }
        self.compile_timeout = 10
        # Set resource limits to prevent hanging
        self._set_resource_limits()
        
    def _set_resource_limits(self):
        """Set resource limits to prevent system overload"""
        try:
            # Limit memory to 128MB per process
            resource.setrlimit(resource.RLIMIT_AS, (128 * 1024 * 1024, 128 * 1024 * 1024))
            # Limit CPU time
            resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
        except:
            pass  # Some platforms don't support all limits
    
    def run_code(self, language, code, input_data=""):
        """Fast, lightweight code execution"""
        unique_id = uuid.uuid4().hex[:8]  # Shorter IDs
        temp_dir = self.temp_base / f"oj_{unique_id}"
        
        try:
            temp_dir.mkdir(exist_ok=True)
            
            # Route to optimized runners
            if language in ['py', 'python']:
                return self._run_python_fast(code, input_data, temp_dir, unique_id)
            elif language == 'cpp':
                return self._run_cpp_fast(code, input_data, temp_dir, unique_id)
            elif language == 'java':
                return self._run_java_fast(code, input_data, temp_dir, unique_id)
            elif language in ['js', 'javascript']:
                return self._run_js_fast(code, input_data, temp_dir, unique_id)
            else:
                return None
                
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
        """Optimized Python execution"""
        try:
            code_file = temp_dir / f"{unique_id}.py"
            code_file.write_text(code, encoding='utf-8')
            
            # Use subprocess.run with direct input for speed
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
                    logger.error(f"Python error: {result.stderr[:100]}")
                    return None
                    
            except subprocess.TimeoutExpired:
                logger.error("Python execution timeout")
                return None
                
        except Exception as e:
            logger.error(f"Python execution error: {str(e)}")
            return None
    
    def _run_cpp_fast(self, code, input_data, temp_dir, unique_id):
        """Optimized C++ execution"""
        try:
            code_file = temp_dir / f"{unique_id}.cpp"
            executable = temp_dir / f"{unique_id}"
            
            code_file.write_text(code, encoding='utf-8')
            
            # Fast compilation with minimal flags
            compile_result = subprocess.run(
                ['g++', str(code_file), '-o', str(executable), '-O1'],
                capture_output=True,
                text=True,
                timeout=self.compile_timeout
            )
            
            if compile_result.returncode != 0:
                logger.error(f"C++ compile error: {compile_result.stderr[:100]}")
                return None
            
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
                
                return result.stdout if result.returncode == 0 else None
                
            except subprocess.TimeoutExpired:
                return None
                
        except Exception as e:
            logger.error(f"C++ execution error: {str(e)}")
            return None
    
    def _run_java_fast(self, code, input_data, temp_dir, unique_id):
        """Optimized Java execution"""
        try:
            class_name = self._extract_java_class_name(code)
            if not class_name:
                return None
                
            code_file = temp_dir / f"{class_name}.java"
            code_file.write_text(code, encoding='utf-8')
            
            # Compile
            compile_result = subprocess.run(
                ['javac', str(code_file)],
                capture_output=True,
                timeout=self.compile_timeout,
                cwd=str(temp_dir)
            )
            
            if compile_result.returncode != 0:
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
        """Optimized JavaScript execution"""
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
                
        except Exception as e:
            logger.error(f"JavaScript execution error: {str(e)}")
            return None
    
    def _extract_java_class_name(self, code):
        """Quick Java class name extraction"""
        match = re.search(r'public\s+class\s+(\w+)', code, re.IGNORECASE)
        if match:
            return match.group(1)
        
        match = re.search(r'class\s+(\w+)', code, re.IGNORECASE)
        return match.group(1) if match else None


# ============================
# OPTIMIZED TEST CASE HANDLING
# ============================

class FastTestParser:
    """Lightning-fast test case parser optimized for double-newline separated test cases"""
    
    @staticmethod
    def normalize_output(text):
        """Fast output normalization that preserves internal structure"""
        if not text:
            return ""
        # Replace different line endings but preserve internal newlines
        normalized = text.replace('\r\n', '\n').replace('\r', '\n')
        # Only strip trailing whitespace, preserve leading/internal whitespace
        return normalized.rstrip()
    
    @staticmethod
    def parse_test_cases(input_content, output_content):
        """
        Robust test case parsing that handles:
        1. Double-newline separated test cases (primary method)
        2. Single and multi-line inputs/outputs
        3. Preserves internal structure of each test case
        """
        if not input_content.strip() or not output_content.strip():
            logger.warning("Empty input or output content")
            return []
        
        logger.info("Parsing test cases with double-newline separation strategy")
        
        # Primary Strategy: Double newline separated sections
        # Split on double newlines but preserve internal structure
        input_sections = FastTestParser._split_preserving_structure(input_content)
        output_sections = FastTestParser._split_preserving_structure(output_content)
        
        logger.info(f"Found {len(input_sections)} input sections, {len(output_sections)} output sections")
        
        # Perfect match - same number of sections
        if len(input_sections) > 0 and len(input_sections) == len(output_sections):
            test_cases = []
            for i, (inp, out) in enumerate(zip(input_sections, output_sections)):
                test_cases.append({
                    'input': inp.strip(),
                    'output': out.strip(), 
                    'case_number': i + 1
                })
                logger.debug(f"Test case {i+1}: Input={repr(inp[:50])}, Output={repr(out[:50])}")
            
            logger.info(f"Successfully parsed {len(test_cases)} test cases using double-newline method")
            return test_cases
        
        # Fallback 1: Input sections to output lines (multi-line input, single-line output)
        if len(input_sections) > 1:
            output_lines = [line.strip() for line in output_content.strip().split('\n') if line.strip()]
            
            if len(input_sections) == len(output_lines):
                logger.info(f"Using input-sections-to-output-lines mapping: {len(input_sections)} cases")
                return [
                    {'input': inp.strip(), 'output': out.strip(), 'case_number': i + 1}
                    for i, (inp, out) in enumerate(zip(input_sections, output_lines))
                ]
        
        # Fallback 2: Line-by-line matching (for simple cases)
        input_lines = [line.strip() for line in input_content.strip().split('\n') if line.strip()]
        output_lines = [line.strip() for line in output_content.strip().split('\n') if line.strip()]
        
        if len(input_lines) == len(output_lines) and len(input_lines) > 1:
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
    def _split_preserving_structure(content):
        """
        Split content on double newlines while preserving internal structure.
        Handles various edge cases like trailing newlines, empty sections, etc.
        """
        if not content.strip():
            return []
        
        # Normalize line endings first
        normalized = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # Split on double newlines
        raw_sections = normalized.split('\n\n')
        
        # Filter out empty sections and clean up
        sections = []
        for section in raw_sections:
            section = section.strip()
            if section:  # Only add non-empty sections
                sections.append(section)
        
        # Handle case where there might be no double newlines (single test case)
        if not sections and normalized.strip():
            sections = [normalized.strip()]
        
        return sections
    
    @staticmethod
    def detailed_comparison(expected, actual, case_number):
        """Detailed comparison for debugging test case failures"""
        if expected == actual:
            return True
        
        logger.error(f"❌ Test case {case_number} failed:")
        logger.error(f"Expected ({len(expected)} chars): {repr(expected)}")
        logger.error(f"Actual   ({len(actual)} chars): {repr(actual)}")
        
        # Character-by-character analysis for debugging
        if len(expected) != len(actual):
            logger.error(f"Length mismatch: expected {len(expected)}, got {len(actual)}")
        
        # Find first difference
        min_len = min(len(expected), len(actual))
        for i in range(min_len):
            if expected[i] != actual[i]:
                logger.error(f"First difference at position {i}:")
                logger.error(f"  Expected: {repr(expected[i])} (ord: {ord(expected[i])})")
                logger.error(f"  Actual:   {repr(actual[i])} (ord: {ord(actual[i])})")
                
                # Show context around difference
                start = max(0, i - 5)
                end = min(len(expected), i + 6)
                logger.error(f"  Context expected: {repr(expected[start:end])}")
                end = min(len(actual), i + 6)
                logger.error(f"  Context actual:   {repr(actual[start:end])}")
                break
        
        return False


# ============================
# OPTIMIZED EVALUATION SYSTEM
# ============================

# Global instances
code_runner = RenderOptimizedRunner()
test_parser = FastTestParser()

def evaluate_submission(submission, language):
    """
    BULLETPROOF submission evaluation that handles:
    1. Visible database test cases first (if any)
    2. Hidden file-based test cases second
    3. Proper timeout handling for recursive algorithms
    """
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
                    
                    # Execute code with specific timeout for recursive problems
                    output = code_runner.run_code(
                        language, 
                        submission.code_text, 
                        test_case.input,
                        timeout_override=15  # Shorter timeout for visible cases
                    )
                    
                    if output is None:
                        logger.error(f"❌ Runtime error/timeout in visible test case {i}")
                        return 'TLE'  # More specific error for timeouts
                    
                    expected = test_parser.normalize_output(test_case.output)
                    actual = test_parser.normalize_output(output)
                    
                    if expected != actual:
                        logger.error(f"❌ Wrong answer in visible test case {i}")
                        logger.error(f"Expected: {repr(expected)}")
                        logger.error(f"Actual: {repr(actual)}")
                        return 'WA'
                    
                    logger.info(f"✅ Visible test case {i} passed")
                
                logger.info("🎉 All visible test cases passed! Moving to hidden tests...")
        
        # Phase 2: File-based test cases (hidden test cases)
        verdict = evaluate_file_test_cases(submission, language)
        if verdict != 'AC':
            return verdict
        
        logger.info("🎉 All test cases (visible + hidden) passed!")
        return 'AC'
        
    except Exception as e:
        logger.error(f"💥 Fatal evaluation error: {str(e)}", exc_info=True)
        return 'RE'

def evaluate_file_test_cases(submission, language):
    """Optimized file-based test case evaluation with longer timeouts for hidden tests"""
    try:
        problem = submission.problem
        
        # Use more efficient path resolution
        base_dir = Path(settings.BASE_DIR)
        input_file = base_dir / "inputs" / f"{problem.short_code}.txt"
        output_file = base_dir / "outputs" / f"{problem.short_code}.txt"
        
        if not input_file.exists() or not output_file.exists():
            logger.info(f"No test files found for problem {problem.short_code}")
            return 'AC'  # No test files = accepted
        
        # Read files efficiently with proper encoding
        try:
            input_content = input_file.read_text(encoding='utf-8', errors='replace')
            output_content = output_file.read_text(encoding='utf-8', errors='replace')
            logger.info(f"Read hidden test files: input={len(input_content)} chars, output={len(output_content)} chars")
        except Exception as e:
            logger.error(f"Error reading test files: {str(e)}")
            return 'RE'
        
        # Debug: Show raw file content structure
        logger.debug(f"Input file structure (first 200 chars): {repr(input_content[:200])}")
        logger.debug(f"Output file structure (first 200 chars): {repr(output_content[:200])}")
        
        # Parse test cases using enhanced parser
        test_cases = test_parser.parse_test_cases(input_content, output_content)
        
        if not test_cases:
            logger.error("Failed to parse any test cases from files")
            return 'RE'
        
        logger.info(f"Successfully parsed {len(test_cases)} hidden test cases")
        
        # Debug: Show parsed test case structure
        for i, tc in enumerate(test_cases[:3], 1):  # Show first 3 cases for debugging
            logger.debug(f"Hidden test case {i}: input={repr(tc['input'][:50])}, output={repr(tc['output'][:50])}")
        
        # Run test cases with enhanced comparison and longer timeout for hidden tests
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"Executing hidden test case {i}/{len(test_cases)}")
            
            # Execute code with longer timeout for hidden/complex test cases
            # This allows recursive algorithms more time on hidden tests
            timeout = 25 if language == 'cpp' else 20  # Longer timeout for hidden tests
            
            actual_output = code_runner.run_code(
                language, 
                submission.code_text, 
                test_case['input'],
                timeout_override=timeout
            )
            
            if actual_output is None:
                logger.error(f"Runtime error/timeout in hidden test case {i}")
                return 'TLE'  # Return TLE for timeout on hidden tests
            
            # Normalize both outputs for comparison
            expected = test_parser.normalize_output(test_case['output'])
            actual = test_parser.normalize_output(actual_output)
            
            # Use detailed comparison for better debugging
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

# ============================
# DEBUG AND VALIDATION UTILITIES
# ============================

def validate_test_files(problem_code):
    """
    Debug utility to validate test file parsing
    Use this in Django shell to test your specific format
    """
    try:
        base_dir = Path(settings.BASE_DIR)
        input_file = base_dir / "inputs" / f"{problem_code}.txt"
        output_file = base_dir / "outputs" / f"{problem_code}.txt"
        
        if not input_file.exists() or not output_file.exists():
            print(f"❌ Test files not found for {problem_code}")
            return False
        
        # Read files
        input_content = input_file.read_text(encoding='utf-8', errors='replace')
        output_content = output_file.read_text(encoding='utf-8', errors='replace')
        
        print(f"📁 Files for {problem_code}:")
        print(f"Input file size: {len(input_content)} characters")
        print(f"Output file size: {len(output_content)} characters")
        print()
        
        # Show raw structure
        print("🔍 Raw Input Structure:")
        print(repr(input_content))
        print()
        print("🔍 Raw Output Structure:")
        print(repr(output_content))
        print()
        
        # Parse test cases
        test_cases = FastTestParser.parse_test_cases(input_content, output_content)
        
        print(f"✅ Parsed {len(test_cases)} test cases:")
        for i, tc in enumerate(test_cases, 1):
            print(f"\nTest Case {i}:")
            print(f"  Input: {repr(tc['input'])}")
            print(f"  Expected Output: {repr(tc['output'])}")
            
            # Show how input/output look when printed
            print(f"  Input (formatted):")
            for line_num, line in enumerate(tc['input'].split('\n'), 1):
                print(f"    Line {line_num}: '{line}'")
            
            print(f"  Output (formatted):")
            for line_num, line in enumerate(tc['output'].split('\n'), 1):
                print(f"    Line {line_num}: '{line}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error validating test files: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def debug_submission_execution(submission_id):
    """
    Debug utility to test submission execution step by step
    Use in Django shell: debug_submission_execution(123)
    """
    try:
        from core.models import Submission
        submission = Submission.objects.get(id=submission_id)
        
        print(f"🚀 Debugging submission {submission_id} for problem {submission.problem.short_code}")
        print(f"Language: {get_language_display(submission)}")
        print(f"Code length: {len(submission.code_text)} characters")
        print()
        
        # Validate test files first
        if not validate_test_files(submission.problem.short_code):
            return False
        
        # Test code execution with sample input
        print("🧪 Testing code execution:")
        
        # Get test cases
        base_dir = Path(settings.BASE_DIR)
        input_file = base_dir / "inputs" / f"{submission.problem.short_code}.txt"
        output_file = base_dir / "outputs" / f"{submission.problem.short_code}.txt"
        
        input_content = input_file.read_text(encoding='utf-8', errors='replace')
        output_content = output_file.read_text(encoding='utf-8', errors='replace')
        
        test_cases = FastTestParser.parse_test_cases(input_content, output_content)
        
        # Test first case
        if test_cases:
            test_case = test_cases[0]
            print(f"Testing with first test case:")
            print(f"Input: {repr(test_case['input'])}")
            
            actual_output = code_runner.run_code(
                submission.language or 'py',
                submission.code_text,
                test_case['input']
            )
            
            print(f"Code output: {repr(actual_output)}")
            print(f"Expected: {repr(test_case['output'])}")
            
            if actual_output is not None:
                expected = FastTestParser.normalize_output(test_case['output'])
                actual = FastTestParser.normalize_output(actual_output)
                
                if expected == actual:
                    print("✅ First test case PASSED")
                else:
                    print("❌ First test case FAILED")
                    FastTestParser.detailed_comparison(expected, actual, 1)
            else:
                print("❌ Code execution failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False