# Design Specification - Research-Based Hydration Tracker PWA

## 1. Product Philosophy & Core Concept

The **Hydration Companion** is designed to feel like a **physical water bottle brought to life digitally**, rather than a generic medical or fitness dashboard.

### Core Interaction Loop
```
See bottle level → Drink water → Bottle level drops → Daily progress increases → Refill bottle → Repeat
```

---

## 2. Fundamental Value Distinctions

To prevent user confusion, the application rigorously distinguishes between four distinct metrics:

| Metric | Example Value | Description | Visual Representation |
| :--- | :--- | :--- | :--- |
| **Daily Hydration Target** | `2.70 L` | Estimated total fluid recommendation for the day | Circular progress ring & text |
| **Consumed Today** | `1.85 L` | Sum of all drinking events logged today | Large numeric display & ring fill |
| **Current Bottle Volume** | `420 ml` | Physical water remaining inside the bottle | **Animated SVG Bottle Fill Level** |
| **Bottle Capacity** | `750 ml` | Maximum volume the physical bottle holds | Bottle container scale & height |

> [!IMPORTANT]
> **Physical Bottle Fill Level** represents **Current Water Remaining in Bottle**, NOT daily target progress. Daily target progress is rendered separately in the circular progress ring.

---

## 3. Design System & Visual Identity

### Color Palette

#### Primary Theme (Ocean Blue)
- **Background Slate**: `#0f172a` (Dark Slate) / `#f1f5f9` (Light Slate)
- **Surface Card**: `rgba(30, 41, 59, 0.7)` with `backdrop-filter: blur(12px)`
- **Primary Water Accent**: `#0ea5e9` (Sky Blue)
- **Primary Hover**: `#0284c7` (Deep Sky)
- **Liquid Gradient Start**: `#38bdf8` (Cyan Blue)
- **Liquid Gradient End**: `#0284c7` (Ocean Blue)
- **Success Green**: `#10b981` (Emerald)

#### Customizable Bottle Themes
1. **Ocean Blue**: `#38bdf8` → `#0284c7`
2. **Emerald Mint**: `#34d399` → `#059669`
3. **Sunset Coral**: `#fb7185` → `#e11d48`
4. **Midnight Obsidian**: `#818cf8` → `#4f46e5`

---

## 4. Hero Animated SVG Water Bottle Component

The physical bottle visualizer is rendered via responsive inline SVG (`viewBox="0 0 200 400"`).

### Liquid Height Mapping Formula
Given bottle body bounds from $Y_{min} = 110$ to $Y_{max} = 320$ (span = 210px):

$$\text{FillPercentage} = \min\left(100, \max\left(0, \frac{\text{CurrentVolume}}{\text{Capacity}} \times 100\right)\right)$$

$$Y_{\text{liquid}} = Y_{max} - \left(210 \times \frac{\text{FillPercentage}}{100}\right)$$

### SVG Layering Architecture
```
┌─────────────────────────────────────────┐
│ Stainless / Glass Cap (Y=20 to Y=45)    │
├─────────────────────────────────────────┤
│ Outer Glass Bottle Shell & Glow Filter  │
│ ┌─────────────────────────────────────┐ │
│ │ ClipPath: #bottleBodyClip           │ │
│ │ ┌─────────────────────────────────┐ │ │
│ │ │ Animated Liquid Fill Rect       │ │ │
│ │ │ Wave Motion Path (wave-animation)│ │ │
│ │ └─────────────────────────────────┘ │ │
│ └─────────────────────────────────────┘ │
│ Measurement Scale Markings (500ml, 1L)  │
│ Glass Reflection Highlight Overlay      │
└─────────────────────────────────────────┘
```

---

## 5. User Interface & Screen Architecture

### 1. Onboarding Flow
- **Screen 1 (Welcome)**: Introduction to the hydration companion.
- **Screen 2 (Age & Sex)**: Collects age (18+) and biological sex for IOM baseline determination.
- **Screen 3 (Activity & Environment)**: Selects activity level (Sedentary, Light, Moderate, High) and typical environment.
- **Screen 4 (Bottle Setup)**: Interactive bottle capacity picker (500ml, 750ml, 1L, 1.5L, Custom).

### 2. Home Screen
- **Daily Progress Header**: Displays `Consumed Today / Target`.
- **Hero Animated Bottle**: Live SVG representation of physical water level.
- **Secondary Goal Progress Ring**: Circular SVG progress bar showing % of daily target achieved.
- **Quick Action Grid**: One-tap quick drink buttons (`+100ml`, `+200ml`, `+250ml`, `+500ml`, `Custom`).
- **Refill Button**: Prominent `↻ Refill Bottle` action button.
- **Glass Vessel Visualizer**: Secondary drinking interaction showing interactive glass emptying animation.

### 3. Drinking History Screen
- Grouped chronological list of all drink and refill events by ISO date (`YYYY-MM-DD`).
- Identifies event source (`quick_add`, `glass`, `custom`, `refill`).

### 4. Hydration Analytics / Statistics Screen
- Metrics: 7-Day Average (L), Goal Completion Rate (%).
- 7-Day Pacing SVG Bar Chart with goal completion color coding.

### 5. "Why this target?" Science & Transparency Screen
- Explains how the user's target was calculated step-by-step.
- Itemized breakdown of baseline dietary reference values and activity adjustments.
- Primary source academic citations (Institute of Medicine, EFSA, WHO).

### 6. Settings Screen
- Bottle capacity & theme customization.
- Data export (JSON backup) and local database reset.

---

## 6. Accessibility & Motion Guidelines

- **WCAG 2.1 AA Compliance**: High-contrast text labels alongside visual graphics.
- **Touch Target Sizing**: Minimum 44×44px interactive touch areas.
- **Motion Safety**: Respects `prefers-reduced-motion` system settings by disabling wave animations for sensitive users.
