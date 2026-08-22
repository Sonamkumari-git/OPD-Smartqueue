# OPD SmartQueue — Interface Direction

## Three directions considered

| Theme Name | Very Brief Intro | Probability |
|---|---|---:|
| Clinical Flight Deck | A calm operational interface inspired by clinical monitoring and aviation dashboards. It makes the live queue legible under time pressure without feeling cold or alarmist. | 0.07 |
| Humanist Care Ledger | A warm, editorial healthcare product shaped by paper-like surfaces and gentle tonal depth. It emphasizes reassurance and humane communication for patients. | 0.04 |
| Municipal Signal System | A civic-service visual language using strong wayfinding, public-signage geometry, and practical information hierarchy. It would feel robust and accessible in a high-volume hospital context. | 0.09 |

## Chosen direction: Clinical Flight Deck

### Design Movement

**Clinical systems design with restrained neo-grotesque typography.** The interface borrows the clarity of an operations console while using a warm, human palette to keep queue information reassuring rather than intimidating.

### Core Principles

1. **Live state over decoration:** Current token, queue movement, doctor availability, and time estimates take precedence over ornamental content.
2. **Layered reassurance:** Every critical metric includes a concise human explanation so patients understand what it means and what to do next.
3. **Operational hierarchy:** Role-specific workspaces share a visual grammar but surface only the actions and information appropriate to the user’s role.
4. **Measured density:** Dense clinical information is arranged in calm horizontal bands, preserving scanability on both a phone and a desktop workstation.

### Color Philosophy

The visual environment uses **mineral navy** as a trustworthy operational anchor, **surgical teal** as the recognizable live-state signal, and **warm porcelain** as the primary canvas. Urgent states use muted saffron or restrained coral rather than saturated warning colors, ensuring alerts are clear without creating needless anxiety.

### Layout Paradigm

The application is arranged as an **asymmetric care rail**: a compact navigation rail establishes role and context, a broad live-work area carries the active queue, and a slender intelligence column surfaces status, connection health, notifications, and prediction context. On mobile, the care rail collapses into a top context bar followed by stacked action bands.

### Signature Elements

1. A **queue pulse line** appears in active queue cards, representing movement and live WebSocket connectivity.
2. **Segmented token capsules** visually bind the department code and sequential number without relying on generic pills everywhere.
3. **Confidence bands** pair wait estimates with a small range marker and plain-language caveat, reinforcing that predictions are estimates.

### Interaction Philosophy

Interactions are direct and verifiable. State-changing actions such as calling a patient, recording vitals, or completing a consultation provide immediate feedback, a concise confirmation, and an updated operational state; destructive or consequential actions require clear confirmation.

### Animation

Motion is purposeful and under 300 ms. Live updates softly sweep along the queue pulse line and refresh the changed metric only; panels use opacity and a subtle 0.98-to-1 scale transition. Urgent calling events may use a single restrained highlight pulse. All non-essential motion respects `prefers-reduced-motion`.

### Typography System

**Manrope** provides the primary utility and numeric system for its open counters and clear dashboards. **Fraunces** is reserved for high-value patient reassurance moments, such as waiting-time guidance and care-status explanations. Headlines use Manrope 700/800, section labels use Manrope 600 with letter spacing, and patient-facing reassurance uses Fraunces 500 sparingly.

### Brand Essence

**OPD SmartQueue is a real-time, privacy-conscious queue and workflow console for hospital teams and patients who need an understandable path through an OPD visit.**

Personality: **composed, precise, humane.**

### Brand Voice

Headlines are factual and calming, CTAs are explicit operational verbs, and microcopy avoids false certainty.

> “Your place in the queue, made clear.”

> “Queue moving. Your return window is approaching.”

### Wordmark & Logo

The mark is a bold, text-free **queue pulse**: three offset vertical arcs converging toward a central care point, suggesting ordered movement and vital monitoring. The wordmark uses a deliberately spaced Manrope treatment in implementation, with the symbol leading at a readable size.

### Signature Brand Color

**Queue Teal — `#0F8F83`** is the ownable live-state color used for the pulse line, primary actions, and active navigation cues.

## Style Decisions

- Operational dashboard numerals, token IDs, queue counts, and metrics use **Manrope**, while Fraunces remains for patient-facing reassurance or explanatory content only.
- Every live queue surface carries an OPD SmartQueue motif: a Queue Teal pulse rail, segmented token treatment, or confidence band that visualizes estimate uncertainty.
- Healthcare imagery remains bright, quiet, and architectural, but it is always subordinate to authoritative live queue state and precise operational scan bands.
