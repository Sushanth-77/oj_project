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
  templates?: Record<string, string> | null;
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

// ─── New Feature Types ───────────────────────────────────────────────────────

export interface Badge {
  slug: string;
  name: string;
  description: string;
  icon: string;
  awardedAt?: Date;
}

export interface Streak {
  currentStreak: number;
  longestStreak: number;
  lastSolvedDate?: Date | null;
}

export interface LeaderboardEntry {
  rank: number;
  userId: string;
  name: string | null;
  email: string;
  image: string | null;
  totalSolved: number;
  score: number;
  easyCount: number;
  mediumCount: number;
  hardCount: number;
}

export interface ProblemStats {
  total: number;
  accepted: number;
  acceptanceRate: number;
  languageBreakdown: { language: string; count: number }[];
}

export interface ProfileData {
  user: {
    id: string;
    name: string | null;
    email: string | null;
    image: string | null;
    createdAt: Date;
  };
  stats: {
    totalSolved: number;
    easyCount: number;
    mediumCount: number;
    hardCount: number;
    totalProblems: number;
    score: number;
    currentStreak: number;
    longestStreak: number;
  };
  badges: Badge[];
  heatmap: Record<string, number>;
  recentSubmissions: {
    id: number;
    verdict: Verdict;
    language: string;
    submitted: Date;
    problem: { name: string; shortCode: string; difficulty: string };
  }[];
}
