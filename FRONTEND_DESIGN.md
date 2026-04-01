# Dream Job Copilot — Frontend Design Document

## 1. Executive Summary

This document describes a **web-based frontend** for the Dream Job Copilot pipeline. The current CLI + Rich-terminal interface is replaced with a modern **React SPA** served by a **Vite** dev server, backed by an **Express.js API** that orchestrates the existing Python pipeline via a child process / REST bridge.

The design prioritises:
- **Guided wizard UX** — users progress through pipeline stages step-by-step
- **Real-time feedback** — Server-Sent Events (SSE) stream pipeline progress to the browser
- **Global job search** — aggregates roles across 10+ job portals worldwide, not limited to any country
- **Dream role focus** — surfaces aspirational roles, not just safe matches, with skill-gap insights
- **Direct application** — every job card links to the original posting; users never get stuck
- **Tailored materials** — AI-generated custom resume + cover letter per role
- **Mobile-friendly** — responsive layout, works on tablets too
- **Minimal friction** — drag-and-drop resume upload, sensible defaults, clear CTAs

---

## 2. High-Level Architecture

```
+------------------------+       +--------------------------+       +----------------------+
|   React SPA (Vite)     |<----->|   Express.js API Server  |<----->|  Python Pipeline      |
|   Port 5173            | HTTP  |   Port 3001              | spawn |  (child_process)      |
|                        |  +    |                          |  or   |                       |
|  • Upload Resume       |  SSE  |  • /api/pipeline/start   | HTTP  |  • LangGraph stages   |
|  • Explore Dream Roles |       |  • /api/pipeline/status  |       |  • OpenAI + Tavily    |
|  • View Global Jobs    |       |  • /api/feedback         |       |  • Multi-portal jobs  |
|  • Give Feedback       |       |  • /api/download/:id     |       |                       |
|  • Download Resumes    |       |  • /api/cover-letter/:id |       |                       |
|  • Cover Letters       |       |  • /api/apply-link/:id   |       |                       |
+------------------------+       +--------------------------+       +----------------------+
```

### Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| Frontend | **React 18** + **Vite** | Fast HMR, modern DX |
| Styling | **Tailwind CSS** | Rapid, utility-first styling |
| State | **React Context** + `useReducer` | Pipeline state is sequential, no need for Redux |
| HTTP | **Axios** | Promise-based, interceptors for error handling |
| Real-time | **Server-Sent Events (SSE)** | Simpler than WebSocket for unidirectional pipeline updates |
| API Server | **Express.js** | Lightweight, widely-known, proxies to Python |
| Python bridge | **child_process.spawn** | Runs `python main.py` with `--non-interactive` + JSON IPC |
| Icons | **Lucide React** | Clean, consistent iconography |
| Notifications | **React Hot Toast** | Non-blocking success/error toasts |
| Animations | **Framer Motion** | Smooth page transitions and loading states |

---

## 3. Global Job Search Strategy

This is the core differentiator. Job search spans **multiple portals globally** using a layered aggregation approach.

### 3.1 Job Source Aggregation

The backend queries the following sources (via Tavily + direct APIs where available):

| Portal | Coverage | Notes |
|---|---|---|
| **LinkedIn Jobs** | Global | Best for professional/tech roles |
| **Indeed** | 60+ countries | High volume, broad coverage |
| **Glassdoor** | Global | Pairs with employee review data |
| **Adzuna** | 16 countries (UK, AU, US, CA, DE, FR, IN...) | Has public API |
| **Remotive** | Global remote | Remote-only tech jobs |
| **We Work Remotely** | Global remote | High-quality remote roles |
| **Stepstone** | Europe (DE, NL, BE, AT) | Europe's largest job board |
| **Naukri** | India | Dominant in the Indian market |
| **JobsDB** | Southeast Asia (SG, HK, TH, PH) | APAC coverage |
| **Seek** | Australia + New Zealand | Dominant in ANZ region |
| **Reed** | United Kingdom | UK's largest job board |
| **The Muse** | US + global remote | Strong company culture data |

### 3.2 Search Query Construction

The pipeline builds **region-aware queries** so users are not siloed to one country:

```
Base query:   "{role_title} {top_skills}"
Variants:
  - Global remote:    "{query} remote global"
  - By region:        "{query} {region_name}" for each selected region
  - Aspirational:     "{dream_role} {adjacent_skills} open to relocation"
  - Visa-friendly:    "{query} visa sponsorship"
```

The user selects their **search scope** on the Preferences page:
- Anywhere in the world (default)
- Specific countries / regions
- Remote-only
- Willing to relocate (with visa sponsorship filter)

### 3.3 Dream Role vs. Safe Match

Two result tracks are surfaced side-by-side:

| Track | Definition | Visual Treatment |
|---|---|---|
| **Safe Match** | >80% skill overlap with current resume | Green badge |
| **Dream Role** | 50-80% overlap but aspirational title/company | Gold star badge |
| **Stretch Role** | <50% overlap — shows skill gap to bridge | Purple "Grow" badge |

Stretch roles include an **AI skill gap card** explaining exactly what to learn to qualify.

---

## 4. Page-by-Page Design

The app follows a **wizard pattern** with a persistent **progress stepper** at the top.

### 4.1 Progress Stepper (persistent header)

```
 +---------------------------------------------------------------------------------+
 |  [1]-----[2]-----[3]-----[4]-----[5]-----[6]-----[7]-----[8]-----[9]-----[10]  |
 | Upload  Profile  Search  Picks  Prefs  Reviews  Best   Resumes Letters  Apply   |
 |  [ok]    [ok]     [on]    [ ]    [ ]     [ ]     [ ]     [ ]     [ ]     [ ]    |
 +---------------------------------------------------------------------------------+
```

- Each step is a numbered circle connected by a line
- Completed (green fill) / Active (indigo pulse animation) / Pending (grey outline)
- Clicking a completed step lets you review (read-only) that stage's output
- Responsive: on mobile, only current + adjacent 2 steps visible; swipe to navigate
- **10 steps** (added Cover Letter as a distinct step before Apply)

---

### 4.2 Page 1 — Welcome & Resume Upload

```
 +---------------------------------------------------------------------+
 |                    Dream Job Copilot                                |
 |           Find the job you actually want, anywhere in the world     |
 |                                                                     |
 |  +-----------------------------------------------------------+      |
 |  |                                                           |      |
 |  |    [PDF icon]  Drag & drop your resume here              |      |
 |  |               or click to browse                         |      |
 |  |                                                           |      |
 |  |               Supports PDF and DOCX                      |      |
 |  +-----------------------------------------------------------+      |
 |                                                                     |
 |  +-- Uploaded ---------------------------------------------------+  |
 |  |  [doc] jane_doe_resume.pdf  (245 KB)          [x Remove]     |  |
 |  +---------------------------------------------------------------+  |
 |                                                                     |
 |  Where do you want to search?                                       |
 |  ( o Anywhere in the world )  ( o Specific countries )             |
 |  ( o Remote only )            ( o Open to relocation )             |
 |                                                                     |
 |  What kind of roles are you dreaming of?  (optional)               |
 |  +-----------------------------------------------------------+      |
 |  | e.g. Head of Engineering, Staff Engineer at FAANG...     |      |
 |  +-----------------------------------------------------------+      |
 |                                                                     |
 |                    [ Start Analysis ]                               |
 +---------------------------------------------------------------------+
```

**Interactions:**
- Drag-and-drop zone with hover highlight
- File type validation (`.pdf`, `.docx` only)
- Max file size: 10 MB
- "Dream role" text hint pre-seeds the aspirational search track
- Search scope selector determines how regions are queried (default: global)
- "Start Analysis" triggers upload → pipeline stages 1–3 run automatically
- A loading overlay with animated progress bar appears during processing

---

### 4.3 Page 2 — Resume Profile (Stage 1 output)

```
 +---------------------------------------------------------------------+
 |  Your Resume Profile                                                |
 |                                                                     |
 |  +-- Profile ---------------------------------+  +-- AI Review ---+ |
 |  | Name:    Jane Doe                         |  |                | |
 |  | Role:    Senior Software Engineer         |  | "Strong cloud  | |
 |  | Exp:     7 years                          |  |  native back-  | |
 |  |                                           |  |  ground with   | |
 |  | Core Skills:                              |  |  leadership... | |
 |  |  [Python] [Go] [AWS] [Kubernetes]         |  |                | |
 |  |  [Docker] [React] [PostgreSQL] ...        |  | Score: 4.5/5   | |
 |  |                                           |  |                | |
 |  | Target Roles (detected):                  |  | Gaps to watch: | |
 |  |  • Staff Software Engineer                |  |  - System      | |
 |  |  • Principal Engineer                     |  |    design depth| |
 |  |  • Engineering Manager                    |  |  - ML exposure | |
 |  |                                           |  |                | |
 |  | Detected regions from resume:             |  |                | |
 |  |  [India] [UK] — override? [edit]          |  |                | |
 |  +-------------------------------------------+  +----------------+ |
 |                                                                     |
 |                    [ Continue to Job Search -> ]                    |
 +---------------------------------------------------------------------+
```

**Components:**
- **ProfileCard** — Name, role, experience, skills as coloured tags/chips
- **ReviewPanel** — AI-generated review text + detected gaps
- Skills rendered as pill badges, colour-coded by category (languages / infra / soft skills)
- "Detected regions" chip — auto-detected from resume location history, editable

---

### 4.4 Page 3 — Global Job Search Results (Stage 2 output)

```
 +---------------------------------------------------------------------+
 |  Job Search Results  (47 found across 8 portals)                    |
 |                                                                     |
 |  Portals searched: [LinkedIn] [Indeed] [Remotive] [Adzuna] [+4]    |
 |                                                                     |
 |  [Filter v]  [Sort v]  [Region v]  [Portal v]  [Type v]            |
 |   Location   Match%    Americas    LinkedIn     Full-time           |
 |                        Europe      Indeed       Contract            |
 |                        APAC        Remote-only  Part-time           |
 |                        Remote                                       |
 |                                                                     |
 |  +-- Job Card ---------------------------------------------------+  |
 |  | [DREAM ROLE star]  Staff Software Engineer    Match: 92%      |  |
 |  | TechCorp · San Francisco, CA · Remote · LinkedIn              |  |
 |  |                                                               |  |
 |  | "Looking for an experienced engineer to lead..."              |  |
 |  |                                                               |  |
 |  | Skills matched: [Python v] [AWS v] [K8s v]  Missing: [Rust x]|  |
 |  |                                                               |  |
 |  | [View Details]      [Save]      [-> Apply on LinkedIn]        |  |
 |  +---------------------------------------------------------------+  |
 |                                                                     |
 |  +-- Job Card ---------------------------------------------------+  |
 |  | [STRETCH ROLE grow] Principal Engineer        Match: 61%      |  |
 |  | DeepMind · London, UK · Hybrid · Glassdoor                    |  |
 |  | Skill gap: needs [ML] [Research experience]                   |  |
 |  | [View Details]      [Save]      [-> Apply on Glassdoor]       |  |
 |  +---------------------------------------------------------------+  |
 |                                                                     |
 |  +-- Job Card ---------------------------------------------------+  |
 |  | [SAFE MATCH check]  Senior Engineer           Match: 88%      |  |
 |  | CloudCo · Singapore · Remote OK · Seek                        |  |
 |  | [View Details]      [Save]      [-> Apply on Seek]            |  |
 |  +---------------------------------------------------------------+  |
 |                                                                     |
 |              [ Continue to Recommendations -> ]                     |
 +---------------------------------------------------------------------+
```

**Features:**
- Source portal badge on every card (LinkedIn / Indeed / Remotive / etc.)
- **"Apply on [Portal]" button** — opens the original job posting URL in a new tab
- Role type badge: Dream Role (gold star) / Safe Match (green check) / Stretch Role (purple grow)
- Inline skill match chips: green ticked = matched, red x = missing
- Filterable by: location/region, portal source, work mode, match score range, role type
- Sortable by: match score, date posted, company name, location
- Match score bar colour: green >80%, amber 50-80%, rose <50%
- Expandable card shows full job description + salary range (where available)
- **"Save" button** bookmarks jobs to a personal shortlist across sessions

---

### 4.5 Page 4 — AI Recommendations (Stage 3 output)

```
 +---------------------------------------------------------------------+
 |  Top Recommendations                                                |
 |  AI-curated picks from 47 results                                   |
 |                                                                     |
 |  [Select All]  [Deselect All]  Selected: 2 of 5                    |
 |                                                                     |
 |  +-- #1 --------------------------------------------------------+  |
 |  | [x]  Staff Software Engineer @ TechCorp      Match: 92%      |  |
 |  |      San Francisco / Remote · LinkedIn                        |  |
 |  |                                                               |  |
 |  |  Why this role:                                               |  |
 |  |  "Your 7 years of Python and cloud-native experience          |  |
 |  |   directly align with TechCorp's microservices stack..."      |  |
 |  |                                                               |  |
 |  |  [-> Apply on LinkedIn]                                       |  |
 |  +---------------------------------------------------------------+  |
 |                                                                     |
 |  +-- #2 --------------------------------------------------------+  |
 |  | [x]  Principal Engineer @ CloudCo            Match: 85%      |  |
 |  |      Seattle / Hybrid · Indeed                                |  |
 |  |  "Strong Kubernetes expertise matches their K8s-first..."     |  |
 |  |  [-> Apply on Indeed]                                         |  |
 |  +---------------------------------------------------------------+  |
 |                                                                     |
 |  +-- Dream Pick (stretch) -------------------------------------+    |
 |  | [ ]  Staff ML Engineer @ DeepMind            Match: 61%     |    |
 |  |      London / Hybrid                                          |    |
 |  |  Skill gap: needs [ML fundamentals] [Research papers]        |    |
 |  |  "If you spend 3-6 months on ML fundamentals, this role      |    |
 |  |   becomes highly reachable. Here's a learning path: ..."     |    |
 |  |  [-> Apply on Glassdoor]   [See Learning Path]               |    |
 |  +---------------------------------------------------------------+  |
 |                                                                     |
 |                    [ Continue to Preferences -> ]                   |
 +---------------------------------------------------------------------+
```

**Interactions:**
- Checkboxes to select/deselect (replaces CLI number-entry)
- "Select All" / "Deselect All"
- AI reasoning displayed per card
- Stretch roles show **Learning Path modal** — a short AI-generated roadmap
- Every card has a direct "Apply on [Portal]" link

---

### 4.6 Page 5 — User Preferences / Feedback (Stage 4)

```
 +---------------------------------------------------------------------+
 |  Refine Your Search                                                 |
 |                                                                     |
 |  Search Scope                                                       |
 |  ( o Global — search everywhere )                                   |
 |  ( o Specific regions )                                             |
 |     [x] North America  [x] Europe  [ ] APAC  [ ] MENA              |
 |  ( o Remote only — no relocation )                                  |
 |  ( o Open to relocation + visa sponsorship )                        |
 |                                                                     |
 |  Preferred Industries                                               |
 |  +-----------------------------------------------------------+      |
 |  | e.g. FinTech, HealthTech, Cloud Computing                 |      |
 |  +-----------------------------------------------------------+      |
 |                                                                     |
 |  Preferred Locations                                                |
 |  +-----------------------------------------------------------+      |
 |  | e.g. San Francisco, London, Singapore, Remote             |      |
 |  +-----------------------------------------------------------+      |
 |                                                                     |
 |  Work Mode                                                          |
 |  ( o Remote )  ( o Hybrid )  ( o Onsite )  ( o No Preference )     |
 |                                                                     |
 |  Salary Expectation                                                 |
 |  +-----------------------------------------------------------+      |
 |  | e.g. $180k-$220k USD / GBP 90k-120k / open               |      |
 |  +-----------------------------------------------------------+      |
 |                                                                     |
 |  Company Preferences  (optional)                                    |
 |  +-----------------------------------------------------------+      |
 |  | e.g. Series B+ startups, no consulting firms              |      |
 |  +-----------------------------------------------------------+      |
 |                                                                     |
 |  Additional Notes                                                   |
 |  +-----------------------------------------------------------+      |
 |  | e.g. Strong engineering culture, flat hierarchy           |      |
 |  +-----------------------------------------------------------+      |
 |                                                                     |
 |         [ <- Back ]              [ Refine Search -> ]              |
 +---------------------------------------------------------------------+
```

**Interactions:**
- Search scope drives which portals and regions are queried in stage 5
- Visa sponsorship filter appended to queries when "open to relocation" selected
- All fields optional (can skip with defaults)
- "Refine Search" triggers stages 5–7 in sequence

---

### 4.7 Page 6 — Refined Results + Employee Reviews (Stages 5-7)

```
 +---------------------------------------------------------------------+
 |  Best Matched Jobs                                                  |
 |  Ranked: 70% role fit + 20% employee rating + 10% location pref    |
 |                                                                     |
 |  +-- #1 --------------------------------------------------------+  |
 |  | Staff Software Engineer @ TechCorp                            |  |
 |  | San Francisco / Remote · LinkedIn                             |  |
 |  |                                                               |  |
 |  | Match: 92%    Employee Rating: 4.2/5 (312 reviews)           |  |
 |  | Combined: ████████████░░ 89.5%                               |  |
 |  |                                                               |  |
 |  | Employee Feedback:                                            |  |
 |  | "Great engineering culture, competitive pay, good WLB.        |  |
 |  |  Some concerns about rapid growth and management changes."    |  |
 |  |                                                               |  |
 |  | Pros: Engineering culture · Compensation · WLB               |  |
 |  | Cons: Rapid growth challenges · Management turnover          |  |
 |  |                                                               |  |
 |  | Salary range (market data): $190k – $230k                    |  |
 |  |                                                               |  |
 |  | [-> Apply on LinkedIn]                                        |  |
 |  +---------------------------------------------------------------+  |
 |                                                                     |
 |         [ Generate Tailored Resumes & Cover Letters -> ]           |
 +---------------------------------------------------------------------+
```

**Features:**
- Combined score bar (3-factor weighted formula)
- Star rating display
- Expandable pros/cons
- **Salary range** from market data (sourced via Tavily/Glassdoor scraping)
- Direct "Apply on [Portal]" link per card

---

### 4.8 Page 7 — Enhanced Resumes (Stage 8)

```
 +---------------------------------------------------------------------+
 |  Tailored Resumes                                                   |
 |                                                                     |
 |  +-- TechCorp — Staff Software Engineer ----------------------------+|
 |  |                                                                  ||
 |  | [Resume] [Cover Letter]  <- tabs                                ||
 |  |                                                                  ||
 |  | +-- Preview ------------------------------------------------+   ||
 |  | |                                                           |   ||
 |  | |  JANE DOE                                                 |   ||
 |  | |  Staff Software Engineer                                  |   ||
 |  | |                                                           |   ||
 |  | |  SUMMARY                                                  |   ||
 |  | |  Results-driven engineer with 7+ years building           |   ||
 |  | |  cloud-native microservices at scale...                   |   ||
 |  | |                                                           |   ||
 |  | |  (scrollable preview)                                     |   ||
 |  | +-----------------------------------------------------------+   ||
 |  |                                                                  ||
 |  | [Toggle: Original | Enhanced | Diff]                            ||
 |  |                                                                  ||
 |  | Changes made:                                                    ||
 |  |  - Reordered skills to match TechCorp's JD keywords             ||
 |  |  - Added quantified achievement in EXPERIENCE section           ||
 |  |  - Tailored summary for Staff Engineer level                    ||
 |  |                                                                  ||
 |  | [Copy to Clipboard]   [Download .txt]   [-> Apply on LinkedIn]  ||
 |  +------------------------------------------------------------------+|
 |                                                                     |
 |  +-- CloudCo — Principal Engineer ----------------------------------+|
 |  |  (similar layout)                                                ||
 |  +------------------------------------------------------------------+|
 |                                                                     |
 |                [ Apply to All Jobs -> ]                             |
 +---------------------------------------------------------------------+
```

**Features:**
- **Tabbed view per job: Resume tab + Cover Letter tab** (new)
- Scrollable preview of enhanced resume
- **Three-way toggle: Original / Enhanced / Diff** (colour-coded line-by-line diff)
- Changes summary bullet list
- Copy to clipboard
- Individual download (.txt)
- **"Apply on [Portal]" button** — direct link, opens original posting in new tab
- "Apply to All" triggers stage 9

---

### 4.9 Page 8 — Cover Letters (NEW — Stage 8b)

```
 +---------------------------------------------------------------------+
 |  Tailored Cover Letters                                             |
 |                                                                     |
 |  +-- TechCorp — Staff Software Engineer ----------------------------+|
 |  |                                                                  ||
 |  | +-- Preview ------------------------------------------------+   ||
 |  | |  Dear Hiring Team at TechCorp,                            |   ||
 |  | |                                                           |   ||
 |  | |  I am excited to apply for the Staff Software Engineer    |   ||
 |  | |  role. With 7+ years building cloud-native systems on     |   ||
 |  | |  AWS and Kubernetes, I have led teams that scaled...      |   ||
 |  | |                                                           |   ||
 |  | |  (scrollable — approx 350 words)                         |   ||
 |  | +-----------------------------------------------------------+   ||
 |  |                                                                  ||
 |  | Tone:  ( o Professional )  ( o Conversational )  ( o Concise )  ||
 |  | Length: ( o Short ~200w )  ( o Standard ~350w )  ( o Long ~500w)||
 |  |                                                                  ||
 |  | [Regenerate with new tone]                                      ||
 |  |                                                                  ||
 |  | [Copy to Clipboard]   [Download .txt]   [-> Apply on LinkedIn]  ||
 |  +------------------------------------------------------------------+|
 |                                                                     |
 |              [ Proceed to Apply -> ]                                |
 +---------------------------------------------------------------------+
```

**Features:**
- One cover letter generated per selected job, tailored to the JD and company
- Tone selector: Professional / Conversational / Concise — triggers regeneration
- Length selector
- "Regenerate" re-calls the LLM with new parameters without re-running the full pipeline
- Copy to clipboard and download per letter
- **"Apply on [Portal]" direct link** — user can paste the cover letter directly into the application form

---

### 4.10 Page 9 — Apply Hub (Stage 9 — Final)

```
 +---------------------------------------------------------------------+
 |  Ready to Apply!                                                    |
 |                                                                     |
 |  +-- Application Log -------------------------------------------+  |
 |  | #  Role                  Company     Portal      Action       |  |
 |  |                                                               |  |
 |  | 1  Staff SW Engineer     TechCorp    LinkedIn    [-> Apply]   |  |
 |  |    Resume [Download]     Cover Letter [Copy]                  |  |
 |  |                                                               |  |
 |  | 2  Principal Engineer    CloudCo     Indeed      [-> Apply]   |  |
 |  |    Resume [Download]     Cover Letter [Copy]                  |  |
 |  |                                                               |  |
 |  | 3  Eng Manager           FinStartup  Glassdoor   [-> Apply]   |  |
 |  |    Resume [Download]     Cover Letter [Copy]                  |  |
 |  +---------------------------------------------------------------+  |
 |                                                                     |
 |  Pro tip: Open each "Apply" link, paste your tailored cover letter  |
 |  and attach your downloaded resume. Both are ready above.           |
 |                                                                     |
 |  Track your applications:                                           |
 |  +-- Checklist ------------------------------------------------+    |
 |  | [ ]  Applied to TechCorp — Staff SE        [Mark Done]      |    |
 |  | [ ]  Applied to CloudCo — Principal Eng    [Mark Done]      |    |
 |  | [ ]  Applied to FinStartup — Eng Manager   [Mark Done]      |    |
 |  +--------------------------------------------------------------+   |
 |                                                                     |
 |  [ Download All Resumes (.zip) ]   [ Download All Letters (.zip) ] |
 |                    [ Start New Search ]                             |
 +---------------------------------------------------------------------+
```

**Features:**
- Each row has a direct **"Apply on [Portal]" link** opening the original job posting
- Inline **Resume Download** + **Cover Letter Copy** per row — so users have everything right where they need it
- **Application checklist** — users tick off as they submit; state saved to sessionStorage
- "Download All Resumes" as ZIP
- "Download All Cover Letters" as ZIP (new)
- "Start New Search" resets the wizard

---

## 5. Component Hierarchy

```
<App>
+-- <Header />                          # Logo + navigation
+-- <ProgressStepper step={current} />  # 10-step wizard indicator
+-- <Routes>
|   +-- <UploadPage />                  # Page 1
|   |   +-- <DropZone />
|   |   +-- <FilePreview />
|   |   +-- <SearchScopeSelector />     # NEW — global/regional/remote
|   +-- <ResumeReviewPage />            # Page 2
|   |   +-- <ProfileCard />
|   |   +-- <SkillBadges />
|   |   +-- <ReviewPanel />
|   |   +-- <GapHighlights />           # NEW — detected skill gaps
|   +-- <JobSearchPage />               # Page 3
|   |   +-- <PortalBadgeBar />          # NEW — shows which portals were queried
|   |   +-- <FilterBar />
|   |   +-- <SortDropdown />
|   |   +-- <JobCard /> (xN)
|   |       +-- <RoleTypeBadge />       # NEW — Dream/Safe/Stretch
|   |       +-- <SkillMatchChips />     # NEW — matched/missing skills inline
|   |       +-- <ApplyButton />         # NEW — direct portal link
|   +-- <RecommendationsPage />         # Page 4
|   |   +-- <RecommendationCard /> (xN)
|   |       +-- <Checkbox />
|   |       +-- <ReasoningText />
|   |       +-- <LearningPathModal />   # NEW — for stretch roles
|   |       +-- <ApplyButton />         # NEW
|   +-- <FeedbackPage />                # Page 5
|   |   +-- <SearchScopeSelector />     # reused
|   |   +-- <TextInput /> (industries, locations, salary, company prefs)
|   |   +-- <RadioGroup /> (work mode)
|   |   +-- <RegionCheckboxGroup />     # NEW — region multi-select
|   |   +-- <TextArea /> (notes)
|   +-- <BestJobsPage />                # Page 6
|   |   +-- <BestJobCard /> (xN)
|   |       +-- <ScoreBar />
|   |       +-- <StarRating />
|   |       +-- <ReviewSummary />
|   |       +-- <SalaryRange />         # NEW
|   |       +-- <ApplyButton />         # NEW
|   +-- <EnhancedResumesPage />         # Page 7
|   |   +-- <ResumePreview /> (xN)
|   |       +-- <TabBar />              # NEW — Resume | Cover Letter tabs
|   |       +-- <DiffToggle />
|   |       +-- <ChangesSummary />      # NEW
|   |       +-- <DownloadButton />
|   |       +-- <ApplyButton />         # NEW
|   +-- <CoverLettersPage />            # Page 8 — NEW
|   |   +-- <CoverLetterPreview /> (xN)
|   |       +-- <ToneSelector />        # NEW
|   |       +-- <LengthSelector />      # NEW
|   |       +-- <RegenerateButton />    # NEW
|   |       +-- <CopyButton />
|   |       +-- <ApplyButton />
|   +-- <ApplyHubPage />                # Page 9 (was ApplicationSummaryPage)
|       +-- <ApplicationTable />
|       +-- <ApplicationChecklist />    # NEW
|       +-- <DownloadAllButton />       # resumes ZIP
|       +-- <DownloadAllLettersButton /> # NEW — cover letters ZIP
+-- <LoadingOverlay />                  # Pipeline processing indicator
+-- <Toaster />                         # Toast notifications
```

---

## 6. API Endpoints (Express.js)

| Method | Endpoint | Description | Request | Response |
|---|---|---|---|---|
| `POST` | `/api/pipeline/start` | Upload resume, start stages 1-3 | `multipart/form-data` + `{ searchScope, dreamRole }` | `{ sessionId, status }` |
| `GET` | `/api/pipeline/status/:sessionId` | SSE stream of pipeline progress | — | SSE events: `{ stage, status, data }` |
| `GET` | `/api/pipeline/result/:sessionId` | Get current pipeline state | — | Full pipeline state JSON |
| `POST` | `/api/feedback/:sessionId` | Submit user selections + preferences | `{ selectedJobs: [], preferences: {} }` | `{ status }` |
| `POST` | `/api/apply/:sessionId` | Trigger stages 8-9 (resumes + cover letters) | — | `{ status }` |
| `POST` | `/api/cover-letter/:sessionId/:jobIndex/regenerate` | Regenerate one cover letter | `{ tone, length }` | `{ coverLetter: string }` |
| `GET` | `/api/download/:sessionId/resume/:jobIndex` | Download a single resume | — | `.txt` file |
| `GET` | `/api/download/:sessionId/cover-letter/:jobIndex` | Download a single cover letter | — | `.txt` file |
| `GET` | `/api/download/:sessionId/resumes/all` | Download all resumes as ZIP | — | `.zip` file |
| `GET` | `/api/download/:sessionId/cover-letters/all` | Download all cover letters as ZIP | — | `.zip` file |
| `GET` | `/api/apply-link/:sessionId/:jobIndex` | Get original job posting URL | — | `{ url, portal }` |

### SSE Event Format

```json
{
  "event": "stage_update",
  "data": {
    "stage": 3,
    "stageName": "recommend_roles",
    "status": "running | completed | error",
    "progress": 33,
    "message": "AI is ranking job matches across 8 portals...",
    "portalsSearched": ["LinkedIn", "Indeed", "Remotive"],
    "result": {}
  }
}
```

---

## 7. State Management

```typescript
interface PipelineState {
  sessionId: string | null;
  currentStage: number;           // 0-10
  status: 'idle' | 'running' | 'paused' | 'completed' | 'error';

  // Stage outputs
  resumeProfile: ResumeProfile | null;
  jobResults: JobRecommendation[];
  recommendations: JobRecommendation[];
  selectedJobs: number[];
  preferences: UserPreferences;
  refinedJobs: JobRecommendation[];
  reviews: EmployeeReview[];
  bestJobs: JobRecommendation[];
  enhancedResumes: EnhancedResume[];
  coverLetters: CoverLetter[];          // NEW
  applications: ApplicationRecord[];
  applicationChecklist: boolean[];      // NEW — tracks which jobs user has applied to

  errors: string[];
}

interface UserPreferences {
  searchScope: 'global' | 'regional' | 'remote' | 'relocation';
  selectedRegions: string[];           // NEW — e.g. ['North America', 'Europe']
  preferredIndustries: string;
  preferredLocations: string;
  remotePreference: string;
  salaryExpectation: string;
  companyPreferences: string;          // NEW
  additionalNotes: string;
}

interface CoverLetter {                // NEW
  jobRole: JobRecommendation;
  text: string;
  tone: 'professional' | 'conversational' | 'concise';
  length: 'short' | 'standard' | 'long';
}

type Action =
  | { type: 'SET_SESSION'; sessionId: string }
  | { type: 'SET_STAGE'; stage: number; status: string }
  | { type: 'SET_RESUME_PROFILE'; profile: ResumeProfile }
  | { type: 'SET_JOB_RESULTS'; jobs: JobRecommendation[] }
  | { type: 'SET_RECOMMENDATIONS'; recs: JobRecommendation[] }
  | { type: 'SET_SELECTED_JOBS'; indices: number[] }
  | { type: 'SET_PREFERENCES'; prefs: UserPreferences }
  | { type: 'SET_REFINED_JOBS'; jobs: JobRecommendation[] }
  | { type: 'SET_REVIEWS'; reviews: EmployeeReview[] }
  | { type: 'SET_BEST_JOBS'; jobs: JobRecommendation[] }
  | { type: 'SET_ENHANCED_RESUMES'; resumes: EnhancedResume[] }
  | { type: 'SET_COVER_LETTERS'; letters: CoverLetter[] }      // NEW
  | { type: 'UPDATE_COVER_LETTER'; index: number; letter: CoverLetter } // NEW
  | { type: 'SET_APPLICATIONS'; apps: ApplicationRecord[] }
  | { type: 'TOGGLE_CHECKLIST'; index: number }                // NEW
  | { type: 'ADD_ERROR'; error: string }
  | { type: 'RESET' };
```

---

## 8. UX Design Principles

| Principle | Implementation |
|---|---|
| **Progressive disclosure** | Show only current stage; completed stages reviewable but collapsed |
| **Never lose data** | Pipeline state persists to `sessionStorage`; page refresh resumes from last stage |
| **Clear feedback loops** | Every button click shows immediate visual response (loading spinners, toasts) |
| **Error recovery** | Errors shown inline with "Retry" buttons; pipeline can resume from failed stage |
| **Accessibility** | Semantic HTML, ARIA labels, keyboard navigation, colour contrast AA compliant |
| **Mobile-first** | Cards stack vertically on small screens; horizontal on desktop |
| **Always one click to apply** | Every job card, at every stage, shows a direct "Apply on [Portal]" link |
| **Global by default** | Search scope defaults to global; users opt in to restrictions, not expansions |
| **Dream + safe tracks** | Both aspirational and safe roles always visible; user chooses their ambition level |

---

## 9. Colour Palette & Visual Language

| Element | Colour | Hex |
|---|---|---|
| Primary (buttons, active steps) | Indigo | `#6366F1` |
| Success (completed steps, safe match) | Emerald | `#10B981` |
| Dream Role badge | Amber | `#F59E0B` |
| Stretch Role badge | Violet | `#8B5CF6` |
| Warning (medium scores) | Amber | `#F59E0B` |
| Error (failures) | Rose | `#F43F5E` |
| Background | Slate 50 | `#F8FAFC` |
| Card background | White | `#FFFFFF` |
| Text primary | Slate 900 | `#0F172A` |
| Text secondary | Slate 500 | `#64748B` |
| Score bar high | Emerald 500 | `#10B981` |
| Score bar medium | Amber 400 | `#FBBF24` |
| Score bar low | Rose 400 | `#FB7185` |
| Skill matched chip | Emerald 100 / Emerald 700 | — |
| Skill missing chip | Rose 100 / Rose 700 | — |

---

## 10. File Structure

```
frontend/
+-- server/                          # Express.js API
|   +-- index.js                     # Express app + SSE + routes
|   +-- pipeline-bridge.js           # Spawns Python pipeline, manages sessions
|   +-- routes/
|   |   +-- pipeline.js              # /api/pipeline/* routes
|   |   +-- feedback.js              # /api/feedback/* routes
|   |   +-- download.js              # /api/download/* routes
|   |   +-- cover-letter.js          # /api/cover-letter/* routes (NEW)
|   |   +-- apply-link.js            # /api/apply-link/* routes (NEW)
|   +-- package.json
+-- client/                          # React + Vite SPA
|   +-- index.html
|   +-- vite.config.js
|   +-- tailwind.config.js
|   +-- postcss.config.js
|   +-- package.json
|   +-- src/
|   |   +-- main.jsx
|   |   +-- App.jsx
|   |   +-- index.css
|   |   +-- context/
|   |   |   +-- PipelineContext.jsx
|   |   +-- hooks/
|   |   |   +-- usePipeline.js
|   |   |   +-- useSSE.js
|   |   +-- pages/
|   |   |   +-- UploadPage.jsx
|   |   |   +-- ResumeReviewPage.jsx
|   |   |   +-- JobSearchPage.jsx
|   |   |   +-- RecommendationsPage.jsx
|   |   |   +-- FeedbackPage.jsx
|   |   |   +-- BestJobsPage.jsx
|   |   |   +-- EnhancedResumesPage.jsx
|   |   |   +-- CoverLettersPage.jsx       # NEW
|   |   |   +-- ApplyHubPage.jsx           # renamed + expanded
|   |   +-- components/
|   |   |   +-- Header.jsx
|   |   |   +-- ProgressStepper.jsx
|   |   |   +-- DropZone.jsx
|   |   |   +-- SearchScopeSelector.jsx    # NEW
|   |   |   +-- ProfileCard.jsx
|   |   |   +-- SkillBadges.jsx
|   |   |   +-- GapHighlights.jsx          # NEW
|   |   |   +-- ReviewPanel.jsx
|   |   |   +-- PortalBadgeBar.jsx         # NEW
|   |   |   +-- JobCard.jsx
|   |   |   +-- RoleTypeBadge.jsx          # NEW
|   |   |   +-- SkillMatchChips.jsx        # NEW
|   |   |   +-- ApplyButton.jsx            # NEW — reusable direct-link button
|   |   |   +-- FilterBar.jsx
|   |   |   +-- RecommendationCard.jsx
|   |   |   +-- LearningPathModal.jsx      # NEW
|   |   |   +-- RegionCheckboxGroup.jsx    # NEW
|   |   |   +-- ScoreBar.jsx
|   |   |   +-- StarRating.jsx
|   |   |   +-- SalaryRange.jsx            # NEW
|   |   |   +-- ReviewSummary.jsx
|   |   |   +-- ResumePreview.jsx
|   |   |   +-- CoverLetterPreview.jsx     # NEW
|   |   |   +-- ToneSelector.jsx           # NEW
|   |   |   +-- ApplicationTable.jsx
|   |   |   +-- ApplicationChecklist.jsx   # NEW
|   |   |   +-- LoadingOverlay.jsx
|   |   |   +-- common/
|   |   |       +-- Button.jsx
|   |   |       +-- Card.jsx
|   |   |       +-- Badge.jsx
|   |   |       +-- Input.jsx
|   |   |       +-- RadioGroup.jsx
|   |   |       +-- TextArea.jsx
|   |   |       +-- TabBar.jsx             # NEW
|   |   +-- api/
|   |       +-- client.js
|   +-- public/
|       +-- favicon.svg
+-- README.md
```

---

## 11. Data Flow Summary

```
User uploads resume + sets search scope (global/regional/remote)
       |
       v
[POST /api/pipeline/start]  -->  Express spawns Python pipeline (stages 1-3)
  - Resume parsed                           |
  - Multi-portal job search fired           |  SSE stage_update events
  - AI ranking across all sources           |
       |  SSE <---------------------------<-+
       v
Frontend shows: Resume Profile -> Global Job Results -> AI Recommendations
  (jobs show Dream/Safe/Stretch badges + direct Apply links per portal)
       |
       v
User selects jobs + enters preferences (scope, regions, industry, etc.)
       |
       v
[POST /api/feedback/:sessionId]  -->  Python pipeline resumes (stages 4-7)
  - Refined multi-portal search                      |
  - Employee review aggregation                      |  SSE events
  - Combined scoring                                 |
       |  SSE <------------------------------------<--+
       v
Frontend shows: Refined Results + Employee Reviews + Salary Data
       |
       v
User clicks "Generate Tailored Resumes & Cover Letters"
       |
       v
[POST /api/apply/:sessionId]  -->  Python pipeline resumes (stages 8-9)
  - Enhanced resume per role                     |
  - Tailored cover letter per role               |  SSE events
  - Application records logged                   |
       |  SSE <----------------------------------<+
       v
Frontend shows:
  Page 7: Enhanced Resumes (with diff view + direct apply links)
  Page 8: Cover Letters (tone/length controls + regenerate)
  Page 9: Apply Hub (checklist + all downloads + direct apply links)
```

---

## 12. Key UX Enhancements over CLI + v1 Design

| CLI / v1 Design | Enhanced Web Experience |
|---|---|
| Single search source (Tavily) | 10+ portals searched globally in parallel |
| Only "safe" matches returned | Dream Role + Safe Match + Stretch Role tracks |
| No direct apply link visible | "Apply on [Portal]" button on every card at every stage |
| No cover letter | AI cover letter per role, with tone/length controls + regenerate |
| Type comma-separated numbers | Click checkboxes with visual cards |
| Text prompts for preferences | Form fields with placeholders, region checkboxes, radio buttons |
| Rich table in terminal | Sortable, filterable card grid with skill-match chips |
| Print to stdout | Real-time SSE progress stepper with animations |
| File saved to disk | Preview in-browser + download + copy |
| No way to go back | Navigate to any completed stage |
| Restart from scratch on error | Resume from failed stage with retry |
| No application tracking | Checklist per job — mark as applied |
| Only resume download | Resume ZIP + Cover Letter ZIP + individual downloads |

---

## 13. Future Enhancements (Out of Scope for v1)

- [ ] User authentication + saved sessions across devices
- [ ] Real automated job application submission via Playwright (form-filling)
- [ ] ATS-optimised PDF export for enhanced resumes
- [ ] Dashboard with application tracking over time (status: applied / interview / offer)
- [ ] Email/Slack notifications for new matching jobs
- [ ] Dark mode toggle
- [ ] Collaborative review (share session with career coach)
- [ ] Resume template selection (multiple visual formats)
- [ ] Interview prep per role — AI mock Q&A based on JD
- [ ] Salary negotiation guide per offer
- [ ] LinkedIn Easy Apply integration (OAuth)
