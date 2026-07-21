import { Verdict, RunResult, EvaluateResult } from "@/types";

export function normalizeOutput(output: string): string[] {
  if (!output) return [];
  
  // Split into lines, trim each line (leading + trailing), and remove trailing empty lines
  const lines = output.split(/\r?\n/).map(line => line.trim());
  
  // Remove trailing empty lines
  while (lines.length > 0 && lines[lines.length - 1] === "") {
    lines.pop();
  }
  
  return lines;
}

export function compareOutputs(expected: string, actual: string): boolean {
  const expectedLines = normalizeOutput(expected);
  const actualLines = normalizeOutput(actual);
  
  if (expectedLines.length !== actualLines.length) {
    return false;
  }
  
  for (let i = 0; i < expectedLines.length; i++) {
    // Exact match after normalization (ignoring trailing whitespace)
    if (expectedLines[i] !== actualLines[i]) {
      // Sometimes numbers might be formatted differently (e.g. 1.0 vs 1)
      // Let's do a strict string comparison for now, as that's standard for most OJs
      return false;
    }
  }
  
  return true;
}

export function evaluateExecution(
  runResult: RunResult,
  expectedOutput: string
): EvaluateResult {
  // Check for Time Limit Exceeded FIRST (Signal 9 or 137 indicates killed by OOM/Timeout)
  // Must be checked before RE because a killed process also has a non-zero exit code.
  if (runResult.signal === "SIGKILL" || Number(runResult.code) === 137) {
    return { verdict: "TLE" };
  }

  // Check for Compilation Error
  if (runResult.code !== 0 && runResult.stderr && !runResult.stdout) {
    return {
      verdict: "CE",
      details: { error: runResult.stderr }
    };
  }
  
  // Check for Runtime Error
  if (runResult.code !== 0) {
    return {
      verdict: "RE",
      details: { error: runResult.stderr || "Process exited with non-zero code" }
    };
  }
  
  // Compare outputs
  const isCorrect = compareOutputs(expectedOutput, runResult.stdout);
  
  if (isCorrect) {
    return { verdict: "AC" };
  } else {
    return {
      verdict: "WA",
      details: {
        expected: expectedOutput,
        actual: runResult.stdout
      }
    };
  }
}
