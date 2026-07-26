"use client";

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import {
  Code, Rocket, List, Brain, TrendingUp, GitBranch, Puzzle, Trophy,
  Bookmark, Lightbulb, Users, CheckCircle, Zap, Flame,
} from 'lucide-react';
import styles from './landing.module.css';

// ─── Animated Counter ──────────────────────────────────────────────────────
function AnimatedCount({ target, suffix = "" }: { target: number; suffix?: string }) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (target === 0) return;
    const step = Math.ceil(target / 60);
    const interval = setInterval(() => {
      setCount((prev) => {
        if (prev + step >= target) { clearInterval(interval); return target; }
        return prev + step;
      });
    }, 16);
    return () => clearInterval(interval);
  }, [target]);
  return <>{count.toLocaleString()}{suffix}</>;
}

export default function LandingPage() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Fetch live platform stats
  const { data: stats } = useQuery<{
    totalProblems: number;
    totalSubmissions: number;
    totalUsers: number;
    totalAC: number;
    acceptanceRate: number;
  }>({
    queryKey: ["platformStats"],
    queryFn: async () => {
      const res = await fetch("/api/stats");
      return res.json();
    },
    staleTime: 60_000,
  });

  useEffect(() => {
    // Particle animation
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const particles: {x: number, y: number, vx: number, vy: number, radius: number}[] = [];
    const resize = () => { canvas.width = window.innerWidth; canvas.height = window.innerHeight; };
    window.addEventListener('resize', resize);
    resize();
    for (let i = 0; i < 50; i++) {
      particles.push({
        x: Math.random() * canvas.width, y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 1, vy: (Math.random() - 0.5) * 1,
        radius: Math.random() * 4 + 2
      });
    }
    let animationId: number;
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      particles.forEach(p => {
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
        if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(0, 212, 170, 0.2)';
        ctx.fill();
      });
      animationId = requestAnimationFrame(animate);
    };
    animate();
    return () => { window.removeEventListener('resize', resize); cancelAnimationFrame(animationId); };
  }, []);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const cards = document.querySelectorAll(`.${styles.floatingCard}`);
      const mouseX = e.clientX / window.innerWidth;
      const mouseY = e.clientY / window.innerHeight;
      cards.forEach((card, index) => {
        const speed = (index + 1) * 0.5;
        const x = (mouseX - 0.5) * speed;
        const y = (mouseY - 0.5) * speed;
        (card as HTMLElement).style.transform = `translate(${x}px, ${y}px)`;
      });
    };
    document.addEventListener('mousemove', handleMouseMove);
    return () => document.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <div className={styles.landingBody}>
      <div className={styles.particles}>
        <canvas ref={canvasRef} style={{ width: '100%', height: '100%', display: 'block' }} />
      </div>

      <header className={styles.header}>
        <Link href="/" className={styles.logo}>
          <Code className="inline-block w-5 h-5 mr-1" />
          CodeMaster
        </Link>
        <nav>
          <ul className={styles.navMenu}>
            <li><a href="#features">Features</a></li>
            <li><a href="#stats">Stats</a></li>
            <li><a href="#problems">Start Now</a></li>
          </ul>
        </nav>
        <div className={styles.authButtons}>
          <Link href="/leaderboard" className={`${styles.btn} ${styles.btnOutline}`}>
            <Trophy className="inline-block w-4 h-4 mr-1" /> Leaderboard
          </Link>
          <Link href="/login" className={`${styles.btn} ${styles.btnPrimary}`}>Get Started</Link>
        </div>
      </header>

      <main className={styles.mainContent}>
        <div className={styles.heroLeft}>
          <h1 className={styles.heroTitle}>Think, code, and solve</h1>
          <p className={styles.heroSubtitle}>all in one platform</p>
          <p className={styles.heroDescription}>
            Master your coding skills with AI-powered hints, a global leaderboard,
            streak tracking, badges, and a rich code editor. Practice algorithms,
            solve challenging problems, and track every step of your journey.
          </p>
          <div className={styles.ctaButtons}>
            <Link href="/login" className={`${styles.btn} ${styles.btnPrimary} ${styles.btnLarge}`}>
              <Rocket className="inline-block w-4 h-4 mr-2" /> Start Coding
            </Link>
            <Link href="/problems" className={`${styles.btn} ${styles.btnOutline} ${styles.btnLarge}`}>
              <List className="inline-block w-4 h-4 mr-2" /> View Problems
            </Link>
          </div>
        </div>

        <div className={styles.heroRight}>
          <div className={`${styles.floatingCard} ${styles.codeSnippet}`}>
            <h4><Code className="inline-block w-4 h-4 mr-1" /> Live Coding</h4>
            <div className={styles.codeText}>
              def two_sum(nums, target):<br/>
              &nbsp;&nbsp;&nbsp;&nbsp;seen = {"{}"}<br/>
              &nbsp;&nbsp;&nbsp;&nbsp;for i, num in enumerate(nums):<br/>
              &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;complement = target - num<br/>
              &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;if complement in seen:<br/>
              &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;return [seen[complement], i]<br/>
              &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;seen[num] = i
            </div>
          </div>
          <div className={`${styles.floatingCard} ${styles.problemCard}`}>
            <h4><Puzzle className="inline-block w-4 h-4 mr-1" /> Challenge</h4>
            <p style={{ color: 'rgba(255,255,255,0.9)', fontSize: '0.9rem' }}>Binary Tree Max Path Sum</p>
            <span className={`${styles.difficulty} ${styles.hard}`}>Hard</span>
          </div>
          <div className={`${styles.floatingCard} ${styles.achievementCard}`}>
            <h4><Flame className="inline-block w-4 h-4 mr-1" /> Streak!</h4>
            <p style={{ color: 'rgba(255,255,255,0.9)', fontSize: '0.9rem' }}>🔥 7-Day Solving Streak</p>
            <p style={{ color: 'rgba(0,212,170,0.9)', fontSize: '0.8rem', marginTop: '0.3rem' }}>Week Warrior badge unlocked!</p>
          </div>
        </div>
      </main>

      {/* ── Live Platform Stats ── */}
      <section id="stats" style={{
        background: 'rgba(0,212,170,0.04)',
        borderTop: '1px solid rgba(0,212,170,0.15)',
        borderBottom: '1px solid rgba(0,212,170,0.15)',
        padding: '3rem 2rem',
      }}>
        <div style={{ maxWidth: '900px', margin: '0 auto', textAlign: 'center' }}>
          <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '0.75rem', letterSpacing: '0.15em', textTransform: 'uppercase', marginBottom: '2rem' }}>
            Platform Stats · Live
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '2rem' }}>
            {[
              { icon: <Puzzle className="w-6 h-6" />, label: "Problems", value: stats?.totalProblems ?? 0, color: "#00d4aa" },
              { icon: <Users className="w-6 h-6" />, label: "Coders", value: stats?.totalUsers ?? 0, color: "#a78bfa" },
              { icon: <Zap className="w-6 h-6" />, label: "Submissions", value: stats?.totalSubmissions ?? 0, color: "#facc15" },
              { icon: <CheckCircle className="w-6 h-6" />, label: "Accepted", value: stats?.totalAC ?? 0, suffix: ` (${stats?.acceptanceRate ?? 0}%)`, color: "#4ade80" },
            ].map((stat) => (
              <div key={stat.label} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
                <div style={{ color: stat.color }}>{stat.icon}</div>
                <div style={{ fontSize: '2.2rem', fontWeight: 800, color: 'white', fontFamily: 'monospace' }}>
                  <AnimatedCount target={stat.value} />
                  {stat.suffix && <span style={{ fontSize: '0.9rem', color: 'rgba(255,255,255,0.5)', fontFamily: 'inherit' }}>{stat.suffix}</span>}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section className={styles.features} id="features">
        <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
          <h2 style={{ color: 'white', fontSize: '2rem', marginBottom: '0.5rem' }}>Everything you need to level up</h2>
          <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '1rem' }}>Built for serious competitive programmers</p>
        </div>
        <div className={styles.featuresGrid}>
          {[
            { icon: <Brain className="w-7 h-7" />, title: "AI-Powered Hints", desc: "3 levels of progressive Socratic hints using Groq AI. Plus instant code review after every submission." },
            { icon: <TrendingUp className="w-7 h-7" />, title: "Profile & Heatmap", desc: "GitHub-style activity heatmap, solve donut chart, streak tracking, and a shareable public profile." },
            { icon: <Trophy className="w-7 h-7" />, title: "Global Leaderboard", desc: "Compete with a difficulty-weighted score system. Weekly and all-time rankings with a top-3 podium." },
            { icon: <Flame className="w-7 h-7" />, title: "Badges & Streaks", desc: "Earn badges for milestones: first solve, streaks, Hard problems, and polyglot coding." },
            { icon: <Bookmark className="w-7 h-7" />, title: "Bookmarks & Notes", desc: "Save problems to your study list and write private markdown notes that auto-save." },
            { icon: <GitBranch className="w-7 h-7" />, title: "Multi-Language", desc: "Submit in Python 3, C++, or C with language-specific boilerplates. Acceptance rates per language shown." },
          ].map((f) => (
            <div key={f.title} className={styles.featureCard}>
              <div className={styles.featureIcon}>{f.icon}</div>
              <h3 className={styles.featureTitle}>{f.title}</h3>
              <p className={styles.featureDescription}>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA ── */}
      <section id="problems" className={styles.features}>
        <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
          <h2 style={{ color: 'white', fontSize: '2.5rem', marginBottom: '1rem' }}>Ready to Start?</h2>
          <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '1.1rem', marginBottom: '2.5rem' }}>
            Join the leaderboard, earn badges, and grow as a programmer
          </p>
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link href="/login" className={`${styles.btn} ${styles.btnPrimary} ${styles.btnLarge}`}>
              <Rocket className="inline-block w-4 h-4 mr-2" /> Start Coding Free
            </Link>
            <Link href="/leaderboard" className={`${styles.btn} ${styles.btnOutline} ${styles.btnLarge}`}>
              <Trophy className="inline-block w-4 h-4 mr-2" /> View Leaderboard
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
