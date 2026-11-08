# DeepShield Design Guidelines

## 1. Design Direction

**Theme:** Dark by default, with Light mode available.

**Visual style:** Minimal, structured, and professional.

DeepShield is a digital content analysis platform. Its interface should make technical information easy to inspect without overwhelming the user.

The design should prioritize:
- Clear visual hierarchy.
- Readable typography.
- Consistent spacing.
- Restrained use of color.
- Minimal decoration.
- Accessible controls and status indicators.

Avoid unnecessary gradients, excessive shadows, decorative animations, and crowded layouts.

## 2. Color System

### Dark Theme

| Element | Color |
|---|---|
| Primary background | `#0B0F19` |
| Secondary background / cards | `#0F172A` |
| Primary text | `#E5E7EB` |
| Secondary text | `#9CA3AF` |
| Borders | `#1F2937` |
| Primary accent | `#60A5FA` |

### Light Theme

| Element | Color |
|---|---|
| Primary background | `#F8FAFC` |
| Secondary background / cards | `#FFFFFF` |
| Primary text | `#0F172A` |
| Secondary text | `#64748B` |
| Borders | `#E2E8F0` |
| Primary accent | `#2563EB` |

### Status Colors

Use status colors consistently and never rely on color alone to communicate meaning.

- Green: verified or positive indicator.
- Amber: inconclusive or requires attention.
- Red: suspicious or negative indicator.
- Blue: informational or currently selected state.

A status color must represent the actual result returned by the analysis module.

## 3. Typography

**Preferred font:** Montserrat.

Use a locally hosted font file when available. Otherwise, use a reliable system sans-serif fallback.

```css
font-family: "Montserrat", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
```

Typography should follow a clear hierarchy:

- Page headings: prominent, medium-to-bold weight.
- Section headings: medium weight.
- Body text: regular weight.
- Supporting text: smaller and muted.
- Metrics and result values: clear, readable, and consistently formatted.

Avoid unnecessarily small text, excessive font-weight variation, and long paragraphs inside cards.

## 4. Layout and Spacing

Organize content into clearly defined sections and modules.

- Use consistent horizontal alignment.
- Maintain predictable spacing between sections.
- Keep cards visually simple.
- Use whitespace to separate information.
- Keep related controls close to their corresponding inputs.
- Avoid unnecessary nested cards.
- Ensure layouts adapt to smaller screens.

Analysis pages should prioritize the submitted content, processing status, and results rather than decorative elements.

## 5. Components

### Navigation
- Consistent navigation across all pages.
- Clear active-page indication.
- Accessible theme toggle.
- Branding without unnecessary version labels or badges.

### Cards
- Subtle background contrast.
- Minimal borders.
- Little or no shadow.
- Consistent padding and corner radius.

### Buttons
- Clear action labels.
- Consistent sizing.
- Visible hover, focus, disabled, and loading states.
- Primary actions should stand out without dominating the page.

### Forms
- Clearly labelled input fields.
- Visible validation messages.
- Appropriate file-format and size guidance.
- Clear distinction between optional and required inputs.

### Results
- Verdict and confidence displayed prominently.
- Supporting evidence grouped by analysis category.
- Metrics should include labels and, where necessary, explanations.
- Missing or unavailable measurements must not be presented as zero or as successful verification.

## 6. Motion and Transitions

Animations should be restrained and purposeful.

- Use short fade or slight-position transitions for content appearance.
- Avoid bouncing, elastic movement, and excessive motion.
- Keep page scrolling natural.
- Respect reduced-motion preferences.
- Do not animate values in a way that could imply a changing or fabricated analysis result.

Use CSS transitions and animations where possible. Additional animation libraries should only be introduced when a specific requirement justifies them.

## 7. Charts and Data Visualization

- Prefer simple charts with clear labels.
- Use consistent stroke widths.
- Avoid unnecessary decorative fills.
- Provide legends and units where needed.
- Ensure chart colors work in both themes.
- Do not display illustrative or placeholder values as actual forensic measurements.

## 8. Accessibility and Responsiveness

- Maintain readable contrast in both themes.
- Support keyboard navigation.
- Provide visible focus states.
- Use descriptive labels for controls.
- Include accessible names for icon-only buttons.
- Avoid communicating important information through color alone.
- Ensure the application works on desktop, tablet, and mobile screens.

## 9. Design Principle

The interface should feel like a focused digital analysis workspace: restrained, readable, consistent, and trustworthy.

Functionality and clarity take priority over visual decoration.