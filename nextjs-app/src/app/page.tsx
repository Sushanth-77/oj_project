"use client";

import { useEffect, useRef } from 'react';
import Link from 'next/link';
import { Code, Rocket, List, Brain, TrendingUp, GitBranch, Puzzle, Trophy } from 'lucide-react';
import styles from './landing.module.css';

export default function LandingPage() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    // Particle animation
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    const particles: {x: number, y: number, vx: number, vy: number, radius: number}[] = [];
    
    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    
    window.addEventListener('resize', resize);
    resize();
    
    for (let i = 0; i < 50; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 1,
        vy: (Math.random() - 0.5) * 1,
        radius: Math.random() * 4 + 2
      });
    }
    
    let animationId: number;
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      particles.forEach(p => {
        p.x += p.vx;
        p.y += p.vy;
        
        if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
        if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
        
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
        ctx.fill();
      });
      
      animationId = requestAnimationFrame(animate);
    };
    
    animate();
    
    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animationId);
    };
  }, []);

  useEffect(() => {
    // Subtle parallax effect
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
            <li><a href="#problems">Problems</a></li>
            <li><a href="#about">About</a></li>
          </ul>
        </nav>
        
        <div className={styles.authButtons}>
          <Link href="/login" className={`${styles.btn} ${styles.btnOutline}`}>Sign In</Link>
          <Link href="/login" className={`${styles.btn} ${styles.btnPrimary}`}>Get Started</Link>
        </div>
      </header>

      <main className={styles.mainContent}>
        <div className={styles.heroLeft}>
          <h1 className={styles.heroTitle}>Think, code, and solve</h1>
          <p className={styles.heroSubtitle}>all in one platform</p>
          <p className={styles.heroDescription}>
            Master your coding skills with our comprehensive online judge platform. 
            Practice algorithms, solve challenging problems, and track your progress 
            as you become a better programmer.
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
            <h4><Puzzle className="inline-block w-4 h-4 mr-1" /> Today's Challenge</h4>
            <p style={{ color: 'rgba(255,255,255,0.9)', fontSize: '0.9rem' }}>Binary Tree Maximum Path Sum</p>
            <span className={`${styles.difficulty} ${styles.hard}`}>Hard</span>
          </div>
          
          <div className={`${styles.floatingCard} ${styles.achievementCard}`}>
            <h4><Trophy className="inline-block w-4 h-4 mr-1" /> Achievement</h4>
            <p style={{ color: 'rgba(255,255,255,0.9)', fontSize: '0.9rem' }}>100 Day Streak!</p>
          </div>
        </div>
      </main>

      <section className={styles.features} id="features">
        <div className={styles.featuresGrid}>
          <div className={styles.featureCard}>
            <div className={styles.featureIcon}>
              <Brain className="w-8 h-8" />
            </div>
            <h3 className={styles.featureTitle}>AI-Powered Hints</h3>
            <p className={styles.featureDescription}>
              Get intelligent hints and explanations powered by advanced AI to help you learn and improve.
            </p>
          </div>
          
          <div className={styles.featureCard}>
            <div className={styles.featureIcon}>
              <TrendingUp className="w-8 h-8" />
            </div>
            <h3 className={styles.featureTitle}>Progress Tracking</h3>
            <p className={styles.featureDescription}>
              Monitor your coding journey with detailed analytics and performance insights.
            </p>
          </div>
          
          <div className={styles.featureCard}>
            <div className={styles.featureIcon}>
              <GitBranch className="w-8 h-8" />
            </div>
            <h3 className={styles.featureTitle}>Multiple Languages</h3>
            <p className={styles.featureDescription}>
              Code in Python, Java, C++, JavaScript and 10+ other programming languages.
            </p>
          </div>
        </div>
      </section>

      <section id="problems" className={styles.features}>
        <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
          <h2 style={{ color: 'white', fontSize: '2.5rem', marginBottom: '1rem' }}>Ready to Start?</h2>
          <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: '1.2rem', marginBottom: '2rem' }}>
            Browse our collection of coding problems and start your journey
          </p>
          <Link href="/problems" className={`${styles.btn} ${styles.btnPrimary} ${styles.btnLarge}`}>
            <List className="inline-block w-4 h-4 mr-2" /> Browse Problems
          </Link>
        </div>
      </section>
    </div>
  );
}
