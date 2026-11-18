# Material Design 3 — Styles Reference

Comprehensive guide covering all M3 Styles subsystems: Color, Typography, Elevation, Shape, Motion, and Icons.

Source: [m3.material.io/styles](https://m3.material.io/styles)

> Content was rephrased for compliance with licensing restrictions.

---

## 1. Color System

### Overview

M3 uses a semantic, role-based color system built on the HCT (Hue, Chroma, Tone) color space. Colors are assigned to UI elements through **color roles** rather than hardcoded hex values, ensuring accessibility and theme adaptability.

Reference: [Color Overview](https://m3.material.io/styles/color/system/overview)

### How It Works

1. A **single source color** (seed) is selected
2. The system generates **five key colors**: Primary, Secondary, Tertiary, Neutral, Neutral Variant
3. Each key color produces a **tonal palette** with 13 tones (0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 99, 100)
4. Tones are mapped to **color roles** (e.g., `primary`, `onPrimary`, `primaryContainer`)
5. Color roles are applied to UI elements

### Color Roles

#### Accent Colors (3 groups)

| Group | Role | Usage |
|-------|------|-------|
| **Primary** | `primary` | Key actions, active states, high-emphasis elements |
| | `onPrimary` | Text/icons on primary color |
| | `primaryContainer` | Standout containers for key elements |
| | `onPrimaryContainer` | Text/icons on primary containers |
| **Secondary** | `secondary` | Less prominent actions, filters, selection |
| | `onSecondary` | Text/icons on secondary color |
| | `secondaryContainer` | Secondary containers |
| | `onSecondaryContainer` | Text/icons on secondary containers |
| **Tertiary** | `tertiary` | Contrasting accents to balance primary/secondary |
| | `onTertiary` | Text/icons on tertiary color |
| | `tertiaryContainer` | Tertiary containers |
| | `onTertiaryContainer` | Text/icons on tertiary containers |

#### Surface Colors

| Role | Usage |
|------|-------|
| `surface` | Default background for cards, sheets, dialogs |
| `onSurface` | Body text, icons on surface |
| `surfaceVariant` | Alternative surface for visual differentiation |
| `onSurfaceVariant` | Secondary text, icons on surface variant |
| `surfaceDim` | Dimmed surface (low-emphasis backgrounds) |
| `surfaceBright` | Bright surface (high-emphasis backgrounds) |
| `surfaceContainerLowest` | Lowest-emphasis container surface |
| `surfaceContainerLow` | Low-emphasis container surface |
| `surfaceContainer` | Default container surface |
| `surfaceContainerHigh` | High-emphasis container surface |
| `surfaceContainerHighest` | Highest-emphasis container surface |
| `inverseSurface` | Snackbars, tooltips (inverted scheme) |
| `inverseOnSurface` | Text on inverse surface |

#### Fixed Colors

| Role | Usage |
|------|-------|
| `primaryFixed` | Remains the same across light and dark themes |
| `primaryFixedDim` | Dimmed variant of primaryFixed |
| `secondaryFixed` | Cross-theme secondary color |
| `tertiaryFixed` | Cross-theme tertiary color |

#### Semantic Colors

| Role | Usage |
|------|-------|
| `error` | Error states, destructive actions |
| `onError` | Text/icons on error color |
| `errorContainer` | Error container background |
| `onErrorContainer` | Text/icons on error container |
| `outline` | Borders, dividers |
| `outlineVariant` | Decorative borders, subtle dividers |
| `scrim` | Background overlay for modals |
| `shadow` | Shadow color |

### Color Scheme Types

| Type | Description | When to Use |
|------|-------------|-------------|
| **Static (Baseline)** | Pre-defined, never changes | Enterprise apps, iOS, M2 migration, stable branding |
| **Dynamic (User-Generated)** | Adapts to user's wallpaper | Android personalization, consumer apps |
| **Dynamic (Content-Based)** | Adapts to in-app content | Media apps, galleries, players |

### Design Rules

- **Always use color roles**, never hardcoded hex values
- Design with **baseline scheme first**, then test with dynamic color
- Both **light and dark themes** must be supported
- Primary and tertiary are most visually prominent; secondary is less chromatic
- **Never use color alone** to convey information — pair with icons, text, or shape
- Use [Material Theme Builder](https://m3.material.io/styles/color/choosing-a-scheme) (Figma plugin) to generate and validate color schemes
- Custom colors can be added by providing a reference color; the system generates four roles: main, on-main, container, on-container

---

## 2. Typography

### Overview

M3 typography is organized into **5 roles**, each with **3 sizes** (Large, Medium, Small), totaling **15 baseline styles** plus **15 emphasized styles** (30 total).

Reference: [Typography Overview](https://m3.material.io/styles/typography/overview)

### Type Scale — 5 Roles

| Role | Purpose | Usage Examples |
|------|---------|----------------|
| **Display** | Largest text, short expressive text | Hero sections, marketing headlines |
| **Headline** | High-emphasis text to mark sections | Page titles, section headings |
| **Title** | Medium-emphasis text, shorter than headlines | Card titles, dialog titles, toolbar text |
| **Body** | Long-form readable text | Paragraphs, descriptions, article content |
| **Label** | Smallest text, utility text | Button text, menu items, tabs, captions, metadata |

### Size Variants

Each role has 3 sizes (properties: font family, size, weight, line height, letter spacing):

| Role | Large | Medium | Small |
|------|-------|--------|-------|
| Display | 57sp | 45sp | 36sp |
| Headline | 32sp | 28sp | 24sp |
| Title | 22sp | 16sp (medium weight) | 14sp (medium weight) |
| Body | 16sp | 14sp | 12sp |
| Label | 14sp (medium weight) | 12sp (medium weight) | 11sp (medium weight) |

### Baseline vs Emphasized Styles

- **Baseline**: Standard weight, default for most content
- **Emphasized**: Heavier weight or italic, used for emphasis and differentiation within the same role

### Applying Typography — Rules

- Use **role names** (Display, Headline, Title, Body, Label) — not pixel sizes
- Match type role to **semantic purpose**, not visual size preference
- Display and Headline are for **short, expressive text only** — never for body copy
- Body is for **long-form readable content** — always ensure ≥14sp minimum
- Label is for **utility/action text** — buttons, captions, metadata
- Set line height to **1.4–1.6×** for body text readability
- Default font: **Roboto** (Roboto Flex for M3 Expressive)
- Custom fonts can replace Roboto but must respect the scale's size, weight, and spacing tokens
- Ensure text contrast meets **WCAG 2.1 AA**: 4.5:1 for normal text, 3:1 for large text

### Design Tokens for Typography

```
md.sys.typescale.display-large.font
md.sys.typescale.display-large.size
md.sys.typescale.display-large.weight
md.sys.typescale.display-large.line-height
md.sys.typescale.display-large.tracking
```

Pattern: `md.sys.typescale.<role>-<size>.<property>`

---

## 3. Elevation

### Overview

Elevation is the relative distance between surfaces along the z-axis, measured in dp (density-independent pixels). In M3, elevation is primarily expressed through **tonal surface overlays** rather than drop shadows.

Reference: [Elevation Overview](https://m3.material.io/styles/elevation/overview)

### Elevation Levels

| Level | dp Value | Usage | Surface Tint |
|-------|----------|-------|--------------|
| **Level 0** | 0dp | Canvas, page background | No tint |
| **Level 1** | 1dp | Cards, navigation rails, search bars | Lowest tint |
| **Level 2** | 3dp | Buttons, chips, elevated cards | Low tint |
| **Level 3** | 6dp | Navigation bars, FABs, snackbars | Medium tint |
| **Level 4** | 8dp | Hover states (interactive) | High tint |
| **Level 5** | 12dp | Dragged states, modals, dialogs | Highest tint |

### Applying Elevation — Rules

- **Prefer surface tonal overlays** over drop shadows for elevation in M3
- Shadows may still be used as a **secondary cue** when needed for clarity
- **Higher elevation = more prominent surface tint** (in both light and dark themes)
- In **dark theme**, tonal overlay is more visible and effective than shadows
- Levels 0–3 are for **resting states** of components
- Levels 4–5 are reserved for **interactive states** (hover, drag)
- **Elevation establishes hierarchy** — higher = closer to user, more important
- Components stacked at the **same level** should use the same elevation
- Never use elevation purely for decoration — it must communicate **spatial relationships**

### Elevation and Interaction States

| Interaction | Elevation Behavior |
|-------------|-------------------|
| Resting | Component's default level (0–3) |
| Hover | +1 level above resting |
| Pressed | Returns to resting level |
| Dragged | Moves to level 4 or 5 |
| Disabled | Level 0 (no elevation) |

---

## 4. Shape

### Overview

M3 uses a **size-based shape scale** with 10 styles defining container corner rounding. The system supports rounded corners, cut corners, shape morphing, and expressive shapes.

Reference: [Shape Overview](https://m3.material.io/styles/shape/overview-principles)

### Corner Radius Scale

| Shape Style | Corner Radius | Usage Examples |
|-------------|---------------|----------------|
| **None** | 0dp (square) | Full-screen containers |
| **Extra Small** | 4dp | Text fields, tooltips |
| **Small** | 8dp | Chips, small buttons |
| **Medium** | 12dp | Cards, dialogs |
| **Large** | 16dp | Large cards, navigation drawers |
| **Extra Large** | 28dp | Large sheets, expanded FABs |
| **Full** | Fully circular | FABs, icon buttons, avatars |

Additionally, M3 Expressive adds top-only and asymmetric variants for each style.

### Shape Principles (M3 Expressive)

1. **Use shapes and text in harmony** — shapes should echo visual attributes of M3 typography for a cohesive feel
2. **Morph shapes to connect function and feeling** — use shape transitions to communicate interaction states, progress, and environmental changes
3. **Be bold and embrace tension** — contrast square and rounded shapes intentionally for visual interest

### Shape Morphing

Shape morph supports smooth transitions between shapes for:
- **Interaction states**: button selected, toggled, pressed
- **Actions in progress**: loading, typing, sending
- **Environmental changes**: sound, temperature, time of day

Think about how shapes react to: tapping, swiping, scrolling, releasing, long pressing.

### Applying Shape — Rules

- Assign shape styles based on **desired roundedness**, not component size
- All shapes are **rectangular by default**, fully rounded on all corners
- Individual corners can be adjusted for **asymmetric shapes**
- **Consistent shape language** — use the same shape style for components at the same hierarchy level
- Shape conveys **role and state** — rounded = friendly/safe, square = structured/formal
- Shape morph should feel **natural and purposeful**, never gratuitous

### Design Tokens for Shape

```
md.sys.shape.corner.none          → 0dp
md.sys.shape.corner.extra-small   → 4dp
md.sys.shape.corner.small         → 8dp
md.sys.shape.corner.medium        → 12dp
md.sys.shape.corner.large         → 16dp
md.sys.shape.corner.extra-large   → 28dp
md.sys.shape.corner.full          → 50% (circular)
```

---

## 5. Motion

### Overview

M3 Expressive introduces a **physics-based motion system** using spring animations. This replaces the legacy easing/duration system for component animations, making transitions feel more alive and natural.

Reference: [Motion Overview](https://m3.material.io/styles/motion/overview/how-it-works)

### Motion Physics System (M3 Expressive)

The system uses **spring composites** defined by two properties:
- **Damping**: How quickly the animation settles (higher = less bounce)
- **Stiffness**: How fast the spring moves (higher = faster animation)

#### Motion Schemes

| Scheme | Feel | When to Use |
|--------|------|-------------|
| **Expressive** | Playful, energetic, bouncy | Consumer apps, creative products, onboarding |
| **Standard** | Calm, professional, smooth | Enterprise apps, productivity tools, data-heavy UIs |

Products should use **one scheme consistently** but can swap schemes for key moments (e.g., celebration animations).

### Transition Patterns

| Pattern | Description | Use Case |
|---------|-------------|----------|
| **Container Transform** | Transforms one element into another, showing a visual relationship | Card → detail page, FAB → full screen, list item → detail |
| **Shared Axis** | Elements move along a shared X, Y, or Z axis | Forward/backward navigation, onboarding steps, tab switching |
| **Fade Through** | Element fades out then a new element fades in | Switching between unrelated destinations (bottom nav) |
| **Fade** | Simple opacity change | Enter/exit of elements that don't have a spatial relationship |

#### Applying Transitions — Rules

- Transitions should have a **unified direction of movement** — group elements along a primary axis
- Only **hero elements** (main image, key content) remain persistent throughout transitions
- Use **Container Transform** when two elements have a clear parent-child relationship
- Use **Shared Axis** when elements share a spatial or navigational relationship
- Use **Fade Through** when switching between completely unrelated views
- Keep transitions **under 500ms** for UI-level animation
- Always respect **`prefers-reduced-motion`** — provide alternatives or skip non-essential animation

### Legacy System (Easing & Duration)

Still used for custom transitions when physics system isn't available:

| Type | Easing | Duration | Usage |
|------|--------|----------|-------|
| **Emphasized** | Cubic-bezier(0.2, 0.0, 0, 1.0) | 500ms | Entering, exiting, large-scale transitions |
| **Emphasized Accelerate** | Cubic-bezier(0.3, 0.0, 0.8, 0.15) | 200ms | Exiting elements |
| **Emphasized Decelerate** | Cubic-bezier(0.05, 0.7, 0.1, 1.0) | 400ms | Entering elements |
| **Standard** | Cubic-bezier(0.2, 0.0, 0, 1.0) | 300ms | Small utility animations |
| **Standard Accelerate** | Cubic-bezier(0.3, 0.0, 1.0, 1.0) | 200ms | Exiting with standard feel |
| **Standard Decelerate** | Cubic-bezier(0.0, 0.0, 0, 1.0) | 250ms | Entering with standard feel |

### Design Tokens for Motion

```
# Spring composites (physics system)
md.sys.motion.spring.fast
md.sys.motion.spring.default
md.sys.motion.spring.slow
md.sys.motion.spring.spatial.fast
md.sys.motion.spring.spatial.default
md.sys.motion.spring.spatial.slow

# Legacy tokens
md.sys.motion.easing.emphasized
md.sys.motion.easing.standard
md.sys.motion.duration.short1    → 50ms
md.sys.motion.duration.short2    → 100ms
md.sys.motion.duration.short3    → 150ms
md.sys.motion.duration.short4    → 200ms
md.sys.motion.duration.medium1   → 250ms
md.sys.motion.duration.medium2   → 300ms
md.sys.motion.duration.medium3   → 350ms
md.sys.motion.duration.medium4   → 400ms
md.sys.motion.duration.long1     → 450ms
md.sys.motion.duration.long2     → 500ms
```

---

## 6. Icons (Material Symbols)

### Overview

Material Symbols is a variable icon font with 3 styles, supporting adjustable optical size, weight, grade, and fill. All icons are designed at 24×24dp grid and can be scaled.

Reference: [Icons Overview](https://m3.material.io/styles/icons/overview)

### Styles

| Style | Look | Best For |
|-------|------|----------|
| **Outlined** | Stroke-based, light, clean | Dense UIs, text-heavy layouts |
| **Rounded** | Rounded stroke endings, softer | Friendly consumer apps |
| **Sharp** | Angular stroke endings, precise | Technical, professional tools |

### Variable Font Axes

| Axis | Range | Default | Effect |
|------|-------|---------|--------|
| **Fill** | 0–1 | 0 (unfilled) | 0 = outlined, 1 = filled (active state) |
| **Weight** | 100–700 | 400 | Matches companion text weight |
| **Grade** | -25 to 200 | 0 | Fine-tune weight without changing size |
| **Optical Size** | 20–48 | 24 | Adjusts detail at different sizes |

### Icon Sizes

| Size | Usage |
|------|-------|
| **20dp** | Desktop, dense layouts, small-scale visuals |
| **24dp** | Standard size (default for all M3 components) |
| **40dp** | Display or headline-level visuals, emphasis |
| **48dp** | Large-screen layouts, hero icons |

### Applying Icons — Rules

- Default size: **24×24dp** — use this unless there's a clear reason for another size
- Match icon **weight to companion text weight** for visual harmony
- Use **Fill=1** for selected/active states, **Fill=0** for unselected/default states
- Adjust **Grade** for dark/light theme: slightly negative in dark mode for better legibility
- Adjust **Optical Size** when rendering at non-standard sizes for pixel crispness
- Use **semantic icon names** (`home`, `search`, `settings`) not visual descriptions
- Icons should be **universally recognizable** — if an icon needs a label to be understood, add one
- Always provide accessible labels for icons used without visible text (`aria-label`, `contentDescription`)
- **Outlined style** stroke weight can be adjusted to complement or contrast your typography weight

### Design Tokens for Icons

```
md.sys.icon.size.default      → 24dp
md.sys.icon.size.small        → 20dp
md.sys.icon.size.large        → 40dp
md.sys.icon.size.display      → 48dp
```

---

## 7. Design Tokens Architecture

### Three-Tier Token System

M3 uses a structured, three-tier design token architecture:

| Tier | Naming Pattern | Description | Example |
|------|---------------|-------------|---------|
| **Reference (ref)** | `md.ref.*` | Raw values (all available options) | `md.ref.palette.primary40` |
| **System (sys)** | `md.sys.*` | Semantic mappings (role-based) | `md.sys.color.primary` |
| **Component (comp)** | `md.comp.*` | Component-specific tokens | `md.comp.filled-button.container.color` |

### How Tokens Flow

```
Reference Token  →  System Token  →  Component Token
md.ref.palette.primary40  →  md.sys.color.primary  →  md.comp.filled-button.container.color
```

- **Reference tokens** are the raw palette — never use these directly in components
- **System tokens** assign semantic meaning — these are what you customize to theme your app
- **Component tokens** map system tokens to specific component properties — typically managed by the framework

### Token Categories

| Category | System Token Prefix | Examples |
|----------|-------------------|----------|
| Color | `md.sys.color.*` | `md.sys.color.primary`, `md.sys.color.surface` |
| Typography | `md.sys.typescale.*` | `md.sys.typescale.body-medium.size` |
| Elevation | `md.sys.elevation.*` | `md.sys.elevation.level1` |
| Shape | `md.sys.shape.*` | `md.sys.shape.corner.medium` |
| Motion | `md.sys.motion.*` | `md.sys.motion.spring.default` |

---

## Quick Reference — M3 Styles at a Glance

| Style | Key Concept | Token Prefix |
|-------|-------------|-------------|
| **Color** | Semantic roles from HCT tonal palettes | `md.sys.color.*` |
| **Typography** | 5 roles × 3 sizes (15 baseline + 15 emphasized) | `md.sys.typescale.*` |
| **Elevation** | 6 levels (0–5) via tonal overlays, not shadows | `md.sys.elevation.*` |
| **Shape** | 10-style corner radius scale + shape morph | `md.sys.shape.*` |
| **Motion** | Physics-based springs (Expressive/Standard schemes) | `md.sys.motion.*` |
| **Icons** | Variable font, 3 styles, 4 axes (fill, weight, grade, optical size) | `md.sys.icon.*` |
