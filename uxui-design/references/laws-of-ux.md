# Laws of UX — Full Reference

Source: [lawsofux.com](https://lawsofux.com/) by Jon Yablonski

All 30 laws documented with definition, design application, and real-world examples.

---

## 1. Aesthetic-Usability Effect

> Users often perceive aesthetically pleasing design as design that's more usable.

**Application:**
- Polish visual details even when they don't affect functionality
- Attractive design creates a halo effect — users tolerate minor usability issues more
- Invest in typography, spacing, color harmony, and iconography

**Example:** Apple products are perceived as intuitive partly because they look beautiful.

---

## 2. Choice Overload

> The tendency for people to get overwhelmed when presented with a large number of options.

**Application:**
- Limit visible options to the most relevant (5–7 max)
- Use progressive disclosure for advanced options
- Provide smart defaults and recommendations
- Group similar options into categories

**Example:** Netflix uses "Top 10 in your country" to reduce decision paralysis.

---

## 3. Chunking

> Individual pieces of an information set are broken down and grouped together in a meaningful whole.

**Application:**
- Break long forms into logical sections with clear headings
- Group phone numbers, credit cards, and codes with spacing (555 123-4567)
- Use cards, dividers, and whitespace to create visual chunks
- Present steps in numbered sequences

**Example:** Checkout flows split into Address → Shipping → Payment → Review.

---

## 4. Cognitive Bias

> A systematic error of thinking that influences our perception and decision-making.

**Application:**
- Be aware of anchoring (first number seen influences judgments)
- Use social proof to leverage bandwagon effect
- Be aware of confirmation bias — users notice info that confirms their beliefs
- Don't exploit biases in dark patterns

**Common biases in UX:**
- **Anchoring**: Show original price before discounted price
- **Loss aversion**: "Don't miss out" framing
- **Scarcity**: "Only 3 left in stock"

---

## 5. Cognitive Load

> The amount of mental resources needed to understand and interact with an interface.

**Types:**
- **Intrinsic**: Inherent complexity of the task
- **Extraneous**: Unnecessary complexity added by poor design
- **Germane**: Mental effort to build long-term understanding

**Application:**
- Eliminate extraneous cognitive load (remove unnecessary elements, reduce visual noise)
- Use familiar patterns (Jakob's Law) to reduce intrinsic load
- Use progressive disclosure — show only what's needed at each step
- Use clear visual hierarchy to guide attention

---

## 6. Doherty Threshold

> Productivity soars when a computer and its users interact at a pace (<400ms) that ensures neither has to wait on the other.

**Application:**
- All interactions must respond in under 400ms
- For slower operations: use skeleton screens, progress bars, or optimistic UI
- Animate UI state changes to signal that something is happening
- Pre-load content where possible

**Metrics:**
- < 100ms: Feels instantaneous
- < 400ms: User stays in flow
- > 1s: User attention may wander
- > 10s: User loses focus entirely

---

## 7. Fitts's Law

> The time to acquire a target is a function of the distance to and size of the target.

**Application:**
- Minimum touch target: **44×44px** (Apple HIG) / **48×48dp** (Material Design)
- Place primary actions where the user's attention already is
- Keep related actions close together
- Make edge/corner targets larger (they stop the cursor)
- Avoid placing destructive actions near frequently-used actions

**Formula:** $T = a + b \log_2\left(1 + \frac{D}{W}\right)$ where D = distance, W = target width

---

## 8. Flow

> The mental state of being fully immersed in an activity with energized focus and enjoyment.

**Application:**
- Match task difficulty to user skill level — too easy = boredom, too hard = anxiety
- Minimize interruptions (notifications, popups, redirects) during focused tasks
- Provide immediate feedback so users know they're on the right path
- Use auto-save to remove fear of losing progress

**Example:** Code editors use syntax highlighting and auto-complete to keep developers in flow.

---

## 9. Goal-Gradient Effect

> The tendency to approach a goal increases with proximity to the goal.

**Application:**
- Always show users how far they are from completion
- Use progress bars, step indicators, and percentage completions
- In loyalty programs, give "head start" points to make users feel closer to a reward
- Show "X more items to free shipping"

**Example:** LinkedIn profile completion meter motivates users to fill in more details.

---

## 10. Hick's Law

> The time it takes to make a decision increases with the number and complexity of choices.

**Formula:** $T = b \log_2(n + 1)$ where n = number of choices

**Application:**
- Minimize choices at critical decision points
- Break complex tasks into smaller steps
- Highlight recommended/default options to reduce decision effort
- Use progressive onboarding — don't dump all features at once
- Keep navigation to max 7 top-level items

**Example:** Google's homepage has one input field — zero choice paralysis.

---

## 11. Jakob's Law

> Users spend most of their time on other sites and prefer your site to work the same way as all the other sites they already know.

**Application:**
- Follow platform conventions (hamburger menu on mobile, logo top-left, search top-right)
- Don't reinvent interaction patterns unless you have a compelling reason
- When redesigning, allow users to preview the new design and revert if needed
- Map controls to real-world equivalents (toggle switches, sliders)

**Example:** YouTube's 2017 redesign let users try/revert the new UI before fully committing.

---

## 12. Law of Common Region

> Elements tend to be perceived as groups if they share an area with a clearly defined boundary.

**Application:**
- Use cards, borders, and background fills to group related content
- Don't rely solely on whitespace — use containers for critical groupings
- Navigation drawers, toolbars, and modals use common region to define context

---

## 13. Law of Proximity

> Objects that are near each other tend to be grouped together.

**Application:**
- Place labels directly above or beside their inputs (not far apart)
- Keep action buttons near the content they act on
- Use whitespace to separate unrelated groups
- Related settings/options should be visually adjacent

---

## 14. Law of Prägnanz

> People perceive and interpret ambiguous or complex images as the simplest form possible.

**Application:**
- Use simple, clean shapes — avoid unnecessary decoration
- Simplify icons to their most recognizable form
- Use conventional UI patterns that users can process instantly
- Reduce visual complexity through whitespace and clear hierarchy

---

## 15. Law of Similarity

> The human eye perceives similar elements as a complete picture, shape, or group, even if separated.

**Application:**
- Use consistent color, shape, and size for elements that share the same function
- Different visual treatment = different function (don't make two different things look the same)
- Use iconographic consistency across an entire product

---

## 16. Law of Uniform Connectedness

> Elements that are visually connected are perceived as more related than elements with no connection.

**Application:**
- Use lines, arrows, and shared containers to show relationships
- Use connecting lines in org charts, flowcharts, and timelines
- Breadcrumbs and step indicators use connection to show sequence

---

## 17. Mental Model

> A compressed model based on what users think they know about a system and how it works.

**Application:**
- Design interfaces that match users' real-world mental models (e.g., trash can = delete)
- Conduct user research to understand existing mental models before designing
- When introducing new concepts, anchor them to familiar existing ones
- If you must break a mental model, invest heavily in onboarding/education

---

## 18. Miller's Law

> The average person can only keep 7 (plus or minus 2) items in their working memory.

**Application:**
- Limit navigation items to 7 max
- Break long lists into categories or paginate
- Don't ask users to remember information from a previous screen
- Chunk content into groups of 3–5 for optimal processing
- Use visible labels instead of relying on memory (don't use icon-only interfaces)

---

## 19. Occam's Razor

> Among competing solutions that predict equally well, the one with the fewest assumptions should be selected.

**Application:**
- When choosing between two design solutions, prefer the simpler one
- Remove any feature, element, or step that doesn't clearly serve the user's goal
- Every element in the UI must justify its existence
- "Perfection is achieved not when there is nothing more to add, but when there is nothing left to take away" — Antoine de Saint-Exupéry

---

## 20. Paradox of the Active User

> Users never read manuals but start using the software immediately.

**Application:**
- Design for discoverability — UI should teach itself through use
- Embed learning into the workflow (tooltips, empty states, contextual hints)
- Do NOT require completing onboarding before allowing use
- Progressive disclosure: reveal features as users are ready for them

---

## 21. Pareto Principle

> 80% of the effects come from 20% of the causes.

**Application:**
- Identify the 20% of features/paths used by 80% of users — optimize those ruthlessly
- Focus design effort on the critical path, not edge cases
- Analytics: find the 3–5 pages/flows that drive the most value
- Prioritize fixing the top 20% of usability issues that cause 80% of friction

---

## 22. Parkinson's Law

> Any task will inflate until all of the available time is spent.

**Application:**
- Set time constraints for tasks to improve completion rates (e.g., countdown timers)
- For checkout flows, remove distractions that extend the session
- Keep forms short — the longer the form, the more time it takes and more it inflates

---

## 23. Peak-End Rule

> People judge an experience largely based on how they felt at its peak and at its end, not the total sum.

**Application:**
- Invest heavily in the **success state** (order confirmed, task completed) — this is the "end"
- Design a memorable peak moment (delight, animation, celebration)
- Error states are peaks too — handle them graciously to avoid negative peaks
- Even bad experiences can be remembered positively if they end well

**Example:** Duolingo's celebratory animations after lesson completion.

---

## 24. Postel's Law

> Be liberal in what you accept, and conservative in what you send.

**Application:**
- Accept flexible input: phone numbers with or without dashes, email in any case
- Auto-format input as the user types (credit card numbers, dates)
- Output clean, consistent, predictable data
- Never force a specific format when you can normalize it in code

---

## 25. Selective Attention

> The process of focusing only on a subset of stimuli — usually those related to our goals.

**Application:**
- Remove everything that competes with the user's primary goal
- Users will ignore elements outside their current focus area
- Use visual hierarchy to guide attention to what matters
- Don't rely on users noticing peripheral elements for critical information
- This is why banners and pop-ups are often ignored (banner blindness)

---

## 26. Serial Position Effect

> Users have a propensity to best remember the first and last items in a series.

**Application:**
- Place the most important navigation items first or last
- In pricing tables, put the recommended plan last
- In lists, ensure the first and last items are the most important
- The middle items in long lists are least remembered — avoid burying critical actions there

---

## 27. Tesler's Law (Law of Conservation of Complexity)

> For any system there is a certain amount of complexity which cannot be reduced.

**Application:**
- Complexity doesn't disappear — it transfers between user and system
- Absorb complexity in code (validation, formatting, defaults) rather than pushing it to the user
- Simple UIs are built on complex systems — never mistake a simple UI for a simple problem
- Ask: "Am I making this simpler for the user, or just hiding the complexity?"

---

## 28. Von Restorff Effect (Isolation Effect)

> When multiple similar objects are present, the one that differs from the rest is most likely to be remembered.

**Application:**
- Use ONE contrasting CTA color per screen — the primary action must stand out
- Highlight recommended/popular options in pricing tables
- Use badges, labels, or color accents to draw attention to new/important items
- Don't over-use contrast — if everything stands out, nothing does

---

## 29. Working Memory

> A cognitive system that temporarily holds and manipulates information needed to complete tasks.

**Application:**
- Never require users to remember information from one screen to use on another
- Show contextual info inline (e.g., password requirements visible while typing)
- In wizards/flows, show a summary of previous steps
- Use auto-fill, pre-populated fields, and smart defaults to reduce memory load
- Capacity: ~4 chunks of information at once (Cowan's updated model)

---

## 30. Zeigarnik Effect

> People remember uncompleted or interrupted tasks better than completed tasks.

**Application:**
- Use progress indicators to create a sense of incompleteness that motivates continuation
- "Your cart has 2 items" exploits Zeigarnik to bring users back
- Incomplete profile prompts ("Your profile is 70% complete") leverage this effect
- Send "you left something behind" emails/notifications strategically
- Don't overuse — it can feel manipulative if not genuine

---

## Laws Grouped by Design Phase

### Information Architecture
Hick's Law, Miller's Law, Chunking, Law of Proximity, Law of Common Region, Law of Similarity, Law of Uniform Connectedness, Serial Position Effect

### Visual Design
Aesthetic-Usability Effect, Von Restorff Effect, Law of Prägnanz, Selective Attention, Cognitive Load

### Interaction Design
Fitts's Law, Doherty Threshold, Postel's Law, Flow, Tesler's Law

### User Psychology
Peak-End Rule, Goal-Gradient Effect, Zeigarnik Effect, Goal-Gradient Effect, Pareto Principle, Paradox of the Active User

### Mental Models & Familiarity
Jakob's Law, Mental Model, Cognitive Bias, Occam's Razor

### Memory
Working Memory, Miller's Law, Serial Position Effect, Chunking
