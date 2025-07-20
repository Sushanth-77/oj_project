# Create your views here.
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CodeSubmissionForm
from .models import CodeSubmission
from core.models import Problem, TestCase, Submission
from django.conf import settings
import os
import uuid
import subprocess
from pathlib import Path

@login_required
def submit_code(request):
    if request.method == "POST":
        form = CodeSubmissionForm(request.POST)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.user = request.user
            
            # Run the code
            output = run_code(
                submission.language, submission.code, submission.input_data or ""
            )
            submission.output_data = output
            submission.save()
            
            # If this is for a specific problem, evaluate against test cases
            if submission.problem:
                verdict = evaluate_submission(submission)
                # Create a Submission record for the problem
                problem_submission = Submission.objects.create(
                    problem=submission.problem,
                    user=request.user,
                    code_text=submission.code,
                    verdict=verdict
                )
                messages.success(request, f'Code submitted for problem {submission.problem.short_code}. Verdict: {verdict}')
            else:
                messages.success(request, 'Code executed successfully!')
            
            return render(request, "submit/result.html", {"submission": submission})
    else:
        form = CodeSubmissionForm()
    
    return render(request, "submit/index.html", {"form": form})

def run_code(language, code, input_data):
    """Execute the code and return output"""
    project_path = Path(settings.BASE_DIR)
    directories = ["codes", "inputs", "outputs"]

    # Create directories if they don't exist
    for directory in directories:
        dir_path = project_path / directory
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)

    codes_dir = project_path / "codes"
    inputs_dir = project_path / "inputs"
    outputs_dir = project_path / "outputs"

    unique = str(uuid.uuid4())

    code_file_name = f"{unique}.{language}"
    input_file_name = f"{unique}.txt"
    output_file_name = f"{unique}.txt"

    code_file_path = codes_dir / code_file_name
    input_file_path = inputs_dir / input_file_name
    output_file_path = outputs_dir / output_file_name

    try:
        # Write code to file
        with open(code_file_path, "w") as code_file:
            code_file.write(code)

        # Write input to file
        with open(input_file_path, "w") as input_file:
            input_file.write(input_data)

        # Create empty output file
        with open(output_file_path, "w") as output_file:
            pass

        if language == "cpp":
            executable_path = codes_dir / unique
            # Compile C++ code
            compile_result = subprocess.run(
                ["clang++", str(code_file_path), "-o", str(executable_path)],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if compile_result.returncode == 0:
                # Execute compiled program
                with open(input_file_path, "r") as input_file:
                    with open(output_file_path, "w") as output_file:
                        run_result = subprocess.run(
                            [str(executable_path)],
                            stdin=input_file,
                            stdout=output_file,
                            stderr=subprocess.PIPE,
                            timeout=5
                        )
            else:
                return f"Compilation Error:\n{compile_result.stderr}"
                
        elif language == "c":
            executable_path = codes_dir / unique
            # Compile C code
            compile_result = subprocess.run(
                ["clang", str(code_file_path), "-o", str(executable_path)],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if compile_result.returncode == 0:
                # Execute compiled program
                with open(input_file_path, "r") as input_file:
                    with open(output_file_path, "w") as output_file:
                        run_result = subprocess.run(
                            [str(executable_path)],
                            stdin=input_file,
                            stdout=output_file,
                            stderr=subprocess.PIPE,
                            timeout=5
                        )
            else:
                return f"Compilation Error:\n{compile_result.stderr}"
                
        elif language == "py":
            # Execute Python script
            with open(input_file_path, "r") as input_file:
                with open(output_file_path, "w") as output_file:
                    run_result = subprocess.run(
                        ["python3", str(code_file_path)],
                        stdin=input_file,
                        stdout=output_file,
                        stderr=subprocess.PIPE,
                        timeout=5
                    )

        # Read the output from the output file
        with open(output_file_path, "r") as output_file:
            output_data = output_file.read()

        return output_data

    except subprocess.TimeoutExpired:
        return "Time Limit Exceeded"
    except Exception as e:
        return f"Runtime Error: {str(e)}"
    finally:
        # Clean up temporary files
        try:
            if code_file_path.exists():
                code_file_path.unlink()
            if input_file_path.exists():
                input_file_path.unlink()
            if output_file_path.exists():
                output_file_path.unlink()
            if language in ["cpp", "c"] and (codes_dir / unique).exists():
                (codes_dir / unique).unlink()
        except:
            pass

def evaluate_submission(submission):
    """Evaluate submission against test cases"""
    if not submission.problem:
        return "AC"  # No problem to evaluate against
    
    test_cases = submission.problem.testcases.all()
    if not test_cases:
        return "AC"  # No test cases to evaluate against
    
    for test_case in test_cases:
        try:
            output = run_code(submission.language, submission.code, test_case.input)
            expected_output = test_case.output.strip()
            actual_output = output.strip()
            
            if actual_output != expected_output:
                return "WA"  # Wrong Answer
                
        except subprocess.TimeoutExpired:
            return "TLE"  # Time Limit Exceeded
        except Exception:
            return "RE"   # Runtime Error
    
    return "AC"  # All test cases passed

@login_required
def submission_history(request):
    """View submission history for the current user"""
    submissions = CodeSubmission.objects.filter(user=request.user)
    return render(request, "submit/history.html", {"submissions": submissions})