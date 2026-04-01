# Dream Job Copilot — Implementation Guardrails

## The North Star
Every screen should feel like it was designed by a team that actually cares about job seekers.
Not a utility. Not a form. An experience that makes you feel capable and excited.

---

## 1. Visual Identity — Non-Negotiable Defaults

- **Font**: Inter (body) + Cal Sans or Bricolage Grotesque (headings) — load from Google Fonts
- **Radius**: `rounded-2xl` for cards, `rounded-full` for badges and buttons — no sharp corners anywhere
- **Shadows**: Layered soft shadows (`shadow-sm` default, `shadow-xl` on hover) — never harsh box shadows
- **Spacing**: Generous padding inside cards (`p-6` minimum). Breathable layouts win over dense ones
- **Background**: Never pure white. Use `slate-50` (#F8FAFC) as the page background with white cards on top
- **Colour discipline**: Stick to the palette in the design doc. Don't introduce ad-hoc colours

---

## 2. Motion & Animation — Make It Feel Alive

- Use **Framer Motion** for all page transitions: slide-up + fade-in, 300ms ease-out
- Cards animate in with a **staggered entrance** (each card 60ms after the previous)
- The progress stepper active step should have a **subtle pulse ring** animation (CSS keyframe)
- Loading states use **skeleton screens** (animated shimmer), never spinners alone
- Score bars and star ratings **animate to their value** on first render (spring animation)
- Button hover: slight scale up (`scale-105`) + shadow deepening — gives tactile feel
- SSE progress messages **typewriter-fade** in, don't just flash

---

## 3. Empty & Loading States — Never Leave the User Stranded

- Every list that could be empty needs a thoughtful empty state: illustration + friendly message + CTA
- Loading overlay must show **what the AI is doing right now** (e.g. "Searching LinkedIn... found 12 roles") — pull from SSE messages
- Long AI operations show a **live log strip** at the bottom of the overlay so users feel progress, not anxiety
- If a stage errors, show the error inline with a clear **"Retry this step"** button — never send users back to the start

---

## 4. Job Cards — The Heart of the App

- Each card must have a **clear visual hierarchy**: role title (large, bold) > company > location/mode > match score
- Match score uses a **coloured pill + mini bar**, not just a number
- Role type badge (Dream / Safe / Stretch) must be **the first thing the eye hits** — top-left of card
- Skill chips (matched = emerald, missing = rose) sit on one line with overflow hidden behind a "+N more" chip
- The **"Apply on [Portal]" button** is always visible without expanding — it's the primary CTA
- On hover, cards lift with shadow and the apply button subtly highlights — invites interaction
- Portal source icon (LinkedIn blue, Indeed purple, etc.) adds credibility and instant recognition

---

## 5. The "Wow" Moments — Build These Explicitly

These are specific moments that should feel delightful:

| Moment | Implementation |
|---|---|
| Resume upload accepted | Green animated checkmark + confetti burst (canvas-confetti, subtle) |
| First job results load | Counter animates up from 0 to N ("47 roles found") |
| AI recommendation card reveals | Cards flip in sequentially like a hand of playing cards |
| Cover letter generated | Typewriter effect as text appears in the preview pane |
| User marks a job as applied | Checkbox ticks with a satisfying spring + row fades to soft green |
| All jobs applied | Full confetti burst + "You're done! Go get that job." hero message |

---

## 6. Typography Rules

- Headings: `text-2xl font-bold tracking-tight text-slate-900`
- Sub-headings: `text-base font-semibold text-slate-700`
- Body: `text-sm text-slate-600 leading-relaxed`
- Labels / badges: `text-xs font-medium uppercase tracking-wide`
- AI-generated text blocks: wrap in a subtle `bg-indigo-50 border-l-4 border-indigo-400 rounded-r-xl p-4` callout — signals "AI said this"
- Numbers that matter (match %, ratings): `text-2xl font-bold` — make them pop

---

## 7. Responsiveness

- Design mobile-first. Every component must work at 375px width
- Cards: full-width on mobile, 2-col grid on `md:`, 3-col on `xl:`
- Progress stepper: collapses to show only current step label + "Step N of 10" on mobile
- The Apply button must always be full-width and thumb-friendly on mobile (`min-h-[48px]`)
- Side-by-side panels (Profile + Review) stack vertically on mobile

---

## 8. Micro-copy — Tone of Voice

- Warm, confident, human. Not corporate. Not robotic.
- Use "we" when the AI is doing something: "We're scanning 10 job portals for you..."
- Use "you" in results: "You matched 92% of the skills for this role"
- Avoid: "Error occurred", "Invalid input", "Please try again"
- Instead: "Something went sideways — let's retry", "This field needs a value to continue"
- Empty state headlines: "No stretch roles yet — try widening your search scope"
- CTA buttons: active verbs — "Find My Dream Job", "See What's Out There", "Make This Resume Mine"

---

## 9. Code Quality Guardrails

- Every component in `components/` takes explicit typed props — no implicit `any`
- No inline styles. Tailwind classes only. If a class string is repeated 3+ times, extract a `cn()` helper
- API calls live exclusively in `src/api/client.js` — no fetch/axios calls inside components
- All SSE subscription logic lives in `useSSE.js` hook — components just consume state
- `PipelineContext` is the single source of truth — no local state that duplicates pipeline data
- Use `React.memo` on `JobCard`, `RecommendationCard`, `CoverLetterPreview` — these re-render often

---

## 10. Performance Guardrails

- Job lists over 20 items: use **windowed rendering** (react-window) — no DOM bloat
- Resume preview pane: debounce re-renders on tone/length change (300ms)
- Images / portal icons: SVG sprites, not individual network requests
- SSE connection: reconnect automatically on drop with exponential backoff (max 3 retries)
- Bundle: keep initial JS chunk under 200KB gzipped — lazy-load each page component

---

## 11. Accessibility Minimums

- All interactive elements reachable and operable by keyboard (Tab + Enter/Space)
- Focus rings visible and styled (indigo, not browser default)
- All images and icons have `aria-label` or `aria-hidden` as appropriate
- Colour is never the only signal — always pair with icon or text (e.g. don't use green/red alone for match score)
- Form inputs always have associated `<label>` elements

---

## One-Line Summary for Your Copilot

> Build every component as if a job seeker is using it at 11pm after a long day — it should feel warm, fast, clear, and quietly exciting. Make the happy paths feel like magic and the error paths feel like support.
