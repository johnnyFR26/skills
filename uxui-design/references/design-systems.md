# Design Systems Standards

Patterns and conventions from the world's leading design teams.

---

## Apple Human Interface Guidelines (HIG)

**Core Principles:** Clarity, Deference, Depth

| Standard | Rule |
|----------|------|
| Touch targets | Minimum 44×44pt |
| Typography | SF Pro — use Dynamic Type for accessibility |
| Spacing | 8pt grid system |
| Safe Areas | Always respect safe area insets on iOS |
| Navigation | Tab Bar (bottom) for primary nav, Navigation Bar for hierarchy |
| Gestures | Swipe back is standard — never break it |
| Color | Always support Dark Mode |
| Icons | Use SF Symbols for consistency with the OS |
| Haptics | Use `UIFeedbackGenerator` for meaningful tactile feedback |

**Key Patterns:**
- Bottom sheets over full-screen modals for secondary actions
- Destructive actions in red, always with confirmation
- Inline validation — never wait for submit to show errors

---

## Google Material Design 3 (Material You)

**Core Principles:** Be Bold, Be Human, Be Personal

> Full M3 Styles reference: [M3 Styles Guide](./m3-styles.md)

| Standard | Rule |
|----------|------|
| Touch targets | Minimum 48×48dp |
| Typography | Type scale with 5 roles × 3 sizes: Display, Headline, Title, Body, Label |
| Spacing | 4dp grid base, 8dp standard increments |
| Elevation | 6 levels (0–5) using tonal surface overlays, not drop shadows |
| Color | HCT-based dynamic color system — semantic roles, not hex values |
| Shape | 10-style corner radius scale (None 0dp → Full circular) |
| Motion | Physics-based spring system (Expressive/Standard schemes) |
| Icons | Material Symbols variable font (outlined, rounded, sharp) |
| Navigation | Navigation bar (bottom) for 3–5 top destinations |
| FAB | One FAB per screen for the primary action |
| Design Tokens | Three-tier system: reference → system → component |

**M3 Color System:**
- 3 accent groups (Primary, Secondary, Tertiary) + Surface + Error
- Each accent group: base, onColor, container, onContainer variants
- Surface hierarchy: surfaceDim → surface → surfaceBright, plus 5 container levels
- Fixed colors stay the same across light/dark themes
- Dynamic color generates schemes from user wallpaper or in-app content
- Always design with baseline scheme first, then test dynamic variations

**M3 Typography:**
- 5 roles: Display (hero), Headline (sections), Title (cards/toolbars), Body (reading), Label (buttons/metadata)
- Each role: Large, Medium, Small — totaling 15 baseline + 15 emphasized styles
- Default font: Roboto (Roboto Flex for M3 Expressive)
- Use role names semantically, never by pixel size preference

**M3 Elevation:**
- Level 0 (0dp): canvas — Level 1 (1dp): cards — Level 2 (3dp): buttons — Level 3 (6dp): nav bars — Level 4 (8dp): hover — Level 5 (12dp): modals
- Tonal overlay intensity increases with level
- Levels 0–3: resting states; Levels 4–5: interactive states

**M3 Shape:**
- Scale: None (0dp) → Extra Small (4dp) → Small (8dp) → Medium (12dp) → Large (16dp) → Extra Large (28dp) → Full (circular)
- Shape morph for interaction states, loading, environmental changes
- Harmonize shape with typography for cohesive feel

**M3 Motion:**
- Physics system uses spring composites (damping + stiffness)
- Two schemes: Expressive (playful, bouncy) and Standard (calm, smooth)
- Transition patterns: Container Transform, Shared Axis, Fade Through, Fade
- Legacy easing/duration system still available for custom transitions

**M3 Icons (Material Symbols):**
- Variable font with 4 axes: Fill (0–1), Weight (100–700), Grade (-25–200), Optical Size (20–48)
- 3 styles: Outlined (clean), Rounded (friendly), Sharp (precise)
- Sizes: 20dp (dense), 24dp (default), 40dp (display), 48dp (hero)
- Fill=1 for active states, Fill=0 for default states

**Key Patterns:**
- Cards use Medium shape (12dp corner radius)
- Dialogs for decisions requiring explicit acknowledgment
- Snackbars for non-critical feedback (auto-dismiss, max one at a time)
- Bottom sheets: Standard (persistent) vs Modal (requires action)
- Use Container Transform for card-to-detail transitions
- Use Shared Axis for forward/backward navigation

---

## Microsoft Fluent 2

**Core Principles:** Familiar, Instinctive, Universal, Inclusive

| Standard | Rule |
|----------|------|
| Touch targets | Minimum 40×40px |
| Typography | Segoe UI — use type ramp from Caption to Display |
| Spacing | 4px base unit |
| Color | Theme-aware (light/dark/high-contrast) |
| Iconography | Fluent System Icons |
| Layer System | Stroke, Fill, Background, Overlay, Scrim |
| Accessibility | Full keyboard navigation and screen reader support mandatory |

**Key Patterns:**
- Command Bar for toolbars (top of surface)
- Pivot/Tab for secondary navigation within a page
- Dialog vs Panel: dialogs are disruptive, panels are side-persistent
- Always provide keyboard shortcuts for power users (Ctrl+S, Ctrl+Z, etc.)

---

## Meta (Facebook) Design

**Core Principles:** Authentic, Playful, Unified

| Standard | Rule |
|----------|------|
| Touch targets | Minimum 44×44px |
| Typography | Optimize for legibility at small sizes in dense feeds |
| Density | Support comfortable and compact modes |
| Accessibility | WCAG 2.1 AA minimum, AAA for text |

**Key Patterns:**
- Inline reactions over separate pages
- Progressive loading (skeleton screens before content)
- Infinite scroll with fixed navigation landmark
- Toast notifications non-blocking and dismissible

---

## Universal Standards (Cross-Platform)

### Color
| Usage | Guideline |
|-------|-----------|
| Contrast (text/bg) | Minimum 4.5:1 (AA), 7:1 (AAA) |
| Primary actions | One dominant brand color for CTA |
| Destructive actions | Red — always `#EF4444` range or platform-equivalent |
| Success | Green — `#22C55E` range |
| Warning | Amber — `#F59E0B` range |
| Error | Red — distinct from destructive, with icon+text+color for accessibility |
| Never color-only | Always pair color with shape, icon, or text for colorblind users |

### Typography
| Level | Usage |
|-------|-------|
| Display/H1 | Hero sections, page titles |
| H2–H3 | Section headings |
| Body L | Main readable content |
| Body S | Secondary content, captions |
| Label | UI labels, metadata, tags |
| Minimum size | 14px / 11pt (never below) |
| Line height | 1.4–1.6× for body text |

### Spacing
- Use an **8px grid** for all spacing (4px for tight internal spacing)
- Consistent padding: 16px (mobile), 24px (tablet), 32px+ (desktop)
- Whitespace is not wasted space — it reduces cognitive load

### Animation & Motion
| Type | Duration | Easing |
|------|----------|--------|
| Micro-interactions | 100–200ms | ease-out |
| Transitions | 200–300ms | ease-in-out |
| Enter animations | 200–400ms | ease-out |
| Exit animations | 150–250ms | ease-in |
| Never | > 500ms for UI feedback | — |

**Principles:**
- Motion should be purposeful — never decorative only
- Reduce motion for users with `prefers-reduced-motion`
- Animations should reinforce spatial models (where did this element come from/go?)

### Accessibility (WCAG 2.1 AA — Mandatory)
- **Contrast**: 4.5:1 for normal text, 3:1 for large text and UI components
- **Keyboard**: All interactive elements focusable and operable via keyboard
- **ARIA**: Use semantic HTML first; ARIA roles only when native semantics are insufficient
- **Focus indicators**: Visible focus ring, never `outline: none` without a replacement
- **Alt text**: All meaningful images have descriptive alt text
- **Error messages**: Linked to inputs via `aria-describedby`
- **Forms**: Always use `<label>` elements, not placeholder-only labels
- **Touch targets**: 44×44px minimum for all interactive elements

### Responsive Design
| Breakpoint | Width | Pattern |
|------------|-------|---------|
| Mobile | < 640px | Single column, bottom navigation |
| Tablet | 640–1024px | Two columns, side navigation optional |
| Desktop | > 1024px | Multi-column, full navigation |

- Mobile-first approach: design for small screens first, enhance for larger
- Test on real devices, not just browser resize
- Consider thumb reach zones on mobile (bottom 2/3 of screen is easiest)

---

## Design Tokens (Reference Structure)

### Generic Token Structure
```
colors/
  brand/primary, secondary, tertiary
  semantic/success, warning, error, info
  neutral/0–1000

typography/
  font-family/
  font-size/xs, sm, md, lg, xl, 2xl...
  font-weight/regular, medium, semibold, bold
  line-height/

spacing/
  0, 1 (4px), 2 (8px), 3 (12px), 4 (16px), 6 (24px), 8 (32px)...

border-radius/
  none, sm (4px), md (8px), lg (12px), xl (16px), full

shadow/
  sm, md, lg, xl

motion/
  duration/fast (100ms), normal (200ms), slow (300ms)
  easing/ease-in, ease-out, ease-in-out
```

### M3 Design Token Architecture (Three-Tier)

```
# Tier 1: Reference tokens (raw values — never use directly in components)
md.ref.palette.primary40
md.ref.palette.neutral90
md.ref.typeface.brand

# Tier 2: System tokens (semantic roles — customize these to theme your app)
md.sys.color.primary
md.sys.color.on-primary
md.sys.color.primary-container
md.sys.color.surface
md.sys.color.error
md.sys.typescale.display-large.size        → 57sp
md.sys.typescale.body-medium.size          → 14sp
md.sys.typescale.label-small.size          → 11sp
md.sys.elevation.level0                    → 0dp
md.sys.elevation.level1                    → 1dp
md.sys.elevation.level2                    → 3dp
md.sys.elevation.level3                    → 6dp
md.sys.elevation.level4                    → 8dp
md.sys.elevation.level5                    → 12dp
md.sys.shape.corner.none                   → 0dp
md.sys.shape.corner.extra-small            → 4dp
md.sys.shape.corner.small                  → 8dp
md.sys.shape.corner.medium                 → 12dp
md.sys.shape.corner.large                  → 16dp
md.sys.shape.corner.extra-large            → 28dp
md.sys.shape.corner.full                   → 50%
md.sys.motion.spring.default               → damping + stiffness composite
md.sys.motion.easing.emphasized            → cubic-bezier(0.2, 0.0, 0, 1.0)
md.sys.icon.size.default                   → 24dp

# Tier 3: Component tokens (framework-managed — map system tokens to components)
md.comp.filled-button.container.color      → md.sys.color.primary
md.comp.filled-button.label-text.color     → md.sys.color.on-primary
md.comp.filled-button.container.shape      → md.sys.shape.corner.full
md.comp.card.container.elevation           → md.sys.elevation.level1
md.comp.card.container.shape               → md.sys.shape.corner.medium
```
