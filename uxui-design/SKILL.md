---
name: uxui-design
description: 'UI/UX design skill following Laws of UX (lawsofux.com), design systems from Apple, Google Material Design 3 (M3 Styles: Color, Typography, Elevation, Shape, Motion, Icons), Microsoft Fluent 2, Meta Design. Use when designing interfaces, reviewing UX, creating components, evaluating usability, defining flows, ensuring accessibility, or applying M3 color roles, type scale, elevation levels, shape scale, motion physics, or Material Symbols.'
argument-hint: 'What are you designing or reviewing? (e.g., checkout flow, onboarding, dashboard, component)'
---

# UI/UX Design Skill

World-class UI/UX design guided by the complete **Laws of UX**, the full **Material Design 3 Styles system** (Color, Typography, Elevation, Shape, Motion, Icons), and patterns from the best design teams on the planet (Apple HIG, Google M3, Microsoft Fluent 2, Meta Design).

> **MANDATORY**: Every design decision MUST be justified by at least one Law of UX, an M3 Style guideline, or a recognized design principle. Never design by intuition alone.

---

## When to Use

- Designing new screens, flows, or components
- Reviewing existing UI for usability problems
- Creating or auditing a design system
- Defining user flows, information architecture, or navigation patterns
- Evaluating accessibility and inclusive design
- Choosing between layout, interaction, or visual alternatives

---

## Workflow

### Step 1 — Understand Context
Before designing, always establish:
1. **Who is the user?** (persona, mental model, prior experience)
2. **What is the primary task?** (the one action that defines success)
3. **What is the environment?** (mobile, desktop, touch, screen reader)
4. **What are existing patterns the user already knows?** → Jakob's Law

### Step 2 — Define Information Architecture
- Map all content and actions into a hierarchy
- Apply **Miller's Law**: group content into chunks of max 7±2 items
- Apply **Law of Proximity** and **Law of Common Region**: visually group related elements
- Apply **Hick's Law**: reduce choices at every decision point
- Apply **Pareto Principle**: identify the 20% of features that cover 80% of use cases — prioritize those

### Step 3 — Design the Flow
- Sketch the critical path (the shortest path to task completion)
- Apply **Goal-Gradient Effect**: show progress indicators to motivate task completion
- Apply **Zeigarnik Effect**: use progress bars/steps for multi-step flows
- Apply **Peak-End Rule**: design the best possible moments at peak interaction and at the end (success state)
- Apply **Paradox of the Active User**: assume users will skip onboarding; design for immediate discoverability

### Step 4 — Design the Interface
Follow the layout and visual rules below (see [Laws of UX Reference](./references/laws-of-ux.md)):

**Hierarchy & Layout**
- Apply **Law of Prägnanz**: use simple, clean shapes and layouts
- Apply **Law of Similarity**: use consistent visual language for similar actions
- Apply **Law of Uniform Connectedness**: visually connect related elements (borders, lines, shared containers)
- Apply **Serial Position Effect**: place primary CTA first or last in lists/navigation

**Typography & Color**
- Apply **Aesthetic-Usability Effect**: beautiful interfaces are perceived as more usable — invest in polish
- Apply **Von Restorff Effect**: use color, size, or contrast to highlight the ONE most important action per screen
- Apply **Selective Attention**: remove visual noise; every element must earn its place
- Apply **M3 Color Roles**: use semantic color roles (`primary`, `onPrimary`, `primaryContainer`) — never hardcoded hex values
- Apply **M3 Type Scale**: use the 5 roles (Display, Headline, Title, Body, Label) with 3 sizes each — match role to semantic purpose
- Apply **M3 Dynamic Color**: support both light/dark themes and consider dynamic color adaptation from user preferences

**Interaction & Targets**
- Apply **Fitts's Law**: make interactive targets large enough (min 44×44px touch), close to the user's focus area
- Apply **Doherty Threshold**: all interactions must respond in <400ms; use optimistic UI or skeleton loaders
- Apply **Postel's Law**: accept flexible input (uppercase/lowercase, spaces in phone numbers); output clean and consistent data
- Apply **M3 Elevation**: use tonal surface overlays (levels 0–5) for depth hierarchy — prefer tonal tint over drop shadows
- Apply **M3 Shape**: use the corner radius scale (None → Extra Small → Small → Medium → Large → Extra Large → Full) to convey hierarchy and role
- Apply **M3 Motion Physics**: use spring-based animations (Expressive or Standard scheme) for natural, fluid interactions
- Apply **M3 Transition Patterns**: Container Transform for parent-child, Shared Axis for navigation, Fade Through for unrelated views
- Apply **M3 Material Symbols**: use the variable icon font (outlined/rounded/sharp) with Fill axis for active states

**Cognitive Load**
- Apply **Cognitive Load** principle: never show more information than needed at each step
- Apply **Chunking**: break complex forms or tasks into digestible sections
- Apply **Working Memory**: do not require users to remember information from one screen to use on another
- Apply **Mental Model**: match the interface to the user's existing mental model of the real world

**Complexity**
- Apply **Tesler's Law**: complexity cannot be eliminated, only transferred — absorb complexity in code, not the UI
- Apply **Occam's Razor**: choose the simplest solution that solves the problem
- Apply **Choice Overload**: when options exceed 5–7 items, consider progressive disclosure or smart defaults

### Step 5 — Apply M3 Styles System
Reference [M3 Styles Guide](./references/m3-styles.md) for every visual decision:

**Color**
- Use semantic **color roles** (`primary`, `secondary`, `tertiary`, `surface`, `error`) — never raw hex values
- Generate schemes from a single seed color using HCT color space and tonal palettes
- Support **light and dark themes** with proper surface tonal mappings
- Use **Container** variants for standout backgrounds, **On** variants for text/icons on those backgrounds
- Consider **dynamic color** (user wallpaper or in-app content) for Android consumer apps

**Typography**
- Map content to the **5 type roles**: Display (hero), Headline (sections), Title (cards), Body (reading), Label (actions/metadata)
- Each role has **3 sizes** (Large, Medium, Small) — pick the size that matches the content's emphasis
- Use **emphasized variants** sparingly for differentiation within the same role
- Body text minimum **14sp**, line height **1.4–1.6×**

**Elevation**
- Use **6 elevation levels** (0–5) with tonal surface overlays, not drop shadows
- Levels 0–3 for resting states, 4–5 for interactive states (hover, drag)
- Higher elevation = more prominent tint = closer to user

**Shape**
- Apply the **10-style corner radius scale** (None 0dp → Full circular) based on desired roundedness
- Use **shape morph** for interaction states, loading, and environmental feedback
- Harmonize shape language with typography — rounded = friendly, square = structured

**Motion**
- Default to **physics-based spring animations** (M3 Expressive or Standard scheme)
- Use **Container Transform** for parent-child transitions, **Shared Axis** for navigation, **Fade Through** for unrelated views
- Keep UI animation **under 500ms**, always respect `prefers-reduced-motion`

**Icons**
- Use **Material Symbols** variable font in outlined, rounded, or sharp style
- Default size **24dp**, match icon **weight to companion text weight**
- Use **Fill=1** for active/selected states, **Fill=0** for default states

### Step 6 — Validate Against Laws of UX Checklist
Run through [Full Checklist](./references/checklist.md) before finalizing any design.

### Step 7 — Review Against Industry Standards
Reference [Design Systems Standards](./references/design-systems.md) for platform-specific patterns.

---

## Core Design Principles (Non-Negotiable)

| Principle | Rule |
|-----------|------|
| **Clarity** | Every element's purpose must be immediately obvious |
| **Feedback** | Every action must produce a visible, timely response (<400ms) |
| **Consistency** | Use the same patterns for the same actions everywhere |
| **Efficiency** | Minimize steps to complete the primary task |
| **Forgiveness** | Allow undo, confirmation for destructive actions, clear error recovery |
| **Accessibility** | Minimum WCAG 2.1 AA — contrast ratio 4.5:1, keyboard nav, ARIA labels |

---

## Red Flags — Never Do These

- More than 7 top-level navigation items (Miller's Law violation)
- CTA buttons smaller than 44×44px on touch (Fitts's Law violation)
- Response time > 400ms without feedback (Doherty Threshold violation)
- Requiring users to remember info across screens (Working Memory violation)
- More than one primary CTA per screen (Von Restorff violation)
- Forms with no inline validation (Postel's Law violation)
- Redesigning familiar patterns without transition support (Jakob's Law violation)
- Hiding all features until onboarding is complete (Paradox of Active User)
- No progress indicator on multi-step flows (Zeigarnik + Goal-Gradient violation)
- Empty/success states without emotional design (Peak-End Rule violation)
- Hardcoded hex color values instead of M3 color roles (M3 Color violation)
- Using drop shadows as primary elevation cue instead of tonal overlays (M3 Elevation violation)
- Typography sized by pixel preference instead of type role mapping (M3 Typography violation)
- Animations without spring physics or exceeding 500ms (M3 Motion violation)
- Icons with mismatched weight to companion text (M3 Icons violation)
- No dark theme support (M3 Color violation)
- Shape inconsistency — mixing arbitrary border-radius values instead of the shape scale (M3 Shape violation)

---

## References

- [Laws of UX — Full Reference](./references/laws-of-ux.md)
- [Material Design 3 — Styles Reference](./references/m3-styles.md)
- [Design Systems Standards](./references/design-systems.md)
- [UX Validation Checklist](./references/checklist.md)
