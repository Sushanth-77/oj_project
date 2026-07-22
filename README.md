# 🚀 CodeMaster — Online Judge Platform

![Next.js](https://img.shields.io/badge/Next.js-16.2-black?logo=next.js&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?logo=typescript&logoColor=white)
![Prisma](https://img.shields.io/badge/Prisma-5.22-2D3748?logo=prisma&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-latest-336791?logo=postgresql&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-4.x-38BDF8?logo=tailwindcss&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)
![Vercel](https://img.shields.io/badge/Deployed_on-Vercel-black?logo=vercel&logoColor=white)

**A full-stack, production-ready Online Judge (OJ) platform — built with Next.js 16, Prisma, PostgreSQL, and AI-powered code review.**

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Database Schema](#-database-schema)
- [API Reference](#-api-reference)
- [Authentication](#-authentication)
- [Code Execution Engine](#-code-execution-engine)
- [AI Code Review](#-ai-code-review)
- [Admin Panel](#-admin-panel)
- [Security](#-security)
- [Environment Variables](#-environment-variables)
- [Getting Started](#-getting-started)
- [Docker Deployment](#-docker-deployment)
- [Vercel Deployment](#-vercel-deployment)
- [Key Design Decisions](#-key-design-decisions)
- [Contributing](#-contributing)

---

## 🌐 Overview

**CodeMaster** is a full-stack Online Judge platform where users can:

- Browse and solve coding problems across multiple difficulty levels
- Submit code in **5 programming languages** and get instant verdicts
- View their personal submission history and track progress
- Request an **AI-powered code review** on any accepted solution
- Admins can create, edit, and manage problems, test cases, and users through a dedicated admin panel

The platform is built entirely as a **single Next.js application** using the App Router paradigm — with server components, server actions, API routes, and a modern React frontend all co-located in one codebase.

---

## ✨ Features

### 🧑‍💻 For Users

| Feature | Description |
|---|---|
| **Problem Browser** | Browse all problems with difficulty filters (Easy / Medium / Hard) and topic tags |
| **In-Browser Code Editor** | Syntax-highlighted editor powered by **CodeMirror 6** with language-specific modes |
| **Multi-language Support** | Submit in **Python, C++, C, Java, or JavaScript** |
| **Instant Verdicts** | Get AC, WA, TLE, RE, CE, or IE verdicts with test case details |
| **Submission History** | View all past submissions with language, verdict, timestamp, and problem link |
| **AI Code Review** | Request an AI review on any submission — powered by Groq's llama-3.1-8b-instant model |
| **Google OAuth Login** | Secure, one-click sign-in via Google — no passwords needed |
| **Progress Tracking** | See which problems you've already solved |

### 🛠️ For Admins

| Feature | Description |
|---|---|
| **Admin Dashboard** | Overview of platform statistics and recent activity |
| **Problem Management** | Create, edit, and delete problems with full Markdown support for problem statements |
| **Test Case Editor** | Add/edit/delete visible and hidden test cases per problem |
| **AI Topic Tagging** | Auto-generate topic tags for problems using Groq AI |
| **Submission Viewer** | Browse all user submissions across the platform |
| **User Management** | View all registered users and manage admin privileges |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Framework** | Next.js 16 (App Router, React Server Components) |
| **Language** | TypeScript 5 |
| **Styling** | Tailwind CSS 4 + CSS Modules |
| **Database** | PostgreSQL (via Supabase / Neon / local) |
| **ORM** | Prisma 5 |
| **Authentication** | NextAuth.js v5 with Google OAuth + Prisma Adapter |
| **Code Editor** | CodeMirror 6 |
| **Code Execution** | Wandbox API (free, no API key required) |
| **AI Integration** | Groq SDK — llama-3.1-8b-instant |
| **Data Fetching** | TanStack React Query v5 |
| **Charts** | Recharts |
| **Icons** | Lucide React |
| **Date Utilities** | date-fns |
| **Validation** | Zod 4 |
| **Containerization** | Docker (multi-stage build) |
| **Deployment** | Vercel |

---

## 📁 Project Structure

`
oj_project/
├── docker-compose.yml          # Docker Compose for local container deployment
├── .gitignore
├── logs/                       # Application logs (gitignored)
├── media/                      # Media files (gitignored)
└── nextjs-app/                 # Main Next.js application
    ├── Dockerfile               # Multi-stage production Docker build
    ├── vercel.json              # Vercel deployment configuration
    ├── next.config.ts           # Next.js config (security headers, CSP, CORS)
    ├── tsconfig.json            # TypeScript configuration
    ├── package.json             # Dependencies and npm scripts
    ├── make-admin.js            # Utility script to promote a user to admin
    ├── prisma/
    │   └── schema.prisma        # Database schema (User, Problem, TestCase, Submission)
    ├── public/                  # Static assets
    └── src/
        ├── app/                 # Next.js App Router pages and API routes
        │   ├── layout.tsx       # Root layout (fonts, metadata, providers)
        │   ├── page.tsx         # Landing page with animated canvas background
        │   ├── globals.css      # Global CSS resets and variables
        │   ├── providers.tsx    # React Query provider wrapper
        │   ├── (auth)/          # Route group: authentication pages
        │   │   ├── login/       # Google OAuth sign-in page
        │   │   └── register/    # Registration (redirects to OAuth)
        │   ├── (judge)/         # Route group: main app pages (requires auth)
        │   │   ├── layout.tsx   # Shared layout with navigation bar
        │   │   ├── problems/    # Problem list and detail/solve pages
        │   │   │   └── [shortCode]/  # Dynamic problem detail + code editor
        │   │   └── submissions/ # User's own submission history
        │   ├── admin/           # Admin panel (requires isAdmin = true)
        │   │   ├── layout.tsx   # Admin sidebar layout
        │   │   ├── dashboard/   # Platform statistics overview
        │   │   ├── problems/    # Problem CRUD
        │   │   │   ├── add/     # Create new problem + test cases
        │   │   │   └── [shortCode]/  # Edit existing problem
        │   │   ├── submissions/ # View all platform submissions
        │   │   └── users/       # User management
        │   └── api/             # Next.js API Route handlers
        │       ├── auth/        # NextAuth.js handler
        │       ├── problems/    # GET all problems, GET by shortCode
        │       │   ├── route.ts
        │       │   ├── [shortCode]/
        │       │   └── solved/  # GET list of solved problem IDs
        │       ├── submissions/ # GET user submissions, POST new submission
        │       │   └── [id]/    # GET single submission details
        │       ├── ai-review/   # POST trigger AI code review via Groq
        │       │   └── [id]/
        │       └── admin/       # Admin-only API routes
        ├── components/
        │   ├── editor/
        │   │   └── CodeEditor.tsx   # CodeMirror 6 wrapper component
        │   ├── layout/              # Navbar, Sidebar, Footer components
        │   ├── admin/               # Admin-specific UI components
        │   └── ui/
        │       └── VerdictBadge.tsx # Color-coded verdict chip component
        ├── lib/
        │   ├── auth.ts          # NextAuth config (Google provider + callbacks)
        │   ├── db.ts            # Prisma client singleton
        │   ├── groq.ts          # Groq AI: code review and topic tag generation
        │   ├── judge.ts         # Verdict evaluation logic (AC/WA/TLE/RE/CE)
        │   ├── piston.ts        # Wandbox API integration for code execution
        │   └── validations.ts   # Zod schemas for API request validation
        ├── types/               # Shared TypeScript types and interfaces
        └── proxy.ts             # API proxy utilities
`

---

## 🗄️ Database Schema

The database uses **PostgreSQL** managed via **Prisma ORM**.

### User

| Field | Type | Description |
|---|---|---|
| id | String (cuid) | Primary key |
| email | String (unique) | User's email from Google |
| name | String? | Display name |
| image | String? | Profile picture URL |
| isAdmin | Boolean | Admin privilege flag (default: false) |
| createdAt | DateTime | Account creation timestamp |
| lastLogin | DateTime? | Last login timestamp |

### Problem

| Field | Type | Description |
|---|---|---|
| id | Int (autoincrement) | Primary key |
| name | String | Problem title |
| shortCode | String (unique) | URL-safe identifier (e.g., two-sum) |
| statement | String | Markdown problem statement |
| difficulty | String | 'E' (Easy), 'M' (Medium), 'H' (Hard) |
| topics | String[] | Array of topic tags |

### TestCase

| Field | Type | Description |
|---|---|---|
| id | Int | Primary key |
| problemId | Int | FK to Problem |
| input | String | Test input |
| output | String | Expected output |
| isHidden | Boolean | Hidden from users (default: false) |
| order | Int | Evaluation order |

### Submission

| Field | Type | Description |
|---|---|---|
| id | Int | Primary key |
| problemId | Int | FK to Problem |
| userId | String | FK to User |
| codeText | String | Full submitted source code |
| language | String | py, cpp, c, java, javascript |
| verdict | String | AC, WA, TLE, RE, CE, PE, IE |
| submitted | DateTime | Submission timestamp |

> **Indexes**: [userId, problemId] and [problemId, verdict] for fast lookups.

### NextAuth Models

The schema also includes standard NextAuth models: **Account**, **Session**, and **VerificationToken**, used by the Prisma Adapter to manage OAuth sessions.

---

## 📡 API Reference

All API routes are under /api/ and follow REST conventions.

### Problems

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | /api/problems | Optional | List all problems |
| GET | /api/problems/[shortCode] | Optional | Get a specific problem with visible test cases |
| GET | /api/problems/solved | Required | Get IDs of all problems solved by the current user |

### Submissions

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | /api/submissions | Required | Get all submissions for the current user |
| POST | /api/submissions | Required | Submit code for a problem; returns verdict |
| GET | /api/submissions/[id] | Required | Get a single submission by ID |

### AI Review

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | /api/ai-review/[id] | Required | Request an AI code review for submission id |

### Admin (requires isAdmin = true)

| Method | Endpoint | Description |
|---|---|---|
| GET/POST | /api/admin/problems | List all problems / Create a new problem |
| GET/PUT/DELETE | /api/admin/problems/[id] | Read, update, or delete a problem |
| GET/POST | /api/admin/problems/[id]/testcases | Manage test cases for a problem |
| GET | /api/admin/submissions | List all platform submissions |
| GET | /api/admin/users | List all users |

---

## 🔐 Authentication

Authentication is handled by **NextAuth.js v5** with:

- **Provider**: Google OAuth 2.0
- **Strategy**: JWT sessions (stateless)
- **Database Adapter**: Prisma Adapter (accounts/sessions in PostgreSQL)
- **Admin check**: isAdmin is embedded in the JWT token and verified server-side on all admin routes

### Making a User an Admin

`ash
# From the nextjs-app directory
node make-admin.js <user-email>
`

---

## ⚙️ Code Execution Engine

Code is executed via the **Wandbox API** — a free, open-source online compiler that requires no API key.

### Supported Languages and Compilers

| Language | Wandbox Compiler | Options |
|---|---|---|
| Python | cpython-3.12.7 | — |
| C++ | gcc-head | warning, c++17, optimize |
| C | gcc-head-c | warning, c11, optimize |
| Java | openjdk-jdk-21+35 | — |
| JavaScript | nodejs-20.3.0 | — |

### Verdict System

| Verdict | Meaning |
|---|---|
| AC — Accepted | Output matches expected output on all test cases |
| WA — Wrong Answer | Output does not match expected output |
| TLE — Time Limit Exceeded | Process killed by SIGKILL or exit code 137 |
| RE — Runtime Error | Non-zero exit code (e.g., segfault, division by zero) |
| CE — Compilation Error | Compiler reports an error before execution |
| PE — Pending | Submission received, not yet evaluated |
| IE — Internal Error | Server-side or API error during evaluation |

### Output Normalization

The judge normalizes outputs before comparison:
- Strips leading/trailing whitespace from each line
- Removes trailing blank lines
- Performs strict line-by-line string comparison

---

## 🤖 AI Code Review

Powered by **Groq** running Meta's llama-3.1-8b-instant model, the AI review feature provides:

- **Overall Rating** (out of 10) based on correctness, readability, and efficiency
- **Time and Space Complexity** analysis (Big-O)
- **Key Improvements** — 1–3 specific, actionable tips including edge cases, idiomatic style, and optimizations

The review is rendered as formatted Markdown using react-markdown with GitHub Flavored Markdown (remark-gfm).

### AI Topic Tagging (Admin)

When a new problem is created, the admin can click "Auto-tag" to have the AI suggest relevant topic tags from a curated list of 24 categories:

Arrays, Strings, Linked Lists, Trees, Graphs, Dynamic Programming, Greedy, Backtracking, Sorting, Searching, Binary Search, Hash Maps, Stacks, Queues, Heaps, Recursion, Math, Two Pointers, Sliding Window, Bit Manipulation, Tries, Union Find, Segment Trees, Matrix

---

## 🛡️ Admin Panel

The admin panel is accessible at /admin/* and requires isAdmin = true.

### Dashboard (/admin/dashboard)
- Platform-wide statistics (total problems, users, submissions)
- Recent activity feed

### Problem Management (/admin/problems)
- **List**: View all problems with status, difficulty, and topic tags
- **Add** (/admin/problems/add): Create a new problem with name, short code, Markdown statement, difficulty, and test cases
- **Edit** (/admin/problems/[shortCode]): Update any problem field or its test cases inline

### Submissions Viewer (/admin/submissions)
- Browse all submissions across all users

### User Management (/admin/users)
- View all registered users with join date and submission count
- Toggle admin privileges

---

## 🔒 Security

Security headers configured in next.config.ts:

| Header | Policy |
|---|---|
| HSTS | max-age=31536000; includeSubDomains; preload |
| Content-Security-Policy | Restricts scripts, styles, fonts, images, and XHR to known-safe origins |
| X-Frame-Options | DENY (anti-clickjacking) |
| X-Content-Type-Options | nosniff (MIME-sniffing prevention) |
| Referrer-Policy | strict-origin-when-cross-origin |
| Permissions-Policy | Camera, microphone, geolocation all disabled |
| CORS | API routes restricted to the app's own origin |

---

## 🔑 Environment Variables

Copy nextjs-app/.env.example to nextjs-app/.env and fill in the values:

`env
# PostgreSQL Database URL
DATABASE_URL="postgresql://user:password@host:5432/dbname?schema=public"

# NextAuth.js — generate with: openssl rand -base64 32
NEXTAUTH_SECRET="your_nextauth_secret_here"
NEXTAUTH_URL="http://localhost:3000"

# Google OAuth — from Google Cloud Console
GOOGLE_CLIENT_ID="your_google_client_id"
GOOGLE_CLIENT_SECRET="your_google_client_secret"

# Groq API Key — from console.groq.com
GROQ_API_KEY="your_groq_api_key"
`

### Where to Get Each Credential

| Variable | Source |
|---|---|
| DATABASE_URL | Supabase, Neon, or local PostgreSQL |
| NEXTAUTH_SECRET | Run: openssl rand -base64 32 |
| NEXTAUTH_URL | Your app's public URL (http://localhost:3000 for local) |
| GOOGLE_CLIENT_ID / SECRET | Google Cloud Console → OAuth 2.0 Client IDs |
| GROQ_API_KEY | console.groq.com (free tier available) |

---

## 🚀 Getting Started

### Prerequisites

- Node.js 20 or later
- npm 9 or later
- A PostgreSQL database (local or cloud)

### 1. Clone the Repository

`ash
git clone https://github.com/Sushanth-77/oj_project.git
cd oj_project/nextjs-app
`

### 2. Install Dependencies

`ash
npm install
`

### 3. Configure Environment Variables

`ash
cp .env.example .env
# Edit .env with your credentials
`

### 4. Set Up the Database

`ash
# Push the Prisma schema to your database
npx prisma db push
`

### 5. Run the Development Server

`ash
npm run dev
`

Open http://localhost:3000 in your browser.

### 6. (Optional) Make Yourself an Admin

After logging in once via Google:

`ash
node make-admin.js your-email@gmail.com
`

---

## 🐳 Docker Deployment

The project includes a multi-stage Dockerfile and docker-compose.yml for containerized deployment.

`ash
# From the project root (oj_project/)
docker-compose up --build
`

This starts the Next.js app on port 3000. Make sure nextjs-app/.env is configured beforehand.

### Dockerfile Stages

| Stage | Base | Purpose |
|---|---|---|
| deps | node:20-alpine | Install npm dependencies (npm ci) |
| builder | node:20-alpine | Generate Prisma client + build Next.js |
| runner | node:20-alpine | Lean production image (node server.js) |

The final image runs as a non-root user (nextjs:nodejs), sets NODE_ENV=production, and exposes port 3000.

---

## ☁️ Vercel Deployment

1. Push your code to GitHub
2. Import the repository at vercel.com/new
3. Set the **Root Directory** to nextjs-app
4. Add all environment variables from .env in the Vercel dashboard
5. Deploy

The vercel.json configures the build command as: npx prisma generate && npm run build

---

## 🧪 Available Scripts

Run all scripts from inside nextjs-app/:

| Script | Command | Description |
|---|---|---|
| Development | npm run dev | Start local dev server with hot reload |
| Build | npm run build | Create production build |
| Start | npm run start | Start production server |
| Lint | npm run lint | Run ESLint checks |
| DB Push | npx prisma db push | Sync schema to database without migration |
| DB Migrate | npx prisma migrate dev | Create and apply a new migration |
| DB Studio | npx prisma studio | Open Prisma Studio GUI |
| Make Admin | node make-admin.js <email> | Promote a user to admin role |

---

## 🏗️ Key Design Decisions

### Why a Single Next.js App?
The original project had a separate Django backend. We migrated everything into a single Next.js application to simplify deployment, reduce operational overhead, and leverage Next.js API Routes as the backend. One repo, one deployment, one set of environment variables.

### Why Wandbox for Code Execution?
Wandbox is a free, open-source, no-API-key-required online compiler supporting all our target languages. It handles sandboxing and resource limits without the complexity of running our own judge sandbox.

### Why Groq for AI?
Groq offers free-tier access to fast LLM inference. The llama-3.1-8b-instant model is fast enough for real-time code review and accurate enough for educational feedback.

### Why JWT Sessions?
JWT sessions are stateless and work seamlessly with Vercel's serverless edge functions without requiring sticky sessions or a session store.

---

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch: git checkout -b feature/my-feature
3. **Commit** your changes: git commit -m "feat: add my feature"
4. **Push** to your branch: git push origin feature/my-feature
5. **Open** a Pull Request

---

## 📄 License

This project is licensed under the **MIT License**.

---

Made with love by Sushanth (https://github.com/Sushanth-77)
