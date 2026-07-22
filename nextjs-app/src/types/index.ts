export type Verdict = "AC" | "WA" | "TLE" | "RE" | "CE" | "PE" | "IE";

export interface TestCase {
  id: number;
  problemId: number;
  input: string;
  output: string;
  isHidden: boolean;
  order: number;
}

export interface Problem {
  id: number;
  name: string;
  shortCode: string;
  statement: string;
  difficulty: "E" | "M" | "H";
  topics: string[];
  createdAt: Date;
  testCases?: TestCase[];
}

export interface Submission {
  id: number;
  problemId: number;
  userId: string;
  codeText: string;
  language: string;
  verdict: Verdict;
  submitted: Date;
  problem?: Problem;
  user?: User;
}

export interface User {
  id: string;
  email: string;
  name?: string | null;
  image?: string | null;
  isAdmin: boolean;
}

export interface RunResult {
  stdout: string;
  stderr: string;
  error?: string;
  code?: number;
  signal?: string;
}

export interface EvaluateResult {
  verdict: Verdict;
  details?: {
    testCaseId?: number;
    expected?: string;
    actual?: string;
    error?: string;
  };
}
