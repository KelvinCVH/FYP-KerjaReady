# KerjaReady Design System

Source of truth for all frontend work. Read this file before building or changing any UI.
Rationale and sources: `docs/design-system-justification.md`.

## 1. Scope and Workflow

- Applies to every page in `frontend/`.
- Landing page (`/`): also apply the Taste skill (`design-taste-frontend`) with the dials in Section 11.
- App pages (auth, candidate, recruiter): follow this file only. The Taste skill does not cover dashboards, tables or multi-step forms.
- When an approved mockup exists in `docs/mockups/<story-key>-<page>.png`, it is the visual source of truth. Use the `image-to-code` skill and skip its image-generation step.
- After each UI story: run the `web-design-guidelines` audit, then capture Playwright screenshots of every changed route at 1280px and 390px wide.

## 2. Design Read

KerjaReady is a career readiness platform for Malaysian technology students and recruiters. Users share personal resume data and may feel uncertain during their job search. The interface must feel calm, trustworthy and clear. Clarity always beats decoration.

## 3. Principles

1. Calm over loud: one accent colour, generous spacing, restrained motion.
2. Honest feedback: show evidence, never judge. A skill not shown in a resume is "not evidenced in the resume", never "missing".
3. Accessible by default: WCAG 2.2 AA is the minimum.
4. One system everywhere: one colour system, one radius system, one icon set.

## 4. Theme

- Light mode only. Do not add `dark:` variants or a `.dark` block.
- `color-scheme: light` is set on `<html>`. `<meta name="theme-color">` is `#fafafa`.
- All colours are CSS variables in `src/index.css`, so a dark theme can be added later without refactoring.

## 5. Colour

### 5.1 Tokens (defined in `src/index.css`)

| Token | Value | Use |
|---|---|---|
| `--background` | zinc-50 `#fafafa` | Page background |
| `--foreground` | zinc-900 `#18181b` | Headings and body text |
| `--card`, `--popover` | white `#ffffff` | Cards, dialogs, menus, input fields |
| `--secondary`, `--muted` | zinc-100 `#f4f4f5` | Subtle backgrounds, skeletons |
| `--muted-foreground` | zinc-600 `#52525b` | Secondary text. Never use a lighter grey for text. |
| `--accent` | zinc-100 `#f4f4f5` | Hover background for ghost and secondary buttons and menu items (neutral, not the brand colour) |
| `--border` | zinc-200 `#e4e4e7` | Dividers and card borders |
| `--input` | zinc-500 `#71717a` | Form control and secondary button borders (meets 3:1 non-text contrast) |
| `--primary` | emerald-700 `#047857` | Primary buttons, links, active navigation |
| `--primary-hover` | emerald-800 `#065f46` | Primary hover |
| `--primary-foreground` | white `#ffffff` | Text on primary |
| `--primary-subtle` | emerald-50 `#ecfdf5` | Decorative tinted surfaces (landing panels, icon tiles). Never for status. |
| `--ring` | emerald-600 `#059669` | Focus ring |
| `--destructive` | red-700 `#b91c1c` | Destructive actions and system errors only |

Use token classes (`bg-primary`, `text-muted-foreground`, `border-input`) wherever a token exists. Use raw palette classes only for the status colours in Section 5.2.

### 5.2 Status Colours

Every status shows a text label and an icon. Colour is never the only signal.

| Meaning | Text | Background | Lucide icon |
|---|---|---|---|
| Evidenced in the resume, Accepted | emerald-800 | emerald-50 | `CircleCheck` |
| Not evidenced in the resume | zinc-700 | zinc-100 | `CircleDashed` |
| Submitted | zinc-700 | zinc-100 | `Clock` |
| Rejected | zinc-800 | zinc-200 | `CircleX` |
| Warning | amber-800 | amber-50 | `TriangleAlert` |
| Error (system or form) | red-700 | red-50 | `CircleAlert` |
| In progress (an assessment still running) | zinc-700 | white with a `--border` outline (badge variant `progress`) | `LoaderCircle`, spinning unless reduced motion is on |

### 5.3 Rules

- Emerald is the only accent colour. Do not introduce another hue for decoration. Exception: skill logos keep their own colours (Section 10).
- Red is reserved for destructive actions and system or form errors. Never use red for scores, assessment results, skill gaps or rejection.
- No gradient text, no glows, no purple or blue accents.
- Text contrast is at least 4.5:1 (3:1 for text 24px and above, or 18.66px bold and above).
- Component boundaries and focus rings are at least 3:1 against their background.
- Check every new colour pair with a contrast checker before using it.

## 6. Typography

- Fonts: Geist Sans (`font-sans`) for all UI and content. Geist Mono (`font-mono`) for scores. Both are self-hosted through `@fontsource-variable/geist` and `@fontsource-variable/geist-mono`. Never load fonts from Google Fonts.
- Numbers that are compared (counts, scores, table columns) use `tabular-nums`.
- Weights: 400 for body text, 500 for labels and buttons, 600 for headings. Do not use weights below 400.
- Body text width is at most `max-w-[65ch]`.
- Headings use `text-balance`. One `<h1>` per page. Never skip heading levels.

| Role | Classes |
|---|---|
| Landing hero headline | `text-4xl md:text-5xl lg:text-6xl font-semibold tracking-tight` |
| Page title (h1) | `text-2xl font-semibold` |
| Section heading (h2) | `text-xl font-semibold` |
| Card title (h3) | `text-base font-semibold` |
| Body | `text-base leading-relaxed` |
| Secondary and helper text | `text-sm text-muted-foreground` |
| Score display | `text-4xl font-mono font-semibold tabular-nums` |

## 7. Spacing and Layout

- Use the Tailwind spacing scale only. No arbitrary pixel values unless documented here.
- App shell: sidebar `w-56`, content padding `p-6 md:p-8`, content width `max-w-5xl`.
- Exception, Resume page: from `2xl`, a 20rem Past Assessments panel sits beside the main column, using `grid-cols-[minmax(0,64rem)_20rem] gap-6`. The main column is still at most `max-w-5xl` (64rem), and narrows slightly between 1536px and about 1660px so the panel fits. Below `2xl`, the page is one `max-w-5xl` column with the panel below the main content. At every width the panel starts open, and its heading is a button that collapses it.
- Landing page: container `max-w-7xl mx-auto px-4 md:px-8`, sections `py-20 md:py-28`.
- Use CSS Grid or flex-wrap for multi-column layouts. Every multi-column layout declares its single-column layout below 768px.
- Use `min-h-[100dvh]`, never `h-screen`.
- Group content with spacing and dividers before using cards. Never put cards inside cards.
- Exception: on the landing page, a component preview (Section 11) may sit inside a panel, because it illustrates real UI rather than grouping content.

## 8. Shape and Elevation

- Radius rule: controls (button, input, select, badge, tab) are 8px. Containers (card, dialog, popover, panel) are 12px. Avatars are circles. No other radii.
- In Tailwind: `rounded-md` and `rounded-lg` are both 8px (controls), and `rounded-xl` is 12px (containers). Do not use `rounded-sm`, `rounded-2xl` or `rounded-full` except for avatars.
- Exceptions: checkboxes use a 4px radius and radio buttons are fully round, so each control keeps its recognisable shape.
- Borders define surfaces. Shadows appear only on overlays (dropdown, popover, dialog), tinted with zinc, never pure black.

## 9. Components

Base: shadcn/ui components in `src/components/ui/` (Nova preset, Radix). Add new ones with `npx shadcn@latest add <name>` from `frontend/`. Never ship a component in its default shadcn styling. Restyle it to this file.

### 9.1 Buttons

| DESIGN.md name | shadcn `variant` | Style |
|---|---|---|
| Primary | `default` | Emerald background, white text, emerald-800 hover |
| Secondary | `outline` or `secondary` | White background, `--input` border, zinc-100 hover |
| Ghost | `ghost` | No border, zinc-100 hover |
| Destructive | `destructive` | Red background, white text. Only inside confirmation dialogs. |

- Sizes: `default` 44px tall (minimum touch target), `lg` 48px for landing page calls to action, `sm` 36px only inside dense tables.
- Use `asChild` with react-router `Link` when a button navigates.
- One primary button per view or section.
- Labels are Title Case, specific, at most 3 words, and fit on one line on desktop. Examples: "Upload Resume", "Generate Roadmap", "Accept Candidate".
- States: hover; `focus-visible` ring (2px `--ring`, 2px offset); active `scale-[0.98]`; disabled (50% opacity, not clickable); loading (spinner plus "Saving…", same button width).

### 9.2 Forms

- Label above the field. Helper text below. Error text below in red-700 with an icon.
- Use the correct `type`, `name` and `autocomplete` values (`email`, `name`, `organization`, `new-password`, `current-password`).
- Never block paste. Turn off spellcheck on email fields and verification codes.
- The submit button stays enabled until the request starts. On a failed submit, move focus to the first invalid field.
- Placeholders show an example and end with "…". Never use a placeholder as a label.

### 9.3 Feedback

- Status badges: Section 5.2, with `rounded-lg text-sm font-medium`.
- Empty states: one sentence explaining what will appear, plus one primary action. Example for the first Skill Gap visit: "Upload your resume and choose a target role to see your skill gap analysis." with an "Upload Resume" button.
- Loading: skeletons that match the final layout. Loading text ends with "…" ("Analysing resume…").
- Announce async results with `aria-live="polite"`.

### 9.4 Destructive Actions

- Rejecting a candidate, deleting a resume and closing a listing all open a confirmation dialog first.
- Rejecting a candidate requires a reason.

### 9.5 Lists

- Lists with more than 50 items are paginated or virtualised.

## 10. Icons

- `lucide-react` only. Stroke width 2. Size 16px inline, 20px in buttons and navigation.
- Icon-only buttons need `aria-label`. Decorative icons get `aria-hidden="true"`.
- Never hand-draw SVG icons.
- Exception, skill logos: a skill with an official logo shows it, in its own colours, in a 44px white tile beside the skill name (`SkillTile`). The logos are SVG files in `public/skill-logos/`, mapped in `src/lib/skillLogos.ts`, with sources and licences in `public/skill-logos/SOURCES.md`. They are decorative, because the name is always shown. Skills without a readable official logo show their letters on an emerald-50 tile.

## 11. Landing Page Rules (Taste Skill)

- Dials: DESIGN_VARIANCE 5, MOTION_INTENSITY 4, VISUAL_DENSITY 3.
- Hero: at most 4 text elements (optional eyebrow, headline of at most 2 lines, subtext of at most 20 words, calls to action). Top padding at most `pt-24`.
- One label per intent across the whole page:

| Intent | Label | Link |
|---|---|---|
| Student registration | Assess My Resume | `/register?role=candidate` |
| Recruiter registration | Find Candidates | `/register?role=recruiter` |
| General registration (header) | Create Account | `/register` |
| Sign in (header, footer) | Sign In | `/sign-in` |

- Footer links: Privacy Notice and Sign In only.
- No three equal feature cards. No "Step 1, Step 2, Step 3" labels. Name steps with verbs, such as "Upload", "Assess" and "Improve".
- Use real images or real component previews. Never build fake screenshots from divs. Example data is labelled "Example".
- At most one eyebrow label per three sections. No version labels, scroll cues or decorative dots.

## 12. Motion

- Landing page: `motion/react` for a one-time fade-up on entry and for hover feedback. App pages: CSS transitions only.
- Duration: 150 to 200ms for UI feedback, up to 600ms for landing entry animations.
- Animate `transform` and `opacity` only. Never use `transition: all`.
- Respect `prefers-reduced-motion`: disable all non-essential motion. `index.css` already shortens transitions globally, and Motion components must use `useReducedMotion()`.

## 13. Content and Copy

- British English spelling: "analyse", "colour", "organisation".
- Title Case for headings, navigation and buttons. Sentence case for body text, helper text, errors and toasts.
- Second person, active voice, short sentences. Use numerals for counts ("3 applications").
- Error messages say what happened and how to fix it. Example: "This email address is not valid. Check it and try again."
- Never use em dashes. Use a full stop, comma or colon instead.
- Do not use: elevate, seamless, unleash, revolutionise, next-gen, transformative.
- Format dates and numbers with `Intl` using the `en-MY` locale.
- Scores and results are supporting signals, not verdicts on a person's competence. Never label a result "pass", "fail" or "ready".

### Enforced Terminology

| Use | Never use |
|---|---|
| Create Account | Sign Up, Register, Get Started |
| Sign In | Log In, Login |
| career readiness | employability |
| skill gap analysis | skills gap, missing skills |
| not evidenced in the resume | missing, lacking, weak |
| match score | fit score, ranking |
| role-aligned resume assessment, candidate insights | readiness score |

## 14. Accessibility Checklist

- Text contrast 4.5:1 (large text 3:1). Component boundaries and focus rings 3:1.
- Every interactive element works with a keyboard and shows a visible focus ring.
- Semantic HTML first: `<button>` for actions, `<a>` or `<Link>` for navigation.
- One `<h1>` per page, headings in order, and a skip link to the main content.
- Every image has `alt` text. Decorative images use `alt=""`.
- Colour is never the only signal.
- Zoom is never disabled.

## 15. Definition of Done for UI Work

- The UI follows this file and matches the approved mockup, if one exists.
- `npm run build` passes with no errors.
- The `web-design-guidelines` audit has no unresolved findings.
- Playwright: every changed route loads with no console errors, with screenshots saved at 1280px and 390px wide in `docs/screenshots/<story-key>/`.