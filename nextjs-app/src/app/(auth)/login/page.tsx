"use client";

import { signIn } from "next-auth/react";
import Link from "next/link";
import { useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import styles from "./login.module.css";

function LoginForm() {
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
    alert("Local authentication is currently disabled. Please use Google Sign In.");
  };

  return (
    <div className="container mt-5" style={{ maxWidth: '500px' }}>
      <div className={`p-4 mx-auto ${styles.card}`}>
        <h1 style={{ textAlign: "center" }} className={styles.cardTitle}>
          <span style={{ color: "green" }}>Login</span>
        </h1>
        <h3 className={styles.cardSubtitle}>Sign In to Your Account</h3>
        <hr />
        
        <form onSubmit={handleFakeSubmit}>
          <div className="form-group mb-3">
            <label htmlFor="username" style={{ fontWeight: 500, color: '#555' }}>Username</label>
            <input
              type="text"
              className={styles.formControl}
              name="username"
              id="username"
              placeholder="Enter your username"
              autoComplete="username"
            />
          </div>
          
          <div className="form-group mb-3">
            <label htmlFor="password" style={{ fontWeight: 500, color: '#555' }}>Password</label>
            <input
              type="password"
              className={styles.formControl}
              name="password"
              id="password"
              placeholder="Enter your password"
              autoComplete="current-password"
            />
          </div>
          
          <p className="mb-3">
            Don't have an account? <Link href="/register" className={styles.link}>Register here</Link>
          </p>
          
          <button type="submit" className={`${styles.btnPrimary} w-100 mb-3`} style={{ display: 'block', width: '100%' }}>
            Sign In
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

export default function LoginPage() {
  return (
    <div className={styles.loginBody}>
      <Link href="/" className={styles.homeLink}>
        &larr; Back to Home
      </Link>
      
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Suspense fallback={<div className="text-center">Loading...</div>}>
          <LoginForm />
        </Suspense>
      </div>
    </div>
  );
}
