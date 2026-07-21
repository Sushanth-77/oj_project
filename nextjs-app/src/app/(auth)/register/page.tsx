"use client";

import { signIn } from "next-auth/react";
import Link from "next/link";
import { useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import styles from "../login/login.module.css";

function RegisterForm() {
  const [isLoading, setIsLoading] = useState(false);
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get("from") || "/problems";

  const handleGoogleLogin = async () => {
    try {
      await signIn("google", { callbackUrl });
    } catch (error) {
      console.error("Login failed:", error);
    }
  };

  const handleFakeSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    alert("Local registration is currently disabled. Please use Google Sign In.");
  };

  return (
    <div className="container mt-5" style={{ maxWidth: '500px' }}>
      <div className={`p-4 mx-auto ${styles.card}`}>
        <h1 style={{ textAlign: "center" }} className={styles.cardTitle}>
          <span style={{ color: "green" }}>Sign Up</span>
        </h1>
        <h3 className={styles.cardSubtitle}>Create Your Account</h3>
        <hr />
        
        <form onSubmit={handleFakeSubmit}>
          <div className="form-group mb-3">
            <label htmlFor="username" style={{ fontWeight: 500, color: '#555' }}>Username</label>
            <input
              type="text"
              className={styles.formControl}
              name="username"
              id="username"
              placeholder="Choose a unique username"
              autoComplete="username"
              required
              minLength={3}
            />
            <div style={{ fontSize: '0.85rem', color: '#666', marginTop: '0.5rem' }}>
              • Username must be at least 3 characters long
            </div>
          </div>
          
          <div className="form-group mb-3">
            <label htmlFor="password" style={{ fontWeight: 500, color: '#555' }}>Password</label>
            <input
              type="password"
              className={styles.formControl}
              name="password"
              id="password"
              placeholder="Create a strong password"
              autoComplete="new-password"
              required
              minLength={6}
            />
            <div style={{ fontSize: '0.85rem', color: '#666', marginTop: '0.5rem' }}>
              • Password must be at least 6 characters long<br/>
              • Use a combination of letters, numbers, and special characters
            </div>
          </div>
          
          <p className="mb-3">
            Already have an account? <Link href="/login" className={styles.link}>Sign in here</Link>
          </p>
          
          <button type="submit" className={`${styles.btnPrimary} w-100 mb-3`} style={{ display: 'block', width: '100%' }}>
            Create Account
          </button>
        </form>

        <div className={styles.divider}>OR</div>

        <button
          onClick={handleGoogleLogin}
          disabled={isLoading}
          className={styles.btnGoogle}
        >
          <img src="https://www.google.com/favicon.ico" alt="Google" width="16" height="16" />
          {isLoading ? "Signing in..." : "Continue with Google"}
        </button>
      </div>
    </div>
  );
}

export default function RegisterPage() {
  return (
    <div className={styles.loginBody}>
      <Link href="/" className={styles.homeLink}>
        &larr; Back to Home
      </Link>
      
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Suspense fallback={<div className="text-center">Loading...</div>}>
          <RegisterForm />
        </Suspense>
      </div>
    </div>
  );
}
