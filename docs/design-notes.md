# Design notes

Short version: the palette and marks come directly from LPU's own logo, not a generic
template, and the typography was chosen for legibility across three scripts, not for looks.
This file is the reasoning, kept separate from the README so the README stays about running
the project.

## Where the colors come from

`frontend/src/assets/brand/lpu-logo.png` and `lpu-emblem.png` are cropped and re-exported from
the logo you provided. The palette was sampled from the actual pixels of that file, not chosen
from a swatch:

| Token | Hex | Source |
|---|---|---|
| `--color-orange` | `#EF7F1A` | sampled from the logo's orange panels |
| `--color-ink` | `#2B2A29` | sampled from the logo's charcoal wordmark |
| `--color-orange-deep` | `#A8520C` | a darker step of the same hue, used for text and links on white so contrast clears WCAG AA (4.98:1 on the page background, 6.95:1 on white) |
| `--color-paper` | `#FAF7F2` | a very light warm off-white close to the logo's circular background, used as the page background instead of pure white |

Everything else (success/danger/info, hairline greys) is a small supporting palette built to sit
quietly next to that orange rather than compete with it — the accent is spent in one place
(primary buttons, active states, citation markers) rather than spread across gradients or
decoration.

## Why not the usual AI-generated look

A few visual patterns show up by default whenever a design brief doesn't pin down a direction:
warm cream background with a serif display face and a terracotta accent near `#D97757`; a
near-black background with one neon accent; the "SaaS card kit" of identical rounded cards with
the same soft grey shadow on everything; tracked-out uppercase eyebrow labels; meta strings
joined with middle dots. None of that was appropriate here — LPU already has a real, specific
brand, and the brief's own colors should win over a default. So:

- The accent orange is a saturated, fully-opaque brand color, not a muted terracotta, and it's
  paired with a humanist **sans-serif**, not a high-contrast serif display.
- Cards use flat panels with 1px hairline borders and a small, purposeful shadow only on hover —
  not a blanket `border-radius` + soft-shadow treatment applied identically everywhere. A chat
  bubble, a source-citation row, and a drive card each look different because they hold different
  kinds of content.
- Numbered markers (`[1]`, `[2]`) on citations are the one place this project genuinely uses
  sequence numbering, because the content really is enumerated — each number maps to one actual
  retrieved passage the person can expand. That's different from decorative `01 / 02 / 03` labels
  on non-sequential content.
- No tracked-out uppercase labels, no em-dash-joined meta strings, no arrow appended to every
  button. Buttons say exactly what they do ("Sign in", "Sync changed documents").

## Type

Three scripts have to render side by side and equally well: English, Hindi (Devanagari) and
Punjabi (Gurmukhi). Rather than pick a display face for Latin and let the other two scripts fall
back to a mismatched system font, the whole UI uses one variable font family per script, all from
the same type family so weight and proportions feel consistent:

- **Source Sans 3 Variable** for Latin text — a humanist sans built for dense UI text, not a
  headline face pressed into service as body copy.
- **Noto Sans Devanagari Variable** and **Noto Sans Gurmukhi Variable** for Hindi and Punjabi —
  purpose-built for those scripts, correctly shaping conjuncts and vowel signs where a generic
  fallback font would not.

Headings use the same family at a heavier weight rather than a second display typeface, since
this is a campus utility, not a marketing site — the goal is a calm, official help-desk register,
closer to a well-run enquiry counter than a startup landing page.

## Layout

The assistant picker (home page) is two clearly-labelled panels rather than one big hero with a
single CTA, because the person's actual first decision is "which assistant do I need" — the UI
should ask that directly instead of decorating a generic landing pattern. The chat screen keeps
messages in a single, left-aligned column capped at a comfortable reading width, with sources
shown as an expandable, numbered list directly under the answer that produced them — grounding is
this app's entire value proposition, so the citations are a first-class, visible part of every
assistant turn, not a footnote.
