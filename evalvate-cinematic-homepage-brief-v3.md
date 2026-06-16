# Evalvate — Cinematic Homepage v3
### Production-Ready Implementation Brief for Antigravity / Codex / Claude Code

This document supersedes v1 and v2 — it folds in the storyboard ("Five Faces") from v2 and adds everything an agent needs to build without further clarification: visual references, camera/sound rules, exact component architecture, GSAP timing maps, Three.js spec, real Higgsfield + Runway prompts, and performance/mobile strategy.

---

## 0. VISUAL MOOD BOARD

**Reference works (study the *restraint*, not the budget):**
- Apple Vision Pro launch film — pacing, silence, single-subject focus
- Apple AirPods Pro page — scroll-pinned product reveal mechanics
- Nike "Dream Crazy" — montage rhythm, cut-to-music structure
- Rivian R1T website — dark, premium, confident typography over real product
- Arc Browser homepage — type-driven storytelling, playful-but-precise motion
- Linear homepage — restraint, dark UI, no wasted motion
- *Interstellar* cinematography (Hoyte van Hoytema) — natural light, shallow depth of field, quiet compositions
- *The Social Network* office scenes — corporate realism, cool-neutral grade, real people in real rooms
- *Succession* corporate interiors — wealth conveyed through stillness and quality of light, not opulence

**Keywords (every visual decision should be checkable against this list):**
`Cinematic` · `Photorealistic` · `Natural skin` · `Shallow depth of field` · `Corporate realism` · `Premium` · `Luxury` · `Quiet` · `Restrained`

**Explicitly NOT:** `Futuristic` · `Sci-fi` · `Cyberpunk` · `Neon` · `Holographic` · `Glowing data UI`

---

## 1. DO NOT

This list is as important as anything else in this document. An agent left unguided will reach for every item below — each one actively damages the "premium brand film" feeling and pushes the page toward "AI demo reel."

```
DO NOT:
- Use glassmorphism anywhere (no frosted-glass cards, no backdrop-blur panels)
- Use neon colors or glowing edges on UI elements
- Use futuristic "holographic" or sci-fi data visualizations
- Use floating 3D shapes, cubes, spheres, or abstract geometry as decoration
- Use particle effects, sparkles, or "energy" animations
- Use stock-photo business imagery (handshakes, generic laptops, fake meeting rooms)
- Use generic SaaS landing page sections (icon-grid "features," pricing tables with checkmarks, testimonial carousels with stock avatars)
- Invent fake dashboards, fake charts, or fake metrics for the product reveal
- Over-animate buttons (no rainbow gradients, no constant shimmer/shine sweeps)
- Generate humans with plastic skin, symmetrical "AI faces," extra fingers, or uncanny expressions
- Use robotic, linear (non-eased) motion anywhere
- Add motion that doesn't serve the story — if a tween can be removed without weakening the emotional beat, remove it
```

---

## 2. CAMERA LANGUAGE

```
CAMERA RULES:
- No drone shots, no aerial reveals
- No spinning/orbiting camera moves
- No "cinematic swoop" transitions between scenes
- No excessive parallax (max 2 depth layers per scene, ever)

USE:
- Slow dolly (lateral movement, max ~5% of frame width across a scene)
- Slow push-in (max ~6% scale change across a scene)
- Static compositions (most scenes should NOT move the "camera" at all)
- Shallow depth of field (subject sharp, background soft)
- Human eye-level framing (camera height = seated/standing eye level, never looking down or up at subjects)

The camera should feel invisible — like the page itself is calm, and the story
is what moves, not the lens.
```

Applied to this build: Act 1's five clips are static or near-static (≤4% push-in). Act 3's Maya clip is the only one with actual subject movement (standing). The Three.js iris in Act 3 is the *only* "non-physical-camera" effect in the entire experience — its rarity is what makes it land.

---

## 3. SOUND DESIGN MASTER SHEET

| Act | Cue | Description | Trigger |
|---|---|---|---|
| 0 | Opening tone | Single low sustained string note, very quiet, slight volume swell across the act | On mount, loops/sustains until Act 1 |
| 1 | Five pulses | One soft low piano note or muted kick per hard-cut (5 total), ascending in volume and slightly tightening in spacing — never a literal "heartbeat" sample | `ScrollTrigger onEnter` per sub-range |
| 2 | Five tones | Soft bell/pad tones, ascending in pitch (whole-tone steps), one per character pairing, Maya's (5th) is the clearest/highest | `ScrollTrigger onEnter` per pairing |
| 3 | Rising tension → release | A single sustained tone rises in pitch/intensity through the act, blooming into a warm full chord exactly as the iris fully opens | Tied to `uIrisRadius` progress (0→1 maps to pitch/volume ramp; chord triggers at `uIrisRadius >= 0.95`) |
| 4 | Warm orchestral release | A short (4–6s), warm string/pad swell, plays once on first entry to this act, then settles to a low sustained pad underneath card animations | `IntersectionObserver`, fires once |
| 5 | Minimal piano | Simple, sparse piano motif (3–5 notes), unhurried, resolves to a held final chord and silence | `IntersectionObserver`, fires once |

**Global rules:**
- All audio is **opt-in** (muted by default, small toggle from Act 0 onward).
- Total combined audio asset size: target **<1.5MB** (short loops/stems, not a continuous music file — build the score from small reusable pieces triggered at the right moments).
- No audio ever autoplays with sound on page load — opt-in only, and even then Act 0's tone should fade in over ~1s, never start abruptly.

---

## 4. REAL PRODUCT SCREENS — NO INVENTED UI

```
PRODUCT VISUALS RULE:

Use actual Evalvate product screenshots/recordings wherever the product
is shown (Act 4 and the Act 4 "glimpse" in Act 3's iris).

DO NOT invent dashboards, charts, scores, or metrics.
DO NOT design a new UI "for the homepage."

Use:
- A real recorded screen capture (or sequence of screenshots) of an
  actual Evalvate mock-interview session in progress
- A real screenshot of an actual feedback/report screen, with real
  (or realistic anonymized) scores
- A real screenshot of the resume analysis view, if one exists

If a screen doesn't exist yet in the product, build the homepage
section to accept a placeholder image with the EXACT dimensions and
crop of the real screen, clearly commented in code
(`{/* TODO: replace with real screen capture, 1920x1080, .png */}`),
rather than generating a fictional one.
```

**For this build:** Acts 4's central card and the secondary cards should be built as **image/video containers with the real product's existing visual style already established** (reuse the dark indigo/violet/cyan UI tokens from the live landing page already built — that *is* the real product's design system, so even placeholder captures will match). Treat the existing "live mock interview card" component (already built, with the typewriter question + metric chips) as **the real UI**, not a homepage invention — it should be screen-recorded from the actual running app for the final asset, with the coded version serving as the interim/fallback render.

---

## 5. COLOR & TYPOGRAPHY SYSTEM

Reuse the existing Evalvate brand system exactly — no new tokens for the cinematic sections (consistency between "the film" and "the product" is part of what makes the transition in Act 3 land).

```css
--bg:        #06060A   /* cinematic base, slightly deeper than product's #08080E */
--surface:   #0F0F1A
--border:    rgba(255,255,255,0.08)
--text:      #F0F0FF
--muted:     #7A7A9A
--indigo:    #6366F1
--violet:    #8B5CF6
--cyan:      #22D3EE
--green:     #34D399
```

**Cinematic-scene grade** (applied to all five Act 1 clips + both Maya clips, via a single shared CSS class — this is the "film LUT"):
```css
filter: contrast(1.05) saturate(0.85) sepia(0.04);
```
This pulls slightly toward the cool-neutral, desaturated "corporate realism" look from the mood board (Social Network / Succession) without any color cast that would clash with the indigo/violet brand palette in Acts 3–5.

**Typography:**
- Display: `Sora` (700/800) — all headlines, Act overlays
- Body: `Inter` (400/500) — captions, subheads
- Data/mono: `JetBrains Mono` (400/500) — live stat, scroll-progress label, Act 1 caption

**Type scale for cinematic overlays:**
| Role | Size | Weight |
|---|---|---|
| Act 0/5 headline | `clamp(2rem, 5vw, 3.5rem)` | Sora 800 |
| Act 1 caption | `clamp(0.8rem, 1.2vw, 0.95rem)` | JetBrains Mono 500 |
| Act 2 focus lines | `clamp(1.25rem, 3vw, 2rem)` | Sora 700 |
| Act 3 transition lines | `clamp(1.5rem, 3.5vw, 2.5rem)` | Sora 700 |
| Act 4 captions | `clamp(1rem, 2vw, 1.4rem)` | Sora 600 |
| Act 5 subhead | `1rem` | Inter 400 |

---

## 6. SITE ARCHITECTURE / FILE STRUCTURE

```
/app
  page.tsx                        — assembles all acts; mounts master ScrollTrigger
  layout.tsx                      — fonts, global providers

/components/cinematic
  CinematicCursor.tsx              — custom cursor (dot / ring / crosshair states)
  ConfidenceMeter.tsx               — scroll progress bar, right edge
  SoundToggle.tsx                   — global mute/unmute, persists via context
  ActZero.tsx
  ActOne.tsx                        — Five Faces montage
  ActTwo.tsx                        — Five Minds typographic field
  ActThree.tsx                      — Maya stands + iris shader
  ActFour.tsx                       — product reveal (real screens)
  ActFive.tsx                       — resolution + CTA + footer

/lib/cinematic
  useScrollTimeline.ts              — master GSAP timeline, matchMedia-aware
  irisShader.ts                     — vertex + fragment shader source (GLSL strings)
  audioSprites.ts                   — Web Audio setup, sprite map, play() helper
  scrollVelocity.ts                 — tracks scroll delta for Act 3 chroma boost

/public/cinematic
  /video
    char1-overpreparer.mp4 (+.webm, +poster.jpg)
    char2-mask.mp4
    char3-veteran.mp4
    char4-exhausted.mp4
    char5-maya-waiting.mp4
    char5-maya-standing.mp4
  /image
    char5-maya-relieved.jpg
    act3-iris-product-still.jpg     — blurred still of Act 4 hero card, for shader uniform
    act4-hero-screen.png            — real product screenshot, mock interview session
    act4-report-screen.png          — real product screenshot, feedback report
    act4-resume-screen.png          — real product screenshot, resume analysis (if available)
  /audio
    pulse-1.mp3 ... pulse-5.mp3      — Act 1 cut hits
    tone-1.mp3 ... tone-5.mp3         — Act 2 pairing tones
    rise.mp3                          — Act 3 rising tension
    release.mp3                       — Act 4 orchestral swell
    piano-outro.mp3                   — Act 5 motif
    open-string.mp3                   — Act 0 sustained tone
```

---

## 7. SCENE HIERARCHY & GSAP TIMELINE MAP

One master timeline (or one ScrollTrigger per act with carefully matched `start`/`end` percentages of total document height). All percentages below are of **total page scroll distance**.

| Scroll % | Act | Pinned? | Key animations |
|---|---|---|---|
| 0–8% | **Act 0** — Cold Open | No | Wordmark fade-in (0→1, 1.2s); breathing-light scale/opacity loop (continuous); live-stat fade-in at 4% |
| 8–34% | **Act 1** — Five Faces | Yes (~200vh) | 5 sub-ranges (~5.2% each): hard-cut video swap, 1.00→1.03 scale push-in per clip, audio pulse on each `onEnter`; caption fade-in during sub-range 5 |
| 34–54% | **Act 2** — Five Minds | Yes (~180vh) | 5 sequential steps (~4% each, slight overlap): thumbnail scale 0.85→1.15 + blur 4px→0 + opacity 0.3→1; text line opacity 0→1→0 per step; previous thumbnail settles to opacity 0.6; step 5 holds, then thumbnails 1–4 → opacity 0 |
| 54–70% | **Act 3** — The Shift | Yes (~150vh) | Maya-standing video `currentTime` scrubbed 0→duration across 0–40% of act; iris `uIrisRadius` 0→1.4 across 40–100% of act; `uChroma` 0→0.3→0 peaking at 70%; text overlays at 0%, 40%, 75% |
| 70–92% | **Act 4** — Product Reveal | Yes (~200vh) | Central card: typewriter + 3 metric bars animate on first `IntersectionObserver` entry; 3 secondary cards stagger in (`opacity 0→1, y 40→0, rotateX 8°→0`, stagger 0.12s, `back.out(1.2)`) |
| 92–100% | **Act 5** — Resolution | No | Background color crossfade `#06060A → #0E0E1C`; breathing-light reappears (warm variant); headline/CTA fade+rise; Maya-relieved thumbnail: fade in → hold 4s → fade out, once |

**Confidence meter:** `ConfidenceMeter` height bound to overall page scroll progress (`0–100%` across the entire 0–100% range above), independent of individual act pins.

---

## 8. THREE.JS REQUIREMENTS (Act 3 only)

- One `<canvas>`, one `WebGLRenderer`, one orthographic camera, one full-screen `PlaneGeometry`, one custom `ShaderMaterial`.
- Uniforms: `uIrisRadius` (float, 0→1.4), `uChroma` (float, 0→0.3→0), `uProductTex` (sampler2D, `act3-iris-product-still.jpg`), `uResolution` (vec2).
- Fragment shader: pixels within `uIrisRadius` of center sample `uProductTex` with RGB-channel offset by `uChroma` and a blur amount proportional to `(1 - uIrisRadius)`; pixels outside render `#06060A`.
- Lazy-init when Act 2 reaches ~80% scroll progress; `dispose()` geometry, material, and renderer context once Act 3 is fully scrolled past.
- Velocity boost: `uChroma`'s target gets `+ (clamp(abs(scrollVelocity), 0, 1) * 0.1)` — see `scrollVelocity.ts`.

No other Three.js, no Spline, no WebGL elsewhere on the page.

---

## 9. HIGGSFIELD ASSET GENERATION PROMPTS

Generate each as: **(1)** a reference still (image generation), **(2)** image-to-video using that still. All clips: 16:9, target 1080p source → export 720p H.264 + WebM, <2.5MB each, 3–5 seconds, seamless loop where noted.

**Shared style suffix** (append to every prompt below):
> *"Cinematic photography, natural skin texture, shallow depth of field, soft directional daylight from camera-left with practical overhead office light fill, cool-neutral color grade, corporate realism in the style of The Social Network and Succession, premium and quiet — not futuristic, not sci-fi, no neon, no glowing UI, no studio backdrop. Static or near-static camera, human eye-level framing."*

---

**1. The Over-Preparer**
> Medium shot of a person in their early twenties wearing a slightly rumpled blazer, seated in a modern corporate waiting area with neutral upholstered chairs. They hold a small stack of printed notes, eyes flicking down to the page and back up, lips moving subtly as if rehearsing silently under their breath. [shared style suffix]
> *Video motion:* subtle, repeating — glance down, glance up, slight lip movement, on a loop. No camera movement.

**2. The Mask**
> Medium shot of a person in their late twenties/early thirties wearing a sharp, well-tailored suit, seated with composed posture, holding a phone. Their thumb scrolls slowly, then pauses for a beat too long; their jaw tightens almost imperceptibly before relaxing again. [shared style suffix]
> *Video motion:* slow scroll-stutter-pause-jaw cycle, on a loop. No camera movement.

**3. The Veteran**
> Medium shot of a person in their mid-forties in simple, well-worn professional attire, seated with a calm but slightly weary expression. They hold a pen, tapping it gently against their knee; the tapping slows and stops, and they exhale quietly. [shared style suffix]
> *Video motion:* pen-tap rhythm slowing to a stop, then a slow exhale, on a loop. No camera movement, very slow push-in (≤3%) across the clip.

**4. The Exhausted**
> Medium shot of a person in their late twenties with visible tiredness — slight shadows under the eyes, hair slightly less composed — seated, holding a coffee cup. They take a long, slow exhale and briefly rub their eyes with the back of one hand before resting it back down. [shared style suffix]
> *Video motion:* one long exhale + eye-rub gesture, then stillness, loop returns to start smoothly. No camera movement.

**5a. The Lead "Maya" — Waiting**
> Medium shot of a person in their mid-twenties with an approachable, ordinary, relatable appearance — neutral professional attire, nothing flashy — seated, hands resting in their lap. They glance toward something off-frame to the right (an implied door), then look down at their hands, then look up again, holding this final upward gaze. [shared style suffix]
> *Video motion:* glance right → glance down → glance up, ending on a held, steady upward gaze (this final frame is the freeze-frame used in Act 2). No camera movement, very slow push-in (≤2%) across the clip.

**5b. The Lead "Maya" — Standing**
> *Generate from the same reference still as 5a, same framing and lighting.* The person rises from their seated position, straightens their posture, and takes one step forward toward the right edge of frame (toward the implied door), maintaining a steady, composed expression with a flicker of resolve. [shared style suffix]
> *Video motion:* stand → straighten → one step, ending mid-stride (this clip's `currentTime` is scrubbed directly via scroll, not played at normal speed). Camera remains static; subject moves within frame.

**5c. The Lead "Maya" — Relieved (static image sufficient)**
> *Generate from the same reference still as 5a/5b, same framing and lighting, different expression direction.* The same person, now with a relaxed posture and the faint trace of a relieved smile, soft even lighting, calm expression. [shared style suffix]
> *Output:* single still image, no video needed.

---

## 10. RUNWAY FALLBACK PROMPTS

If Higgsfield output for any clip shows artifacts (warped hands, flickering, inconsistent lighting), regenerate that clip via Runway Gen-3 image-to-video using the **same reference still** with these condensed prompts (Runway responds better to shorter, motion-focused prompts):

| Clip | Runway motion prompt |
|---|---|
| 1. Over-Preparer | "Subtle repeating motion: eyes glance down to papers and back up, lips move slightly. Camera static." |
| 2. The Mask | "Subtle motion: thumb scrolls on phone, pauses, jaw tightens slightly then relaxes. Camera static." |
| 3. Veteran | "Subtle motion: pen taps against knee, slows to a stop, quiet exhale. Camera static, very slow push-in." |
| 4. Exhausted | "Subtle motion: long exhale, hand rubs eyes briefly, returns to rest. Camera static." |
| 5a. Maya waiting | "Subtle motion: glance right, glance down, glance up, hold steady gaze. Camera static, very slow push-in." |
| 5b. Maya standing | "Person stands up from seated position, straightens, takes one step forward. Camera static." |

For all Runway generations: set motion strength to **low-to-medium** (high motion strength is the most common cause of warping in single-character portrait clips).

---

## 11. LOADING STRATEGY

1. **First paint (<500KB):** Act 0 only — text, breathing-light CSS gradient, noise texture. No video, no JS framework dependencies beyond what's needed for the fade-in.
2. **GSAP + ScrollTrigger:** loaded via dynamic `import()`, `strategy="afterInteractive"` — not blocking first paint.
3. **Act 1 videos:** clip *n* and clip *n+1* only ever have `src` set at once (preload-next pattern); clip *n-1*'s `src` is removed once its sub-range ends. Poster images shown before each clip's `src` resolves.
4. **Act 2 thumbnails:** use the same `*-poster.jpg` files already loaded for Act 1 — zero new requests.
5. **Three.js (Act 3):** code-split into its own chunk, dynamically imported only when Act 2 reaches ~80% progress; `act3-iris-product-still.jpg` preloaded slightly earlier.
6. **Act 4 real product screens:** lazy-loaded via `IntersectionObserver`, `next/image` with explicit dimensions to avoid layout shift.
7. **Audio sprites:** loaded lazily, only after the user interacts with `SoundToggle` (i.e., never downloaded at all for the ~majority of users who never enable sound).

---

## 12. MOBILE STRATEGY

- `matchMedia('(max-width: 768px)')` and `prefers-reduced-motion: reduce` both route to the same simplified variant.
- **No pinning anywhere.** Acts become `scroll-snap-align: start` sections in a `scroll-snap-type: y proximity` container.
- **Act 1:** five poster images in a horizontal `scroll-snap-type: x mandatory` swipeable carousel; caption below.
- **Act 2:** all five thumbnail+line pairs shown as a simple vertical stack of cards, fading in via `IntersectionObserver` (no staggered reveal choreography).
- **Act 3:** `char5-maya-standing` becomes a static poster; iris becomes a CSS `clip-path: circle(0% → 75%)` reveal, `transition: clip-path 1.2s ease-out`, triggered once on entry.
- **Act 4:** cards stack vertically, simple fade+rise via `IntersectionObserver`, no hover tooltips (replace with persistent small captions).
- **Act 5:** unchanged — already non-pinned, lightweight.
- `CinematicCursor`: disabled entirely (`@media (hover: hover) and (pointer: fine)` gate).
- Persistent header/CTA: full opacity from the start (no fade-in delay).

---

## 13. PERFORMANCE BUDGET

| Asset category | Target |
|---|---|
| First paint (Act 0) | <500KB |
| Total video (5 character clips + 2 Maya clips, 720p H.264) | <17.5MB combined, but never more than ~5MB buffered simultaneously |
| Total audio (all sprites) | <1.5MB combined, 0KB if sound never enabled |
| Three.js + iris shader chunk | <150KB gzipped |
| Real product screenshots (Act 4) | <1MB combined (WebP/AVIF, properly sized) |
| **Total page weight, fully loaded** | **<25MB** (desktop, sound enabled); **<10MB** (mobile variant) |
| Lighthouse mobile performance | ≥80 (reduced-motion/mobile variant) |

---

## 14. ACCEPTANCE CHECKLIST

- [ ] Every visual choice can be traced to the mood board / keyword list in Section 0; nothing from Section 1's "Do Not" list appears anywhere
- [ ] Act 1's five clips share an identical color grade (shared CSS filter class) and identical lighting direction
- [ ] No camera movement exceeds the limits in Section 2 (push-ins ≤6%, dolly ≤5% of frame width, zero spins/swoops)
- [ ] Act 4 renders real product screenshots (or clearly-marked placeholders matching real dimensions) — no invented charts/metrics
- [ ] All audio is silent-by-default and totals <1.5MB
- [ ] At most 1–2 video assets buffered at any scroll position (verify in Network tab)
- [ ] Mobile/reduced-motion variant passes Lighthouse ≥80 and tells the full story (all five characters, all five lines, Maya's arc, product reveal, CTA) without any pinning
- [ ] Persistent header CTA is clickable from the very first frame on every breakpoint
- [ ] Three.js context for Act 3 is created lazily and `dispose()`-d after use
