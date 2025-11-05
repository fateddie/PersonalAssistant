# Universal Rules Database for AI-Assisted Development

**Version:** 1.0  
**Last Updated:** October 19, 2025  
**Purpose:** Comprehensive rules, patterns, and standards for consistent AI-assisted development

---

## 📋 Table of Contents

1. [Core Philosophy](#core-philosophy)
2. [The 23 Fundamental Rules](#the-23-fundamental-rules)
3. [Project-Specific Rule Sets](#project-specific-rule-sets)
4. [Code Quality Standards](#code-quality-standards)
5. [Security Checklist](#security-checklist)
6. [Architecture Patterns](#architecture-patterns)
7. [Common Pitfalls & Solutions](#common-pitfalls--solutions)
8. [AI Assistant Instructions](#ai-assistant-instructions)

---

## Core Philosophy

### Principles for All Projects

1. **Consistency Over Cleverness** - Simple, predictable code beats clever tricks
2. **Security by Default** - Every feature designed with security first
3. **Performance Matters** - Optimize for speed and scalability from day one
4. **Document Everything** - Code should be self-explanatory with clear docs
5. **Test Early, Test Often** - Catch bugs before they reach production
6. **Plan Before Coding** - Think through the approach before implementation

### Development Mindset

- **Write code for humans first, machines second**
- **Every function should do ONE thing well**
- **Delete code is better than commented code**
- **If you copy-paste twice, make it a function**
- **Errors should be helpful, not cryptic**

---

## The 23 Fundamental Rules

### 📐 UI & Component Rules (1-3)

#### Rule #1: Always Use DaisyUI (Next.js Projects)
```typescript
// ✅ CORRECT: Use DaisyUI components
<button className="btn btn-primary">Click Me</button>

// ❌ WRONG: Custom button styles
<button className="bg-blue-500 hover:bg-blue-700 px-4 py-2">Click Me</button>
```

**Checklist:**
- [ ] DaisyUI installed (`npm list daisyui`)
- [ ] Component uses DaisyUI classes
- [ ] No duplicate custom styles that DaisyUI provides
- [ ] Consistent theme across all components

#### Rule #2: Create Modular UI Components
```typescript
// ✅ CORRECT: Small, reusable components
// TaskCard.tsx
export function TaskCard({ task, onComplete }: TaskCardProps) {
  return <div className="card">...</div>;
}

// TaskList.tsx
export function TaskList({ tasks }: TaskListProps) {
  return tasks.map(task => <TaskCard key={task.id} task={task} />);
}

// ❌ WRONG: Monolithic component
export function TaskManager() {
  // 500 lines of mixed logic and UI
}
```

**When to Break Down:**
- Component exceeds 200 lines
- Component has 3+ different responsibilities
- You're repeating UI patterns
- Component is hard to test

**Ask Before Breaking:**
"Should I break this component down further?"

#### Rule #3: Component Documentation
```typescript
/**
 * TaskCard Component
 * 
 * Purpose: Displays a single task with actions (complete, edit, delete)
 * Location: /src/components/TaskCard.tsx
 * Used in: TaskList, Dashboard
 * 
 * Props:
 * @param task - Task object from Supabase
 * @param onComplete - Callback when task is marked complete
 * @param onEdit - Callback to open edit modal
 * @param onDelete - Callback to delete task
 * 
 * Dependencies:
 * - DaisyUI for styling
 * - Supabase for data updates
 * 
 * Example:
 * ```tsx
 * <TaskCard 
 *   task={myTask} 
 *   onComplete={handleComplete}
 *   onEdit={handleEdit}
 *   onDelete={handleDelete}
 * />
 * ```
 */
export function TaskCard({ task, onComplete, onEdit, onDelete }: TaskCardProps) {
  // Implementation
}
```

**Documentation Requirements:**
- [ ] Component purpose clearly stated
- [ ] Location in project specified
- [ ] All props documented with types
- [ ] Dependencies listed
- [ ] Usage example provided

---

### 🚀 Deployment & Architecture Rules (4-7)

#### Rule #4: Vercel Compatibility for Endpoints
```typescript
// ✅ CORRECT: Vercel-compatible API route
// app/api/tasks/route.ts
export async function GET(request: Request) {
  // Works on Vercel
  const { searchParams } = new URL(request.url);
  return Response.json({ data: tasks });
}

// ❌ WRONG: Express-style that breaks on Vercel
export default function handler(req: any, res: any) {
  res.status(200).json({ data: tasks });
}
```

**Vercel Compatibility Checklist:**
- [ ] Uses Next.js API Routes pattern
- [ ] Returns Response.json() or NextResponse
- [ ] Environment variables accessed via process.env
- [ ] No file system writes (use Supabase Storage)
- [ ] Tested locally with `npm run build` && `npm start`

#### Rule #5: Design Quick and Scalable Endpoints
```typescript
// ✅ CORRECT: Optimized endpoint
export async function GET(request: Request) {
  // 1. Early validation
  if (!userId) return Response.json({ error: 'Unauthorized' }, { status: 401 });
  
  // 2. Efficient query with pagination
  const { data, error } = await supabase
    .from('tasks')
    .select('id, title, completed')
    .eq('user_id', userId)
    .limit(50); // Prevent huge responses
  
  // 3. Quick response
  return Response.json({ data }, { status: 200 });
}

// ❌ WRONG: Slow, unscalable endpoint
export async function GET(request: Request) {
  // No validation
  // Gets ALL data (could be thousands)
  const allTasks = await supabase.from('tasks').select('*');
  
  // Complex processing on server
  const processed = allTasks.map(task => {
    // Heavy computation
  });
  
  return Response.json({ data: processed });
}
```

**Performance Targets:**
- API response time: < 200ms (p95)
- Database queries: < 100ms (p95)
- Pagination: Always limit results
- Caching: Use where appropriate

#### Rule #6: Asynchronous Data Handling
```typescript
// ✅ CORRECT: Streaming response for long operations
export async function POST(request: Request) {
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      // Step 1: Send immediate response
      controller.enqueue(encoder.encode('data: {"status":"processing"}\n\n'));
      
      // Step 2: Process with OpenAI
      const aiResponse = await openai.chat.completions.create({...});
      controller.enqueue(encoder.encode(`data: ${JSON.stringify(aiResponse)}\n\n`));
      
      // Step 3: Save to database
      await supabase.from('results').insert({...});
      controller.enqueue(encoder.encode('data: {"status":"complete"}\n\n'));
      
      controller.close();
    },
  });
  
  return new Response(stream, {
    headers: { 'Content-Type': 'text/event-stream' },
  });
}

// ❌ WRONG: User waits for everything
export async function POST(request: Request) {
  const aiResponse = await openai.chat.completions.create({...}); // 10 seconds
  await supabase.from('results').insert({...}); // 2 seconds
  return Response.json({ data: aiResponse }); // User waited 12 seconds!
}
```

#### Rule #7: API Response Documentation
```typescript
/**
 * GET /api/tasks
 * 
 * Fetches user's tasks with optional filtering
 * 
 * Query Parameters:
 * - completed: boolean (optional) - Filter by completion status
 * - limit: number (optional, default: 50) - Max results
 * 
 * Response Structure:
 * {
 *   success: boolean,
 *   data: {
 *     tasks: Array<{
 *       id: string,
 *       title: string,
 *       completed: boolean,
 *       created_at: string
 *     }>,
 *     total: number,
 *     page: number
 *   },
 *   error?: string
 * }
 * 
 * Status Codes:
 * - 200: Success
 * - 401: Unauthorized (no valid session)
 * - 500: Server error
 * 
 * Example:
 * fetch('/api/tasks?completed=false&limit=10')
 */
export async function GET(request: Request) {
  // Implementation
}
```

---

### 🗄️ Backend & Database Rules (8-12)

#### Rule #8: Use Supabase with SSR
```typescript
// ✅ CORRECT: Server-side Supabase client
// lib/supabase-server.ts
import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';

export function createClient() {
  const cookieStore = cookies();
  
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get(name: string) {
          return cookieStore.get(name)?.value;
        },
      },
    }
  );
}

// ❌ WRONG: Client-side only (exposes service role key)
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY! // 🚨 NEVER on client!
);
```

**Supabase SSR Checklist:**
- [ ] Server components use server client
- [ ] Client components use client client
- [ ] Service role key NEVER exposed to client
- [ ] Row Level Security (RLS) enabled
- [ ] Auth checked before database operations

#### Rule #9: Maintain Existing Functionality
```typescript
// ✅ CORRECT: Adding feature preserves existing behavior
export async function createTask(task: Task) {
  // NEW: Validate task data
  if (!task.title || task.title.trim().length === 0) {
    throw new Error('Title is required');
  }
  
  // EXISTING: Original create logic (preserved)
  const { data, error } = await supabase
    .from('tasks')
    .insert(task)
    .select()
    .single();
  
  // NEW: Additional logging
  console.log('[Task Created]', data?.id);
  
  return { data, error };
}

// ❌ WRONG: Breaking existing functionality
export async function createTask(task: Task) {
  // Changed return type - breaks existing code!
  const { data } = await supabase.from('tasks').insert(task);
  return data; // Missing error handling that existed before
}
```

**Before Making Changes:**
1. Read existing code thoroughly
2. Identify all places function is used
3. Add feature without changing signature
4. Test existing use cases still work

#### Rule #10: Comprehensive Error Handling
```typescript
// ✅ CORRECT: Detailed error handling
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const userId = searchParams.get('userId');
    
    if (!userId) {
      console.error('[API Error] Missing userId parameter');
      return Response.json(
        { error: 'userId parameter is required' },
        { status: 400 }
      );
    }
    
    const { data, error } = await supabase
      .from('tasks')
      .select('*')
      .eq('user_id', userId);
    
    if (error) {
      console.error('[Supabase Error]', {
        message: error.message,
        details: error.details,
        hint: error.hint,
        userId
      });
      return Response.json(
        { error: 'Failed to fetch tasks' },
        { status: 500 }
      );
    }
    
    console.log('[API Success] Fetched tasks', { count: data.length, userId });
    return Response.json({ data }, { status: 200 });
    
  } catch (error) {
    console.error('[Unexpected Error]', error);
    return Response.json(
      { error: 'An unexpected error occurred' },
      { status: 500 }
    );
  }
}

// ❌ WRONG: Silent failures
export async function GET(request: Request) {
  const data = await supabase.from('tasks').select('*');
  return Response.json({ data }); // What if it failed?
}
```

#### Rule #11: Optimize for Speed
```typescript
// ✅ CORRECT: Optimized data fetching
export default function Dashboard() {
  // 1. Fetch only needed fields
  const { data: tasks } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => supabase
      .from('tasks')
      .select('id, title, completed, due_date') // Only what we need
      .order('created_at', { ascending: false })
      .limit(20), // Paginate
    staleTime: 60000, // Cache for 1 minute
  });
  
  return <TaskList tasks={tasks} />;
}

// ❌ WRONG: Fetching everything
export default function Dashboard() {
  const [tasks, setTasks] = useState([]);
  
  useEffect(() => {
    // Fetches ALL tasks, ALL fields, on every render
    supabase.from('tasks').select('*').then(({ data }) => setTasks(data));
  }, []); // Missing dependencies
  
  return <TaskList tasks={tasks} />;
}
```

**Optimization Checklist:**
- [ ] Only fetch needed fields (SELECT specific columns)
- [ ] Use pagination/limits
- [ ] Implement caching (React Query, SWR)
- [ ] Lazy load heavy components
- [ ] Optimize images (Next.js Image component)

#### Rule #12: Complete Code Verification
```typescript
// ✅ CORRECT: All imports, types, exports correct
// types/task.ts
export interface Task {
  id: string;
  title: string;
  completed: boolean;
  user_id: string;
}

// components/TaskCard.tsx
import { Task } from '@/types/task'; // ✅ Correct import path

export function TaskCard({ task }: { task: Task }) {
  return <div>{task.title}</div>;
}

// ❌ WRONG: Missing imports, wrong paths
export function TaskCard({ task }: { task: Task }) { // Task is undefined
  return <div>{task.title}</div>;
}
```

**Verification Steps:**
1. All imports resolve correctly
2. No TypeScript errors (`npm run type-check`)
3. No ESLint errors (`npm run lint`)
4. All files in correct locations
5. Build succeeds (`npm run build`)

---

### 💻 Language & Type Safety Rules (13)

#### Rule #13: Use TypeScript Strictly
```typescript
// ✅ CORRECT: Strict TypeScript
interface CreateTaskInput {
  title: string;
  description?: string;
  due_date?: Date;
  user_id: string;
}

export async function createTask(input: CreateTaskInput): Promise<Task> {
  const { data, error } = await supabase
    .from('tasks')
    .insert(input)
    .select()
    .single();
  
  if (error) throw new Error(`Failed to create task: ${error.message}`);
  
  return data as Task;
}

// ❌ WRONG: Using 'any' defeats the purpose
export async function createTask(input: any): Promise<any> {
  const { data } = await supabase.from('tasks').insert(input);
  return data;
}
```

**TypeScript Standards:**
- [ ] `strict: true` in tsconfig.json
- [ ] No `any` types (use `unknown` if needed)
- [ ] All props interfaces defined
- [ ] Return types explicit
- [ ] Type guards for user input

---

### 🔒 Security & Performance Rules (14-17)

#### Rule #14: Security and Scalability
```typescript
// ✅ CORRECT: Secure, scalable endpoint
import { rateLimit } from '@/lib/rate-limit';

export async function POST(request: Request) {
  // 1. Rate limiting
  const ip = request.headers.get('x-forwarded-for') || 'unknown';
  const rateLimitResult = await rateLimit(ip);
  if (!rateLimitResult.success) {
    return Response.json({ error: 'Too many requests' }, { status: 429 });
  }
  
  // 2. Authentication
  const session = await getServerSession();
  if (!session) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 });
  }
  
  // 3. Input validation
  const body = await request.json();
  const validatedInput = taskSchema.parse(body); // Zod validation
  
  // 4. Database with RLS
  const { data, error } = await supabase
    .from('tasks')
    .insert({
      ...validatedInput,
      user_id: session.user.id, // Force user ownership
    });
  
  return Response.json({ data }, { status: 201 });
}

// ❌ WRONG: Insecure endpoint
export async function POST(request: Request) {
  const body = await request.json();
  // No auth, no validation, no rate limiting
  const { data } = await supabase.from('tasks').insert(body);
  return Response.json({ data });
}
```

#### Rule #15: Error Checks and Logging
```typescript
// ✅ CORRECT: Comprehensive logging
export async function processTask(taskId: string) {
  console.log('[processTask] Starting', { taskId });
  
  try {
    const task = await fetchTask(taskId);
    if (!task) {
      console.warn('[processTask] Task not found', { taskId });
      return { success: false, error: 'Task not found' };
    }
    
    console.log('[processTask] Processing', { taskId, title: task.title });
    
    const result = await performProcessing(task);
    
    console.log('[processTask] Complete', { taskId, result });
    return { success: true, data: result };
    
  } catch (error) {
    console.error('[processTask] Error', {
      taskId,
      error: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined,
    });
    return { success: false, error: 'Processing failed' };
  }
}
```

#### Rule #16: Protect Endpoints
```typescript
// ✅ CORRECT: Protected endpoint
import { verifyAuth } from '@/lib/auth';
import { rateLimit } from '@/lib/rate-limit';

export async function POST(request: Request) {
  // 1. Rate limit by IP
  const limiter = await rateLimit(request);
  if (!limiter.success) {
    return Response.json({ error: 'Rate limit exceeded' }, { status: 429 });
  }
  
  // 2. Verify API key or session
  const authHeader = request.headers.get('authorization');
  const apiKey = authHeader?.replace('Bearer ', '');
  
  if (!apiKey || !(await verifyAuth(apiKey))) {
    return Response.json({ error: 'Invalid API key' }, { status: 401 });
  }
  
  // 3. Process request
  // ...
}

// lib/rate-limit.ts
import { Ratelimit } from '@upstash/ratelimit';
import { Redis } from '@upstash/redis';

const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(10, '10 s'), // 10 requests per 10 seconds
});

export async function rateLimit(request: Request) {
  const ip = request.headers.get('x-forwarded-for') || 'anonymous';
  return await ratelimit.limit(ip);
}
```

#### Rule #17: Secure Database Access
```sql
-- ✅ CORRECT: Row Level Security enabled
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

-- Users can only see their own tasks
CREATE POLICY "Users can view own tasks" ON tasks
  FOR SELECT
  USING (auth.uid() = user_id);

-- Users can only insert tasks for themselves
CREATE POLICY "Users can create own tasks" ON tasks
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Users can only update their own tasks
CREATE POLICY "Users can update own tasks" ON tasks
  FOR UPDATE
  USING (auth.uid() = user_id);

-- Users can only delete their own tasks
CREATE POLICY "Users can delete own tasks" ON tasks
  FOR DELETE
  USING (auth.uid() = user_id);
```

---

### 🛠️ Development Process Rules (18-23)

#### Rule #18: Plan Before Coding
```markdown
# ✅ CORRECT: Plan first

## Task: Add task priority feature

### 1. Analysis
- Current: Tasks have no priority
- Need: Users want to prioritize tasks (high, medium, low)
- Impact: Database schema, UI, API

### 2. Plan
1. Update database schema (add priority column)
2. Create migration script
3. Update TypeScript types
4. Modify API endpoints to accept priority
5. Update TaskCard component to show priority
6. Add priority filter to TaskList
7. Write tests

### 3. Edge Cases
- What if existing tasks have no priority? (Default to 'medium')
- Can users change priority after creation? (Yes)
- Should priority affect sort order? (Yes, high first)

### 4. Implementation
[Now start coding...]

# ❌ WRONG: Jump straight to coding
// Just start changing files without planning
```

#### Rule #19: Use Specified Tech Stack
```yaml
# Project Tech Stack Registry

PersonalAssistant:
  frontend: Next.js 14 (App Router, SSR)
  language: TypeScript
  styling: Tailwind CSS + DaisyUI
  backend: Supabase
  auth: NextAuth.js + Supabase Auth
  deployment: Vercel
  testing: Playwright
  
ManagementTeam:
  backend: Python 3.11 + FastAPI
  database: PostgreSQL
  cache: Redis
  testing: pytest
  formatting: Black + Ruff
```

#### Rule #20: Consistent Styles
```typescript
// ✅ CORRECT: Reuse existing input style
// Copy from existing sign-in page
export function TaskForm() {
  return (
    <input
      type="text"
      className="input input-bordered w-full" // Same as sign-in
      placeholder="Task title"
    />
  );
}

// ❌ WRONG: New custom style
export function TaskForm() {
  return (
    <input
      type="text"
      className="border-2 border-gray-300 rounded-lg p-3" // Different!
      placeholder="Task title"
    />
  );
}
```

#### Rule #21: Specify Files
```markdown
# ✅ CORRECT: Clear file specification

To add priority feature, modify these files:

1. **database/migrations/add_priority.sql**
   - Add priority column to tasks table

2. **src/types/task.ts**
   - Add priority to Task interface

3. **src/app/api/tasks/route.ts**
   - Update POST to accept priority
   - Update GET to filter by priority

4. **src/components/TaskCard.tsx**
   - Display priority badge

# ❌ WRONG: Vague instructions
"Update the task components and API"
```

#### Rule #22: Flat Component Structure
```
✅ CORRECT:
src/components/
├── TaskCard.tsx
├── TaskList.tsx
├── TaskForm.tsx
├── Dashboard.tsx
└── Sidebar.tsx

❌ WRONG:
src/components/
├── tasks/
│   ├── components/
│   │   ├── TaskCard.tsx
│   │   └── TaskList.tsx
├── dashboard/
│   └── components/
│       └── Dashboard.tsx
```

#### Rule #23: Efficient Communication
```markdown
# ✅ CORRECT: Efficient single message

"Add task priority feature:
1. Database: Add priority enum (high, medium, low) 
2. API: Update POST /api/tasks to accept priority
3. UI: Add priority selector to TaskForm
4. Default: Set existing tasks to 'medium'"

# ❌ WRONG: Multiple back-and-forth messages
User: "Add priority to tasks"
AI: "Where should I add it?"
User: "In the database"
AI: "What values?"
User: "High, medium, low"
AI: "Should I update the API?"
User: "Yes"
[10 messages instead of 1]
```

---

## Project-Specific Rule Sets

### Next.js Projects

```typescript
// File Structure
/src
  /app
    /api
      /tasks
        route.ts
    /dashboard
      page.tsx
    layout.tsx
    page.tsx
  /components
    TaskCard.tsx
    TaskList.tsx
  /lib
    supabase.ts
    utils.ts
  /types
    task.ts
    user.ts

// Naming Conventions
- Components: PascalCase (TaskCard.tsx)
- Files: kebab-case (voice-processor.ts)
- API Routes: kebab-case (api/voice-commands)
- Functions: camelCase (handleSubmit)
- Constants: SCREAMING_SNAKE_CASE (API_BASE_URL)
```

### Python Projects

```python
# File Structure
/src
  /agents
    strategy_agent.py
  /api
    routes.py
  /models
    task.py
  /utils
    helpers.py
/tests
  test_agents.py
/config
  env_manager.py
  .env

# Naming Conventions
- Modules: snake_case (strategy_agent.py)
- Classes: PascalCase (StrategyAgent)
- Functions: snake_case (process_task)
- Constants: SCREAMING_SNAKE_CASE (MAX_RETRIES)
```

---

## Code Quality Standards

### TypeScript Configuration
```json
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true
  }
}
```

### ESLint Configuration
```json
// .eslintrc.json
{
  "extends": ["next/core-web-vitals"],
  "rules": {
    "no-console": "warn",
    "no-debugger": "error",
    "prefer-const": "error",
    "react-hooks/exhaustive-deps": "warn"
  }
}
```

### Prettier Configuration
```json
// .prettierrc
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2
}
```

---

## Security Checklist

### Every API Endpoint Must:
- [ ] Verify authentication
- [ ] Validate all inputs
- [ ] Implement rate limiting
- [ ] Return appropriate status codes
- [ ] Log errors without exposing sensitive data
- [ ] Use parameterized queries
- [ ] Never expose service keys to client

### Every Database Table Must:
- [ ] Have Row Level Security enabled
- [ ] Have appropriate RLS policies
- [ ] Validate foreign key relationships
- [ ] Have proper indexes
- [ ] Audit sensitive operations

### Every Environment Variable Must:
- [ ] Be documented in .env.example
- [ ] Never be committed to git
- [ ] Be validated on startup
- [ ] Use different values per environment

---

## Architecture Patterns

### Component Pattern
```typescript
/**
 * Standard Component Template
 */
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface ComponentNameProps {
  // Required props
  requiredProp: string;
  // Optional props
  optionalProp?: number;
  // Callbacks
  onAction?: () => void;
}

export function ComponentName({
  requiredProp,
  optionalProp = 0,
  onAction,
}: ComponentNameProps) {
  // 1. Hooks
  const [state, setState] = useState<StateType>(initialState);
  const router = useRouter();
  
  // 2. Effects
  useEffect(() => {
    // Side effects
  }, [dependencies]);
  
  // 3. Event handlers
  const handleClick = () => {
    // Handle event
    onAction?.();
  };
  
  // 4. Render
  return (
    <div className="container">
      {/* JSX */}
    </div>
  );
}
```

### API Route Pattern
```typescript
/**
 * Standard API Route Template
 */
import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { z } from 'zod';

// 1. Input validation schema
const inputSchema = z.object({
  title: z.string().min(1).max(255),
  description: z.string().optional(),
});

// 2. GET handler
export async function GET(request: NextRequest) {
  try {
    // Auth check
    const session = await getServerSession();
    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    
    // Parse query params
    const { searchParams } = new URL(request.url);
    const limit = parseInt(searchParams.get('limit') || '50');
    
    // Database query
    const { data, error } = await supabase
      .from('tasks')
      .select('*')
      .eq('user_id', session.user.id)
      .limit(limit);
    
    if (error) throw error;
    
    return NextResponse.json({ data }, { status: 200 });
    
  } catch (error) {
    console.error('[API Error]', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

// 3. POST handler
export async function POST(request: NextRequest) {
  try {
    // Auth check
    const session = await getServerSession();
    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    
    // Parse and validate body
    const body = await request.json();
    const validatedInput = inputSchema.parse(body);
    
    // Database insert
    const { data, error } = await supabase
      .from('tasks')
      .insert({
        ...validatedInput,
        user_id: session.user.id,
      })
      .select()
      .single();
    
    if (error) throw error;
    
    return NextResponse.json({ data }, { status: 201 });
    
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: 'Invalid input', details: error.errors },
        { status: 400 }
      );
    }
    
    console.error('[API Error]', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

---

## Common Pitfalls & Solutions

### Pitfall #1: Not Using Server Components
```typescript
// ❌ WRONG: Client component for static data
'use client';
export default function Dashboard() {
  const [data, setData] = useState([]);
  useEffect(() => {
    fetch('/api/data').then(res => res.json()).then(setData);
  }, []);
  return <div>{data}</div>;
}

// ✅ CORRECT: Server component
export default async function Dashboard() {
  const { data } = await supabase.from('tasks').select('*');
  return <div>{data}</div>;
}
```

### Pitfall #2: Exposing Secrets
```typescript
// ❌ WRONG: Secret in client code
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY // 🚨 Exposed!
);

// ✅ CORRECT: Only on server
// Server-side only file
import { createClient } from '@supabase/supabase-js';

export const supabaseAdmin = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY! // Safe on server
);
```

### Pitfall #3: No Input Validation
```typescript
// ❌ WRONG: Trust user input
export async function POST(request: Request) {
  const body = await request.json();
  await supabase.from('tasks').insert(body); // Dangerous!
}

// ✅ CORRECT: Validate everything
import { z } from 'zod';

const taskSchema = z.object({
  title: z.string().min(1).max(255),
  description: z.string().max(1000).optional(),
  due_date: z.string().datetime().optional(),
});

export async function POST(request: Request) {
  const body = await request.json();
  const validated = taskSchema.parse(body); // Throws if invalid
  await supabase.from('tasks').insert(validated);
}
```

---

## AI Assistant Instructions

### When Receiving a Request:

1. **READ** existing code and patterns first
2. **PLAN** the approach before coding
3. **ASK** clarifying questions if needed
4. **FOLLOW** the 23 Rules strictly
5. **SPECIFY** which files to modify
6. **DOCUMENT** all changes clearly
7. **VERIFY** code compiles and runs

### Response Template:
```markdown
## Understanding the Request
[Summarize what user wants]

## Current State Analysis
[What exists now]

## Plan
1. Step 1
2. Step 2
3. Step 3

## Files to Modify/Create
- `src/components/NewComponent.tsx` - Create new component
- `src/app/api/endpoint/route.ts` - Update API

## Implementation
[Show code with clear comments]

## Testing Steps
1. Run `npm run type-check`
2. Run `npm run lint`
3. Test in browser at http://localhost:3000
```

### Quality Checks Before Responding:
- [ ] Follows the 23 Rules
- [ ] No TypeScript errors
- [ ] No security vulnerabilities
- [ ] Proper error handling
- [ ] Clear documentation
- [ ] Efficient and scalable

---

## Version History

**v1.0** (Oct 19, 2025)
- Initial comprehensive rules database
- 23 fundamental rules documented
- Project-specific patterns added
- Security checklist included
- Common pitfalls catalogued

---

**Last Updated:** October 19, 2025  
**Maintainer:** Robert Freyne  
**License:** Use freely for all projects

