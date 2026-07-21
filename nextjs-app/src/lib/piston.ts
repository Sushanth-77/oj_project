import { RunResult } from "@/types";

// Wandbox - 100% free, no API key required, open source
// https://wandbox.org
const WANDBOX_API = "https://wandbox.org/api/compile.json";

// Wandbox compiler names + predefined option keys (comma-separated)
const LANGUAGE_MAP: Record<string, { compiler: string; options?: string }> = {
  python:     { compiler: "cpython-3.12.7" },
  cpp:        { compiler: "gcc-head",   options: "warning,c++17,optimize" },
  c:          { compiler: "gcc-head-c", options: "warning,c11,optimize" },
  java:       { compiler: "openjdk-jdk-21+35" },
  javascript: { compiler: "nodejs-20.3.0" },
};

export async function executeCode(
  languageId: string,
  code: string,
  input: string = ""
): Promise<RunResult> {
  const langConfig = LANGUAGE_MAP[languageId];

  if (!langConfig) {
    throw new Error(`Unsupported language: ${languageId}`);
  }

  try {
    const body: Record<string, string> = {
      compiler: langConfig.compiler,
      code,
      stdin: input,
    };

    if (langConfig.options) {
      body["options"] = langConfig.options;
    }

    const response = await fetch(WANDBOX_API, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`Wandbox API error: ${response.statusText}`);
    }

    const data = await response.json();

    // Compilation error
    if (data.compiler_error) {
      return {
        stdout: "",
        stderr: data.compiler_error,
        code: 1,
      };
    }

    const exitCode = parseInt(data.status ?? "0", 10);

    return {
      stdout: data.program_output ?? "",
      stderr: data.program_error ?? "",
      code: exitCode,
    };
  } catch (error: any) {
    return {
      stdout: "",
      stderr: `Execution error: ${error.message}`,
      code: -1,
    };
  }
}
