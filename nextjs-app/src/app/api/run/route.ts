import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { executeCode } from "@/lib/piston";
import { z } from "zod";

const runSchema = z.object({
  code: z.string().min(1, "Code is required"),
  language: z.enum(["python", "cpp", "c", "java", "javascript"]),
  stdin: z.string().default(""),
});

// POST /api/run — execute code against custom input (no DB write)
export async function POST(request: Request) {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const json = await request.json();
    const result = runSchema.safeParse(json);

    if (!result.success) {
      return NextResponse.json(
        { error: "Invalid input", details: result.error.format() },
        { status: 400 }
      );
    }

    const { code, language, stdin } = result.data;

    const runResult = await executeCode(language, code, stdin);

    // Determine if it was a compilation error
    const isCompileError =
      runResult.code !== 0 && runResult.stderr && !runResult.stdout;

    return NextResponse.json({
      stdout: runResult.stdout || "",
      stderr: runResult.stderr || "",
      exitCode: runResult.code,
      isCompileError: !!isCompileError,
    });
  } catch (error: any) {
    console.error("Run error:", error);
    return NextResponse.json({ error: "Execution failed" }, { status: 500 });
  }
}
