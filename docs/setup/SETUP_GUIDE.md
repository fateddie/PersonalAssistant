# PersonalAssistant - Setup Guide

**Project:** Personal Assistant  
**Version:** 1.0  
**Last Updated:** October 19, 2025

---

## 🚀 Quick Start

### Prerequisites

- **Node.js** v18+ ([Download](https://nodejs.org/) or use [nvm](https://github.com/nvm-sh/nvm))
- **npm** (comes with Node.js)
- **Git** for version control
- **Supabase Account** ([Sign up free](https://supabase.com))

### Setup Steps

1. **Clone the repository** (if not already done)

   ```bash
   cd ~/Documents/ClaudeCode/PersonalAssistant
   ```

2. **Run the automated setup script**

   ```bash
   ./scripts/setup-project.sh
   ```

   This script will:

   - ✅ Verify Node.js v18+ installed
   - ✅ Install all npm dependencies
   - ✅ Check TypeScript configuration
   - ✅ Verify DaisyUI and tech stack
   - ✅ Validate environment variables
   - ✅ Check 23 Rules compliance
   - ✅ (Optional) Run production build

3. **Configure environment variables**

   ```bash
   cp .env.example .env.local
   # Edit .env.local with your actual credentials
   ```

4. **Start development server**

   ```bash
   npm run dev
   ```

5. **Open in browser**
   ```
   http://localhost:3000
   ```

---

## 🎯 Tech Stack

This project uses the following technologies (as per **Rule #19**):

### Frontend

- **Next.js 14** - React framework with App Router and SSR
- **TypeScript** - Type-safe JavaScript (Rule #13)
- **Tailwind CSS** - Utility-first CSS framework
- **DaisyUI** - Component library (Rule #1)

### Backend

- **Supabase** - PostgreSQL database with SSR (Rule #8)
  - Authentication (email, OAuth)
  - PostgreSQL database
  - Row Level Security (RLS)
  - Storage for files/images
  - Realtime subscriptions

### Deployment

- **Vercel** - Free tier hosting (Rule #4)
- **GitHub** - Version control

### Additional Tools

- **OpenAI API** - Voice commands and AI features
- **NextAuth.js** - Authentication management
- **Playwright** - E2E testing

---

## 📋 The 23 Rules for Consistent Code

These rules **MUST** be followed for every piece of code written:

### UI & Components

**Rule #1: Always Use DaisyUI**

- Utilize DaisyUI for all UI components
- Maintain consistent styling across the application
- Check: `npm list daisyui --depth=0`

**Rule #2: Create New UI Components**

- Always create modular UI components
- Break into smaller, manageable pieces
- Facilitate easy bug fixes and maintenance
- Ask before breaking components down

**Rule #3: Component Documentation**

- Each component MUST include a comment at the top
- Explain purpose, functionality, and location

```typescript
/**
 * TaskCard Component
 *
 * Purpose: Displays a single task with complete/edit/delete actions
 * Location: /src/components/TaskCard.tsx
 *
 * Props:
 * - task: Task object from database
 * - onComplete: Callback for task completion
 * - onEdit: Callback for editing
 */
```

### Deployment & Architecture

**Rule #4: Vercel Compatibility for Endpoints**

- Ensure ALL endpoints work when deployed on Vercel
- Test locally (localhost:3000) then deploy
- Always consider in ALL code you write

**Rule #5: Design Quick and Scalable Endpoints**

- Optimize performance for increased load
- Design all endpoints to be quick and scalable

**Rule #6: Asynchronous Data Handling**

- Implement async operations for chained endpoints
- Use data streaming to prevent long wait times
- Show data quickly using client-side rendering
- Example: OpenAI → Reddit API chaining

**Rule #7: API Response Documentation**

- Add comments in endpoints outlining response structure
- Facilitates easier API chaining

```typescript
/**
 * Response Structure:
 * {
 *   success: boolean,
 *   data: {
 *     tasks: Task[],
 *     total: number
 *   },
 *   error?: string
 * }
 */
```

### Backend & Database

**Rule #8: Use Supabase with SSR**

- Integrate Supabase using Server-Side Rendering
- Ensure secure and efficient data access
- Check: `src/lib/supabase.ts` exists

**Rule #9: Maintain Existing Functionality**

- When debugging or adding features, preserve existing functionality
- Don't break current features

**Rule #10: Comprehensive Error Handling and Logging**

- For complex APIs, include detailed error checks
- Add logging for debugging (especially on Vercel)

```typescript
try {
  // API logic
} catch (error) {
  console.error("[API Error]", error);
  return { error: "Descriptive error message" };
}
```

**Rule #11: Optimize for Quick and Easy Use**

- Fast and user-friendly application
- Rapidly pull data from databases/APIs
- Minimize need for loading animations

**Rule #12: Complete Code Verification**

- Ensure code is complete, correct, error-free, bug-free
- Verify all dependencies between files
- Ensure all imports are accurate

### Language & Type Safety

**Rule #13: Use TypeScript**

- All development MUST be done using TypeScript
- Strict mode enabled in tsconfig.json
- No `any` types without justification

### Security & Performance

**Rule #14: Ensure Application Security and Scalability**

- Build secure, hack-proof, scalable application
- Use modern techniques to reduce server workload
- Minimize operational costs

**Rule #15: Include Error Checks and Logging**

- All code MUST contain error checks and logging
- Handle edge cases effectively
- Follow senior developer standards

**Rule #16: Protect Exposed Endpoints**

- Implement rate limiting
- Secure endpoints with API keys or authentication
- Prevent unauthorized access

**Rule #17: Secure Database Access**

- All database interactions performed securely
- Follow best practices to protect user data
- Use Row Level Security (RLS) in Supabase

### Development Process

**Rule #18: Step-by-Step Planning for Every Task**

- For EVERY task or message, FIRST:
  1. Plan the approach meticulously
  2. Read and understand existing code
  3. Identify what needs to be done
  4. Create detailed step-by-step plan
  5. Consider all edge cases
  6. THEN implement and write code

**Rule #19: Utilize Specified Technology Stack**

- **Frontend:** Next.js (v14) with App Router and SSR
- **Backend:** Supabase
- **Deployment:** Vercel (Free Plan)
- **Styling:** Tailwind CSS and DaisyUI
- **Payment:** Stripe (future)

**Rule #20: Consistent Use of Existing Styles**

- Use existing styles from codebase
- Example: Input forms from sign-in page
- Maintain consistency in:
  - Padding
  - Animations
  - Styles
  - Tooltips
  - Popups
  - Alerts
- Reuse existing components whenever possible

**Rule #21: Specify Script/File for Code Changes**

- ALWAYS specify which script or file needs modification
- Ensures clarity and organization

**Rule #22: Organize UI Components Properly**

- ALL UI components MUST reside in `/src/components` folder
- DO NOT create additional component folders
- Place ALL components within this designated folder
- Flat structure, no deep nesting

**Rule #23: Efficient Communication**

- Be efficient in number of AI chat messages
- Optimize interactions for productivity
- Streamline development process

---

## 🛠️ Development Workflow

### Daily Development

```bash
# Start development server
npm run dev

# In another terminal, watch for type errors
npm run type-check --watch

# Run linter
npm run lint

# Format code
npx prettier --write .
```

### Before Committing

```bash
# Type check
npm run type-check

# Lint
npm run lint

# Test build
npm run build

# Run tests (if available)
npm test
```

### Code Quality Standards

From `.claude/quality-gates.yaml`:

**TypeScript:**

- Strict mode: `true`
- No `any` types: error
- No unused vars: error
- Prefer `const`: error

**ESLint:**

- `react-hooks/rules-of-hooks`: error
- `react-hooks/exhaustive-deps`: warn
- `no-console`: warn (remove for production)
- `no-debugger`: error

**Prettier:**

- Semi: `true`
- Single quotes: `true`
- Trailing comma: `es5`
- Tab width: `2`
- Print width: `100`

**File Structure:**

- Components: `/src/components` (flat)
- API routes: `/src/app/api`
- Utilities: `/src/lib`
- Types: `/src/types`
- Tests: `/tests`

**Naming Conventions:**

- Components: `PascalCase` (TaskManager.tsx)
- Files: `kebab-case` (voice-processor.ts)
- Functions: `camelCase` (handleSubmit)
- Constants: `SCREAMING_SNAKE_CASE` (API_BASE_URL)
- Types: `PascalCase` (TaskType)

---

## 🔐 Environment Variables

### Required Variables

Create `.env.local` with these required values:

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-key
SUPABASE_JWT_SECRET=your-jwt-secret

# NextAuth
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=generate-with-openssl-rand-base64-32

# Google OAuth
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
```

### Optional Variables

```bash
# OpenAI (for AI features)
OPENAI_API_KEY=sk-proj-your-key

# App
NEXT_PUBLIC_APP_URL=http://localhost:3000
NODE_ENV=development
```

### Getting Credentials

**Supabase:**

1. Go to [supabase.com/dashboard](https://supabase.com/dashboard)
2. Create new project
3. Settings > API > Copy URL and keys

**Google OAuth:**

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create OAuth 2.0 Client ID
3. Add redirect URI: `http://localhost:3000/api/auth/callback/google`
4. Copy Client ID and Secret

**NextAuth Secret:**

```bash
openssl rand -base64 32
```

---

## 📦 npm Scripts

| Command              | Description                               |
| -------------------- | ----------------------------------------- |
| `npm run dev`        | Start development server (localhost:3000) |
| `npm run build`      | Build for production                      |
| `npm start`          | Start production server                   |
| `npm run lint`       | Run ESLint                                |
| `npm run type-check` | Check TypeScript compilation              |
| `npm test`           | Run Playwright tests                      |

---

## 🧪 Testing

### E2E Tests (Playwright)

```bash
# Run all tests
npm test

# Run specific test file
npx playwright test tests/auth.spec.ts

# Run in UI mode
npx playwright test --ui

# Generate test report
npx playwright show-report
```

### Test Structure

- **Location:** `/tests`
- **Framework:** Playwright
- **Coverage:** Authentication, task management, UI interactions

---

## 🚢 Deployment (Vercel)

### First Deployment

1. **Push to GitHub**

   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Connect to Vercel**

   - Go to [vercel.com](https://vercel.com)
   - Import repository
   - Add environment variables
   - Deploy

3. **Set Environment Variables in Vercel**
   - Project Settings > Environment Variables
   - Add all variables from `.env.local`
   - Update `NEXTAUTH_URL` to production URL

### Continuous Deployment

Every push to `main` branch automatically deploys to production.

---

## 🔍 Troubleshooting

### "Module not found" errors

```bash
rm -rf node_modules package-lock.json
npm install
```

### TypeScript errors

```bash
npm run type-check
# Fix errors shown
```

### Supabase connection issues

- Verify `.env.local` has correct values
- Check Supabase project is active
- Verify RLS policies allow access

### Build failures

- Check all environment variables are set
- Run `npm run lint` to find code issues
- Check `npm run type-check` for type errors

---

## 📚 Additional Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [Supabase Documentation](https://supabase.com/docs)
- [DaisyUI Components](https://daisyui.com/components/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Vercel Deployment](https://vercel.com/docs)

### Project Documentation

- `docs/ARCHITECTURE.md` - System architecture
- `docs/setup/PROJECT_SETUP_TEMPLATE.md` - Universal setup guide
- `.claude/quality-gates.yaml` - Code quality standards
- `.claude/subagents.yaml` - Specialized development agents
- `STARTUP_GUIDE.md` - Comprehensive startup guide

---

## ✅ Setup Checklist

Use this checklist to verify your setup:

- [ ] Node.js v18+ installed
- [ ] Repository cloned
- [ ] `npm install` completed successfully
- [ ] `.env.local` created with all required variables
- [ ] Supabase project created and connected
- [ ] Google OAuth credentials configured
- [ ] `npm run dev` starts without errors
- [ ] Can access http://localhost:3000
- [ ] TypeScript compilation succeeds
- [ ] ESLint shows no errors
- [ ] All 23 Rules documented understood
- [ ] Code quality gates reviewed

---

**Last Updated:** October 19, 2025  
**Maintainer:** Robert Freyne  
**Status:** ✅ Production Ready

---

**Remember:** Follow the 23 Rules for every piece of code you write. They ensure consistency, quality, and scalability across the entire application.
