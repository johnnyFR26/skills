# UX Validation Checklist

Use this checklist before finalizing any design. Every item maps to at least one Law of UX.

---

## 1. Information Architecture

- [ ] Navigation has **7 or fewer** top-level items *(Miller's Law)*
- [ ] Content is grouped into logical chunks with clear visual separators *(Chunking, Law of Common Region)*
- [ ] Related elements are visually adjacent *(Law of Proximity)*
- [ ] Similar-function elements share the same visual treatment *(Law of Similarity)*
- [ ] Connected elements are visually linked *(Law of Uniform Connectedness)*
- [ ] Primary action is placed first or last in sequences *(Serial Position Effect)*
- [ ] Most important 20% of features are prominently accessible *(Pareto Principle)*

---

## 2. Cognitive Load

- [ ] No screen requires the user to remember information from a previous screen *(Working Memory)*
- [ ] No more than 5–7 options presented at any decision point *(Hick's Law, Choice Overload)*
- [ ] Complex tasks are broken into clearly labeled steps *(Chunking)*
- [ ] Visual noise is minimal — every element has a purpose *(Selective Attention, Occam's Razor)*
- [ ] Complexity is absorbed by the system, not pushed to the user *(Tesler's Law)*
- [ ] Interface matches users' existing mental models and real-world expectations *(Mental Model, Jakob's Law)*

---

## 3. Visual Hierarchy

- [ ] There is ONE dominant CTA per screen *(Von Restorff Effect)*
- [ ] Layouts use simple, clean shapes and alignment *(Law of Prägnanz)*
- [ ] Typography hierarchy is clear: headings, body, labels are visually distinct *(Aesthetic-Usability Effect)*
- [ ] Color contrast ratio is minimum 4.5:1 for text (WCAG 2.1 AA) *(Accessibility)*
- [ ] Color is never the ONLY indicator of state (add icon/text for colorblind users) *(Accessibility)*
- [ ] Design is visually polished and consistent *(Aesthetic-Usability Effect)*

---

## 3b. M3 Styles Compliance

### Color
- [ ] Colors use **semantic roles** (`primary`, `onPrimary`, `primaryContainer`) — no hardcoded hex *(M3 Color)*
- [ ] Both **light and dark themes** are supported with correct surface mappings *(M3 Color)*
- [ ] Container/onContainer pairs maintain proper **contrast ratios** *(M3 Color)*
- [ ] **Error** color is used for error states, **not primary red** *(M3 Color)*
- [ ] Dynamic color is considered for Android consumer apps *(M3 Color)*

### Typography
- [ ] Content uses **M3 type roles** (Display, Headline, Title, Body, Label) — not arbitrary sizes *(M3 Typography)*
- [ ] Type roles match **semantic purpose**: Display/Headline for emphasis, Body for reading, Label for actions *(M3 Typography)*
- [ ] Body text is **≥14sp** with line height **1.4–1.6×** *(M3 Typography)*
- [ ] Emphasized variants are used sparingly for **differentiation within the same role** *(M3 Typography)*

### Elevation
- [ ] Elevation uses **tonal surface overlays**, not drop shadows as primary cue *(M3 Elevation)*
- [ ] Resting components use levels **0–3**, interactive states use levels **4–5** *(M3 Elevation)*
- [ ] Disabled elements have **no elevation** (Level 0) *(M3 Elevation)*

### Shape
- [ ] Corner radii use the **M3 shape scale** (None, Extra Small, Small, Medium, Large, Extra Large, Full) *(M3 Shape)*
- [ ] Shape language is **consistent** — same hierarchy level uses same shape style *(M3 Shape)*
- [ ] Shape morph is considered for **interaction states and loading feedback** *(M3 Shape)*

### Motion
- [ ] Animations use **spring physics** (Expressive or Standard scheme) *(M3 Motion)*
- [ ] Correct **transition pattern** is used: Container Transform (parent-child), Shared Axis (navigation), Fade Through (unrelated) *(M3 Motion)*
- [ ] UI animations are **under 500ms** *(M3 Motion)*
- [ ] `prefers-reduced-motion` is respected *(M3 Motion + Accessibility)*

### Icons
- [ ] Icons use **Material Symbols** with correct style (outlined, rounded, or sharp) *(M3 Icons)*
- [ ] Icon **weight matches companion text weight** *(M3 Icons)*
- [ ] Active/selected states use **Fill=1**, default states use **Fill=0** *(M3 Icons)*
- [ ] Icon-only interactive elements have **accessible labels** (`aria-label`) *(M3 Icons + Accessibility)*

---

## 4. Interaction Design

- [ ] All touch targets are minimum 44×44px *(Fitts's Law)*
- [ ] Primary actions are placed near the user's current focus area *(Fitts's Law)*
- [ ] All interactions produce visible feedback in < 400ms *(Doherty Threshold)*
- [ ] Long operations show skeleton screens, progress bars, or optimistic UI *(Doherty Threshold)*
- [ ] Destructive actions are separated from safe actions *(Fitts's Law + Safety)*
- [ ] Input fields accept flexible formats (phone, dates, email) *(Postel's Law)*
- [ ] Data is output in clean, consistent format *(Postel's Law)*

---

## 5. User Flow

- [ ] Progress is visible on multi-step flows (step indicator, progress bar) *(Goal-Gradient Effect, Zeigarnik Effect)*
- [ ] Users can see how close they are to completing the main task *(Goal-Gradient Effect)*
- [ ] The flow doesn't require completing onboarding to start using the product *(Paradox of the Active User)*
- [ ] Error recovery is clear and recoverable *(Forgiveness Principle)*
- [ ] Success state is celebrated with a positive moment *(Peak-End Rule)*
- [ ] The most emotionally impactful moment in the flow is designed intentionally *(Peak-End Rule)*

---

## 6. Familiarity & Conventions

- [ ] Platform conventions are followed (back gesture, navigation placement) *(Jakob's Law)*
- [ ] Interactive elements look interactive (affordance) *(Mental Model)*
- [ ] Icons use universally recognized symbols *(Mental Model, Jakob's Law)*
- [ ] If breaking a convention, transition support is provided *(Jakob's Law)*

---

## 7. Performance & Flow State

- [ ] UI responds in < 100ms for direct manipulation *(Doherty Threshold, Flow)*
- [ ] No unexpected interruptions (modals, pop-ups) during focused tasks *(Flow)*
- [ ] Auto-save is implemented where relevant *(Flow)*
- [ ] Task difficulty is appropriate for the user's skill level *(Flow)*

---

## 8. Motivation & Engagement

- [ ] Multi-step forms/tasks show a progress indicator *(Zeigarnik Effect)*
- [ ] Empty states are designed — not just blank *(Paradox of the Active User)*
- [ ] Success states are intentional and positive *(Peak-End Rule)*
- [ ] The UI teaches itself through use, not manual *(Paradox of the Active User)*

---

## 9. Accessibility (WCAG 2.1 AA — Mandatory)

- [ ] All interactive elements are keyboard-navigable (Tab, Enter, Space, Arrow keys)
- [ ] Focus indicators are visible — never `outline: none` without a replacement
- [ ] All images have meaningful `alt` text
- [ ] Form inputs have associated `<label>` elements
- [ ] Error messages are linked to inputs via `aria-describedby`
- [ ] Dynamic content changes are announced to screen readers (`aria-live`)
- [ ] Videos have captions/subtitles
- [ ] `prefers-reduced-motion` is respected in animations
- [ ] Color contrast ratio: 4.5:1 for normal text, 3:1 for large text/UI components

---

## 10. Responsive & Cross-Platform

- [ ] Design starts from mobile (smallest viewport) *(Mobile-first)*
- [ ] Touch targets remain 44px+ on all viewports *(Fitts's Law)*
- [ ] Thumb reach zones are respected on mobile *(Fitts's Law)*
- [ ] Layout adapts gracefully across breakpoints (320px → 1440px+)
- [ ] Dark mode is supported (or explicitly excluded with reason)

---

## Quick Severity Matrix

| Violation | Severity |
|-----------|----------|
| No feedback on action | Critical |
| Touch target < 44px | Critical |
| Contrast ratio < 4.5:1 | Critical |
| Hardcoded hex instead of M3 color roles | High |
| No dark theme support | High |
| Drop shadows instead of tonal overlays (M3) | High |
| More than 7 nav items | High |
| Requiring memory across screens | High |
| Single screen with > 7 choices | High |
| No progress on multi-step flows | High |
| Typography by pixel size, not type role | High |
| Arbitrary border-radius, not shape scale | Medium |
| No spring physics for animations | Medium |
| Wrong transition pattern (e.g., Fade Through for parent-child) | Medium |
| Icon weight mismatched with text | Medium |
| No success/empty state | Medium |
| Unconventional patterns | Medium |
| No motion reduction support | Medium |
| Missing alt text | Critical (accessibility) |
| Form without labels | Critical (accessibility) |
| Icon-only button without aria-label | Critical (accessibility) |

---

## Sign-off Criteria

A design is ready for development when:
1. All **Critical** items are resolved
2. All **High** items are resolved or have a documented exception
3. Laws of UX violations have been reviewed and intentional exceptions are justified
4. Accessibility audit has been run (aXe, Lighthouse, or manual screen reader test)
