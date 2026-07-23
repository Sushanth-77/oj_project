// lib/badges.ts — Badge definitions and award logic

import { prisma } from "@/lib/db";
import { startOfDay } from "date-fns";

// All badges in the system
export const BADGE_DEFINITIONS = [
  // Solve count badges
  { slug: "first_solve",    name: "First Blood",     description: "Solve your first problem",        icon: "🩸" },
  { slug: "solve_10",       name: "Problem Crusher",  description: "Solve 10 problems",               icon: "💪" },
  { slug: "solve_25",       name: "Code Warrior",     description: "Solve 25 problems",               icon: "⚔️" },
  { slug: "solve_50",       name: "Half Century",     description: "Solve 50 problems",               icon: "🏅" },
  { slug: "solve_100",      name: "Centurion",        description: "Solve 100 problems",              icon: "🏆" },
  // Difficulty badges
  { slug: "hard_1",         name: "Hard Mode",        description: "Solve a Hard problem",            icon: "🔥" },
  { slug: "hard_5",         name: "Dragon Slayer",    description: "Solve 5 Hard problems",           icon: "🐉" },
  { slug: "hard_10",        name: "Legend",           description: "Solve 10 Hard problems",          icon: "⭐" },
  // Streak badges
  { slug: "streak_3",       name: "On A Roll",        description: "3-day solving streak",            icon: "🔄" },
  { slug: "streak_7",       name: "Week Warrior",     description: "7-day solving streak",            icon: "📅" },
  { slug: "streak_30",      name: "Unstoppable",      description: "30-day solving streak",           icon: "🚀" },
  // Special
  { slug: "polyglot",       name: "Polyglot",         description: "Submit in 3 different languages", icon: "🌐" },
];

/**
 * Seed all badge definitions into the DB (idempotent — uses upsert).
 */
export async function seedBadges() {
  for (const badge of BADGE_DEFINITIONS) {
    await prisma.badge.upsert({
      where: { slug: badge.slug },
      update: { name: badge.name, description: badge.description, icon: badge.icon },
      create: badge,
    });
  }
}

/**
 * Award a badge to a user if they don't already have it.
 * Returns true if newly awarded, false if already had it.
 */
async function awardBadge(userId: string, slug: string): Promise<boolean> {
  const badge = await prisma.badge.findUnique({ where: { slug } });
  if (!badge) return false;

  try {
    await prisma.userBadge.create({ data: { userId, badgeId: badge.id } });
    return true;
  } catch {
    // Unique constraint = already has it
    return false;
  }
}

/**
 * Run after a successful (AC) submission. Awards any newly earned badges and updates streaks.
 */
export async function processAcSubmission(userId: string): Promise<string[]> {
  const awarded: string[] = [];

  // ── 1. Update streak ─────────────────────────────────────────────────────────
  const today = startOfDay(new Date());
  const streak = await prisma.streak.findUnique({ where: { userId } });

  if (!streak) {
    await prisma.streak.create({
      data: { userId, currentStreak: 1, longestStreak: 1, lastSolvedDate: today },
    });
  } else {
    const lastDate = streak.lastSolvedDate ? startOfDay(streak.lastSolvedDate) : null;
    const daysDiff = lastDate
      ? Math.round((today.getTime() - lastDate.getTime()) / (1000 * 60 * 60 * 24))
      : null;

    let newCurrent: number;
    if (daysDiff === null || daysDiff > 1) {
      newCurrent = 1; // Streak broken or first time
    } else if (daysDiff === 1) {
      newCurrent = streak.currentStreak + 1; // Extended!
    } else {
      newCurrent = streak.currentStreak; // Same day, no change
    }

    await prisma.streak.update({
      where: { userId },
      data: {
        currentStreak: newCurrent,
        longestStreak: Math.max(newCurrent, streak.longestStreak),
        lastSolvedDate: today,
      },
    });

    // Award streak badges
    if (newCurrent >= 3  && await awardBadge(userId, "streak_3"))  awarded.push("streak_3");
    if (newCurrent >= 7  && await awardBadge(userId, "streak_7"))  awarded.push("streak_7");
    if (newCurrent >= 30 && await awardBadge(userId, "streak_30")) awarded.push("streak_30");
  }

  // ── 2. Count unique solved problems ────────────────────────────────────────
  const solvedProblems = await prisma.submission.findMany({
    where: { userId, verdict: "AC" },
    select: { problemId: true, problem: { select: { difficulty: true } } },
    distinct: ["problemId"],
  });

  const totalSolved = solvedProblems.length;
  const hardSolved = solvedProblems.filter((s) => s.problem.difficulty === "H").length;

  if (totalSolved >= 1   && await awardBadge(userId, "first_solve"))  awarded.push("first_solve");
  if (totalSolved >= 10  && await awardBadge(userId, "solve_10"))     awarded.push("solve_10");
  if (totalSolved >= 25  && await awardBadge(userId, "solve_25"))     awarded.push("solve_25");
  if (totalSolved >= 50  && await awardBadge(userId, "solve_50"))     awarded.push("solve_50");
  if (totalSolved >= 100 && await awardBadge(userId, "solve_100"))    awarded.push("solve_100");

  if (hardSolved >= 1    && await awardBadge(userId, "hard_1"))       awarded.push("hard_1");
  if (hardSolved >= 5    && await awardBadge(userId, "hard_5"))       awarded.push("hard_5");
  if (hardSolved >= 10   && await awardBadge(userId, "hard_10"))      awarded.push("hard_10");

  // ── 3. Polyglot badge ────────────────────────────────────────────────────────
  const languages = await prisma.submission.findMany({
    where: { userId, verdict: "AC" },
    select: { language: true },
    distinct: ["language"],
  });
  if (languages.length >= 3 && await awardBadge(userId, "polyglot")) awarded.push("polyglot");

  return awarded;
}
