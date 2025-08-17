# compiler/views.py - RENDER-OPTIMIZED VERSION with async handling
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
# FIXED TEST CASE PARSER
# ============================

class RenderTestParser:
    """Fixed test case parser for your file format"""
    
    @staticmethod
    def normalize_output(text):
        """Normalize output for comparison"""
        if not text:
            return ""
        return text.replace('\r\n', '\n').replace('\r', '\n').rstrip()
    
    @staticmethod
    def parse_test_cases(input_content, output_content):
        """Parse test cases using EXACTLY your format (double newline separation)"""
        if not input_content.strip() or not output_content.strip():
            return []
        
        logger.info("🔍 Parsing test cases with double newline strategy")
        
        # Normalize line endings
        input_content = input_content.replace('\r\n', '\n').replace('\r', '\n')
        output_content = output_content.replace('\r\n', '\n').replace('\r', '\n')
        
        # Split by double newlines (your format)
        input_sections = []
        output_sections = []
        
        # Split input by double newlines
        raw_input_sections = input_content.split('\n\n')
        for section in raw_input_sections:
            section = section.strip()
            if section:
                input_sections.append(section)
        
        # Split output by double newlines  
        raw_output_sections = output_content.split('\n\n')
        for section in raw_output_sections:
            section = section.strip()
            if section:
                output_sections.append(section)
        
        logger.info(f"📊 Found {len(input_sections)} inputs, {len(output_sections)} outputs")
        
        # Verify counts match
        if len(input_sections) != len(output_sections):
            logger.error(f"❌ Mismatch: {len(input_sections)} inputs vs {len(output_sections)} outputs")
            return []
        
        # Create test cases
        test_cases = []
        for i, (inp, out) in enumerate(zip(input_sections, output_sections)):
            test_cases.append({
                'input': inp,
                'output': out,
                'case_number': i + 1
            })
            logger.debug(f"📝 Test case {i+1}: Input={repr(inp[:30])}, Output={repr(out[:30])}")
        
        logger.info(f"✅ Successfully parsed {len(test_cases)} test cases")
        return test_cases
    
    @staticmethod
    def detailed_comparison(expected, actual, case_number):
        """Detailed output comparison with logging"""
        if expected == actual:
            logger.info(f"✅ Test case {case_number}: PASS")
            return True
        
        logger.error(f"❌ Test case {case_number}: FAIL")
        logger.error(f"Expected ({len(expected)} chars): {repr(expected)}")
        logger.error(f"Actual ({len(actual)} chars): {repr(actual)}")
        
        # Character-by-character comparison for debugging
        min_len = min(len(expected), len(actual))
        for i in range(min_len):
            if expected[i] != actual[i]:
                logger.error(f"First difference at position {i}: expected {repr(expected[i])}, got {repr(actual[i])}")
                break
        
        return False


# ============================
# RENDER-OPTIMIZED EVALUATION
# ============================

# Global instances
code_runner = RenderOptimizedRunner()
test_parser = RenderTestParser()

def evaluate_submission(submission, language):
    """Render-optimized submission evaluation with async handling"""
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
                    
                    expected = test_parser.normalize_output(test_case.output)
                    actual = test_parser.normalize_output(output)
                    
                    if not test_parser.detailed_comparison(expected, actual, i):
                        return 'WA'
        
        # Phase 2: File-based test cases (hidden)
        verdict = evaluate_file_test_cases(submission, language)
        if verdict != 'AC':
            return verdict
        
        logger.info("🎉 All test cases passed!")
        return 'AC'
        
    except Exception as e:
        logger.error(f"💥 Evaluation error: {str(e)}", exc_info=True)
        return 'RE'

def evaluate_file_test_cases(submission, language):
    """Render-optimized file test case evaluation"""
    try:
        problem = submission.problem
        
        # FIXED: Use correct file paths
        base_dir = Path(settings.BASE_DIR)
        input_file = base_dir / "inputs" / f"{problem.short_code}.txt"
        output_file = base_dir / "outputs" / f"{problem.short_code}.txt"
        
        logger.info(f"🔍 Looking for test files:")
        logger.info(f"   Input: {input_file}")
        logger.info(f"   Output: {output_file}")
        logger.info(f"   Input exists: {input_file.exists()}")
        logger.info(f"   Output exists: {output_file.exists()}")
        
        if not input_file.exists() or not output_file.exists():
            logger.info(f"No test files found for problem {problem.short_code} - accepting")
            return 'AC'
        
        # Read files
        try:
            input_content = input_file.read_text(encoding='utf-8', errors='replace')
            output_content = output_file.read_text(encoding='utf-8', errors='replace')
            logger.info(f"📖 Read files: input={len(input_content)} chars, output={len(output_content)} chars")
        except Exception as e:
            logger.error(f"Error reading test files: {str(e)}")
            return 'RE'
        
        # Parse test cases using FIXED parser
        test_cases = test_parser.parse_test_cases(input_content, output_content)
        
        if not test_cases:
            logger.error("Failed to parse test cases")
            return 'RE'
        
        logger.info(f"📋 Running {len(test_cases)} hidden test cases")
        
        # Execute all test cases
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"🔬 Executing hidden test case {i}/{len(test_cases)}")
            
            # Render-optimized timeout
            timeout = 15 if language == 'cpp' else 12
            
            actual_output = code_runner.run_code(
                language, 
                submission.code_text, 
                test_case['input'],
                timeout_override=timeout
            )
            
            if actual_output is None:
                logger.error(f"💥 Execution failed in hidden test case {i}")
                return 'RE'
            
            # Compare outputs
            expected = test_parser.normalize_output(test_case['output'])
            actual = test_parser.normalize_output(actual_output)
            
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