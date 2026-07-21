import { z } from "zod";

export const problemSchema = z.object({
  name: z.string().min(3, "Name must be at least 3 characters"),
  shortCode: z.string().min(2, "Short code must be at least 2 characters").regex(/^[A-Z0-9_-]+$/, "Uppercase letters, numbers, underscores, dashes only"),
  statement: z.string().min(10, "Statement must be at least 10 characters"),
  difficulty: z.enum(["E", "M", "H"]),
});

export const testCaseSchema = z.object({
  input: z.string(),
  output: z.string().min(1, "Expected output is required"),
  isHidden: z.boolean().default(false),
  order: z.number().int().positive().default(1),
});

export const createProblemSchema = problemSchema.extend({
  testCases: z.array(testCaseSchema).min(1, "At least one test case is required"),
});

export const submissionSchema = z.object({
  problemId: z.number().int().positive(),
  codeText: z.string().min(10, "Code must be at least 10 characters"),
  language: z.enum(["python", "cpp", "c"]),
});
