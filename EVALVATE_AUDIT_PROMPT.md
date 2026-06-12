# 🔴 EVALVATE — BRUTAL V1 AUDIT PROTOCOL
### Role: You are a Senior Due Diligence Engineer at YCombinator / a16z / Google Ventures.
### Mission: Tear this product apart before any investor, client, or demo does it for us.
### Stakes: This is a LIVE PITCH product. Fake data, broken flows, or non-functional tech = instant pass.

---

## CONTEXT
This is **Evalvate** (evalvate.dev) — an AI-powered mock interview platform.
Tech stack: **Next.js 14 App Router, Supabase, Prisma, Gemini AI, ElevenLabs TTS/STT, MediaPipe facial/eye tracking, Vercel deployment.**
Founders are actively pitching YC and real enterprise clients. This audit must be the harshest technical review possible.

**Your job: Go through EVERY file in this repository. Flag everything. Show no mercy.**

---

## 🚨 SECTION 0 — THE CARDINAL SINS (CHECK THESE FIRST, STOP IF FOUND)

These are instant disqualifiers. If any exist, flag them as `[FATAL]` before continuing.

### 0.1 — Fake / Hardcoded Data Detection
Search every single file for the following patterns and list each occurrence with file path + line number:

```
SEARCH PATTERNS:
- Any array of objects that looks like mock interview questions hardcoded in component files
- Variables named: mockData, dummyData, testData, sampleData, fakeData, placeholderData, hardcodedQuestions
- Interview scores, feedback strings, or performance metrics that are static/fixed
- Any `Math.random()` or `Math.floor(Math.random())` used to GENERATE scores or feedback (not for IDs)
- Any `setTimeout` used to fake "AI is thinking" or "processing" delays without actual API calls behind them
- Any `.json` file in `/public` or `/data` folders that feeds the actual interview logic
- Any `return { score: 87, feedback: "Good job" }` style static returns in API routes
- "Lorem ipsum", "John Doe", "test@example.com", "Sample Question", "Demo Answer" anywhere in production code paths
- Graphs or charts fed by hardcoded arrays instead of real DB queries
- The word `TODO`, `FIXME`, `HACK`, `PLACEHOLDER`, `TEMP`, `WIP` in any production-path code
```

### 0.2 — API Routes That Don't Actually Call AI
Check every file in `/app/api/` or `/pages/api/`:

```
FOR EACH API ROUTE, VERIFY:
- Does it actually call Gemini / ElevenLabs / MediaPipe or does it return static JSON?
- Is there a real `await` to an external AI service?
- Does it handle the case where the AI API is DOWN or rate-limited?
- Is the response being passed through, or is a hardcoded string being returned?
- Does `/api/interview/facial` actually receive and process real MediaPipe data, or does it just acknowledge?
- Does `/api/interview/generate-question` call Gemini with a real prompt, or return from a question bank?
- Does `/api/report/generate` build a real dynamic report from session data, or return a template?
```

---

## 🔴 SECTION 1 — AUTHENTICATION & SECURITY AUDIT

```
CHECK:
[ ] Are Supabase keys exposed anywhere in frontend code? (NEXT_PUBLIC_ prefix check)
[ ] Is there any API route without auth middleware that should be protected?
[ ] Can a logged-out user access /dashboard, /interview/[id], /report/[id] by direct URL?
[ ] Is the Gemini API key, ElevenLabs API key stored only in .env.local and server-side?
[ ] Are there any console.log() calls that print API keys, tokens, or user data?
[ ] Is user interview data scoped per user_id in every DB query, or can User A see User B's data?
[ ] Are Prisma queries using `where: { userId }` consistently or are there unscoped queries?
[ ] Is there proper session validation in every protected API route?
[ ] Check /middleware.ts — does it actually protect routes or is it a skeleton?
[ ] Is there rate limiting on any AI API routes? (Critical for demo — one bad demo can cost $100+)
[ ] Any hardcoded admin credentials or bypass logic?
[ ] Any `SKIP_AUTH=true` or similar environment flags that could accidentally be set in prod?
```

---

## 🔴 SECTION 2 — DATABASE & PRISMA INTEGRITY AUDIT

```
CHECK EVERY FILE IN /prisma/ AND EVERY DB CALL:

[ ] Is the Prisma schema.prisma complete and does every model reflect actual product logic?
[ ] Are there tables/models defined but never used in the app? (Dead schema)
[ ] Are there features in the UI that have NO corresponding schema? (Features built on air)
[ ] Does the Interview model store: userId, jobRole, difficulty, startTime, endTime, status?
[ ] Does the Question model store: text, orderIndex, expectedAnswer, actualAnswer, score, feedback?
[ ] Does the Report model store: overallScore, emotionScore, eyeContactScore, speechScore, generatedAt?
[ ] Are there any raw SQL queries bypassing Prisma in Supabase edge functions?
[ ] Are migrations up to date? Run: `npx prisma migrate status` — are there pending migrations?
[ ] Does every Prisma create/update/delete have error handling (try/catch)?
[ ] Is there any data that's shown in the UI but NEVER saved to DB? (Phantom data)
[ ] Are interview sessions properly CLOSED (endTime set) or do they stay open forever?
[ ] Is there an index on userId, interviewId for performance on repeated queries?
[ ] Can the app function if the DB is cold/slow? (Connection pooling check)
```

---

## 🔴 SECTION 3 — GEMINI AI INTEGRATION AUDIT

```
CHECK EVERY FILE THAT IMPORTS OR CALLS GEMINI:

[ ] What model is being used? (gemini-pro, gemini-1.5-flash, gemini-1.5-pro?) — State it clearly
[ ] Is the model version hardcoded or environment-configurable?
[ ] What happens when Gemini returns an empty response or garbled JSON?
[ ] Is there JSON parsing with try/catch around every Gemini response?
[ ] Is the system prompt for question generation actually good, or is it one line?
[ ] Does the question generation prompt take jobRole + experienceLevel + previousQuestions into account?
[ ] Does the answer evaluation prompt receive: question + userAnswer + jobRole + expectedSkills?
[ ] Is there any prompt injection risk? (User input going directly into prompts without sanitization)
[ ] Are follow-up questions contextually aware of previous answers in the session?
[ ] What is the token limit set to? Is it appropriate for the use case?
[ ] Is there a fallback if Gemini quota is exceeded mid-interview?
[ ] Does the feedback generated feel generic ("Great answer!") or is it actually specific to the answer?
[ ] Is the evaluation rubric defined in the prompt or left to Gemini to decide?
[ ] Are scores (0-100) coming from Gemini or calculated separately?
[ ] Is there a conversation history being maintained across questions in one session?
[ ] Show me the FULL system prompt being sent to Gemini for: (a) question gen, (b) answer eval
```

---

## 🔴 SECTION 4 — ELEVENLABS TTS/STT INTEGRATION AUDIT

```
CHECK EVERY FILE THAT CALLS ELEVENLABS:

[ ] Is the Voice ID for Rachel hardcoded or in an env variable?
[ ] Is the model `eleven_monolingual_v1` still being used? (Check if a better/cheaper model exists)
[ ] Is TTS called for EVERY question or only on user request?
[ ] What is the average latency of a TTS call? Is there a loading state shown?
[ ] Is the audio blob being cached or is TTS called fresh every time (wasted API credits)?
[ ] If TTS fails, does the user see the question text anyway, or is the interview broken?
[ ] For STT: is it ElevenLabs STT or browser Web Speech API or something else? State clearly.
[ ] Is the STT transcript being cleaned/normalized before being sent to Gemini for evaluation?
[ ] What happens if the user's mic is blocked by browser permissions?
[ ] Is there a manual "type your answer" fallback if STT fails?
[ ] Is the audio stream properly stopped/cleaned up after each question? (Memory leak risk)
[ ] Are ElevenLabs API errors being caught and shown to the user?
```

---

## 🔴 SECTION 5 — MEDIAPIPE FACIAL/EYE TRACKING AUDIT

This is the most likely area to have fake/non-functional code. Be extremely thorough.

```
CHECK EVERY FILE RELATED TO FACIAL TRACKING:

[ ] Is MediaPipe actually loaded and initialized in the browser, or just imported?
[ ] Is the webcam stream actually being processed frame-by-frame?
[ ] What FPS is MediaPipe running at? Is it actually processing or just showing a preview?
[ ] Are landmarks being detected and what specific landmarks are used for:
    - Eye contact score
    - Attentiveness/distraction detection
    - Emotion detection (if claimed)
[ ] Is the `faceLandmarker` or `faceDetector` model actually being used?
[ ] Is the EYE CONTACT SCORE calculated from real gaze estimation or just face-detected-or-not?
[ ] What is the scoring formula for eye contact? Show me the exact calculation.
[ ] Is emotion data (happy, nervous, confused) being detected or is it hardcoded/random?
[ ] Does the `/api/interview/facial` endpoint receive actual landmark data or just a flag?
[ ] Is facial data being sent to the server during the interview or only at the end?
[ ] What happens on mobile where MediaPipe performance degrades?
[ ] What happens if the user has no camera or denies permission?
[ ] Are there any `Math.random()` calls generating fake "attention scores"?
[ ] Is the facial score shown in the report actually derived from session data?
[ ] Check if there's a `fakeFacialScore` or similar variable used as a fallback
[ ] Is the webcam feed actually mirrored and rendering in the interview UI?
```

---

## 🔴 SECTION 6 — INTERVIEW FLOW INTEGRITY AUDIT

This is the CORE product. Every step must work end-to-end without shortcuts.

```
TRACE THE COMPLETE INTERVIEW FLOW:

PRE-INTERVIEW:
[ ] Job role selection — is it dynamic or a hardcoded dropdown?
[ ] Difficulty selection — does it actually affect question generation?
[ ] Experience level — does it actually affect question generation?
[ ] Resume upload — if present, is it actually parsed and used in question context?
[ ] Camera/mic permission check — does it properly fail/warn?

DURING INTERVIEW:
[ ] Question 1 appears — is it from Gemini or from a static bank?
[ ] TTS speaks the question — does it actually work?
[ ] User answers via voice — is STT capturing it?
[ ] STT transcript shows up — is it accurate?
[ ] User submits answer — does it hit an API route?
[ ] Follow-up question is generated — is it contextually aware of the previous answer?
[ ] Number of questions — is it configurable or fixed?
[ ] Timer — is there a per-question timer? What happens when it runs out?
[ ] Live facial tracking running — is the score being accumulated?

POST-INTERVIEW:
[ ] Session ends — is endTime saved to DB?
[ ] Report generation triggered — is it async or blocking?
[ ] Report shows: overall score, per-question breakdown, facial/eye score, speech quality
[ ] Is the report data actually from THIS session or is it a generic template?
[ ] Can the user download/share the report?
[ ] Is the interview history saved and visible in the dashboard?

FLAG ANY STEP THAT:
- Uses setTimeout to simulate processing
- Returns static data
- Skips the actual AI call
- Has a `// TODO: implement` comment
```

---

## 🔴 SECTION 7 — REPORT GENERATION AUDIT

The report is what the user PAYS for. It must be real.

```
CHECK THE REPORT SYSTEM:

[ ] Show me the exact data structure of a generated report in the DB
[ ] Is the overall score a real weighted average of sub-scores?
[ ] What is the weighting formula? (Technical: X%, Communication: Y%, Eye Contact: Z%)
[ ] Is the per-question feedback generated by Gemini or is it template strings?
[ ] Is the "Strengths" section generated dynamically or from a template?
[ ] Is the "Areas for Improvement" section generated dynamically or from a template?
[ ] Does the report differ meaningfully between a good interview and a bad interview?
[ ] Are the charts/graphs in the report fed by real data or hardcoded values?
[ ] Is there a PDF export? Does it actually work?
[ ] Is the report URL shareable without requiring login? (Needed for demos)
[ ] Does the report load fast or does it regenerate on every visit?
[ ] Is there a loading state while the report is being generated?
[ ] What happens if Gemini fails during report generation?
```

---

## 🔴 SECTION 8 — FRONTEND & UX QUALITY AUDIT

```
COMPONENT-BY-COMPONENT CHECK:

[ ] Open /app directory — list every page route. Are any pages 404 or empty shells?
[ ] Is there a proper landing page at / that explains what Evalvate does in <10 seconds?
[ ] Is the onboarding flow complete? (Sign up → first interview → report)
[ ] Are loading states shown everywhere an async operation happens?
[ ] Are error states shown everywhere an API call can fail?
[ ] Is there an empty state for: no interviews done yet, no reports, failed interview
[ ] Are forms validated before submission?
[ ] Is the UI responsive on mobile? (Investors will check on their phone)
[ ] Any broken images (404 on /public assets)?
[ ] Any console errors on page load?
[ ] Is there a 404 page?
[ ] Is there proper SEO metadata (title, description, og:image) on key pages?
[ ] Does the favicon exist and look professional?
[ ] Are there any TypeScript errors? Run `npx tsc --noEmit` and report all errors
[ ] Are there any ESLint errors? Run `npx eslint . --ext .ts,.tsx` and report
[ ] Are there spelling errors in UI copy? (Instant credibility killer in demos)
[ ] Is "Evalvate" consistently spelled everywhere (not "Evalurate", "Evalulate", etc.)?
[ ] Is the color scheme consistent across all pages?
[ ] Are buttons/CTAs clearly labeled and functional?
[ ] Does the nav/sidebar have any broken links?
```

---

## 🔴 SECTION 9 — PERFORMANCE & SCALABILITY AUDIT

```
[ ] Run `next build` — does it build without errors or warnings?
[ ] How many API routes exist? Are any doing N+1 queries?
[ ] Are images optimized with next/image?
[ ] Are there any large uncompressed assets in /public?
[ ] Is MediaPipe loaded lazily or does it block page load?
[ ] Is the Gemini client initialized per-request or once at module level?
[ ] Is the Prisma client initialized with connection pooling?
[ ] Are there any API routes without response caching that could be cached?
[ ] What is the bundle size? Run `next build && next analyze` if configured
[ ] Are there any memory leaks in useEffect hooks? (Missing cleanup for webcam/MediaPipe)
[ ] Does the app handle concurrent users or will it break on shared resources?
[ ] Are AI API calls protected from being called multiple times on double-click?
```

---

## 🔴 SECTION 10 — ENVIRONMENT & DEPLOYMENT AUDIT

```
[ ] Does a .env.example file exist with all required keys documented?
[ ] List every environment variable the app requires and confirm each is set in Vercel
[ ] Is there a .env.local file accidentally committed to git? CHECK .gitignore
[ ] Does the app deploy to Vercel cleanly with zero build errors?
[ ] Are there any `console.log()` statements in production code? (Security + performance)
[ ] Is there error monitoring set up? (Sentry, LogRocket, or similar)
[ ] Is there analytics set up? (Needed to show traction to investors)
[ ] Does the Vercel deployment use the correct environment (production vs preview)?
[ ] Are there any CORS issues on API routes?
[ ] Is the Supabase project on a paid plan or free tier? (Free tier pauses after inactivity — DEMO KILLER)
[ ] Is there a custom domain configured or is it still on vercel.app?
[ ] Are all Prisma migrations applied to the production database?
```

---

## 🔴 SECTION 11 — BUSINESS LOGIC & PRODUCT COMPLETENESS

```
[ ] Can a complete stranger sign up and complete a full interview without any help?
[ ] Is there a "try without signup" or demo mode for quick investor demos?
[ ] Are there at least 3 distinct job roles working end-to-end?
[ ] Is there at least 2 difficulty levels working end-to-end?
[ ] Does the dashboard show a history of past interviews with scores?
[ ] Is there any pricing page or plan differentiation in the UI?
[ ] Is there a way for B2B clients (institutes/companies) to manage multiple users?
[ ] Is there a "coach" or "admin" role, or is it purely candidate-facing?
[ ] Does the product have a clear differentiation from interviewing.io, Pramp, or Practice Interview?
[ ] Is there any onboarding walkthrough or first-time user guidance?
[ ] Are there any features that are advertised on the landing page but don't actually work?
```

---

## 🔴 SECTION 12 — CODE QUALITY & MAINTAINABILITY

```
[ ] Are there any files over 500 lines that should be broken up?
[ ] Are API route handlers mixing business logic with HTTP handling?
[ ] Is there a /lib or /utils folder with reusable logic, or is everything inline?
[ ] Are there duplicated API calls across multiple components?
[ ] Are there any unused imports, dead components, or orphaned pages?
[ ] Are types defined for all API responses, or is `any` used everywhere?
[ ] Is error handling consistent (always try/catch, always returns proper HTTP status codes)?
[ ] Are HTTP status codes correct? (401 for unauthorized, 403 for forbidden, 422 for validation)
[ ] Are there any `as any` TypeScript casts hiding type errors?
[ ] Is the folder structure logical and navigable by a new developer?
```

---

## 🔴 SECTION 13 — THE "LIVE DEMO" STRESS TEST

This is what will happen in every investor meeting and enterprise sales call. Simulate it.

```
SIMULATE THIS EXACT SCENARIO:
1. Open evalvate.dev in an incognito window (no existing session)
2. Sign up with a new email
3. Select: "Software Engineer" interview, "Mid-Level", 5 questions
4. Grant camera and microphone permissions
5. Start interview
6. Answer ALL 5 questions verbally
7. End interview
8. Wait for report
9. View report

AT EACH STEP, REPORT:
[ ] Did it work? YES / NO / PARTIALLY
[ ] Time taken (seconds)
[ ] Any error shown to user
[ ] Any silent failure (appeared to work but data wasn't saved)
[ ] Quality of AI output (question, feedback, score)
[ ] Did facial tracking scores appear in the report?
[ ] Is the report data unique to this session?

ALSO TEST:
[ ] What happens if you close the browser mid-interview?
[ ] What happens if the internet disconnects for 5 seconds mid-interview?
[ ] What happens if Gemini returns a non-JSON response?
[ ] What happens on Safari (iOS) — does TTS/STT work?
```

---

## 🔴 SECTION 14 — THE INVESTOR "SHOW ME THE DATA" TEST

```
If an investor asks: "Show me a real user's report" — can you?
[ ] Is there at least 1 complete end-to-end interview in the production database right now?
[ ] Does the report look impressive and data-rich, or sparse and generic?
[ ] Are the scores defensible? ("Why did this answer get 73?" should have an answer)
[ ] Is there any usage analytics? (total interviews done, avg score, return user rate)
[ ] Is there a way to export or share a report URL for an investor to view independently?
```

---

## 📋 FINAL OUTPUT FORMAT

After auditing EVERY file and section above, produce this exact output:

```
═══════════════════════════════════════════════════
EVALVATE V1 — FULL AUDIT REPORT
Audited: [date]
Files Checked: [X]
═══════════════════════════════════════════════════

[FATAL] — HARDCODED/FAKE DATA FOUND:
  → file: [path], line: [N], issue: [description]
  → file: [path], line: [N], issue: [description]

[CRITICAL] — BROKEN CORE FLOWS:
  → [description, file reference]

[HIGH] — SECURITY ISSUES:
  → [description, file reference]

[HIGH] — AI INTEGRATION GAPS:
  → [description, file reference]

[MEDIUM] — UX / PRODUCT GAPS:
  → [description, file reference]

[LOW] — CODE QUALITY / POLISH:
  → [description, file reference]

═══════════════════════════════════════════════════
DEMO READINESS SCORE: [X/10]
INVESTOR READINESS SCORE: [X/10]
WHAT WILL BREAK IN FIRST LIVE DEMO: [list]
WHAT MUST BE FIXED IN NEXT 48 HOURS: [list]
WHAT CAN WAIT: [list]
═══════════════════════════════════════════════════
```

---

## ⚡ QUICK COMMANDS TO RUN RIGHT NOW

Paste these in terminal before starting the file audit:

```bash
# 1. Find all hardcoded data patterns
grep -rn "mockData\|dummyData\|testData\|sampleData\|fakeData\|hardcoded\|placeholder\|lorem ipsum" --include="*.ts" --include="*.tsx" --include="*.js" .

# 2. Find all TODOs and FIXMEs
grep -rn "TODO\|FIXME\|HACK\|TEMP\|WIP\|PLACEHOLDER" --include="*.ts" --include="*.tsx" .

# 3. Find all Math.random() uses
grep -rn "Math.random\|Math.floor" --include="*.ts" --include="*.tsx" .

# 4. Find all setTimeout uses (potential fake loading states)
grep -rn "setTimeout" --include="*.ts" --include="*.tsx" .

# 5. Find all console.log in production code
grep -rn "console.log\|console.error\|console.warn" --include="*.ts" --include="*.tsx" --include="*.js" . | grep -v "node_modules" | grep -v ".next"

# 6. Find hardcoded scores or numbers that look like fake metrics
grep -rn "score: [0-9]\|feedback: \"\|rating: [0-9]" --include="*.ts" --include="*.tsx" .

# 7. Find any accidental .env commits
git log --all --full-history -- "**/.env*"

# 8. Check for TypeScript errors
npx tsc --noEmit 2>&1 | head -50

# 9. Find all API routes
find . -path "*/api/**" -name "*.ts" -not -path "*/node_modules/*" | sort

# 10. Check if prisma is in sync
npx prisma migrate status
```

---

> **REMEMBER:** You are not auditing this to be nice. You are auditing this as if a single bug during a YC partner demo will kill the company. Be surgical. Be brutal. Be specific. Every finding needs a file path and line number. No vague feedback. No "this looks okay" without verification. Check. Every. File.
