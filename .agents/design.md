# Design Specification — Hydration Companion PWA

## 1. Product Philosophy

### Core Concept

Hydration Companion should feel like **a physical water bottle brought to life digitally**.

It is not a medical dashboard, fitness tracker, productivity tool, or generic analytics application.

The experience should feel:

- Calm
- Inviting
- Tactile
- Friendly
- Comfortable
- Personal
- Lightweight
- Pleasant to revisit throughout the day

The core emotional idea is:

> **My water bottle, but alive.**

The user should not feel judged, pressured, or evaluated every time they open the app.

### Core Interaction Loop

```text
See bottle → Drink → Bottle level changes → Daily progress updates
→ Refill → Continue drinking
```

The bottle is the primary visual object. Data supports the bottle experience rather than dominating it.

---

# 2. Fundamental Value Distinctions

The application must clearly distinguish between four separate concepts.

| Metric | Example | Meaning | Primary Representation |
|---|---:|---|---|
| Daily Hydration Target | 2.70 L | Estimated total fluid recommendation for the day | Small progress indicator + text |
| Consumed Today | 1.85 L | Total fluid logged today | Large numeric display |
| Current Bottle Volume | 420 ml | Water physically remaining in the bottle | Animated bottle fill |
| Bottle Capacity | 750 ml | Maximum physical capacity | Bottle configuration |

### Important Rule

The animated bottle **must represent Current Bottle Volume only**.

It must never represent daily target completion.

Daily hydration progress and physical bottle volume are separate concepts and must remain visually distinguishable.

---

# 3. Visual Identity

## Design Direction

The visual language should feel inspired by:

- Blue-gray interiors
- Clear and tinted glass
- Water
- Soft daylight
- Ceramic
- Natural materials
- Muted colors
- Quiet indoor spaces
- Physical bottles and drinking glasses

The application should feel **light without being white**.

The canvas should have enough color and atmosphere that the interface feels like an environment rather than a white webpage.

### Avoid

- Clinical white interfaces
- Dark SaaS dashboards
- Neon gradients
- Excessive glassmorphism
- Excessive blur
- Large glowing charts
- Generic AI dashboard layouts
- Dense KPI grids
- Excessive floating cards
- Aggressive gamification

---

# 4. Visual Principles

## 4.1 Atmospheric Backgrounds

Background color is a major part of the visual identity.

The default theme should use a muted blue-gray background rather than white.

Use large, calm color fields and subtle tonal variation.

Do not create a white canvas with colored cards placed on top.

## 4.2 Bottle First

The bottle is the main visual object on the Today screen.

Supporting UI should visually recede.

## 4.3 Less Card-Based UI

Avoid the pattern:

```text
Card
Card
Card
Card
```

Use:

- Whitespace
- Typography
- Soft surfaces
- Subtle dividers
- Organic background shapes
- Physical-looking controls

Cards should be reserved for sections that genuinely need containment.

## 4.4 Soft Rather Than Glossy

Use subtle depth.

Prefer:

```text
soft shadow
subtle translucency
muted surfaces
natural highlights
```

Avoid:

```text
neon glow
heavy shadow
strong blur
high-contrast glassmorphism
```

## 4.5 Quiet Motion

Animations should communicate physicality.

Nothing should continuously move merely to make the interface look animated.

---

# 5. Theme System

The application should support multiple complete visual themes.

Themes must change the **environment around the bottle**, not just swap the bottle gradient.

Each theme controls:

- Background
- Secondary background
- Surface
- Primary text
- Secondary text
- Water color
- Accent color
- Positive state
- Border color
- Bottle appearance
- Optional decorative ambient shapes

The selected theme should persist across sessions.

## Theme Selection UI

The Settings screen should show themes as visual previews rather than text-only options.

Example:

```text
Choose your atmosphere

○ Ocean Mist
○ Sage Morning
○ Rose Water
○ Warm Sand
○ Midnight Pool
```

Each option should display a miniature preview of the complete interface.

---

# 6. Theme 1 — Ocean Mist

## Personality

Calm, fresh, watery, balanced.

This is the **default theme**.

## Colors

```text
Background:       #D9E7E8
Background Deep:  #C5D9DC
Surface:          #E5EFEE
Surface Raised:   #EDF3F0

Primary Water:    #67AFC4
Deep Water:       #3E8198
Soft Water:       #B9DDE5

Primary Text:     #263B42
Secondary Text:   #5D737A
Muted Text:       #809298

Border:           #C4D4D6
Success:          #7EAE91
```

## Bottle

```text
Water Start: #8ACFDF
Water End:   #4C98B1
```

The overall experience should resemble cool blue glass in soft daylight.

---

# 7. Theme 2 — Sage Morning

## Personality

Natural, gentle, earthy, restorative.

This theme should feel slightly warmer than Ocean Mist.

## Colors

```text
Background:       #DDE4DA
Background Deep:  #CBD6C8
Surface:          #E8ECE2
Surface Raised:   #F0F1E8

Primary Water:    #70A99A
Deep Water:       #4D8175
Soft Water:       #B8D5CA

Primary Text:     #293B36
Secondary Text:   #60736C
Muted Text:       #84918C

Border:           #C8D2C8
Success:          #729D7F
```

## Bottle

```text
Water Start: #A4D1C0
Water End:   #5E9B89
```

The bottle should resemble muted green-tinted glass.

---

# 8. Theme 3 — Rose Water

## Personality

Soft, warm, intimate, playful without becoming childish.

The pink should remain muted and dusty.

## Colors

```text
Background:       #E7DCDD
Background Deep:  #D9CBCD
Surface:          #EEE6E3
Surface Raised:   #F4ECE8

Primary Water:    #C88994
Deep Water:       #9D626F
Soft Water:       #E2B8BD

Primary Text:     #443238
Secondary Text:   #79636A
Muted Text:       #99858A

Border:           #D8C9C9
Success:          #7FA18B
```

## Bottle

```text
Water Start: #E7B9BF
Water End:   #B87380
```

Avoid bright pinks, magenta, or candy-like gradients.

---

# 9. Theme 4 — Warm Sand

## Personality

Warm, cozy, earthy, relaxed.

This theme is deliberately less blue and should feel like warm ceramic and sunlight.

## Colors

```text
Background:       #E5DED0
Background Deep:  #D5CBBB
Surface:          #EEE8DC
Surface Raised:   #F3EDE2

Primary Water:    #6797A0
Deep Water:       #476F77
Soft Water:       #B5D0D0

Primary Text:     #3E3930
Secondary Text:   #706A5E
Muted Text:       #918A7C

Border:           #D2C9B9
Success:          #78997D
```

## Bottle

```text
Water Start: #9BC6CC
Water End:   #578B96
```

The warm background contrasts with the cool water.

---

# 10. Theme 5 — Midnight Pool

## Personality

Quiet, deep, atmospheric, evening-oriented.

This is the dark theme.

It should not resemble a typical developer dashboard.

## Colors

```text
Background:       #172A30
Background Deep:  #102126
Surface:          #20383F
Surface Raised:   #28434A

Primary Water:    #76BFD0
Deep Water:       #4A94A7
Soft Water:       #315F6A

Primary Text:     #E3ECEB
Secondary Text:   #AFC0C2
Muted Text:       #81979B

Border:           #355158
Success:          #8BB79A
```

## Bottle

```text
Water Start: #82C7D6
Water End:   #438A9F
```

Use soft contrast rather than pure black and white.

---

# 11. Theme Rules

Themes should follow these rules:

1. No theme should use pure white as its dominant background.
2. No theme should use pure black as its dominant background.
3. Water must remain visually distinguishable from the surrounding background.
4. Text must meet WCAG contrast requirements.
5. Accent colors should remain muted and natural.
6. Themes must never alter the meaning of metrics.
7. Theme selection must not change hydration calculations.
8. Decorative shapes must remain subtle.

---

# 12. Typography

Typography should feel friendly and contemporary.

Recommended fonts:

```text
DM Sans
Nunito Sans
Plus Jakarta Sans
```

Use one primary typeface throughout the application.

Avoid:

- Excessive all caps
- Tiny labels
- Extremely heavy headings
- Dense numerical typography
- Too many font weights

## Hero Number

```text
1.85 L
```

Large and confident, but not oversized.

## Supporting Text

```text
of 2.70 L today
```

Quiet and secondary.

## Conversational Copy

```text
You're doing well.
```

```text
A little more water?
```

```text
Your bottle is getting low.
```

The application should sound like a friendly companion, not a health-monitoring system.

---

# 13. Hero Animated Bottle

The bottle is the primary visual component.

It should feel like a physical object rather than a technical visualization.

## Visual Characteristics

The bottle should include:

- Translucent body
- Soft water color
- Subtle glass reflection
- Physical cap
- Gentle shadow beneath the bottle
- Minimal measurement markings
- Natural water surface
- Optional subtle condensation
- Slight material imperfections where appropriate

Avoid excessive glow.

## SVG Architecture

Use responsive inline SVG.

```text
viewBox="0 0 200 400"
```

Layering:

```text
Bottle Shadow
      ↓
Bottle Body
      ↓
Liquid Clip Path
      ↓
Liquid Fill
      ↓
Water Surface
      ↓
Measurement Markings
      ↓
Glass Reflection
      ↓
Bottle Cap
```

## Bottle Body Bounds

```text
Ymin = 110
Ymax = 320
Span = 210px
```

## Liquid Height

```text
FillPercentage =
min(
    100,
    max(
        0,
        CurrentBottleVolume / BottleCapacity * 100
    )
)
```

```text
Yliquid =
Ymax - (210 * FillPercentage / 100)
```

The liquid must be clipped to the physical bottle body.

---

# 14. Bottle Animation

Animation should communicate physical movement.

## Drinking

When the user logs water:

1. Bottle tilts slightly.
2. Water surface responds.
3. Liquid level decreases.
4. Bottle settles back.
5. A subtle confirmation appears.

Target duration:

```text
600–1000ms
```

## Refilling

When the user refills:

1. Bottle moves subtly.
2. Liquid rises smoothly.
3. Water surface settles.
4. Bottle returns to rest.

The animation should feel like watching a real bottle fill.

## Idle State

The bottle should mostly remain still.

Optional:

- Very subtle water movement
- Occasional reflection movement

No continuous bouncing or floating.

---

# 15. Home Screen — Today

The Today screen should answer:

1. How much have I had today?
2. How much is left in my bottle?
3. Can I quickly log another drink?

## Recommended Composition

```text
Good afternoon

1.85 L
of 2.70 L today


             [ BOTTLE ]
             [         ]
             [  WATER  ]
             [  WATER  ]
             [_________]

          420 ml left


   +100 ml   +250 ml   +500 ml

            Custom

        ↻ Refill bottle
```

The background should be visually rich enough to avoid feeling like a white webpage.

The bottle can sit over a subtle organic ambient shape or tonal gradient.

Do not place the bottle inside a conventional card.

---

# 16. Daily Progress

Daily progress should be visible without dominating the interface.

Primary:

```text
1.85 L
of 2.70 L today
```

Optional small progress bar:

```text
████████████░░░░
```

Do not use a large circular progress ring on the Today screen.

The bottle remains the dominant visual representation.

---

# 17. Quick Drink Actions

Default:

```text
+100 ml
+250 ml
+500 ml
Custom
```

Buttons should:

- Have at least 44×44px touch area
- Use soft rounded corners
- Have strong text contrast
- Use subtle pressed states
- Feel tactile rather than glossy

Avoid putting every action into a floating card.

---

# 18. Refill Interaction

Primary action:

```text
↻ Refill bottle
```

Refilling must not increase Consumed Today.

It only changes:

```text
Current Bottle Volume
```

Confirmation:

```text
Bottle refilled
750 ml ready to drink
```

The visual transition should make the distinction obvious.

---

# 19. Drinking Glass Interaction

A secondary digital glass can be used for a more physical drinking interaction.

Example:

```text
Glass contains 250 ml
        ↓
Tap / drag to drink
        ↓
Glass empties
        ↓
250 ml added to consumption
```

The glass must remain secondary to the bottle.

---

# 20. History

History should feel like a calm timeline rather than a database.

Example:

```text
Today

10:42 AM    +250 ml
            Quick add

9:15 AM     +200 ml
            Glass

8:02 AM     Refilled
            750 ml


Yesterday

7:40 PM     +250 ml
            Quick add
```

Internal event sources:

```text
quick_add
glass
custom
refill
```

Visible labels should use friendly language.

---

# 21. Insights

Call the analytics area **Insights**, not Analytics or Statistics.

The goal is to help users notice patterns rather than judge performance.

Primary metrics:

```text
7-day average
1.92 L
```

```text
Days reached
5 / 7
```

Keep the number of metrics small.

## Seven-Day Chart

Use a simple vertical bar chart.

The target line should be subtle.

Do not use aggressive red/green performance colors.

Missing a target should never look like failure.

---

# 22. Why This Amount?

Use the conversational title:

```text
Why this amount?
```

Opening copy:

```text
Your hydration target isn't a universal number.

We estimate it using your age, sex, activity level and typical environment.
```

Show the reasoning progressively:

```text
Your baseline
      ↓
Activity adjustment
      ↓
Environment adjustment
      ↓
Estimated daily target
```

Detailed methodology should remain available for transparency.

Potential authoritative sources:

- Institute of Medicine / National Academies
- EFSA
- WHO

Do not present scientific citations as a wall of academic text.

---

# 23. Onboarding

Onboarding should feel like setting up a personal bottle.

## Screen 1 — Welcome

```text
Meet your water bottle.

A calmer way to keep track of drinking water.

[ Let's set it up ]
```

## Screen 2 — About You

Collect:

- Age
- Biological sex

Only collect information necessary for the hydration estimation.

## Screen 3 — Your Day

```text
How active are your typical days?

○ Mostly sitting
○ A little active
○ Fairly active
○ Very active
```

## Screen 4 — Environment

Ask about the user's typical environment using conversational language.

## Screen 5 — Choose Your Bottle

Show visual bottle previews:

```text
500 ml
750 ml
1 L
1.5 L
Custom
```

The bottle preview updates as capacity changes.

## Screen 6 — Choose Your Atmosphere

Let the user choose a visual theme:

```text
Ocean Mist
Sage Morning
Rose Water
Warm Sand
Midnight Pool
```

This should be optional and can be changed later.

## Completion

```text
Your bottle is ready.

Let's make staying hydrated feel a little easier.
```

---

# 24. Settings

Settings should remain simple.

## Bottle

- Bottle capacity
- Bottle appearance
- Measurement unit

## Appearance

- Theme
- Reduced motion
- Accessibility

## Notifications

- Reminder frequency
- Quiet hours
- Enable / disable reminders

## Data

- Export data
- Reset local data

Do not turn Settings into an administrative dashboard.

---

# 25. Navigation

Recommended primary navigation:

```text
Today
History
Insights
You
```

## Today

Current hydration state and bottle.

## History

Past drinking and refill events.

## Insights

Longer-term patterns.

## You

Bottle configuration, themes, preferences, accessibility, notifications and data.

The science explanation should be accessible from Today or Insights through:

```text
Why this amount?
```

---

# 26. Notifications

Notifications should feel like gentle reminders rather than alarms.

Avoid:

```text
You are behind your hydration target!
```

Prefer:

```text
Your bottle has been sitting for a while.
A drink might be nice.
```

or:

```text
Time for a little water?
```

Notifications should be infrequent, configurable, and user-controlled.

---

# 27. Accessibility

Target:

```text
WCAG 2.1 AA
```

## Touch Targets

Minimum:

```text
44 × 44 px
```

## Contrast

All important text must meet appropriate contrast requirements for the selected theme.

Do not rely solely on:

- Color
- Animation
- Bottle fill
- Icons

to communicate information.

## Screen Readers

Bottle state should have a textual representation:

```text
Bottle contains 420 milliliters of 750 milliliters.
```

Daily progress:

```text
You have consumed 1.85 liters of your 2.70 liter daily target.
```

---

# 28. Motion and Reduced Motion

Motion should communicate physicality rather than decoration.

Use animation for:

- Drinking
- Refilling
- Opening and closing interactions
- Small confirmations
- Theme transitions

Avoid:

- Constant floating objects
- Pulsing buttons
- Excessive spring animations
- Continuous decorative movement

Respect:

```css
prefers-reduced-motion
```

When enabled:

- Disable bottle tilt
- Disable wave animation
- Disable decorative movement
- Use short opacity and position transitions

---

# 29. Responsive Design

The application is a mobile-first PWA.

## Mobile

Recommended hierarchy:

```text
Greeting
↓
Daily consumption
↓
Bottle
↓
Bottle volume
↓
Quick actions
↓
Refill
```

The bottle should occupy the majority of the visual focus.

## Tablet / Desktop

Use additional whitespace rather than turning the application into a dashboard.

The bottle can remain centered while supporting information moves around it.

Do not simply scale every component upward.

---

# 30. Design Anti-Patterns

## Avoid AI-Generated Dashboard Aesthetics

Do not use:

- White canvas with blue cards everywhere
- Dark navy dashboard as the default
- Excessive glassmorphism
- Neon gradients
- Large glowing progress rings
- Dense KPI grids
- Excessive rounded rectangles
- Tiny uppercase labels everywhere
- Constant animations
- Overly technical language

## Avoid Clinical Aesthetics

Do not make the product resemble:

- Hospital software
- Clinical monitoring systems
- Medical records
- Calorie trackers
- Fitness performance dashboards

## Avoid Gamification Pressure

Do not use:

- Streak anxiety
- Failure states
- Aggressive red warnings
- Competitive leaderboards
- Excessive badges
- Celebration animations for every action

Hydration should feel like a normal part of the user's day.

---

# 31. Design Quality Bar

Every screen should pass these questions:

### Does it feel inviting?

The interface should make the user want to open it.

### Does the bottle remain important?

The bottle should remain the visual identity of the product.

### Does the interface feel comfortable?

There should be enough breathing room without creating an empty white canvas.

### Is the data understandable?

The distinction between daily consumption and bottle volume must remain obvious.

### Does it feel human?

Copy should be conversational and calm.

### Does it feel physical?

Bottle, water, glass, shadows and motion should suggest real objects.

### Is there unnecessary UI?

If a component exists only because dashboards usually have that component, remove it.

---

# 32. Overall Experience

The final experience should feel closer to:

```text
a beautiful physical water bottle
        +
a calm personal companion
        +
a quiet daily ritual
```

and less like:

```text
a health dashboard
        +
a fitness tracker
        +
a data analytics application
```

The guiding design question is:

> **Does this make drinking water feel easier and more pleasant?**

The product should feel **quietly useful rather than impressively complicated**.

It should have enough color and personality to feel alive, but enough restraint to remain calm.

The ideal impression is:

> **I like having this little thing around.**
