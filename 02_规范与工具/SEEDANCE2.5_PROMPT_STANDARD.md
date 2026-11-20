# Seedance 2.5 Prompt Engineering Standard & Workflow Specification

*Asset-first, two-phase pipeline for short drama and cinematic production.*

**Epistemic note:** Section 1 explains failure modes from first principles and observed behavior. Seedance's internals are not public, so these are working hypotheses. Every countermeasure below is designed to be testable: if a layer doesn't move your results, drop it.

## 1. Root-Cause Diagnosis

### 1.1 Frozen puppets and dead world

**Mechanism (hypothesis).** A video diffusion model denoises toward the most probable, temporally consistent clip. Static is the cheapest consistent solution. Motion appears only where the text gives the model a reason to spend capacity: tokens with explicit motion verbs get cross-attention weight, and anything unmentioned falls back to the prior "hold still." A speaking character carries the densest motion vocabulary (mouth, head, gesture), so attention concentrates there. Listeners and backgrounds receive no motion tokens, so they inherit the static default.

**Fix: the Motion Budget.** Every visible entity and every visible environmental layer must receive its own motion verb with amplitude and rhythm. Silence in the prompt is read as an instruction to freeze.

- **Three-Layer World:** Foreground (principals), Midground (secondary people, props, steam, fabric), Background (weather, light, distant movement, air particles). Each layer gets at least one continuous motion and one occasional event.
- **Idle Behavior Library:** listeners are never "listening." Give them physical idle behavior (thumb rubbing a tool, weight shift, slow blink, gaze drifting to an object and back, breathing visible in the shoulders).
- **Continuous vs. punctuated motion:** continuous (rain streaks, flickering sign, steam) keeps the world alive; punctuated (a drip, a gust, a passing shadow) breaks loop-like repetition.

### 1.2 Literal dyeing

**Mechanism (hypothesis).** The text encoder binds color and state words to the nearest noun and broadcasts them over its whole region. "Face turned red" becomes "face + red." The model has no vascular or physiological model to interpret an idiom as a local, subtle perfusion change, so it paints the region. "Went black" becomes a global luminance instruction. Idioms like "gritted teeth" or "cold sweat" retrieve exaggerated, stylized training examples (horror, anime, theatre).

**Fix: the Physiological Translation Layer.** Never write the idiom. Translate every emotion into three observable channels:

1. **Mechanism:** what is physically happening (small muscles, breath, gaze, posture).
2. **Locality and degree:** where it appears and how faint ("faint, uneven warmth high on the cheekbones and ear tips").
3. **Preservation clause:** what must not change ("natural skin tone unchanged elsewhere, no color grading shift").

Translate camera and light effects the same way. "Vision went black" becomes a slow focus drift, a long blink, a slight vignette, and background defocus. Never use the words black, dark, fade, or red as state descriptors of a person.

**Positive-only phrasing.** Negations still place the forbidden tokens in context ("no green skin" can still invite green). Prefer positive anchors ("natural, healthy skin tone throughout") and keep any hard negatives in one short trailing constraint block.

### 1.3 Synchronized hive-mind

**Mechanism (hypothesis).** A collective phrase ("the crowd bowed their heads") is one conditioning signal broadcast to all instances of "person." With no per-person differentiation, every instance receives the same trajectory, onset time, and amplitude.

**Fix: Individuation and Stagger.**

- Never use collective verbs. Break the crowd into named slots by screen position ("man in gray cap, far left").
- Individuate at most three foreground slots; give the rest simple distinct tasks, not a shared reaction.
- For each slot assign a different action, **onset offset** (e.g., +0.0s, +0.8s, +1.6s), **amplitude** (slight, moderate, none), and **speed**.
- Include at least one slot that does not react or reacts late. Real groups are asymmetric.

### 1.4 Other failures

| Failure | Cause | Countermeasure |
| --- | --- | --- |
| Limb melting | Too many simultaneous articulations in one clip | **Action Budget:** per 5 s, one primary action, one secondary action, plus ambient motion only |
| No follow-through | Action described by its peak only | **Three-beat verbs:** anticipation, action, settle. State the terminal pose. |
| Walkie-talkie dialogue | Alternating clean turns, listener idle | Listener reaction before reply, slight overlap or pause, shared object of attention, gaze breaks |
| Identity and prop drift | Text re-describes faces, so each shot resamples them | **Reference-first identity:** references carry identity, text carries only state deltas and action |

### 1.5 Lack of Kinetics, Flat Pacing & Missing Cadence (The "Floating Slideshow" Syndrome)

**Mechanism (hypothesis).** Video diffusion models denoise temporal latents via uniform, linear mathematical interpolation across frames. Unless explicit kinetic forces, acceleration profiles, and physical damping are dictated, the model defaults to a constant average linear velocity—yielding weightless, floaty, slow-motion gliding. Furthermore, if all shots are assigned identical durations (e.g., rigid 5-second blocks), the edit cadence acts like an artificial metronome, completely suffocating dramatic tension and emotional breathing.

**Fix: The Respiratory Kinetic Architecture (Non-Linear Dynamics + Cadence Wave).**

1. **Macro Cadence (Inter-Shot Breathing Curve):** Never cut a scene into equal time slices. Mirror dramatic tension like a respiratory heartbeat:
   - **Tension Build / Suspense (Inhale):** 4 to 6 seconds. Static frame or ultra-slow push; minute micro-actions (breath in shoulders, drifting dust); suffocating stillness.
   - **Ignition / Burst / Clash (Exhale):** 1.5 to 3 seconds. Rapid, explosive velocity; concentrated kinetic vectors; zero wasted frames.
   - **Aftermath / Resonance (Hold):** 4 to 5 seconds. Movement settle, settling dust, lingering breath, auditory vacuum before the next cycle.
2. **Micro Kinetics (Intra-Shot Non-Linear Easing):** Apply classic animation principles (Anticipation ➔ Burst ➔ Impact Lock ➔ Follow-Through):
   - **Anticipation (0.5–0.8s):** Brief freeze or center-of-gravity drop (e.g., heel digs into gravel, shoulders tense, breath held).
   - **Explosive Burst:** Abrupt acceleration with stated impulse (e.g., snaps forward with sudden momentum, sudden kinetic burst).
   - **Impact Lock & Inertia Damping (Follow-Through):** Abrupt kinetic stop, followed by secondary overshoot (coat tails, loose hair, or dust puff forward in inertia, then slowly settle).
3. **Dynamic Contrast (Motion Asymmetry):** When the principal is stationary, maximize environmental motion (wind-whipped grass, fluttering curtains). When the principal is in violent motion, lock the camera to an absolute, unmoving axis to amplify relative velocity and impact clarity.

## 2. The Compensatory Layers (Prompt Anatomy)

Every shot prompt contains these blocks, in this order:

1. **Reference binding:** which assets apply, and their role.
2. **Shot grammar:** shot size, angle, lens feel, camera movement (one movement only), duration.
3. **Spatial blocking:** who is where, relative to what, facing which direction.
4. **Timeline:** second-by-second beats for the principals, with anticipation, action, settle.
5. **Ambient Motion Budget:** foreground idle, midground, background layers.
6. **Dialogue:** lines with timing, speaker, delivery, listener reaction.
7. **Light and color:** motivated source, with a skin-tone preservation clause when emotion involves the face.
8. **Stability constraints:** short, positive-first closing block.

**Core rules.**

- One shot, one emotional beat, one camera move.
- **Dynamic shot duration hierarchy (Cadence Wave):** 1.5 to 3.0 s for bursts, impacts, or sharp cuts; 4.0 to 6.0 s for suspense, emotional confession, or aftermath. Never use uniform shot lengths across an entire scene.
- **Non-linear kinetic easing:** Reject constant-velocity motion. Every major action must specify anticipation (micro-freeze/weight drop), sudden kinetic impulse (burst), and impact lock with secondary inertia (follow-through).
- Dialogue: at most two short lines per shot, about 2.5 words per second of speech.
- Use specific nouns and kinetic verbs. Avoid adjectives that name an end state of the body.
- Metaphor is for the script, never for the prompt.

### 2.1 Physiological Translation Table (starter set)

| Script idiom | Translate to |
| --- | --- |
| Blushed, face turned red | Faint, uneven warmth high on cheekbones and ear tips, building slowly. Natural skin tone elsewhere unchanged. Gaze drops, chin tucks slightly. |
| Turned pale with fear | Face stills, blink rate drops, lips press thin, breath held then shallow. Skin tone natural, lighting unchanged. |
| Vision went black, dizzy | Slow long blink, background focus drifts soft, hand reaches for the nearest surface. Exposure unchanged. |
| Gnashed teeth | Jaw muscle tightens at the hinge, lips stay closed and pressed, nostrils flare slightly. Mouth otherwise natural. |
| Cold sweat | Single faint sheen at the temple catching the light, subtle swallow. |
| Heart sank | Shoulders drop a few centimeters, exhale through the nose, eyes lower and unfocus. |
| Trembled with rage | Fine tremor in the fingers only, knuckles whiten slightly at the grip, steady voice. |
| Everyone felt ashamed | Name 2 to 3 individuals. Each gets a different gaze or posture change, staggered 0.5 to 1.5 s apart. |
| Tears welled up | Eyes glisten at the lower lids, one blink, a single tear that does not yet fall. |

### 2.2 Kinetic Dynamics & Easing Lexicon (starter set)

| Kinetic Intent | Avoid (Uniform/Sluggish) | Translate to (Non-Linear Easing & Follow-Through) |
| --- | --- | --- |
| **Sudden Reach / Grab** | Reaches out and grabs the ticket | Pauses fingers for 0.5s at the pocket hem (anticipation), then snaps hand forward with sudden momentum, fingers clamping onto the card stock with an abrupt lock; sleeve cuff slides forward and settles. |
| **Sharp Turn / Head Snap** | Turns his head to look at her | Holds gaze straight for a beat, then turns head abruptly toward her off-frame position with an audible breath; ear tips and hair tufts overshoot slightly before snapping into a locked, steady stare. |
| **Rising / Standing Up** | Stands up from the chair | Braces both palms flat on the desk, leans torso forward (anticipation), pushes up with an explosive upward thrust, rising tall; apron strings and unbuttoned jacket swing forward in inertia, then sway to a damped rest. |
| **Impact / Strike / Slam** | Slams his fist on the table | Lifts forearm with a brief suspended hesitation, then drives fist down in high velocity; knuckles strike the wood with sharp impact lock; surrounding dust motes puff outward and loose tools chatter on the surface. |
| **Sudden Freeze / Shock** | Stops moving, shocked | Mid-movement, right hand instantly arrests with visible muscular tension; breath cuts off mid-inhalation, shoulders locking rigid while small hanging pendants continue their faint residual sway. |

## 3. Asset-Shot Interlock Architecture

### 3.1 Principle

**References own identity. Text owns behavior.** If a face, outfit, or room layout is in a reference, do not describe it in the video prompt beyond a delta. This frees attention for acting and motion. The cleaner the reference (empty hands, neutral pose, no baked-in emotion), the more freedom the model has to act.

### 3.2 Asset categories and IDs

| Code | Asset | Purpose | Requirements |
| --- | --- | --- | --- |
| **CHR-name-TURN** | Character turnaround sheet | Identity: face, hair, build, outfit | Neutral standing pose, **empty hands**, front, 3/4, profile, back, flat even light, plain background |
| **CHR-name-EXP** | Expression and state variants | Emotion anchors without baked-in dyeing | Neutral, guarded, guilty-subdued, tearful-held; natural skin tone in all |
| **CHR-name-STATE** | Costume or condition states | Rain-wet, torn, injured, changed outfit | Only when the script changes the state |
| **SCN-place-MASTER** | Empty scene master plate | Layout and lighting truth | No people, wide, eye level |
| **SCN-place-ANGLE-x** | Reverse and detail slices | Cross-shot spatial consistency | Same lighting, same set dressing |
| **SCN-place-MAP** | Top-down blocking map | Fix left/right and screen direction | Simple plan, labelled |
| **PRP-item** | Hero props, isolated | Prop consistency | Isolated on neutral ground, 2 angles, scale reference |
| **LIT-scene** | Light and color reference | Mood without tinting skin | Same set, key light direction and color temperature |

### 3.3 Tagging in video prompts

Use your platform's reference syntax. Below it is written `@ImageN`; map each tag to an asset ID in a **Reference Table** at the top of the prompt.

- Role-binding sentence: `@Image1 is Nora (identity and outfit only). @Image4 is the workshop (layout and lighting only).`
- Role-limiting phrase: always say what the reference is used **for**, so the model doesn't copy its pose or expression.
- Delta statements only: "Nora, rain-damp hair at the ends" is allowed. Re-describing her face is not.
- Props enter a shot only if the shot's timeline uses them.

## 4. The System Prompt (deploy as-is)

```text
YOU ARE: an Elite AI Cinematic Director and Video Diffusion Prompt Architect for Seedance 2.5 short-drama production.

MISSION: Convert a script scene into (A) an Asset Requirement Checklist with image-generation prompts, and (B) a shot-by-shot Seedance 2.5 video prompt set. Output is directly production-ready.

MENTAL MODEL OF THE VIDEO MODEL:
- It freezes anything that has no motion verb. Silence means static.
- It defaults to constant, linear velocity. Without explicit acceleration profiles, damping, and anticipation, it generates weightless, floaty slow-motion.
- It paints literal colors and states onto regions named in the prompt. It does not understand idioms or physiology.
- It copies one collective instruction to every person in frame, simultaneously.
- It distorts limbs when too many articulations occur in one clip.
- It resamples identity when text re-describes faces.
Your job is to compensate for each of these in every prompt.

WORKFLOW (follow in order):
1. SCENE ANALYSIS: list characters, location, props, emotional arc, light, time of day, weather, and each character's goal.
2. ASSET CHECKLIST (Phase 1): produce assets using codes CHR-<name>-TURN, CHR-<name>-EXP, CHR-<name>-STATE, SCN-<place>-MASTER, SCN-<place>-ANGLE-<x>, SCN-<place>-MAP, PRP-<item>, LIT-<scene>. Turnarounds must have empty hands and neutral pose. Each asset gets a ready-to-use image prompt. Include only assets the scene actually needs.
3. SHOT LIST (Phase 2): split the scene into dynamic cadence shots: 1.5 to 3.0 s for bursts/impacts, 4.0 to 6.0 s for suspense/confession/aftermath. Mirror the dramatic breathing curve; never use uniform durations across a scene. One shot = one emotional beat = one camera movement. Max two short dialogue lines per shot.
4. SHOT PROMPTS: write each with the blocks below.
5. SELF-AUDIT: run the checklist at the end and fix violations before output.

SHOT PROMPT TEMPLATE (use these headings exactly):
REFERENCES: tag -> asset ID -> role (identity only / layout only / prop only).
SHOT: size, angle, lens feel, ONE camera move, duration.
BLOCKING: positions, facing directions, distances, relative to scene map.
TIMELINE: second-by-second beats for each principal. Each action expressed as anticipation -> action -> settle, ending in a stated final pose.
AMBIENT MOTION BUDGET: Foreground idle (non-active principals), Midground (other people, props, cloth, steam), Background (weather, light, air, distant movement). Each layer has at least one continuous and one occasional motion.
DIALOGUE: speaker, line, start second, delivery in physical terms; listener's pre-reaction and idle behavior; natural gap or overlap.
LIGHT AND COLOR: motivated source and direction. If any face emotion occurs, add: natural skin tone preserved, no color grading shift on skin.
CONSTRAINTS: one short block. Positive-first. Max 4 hard negatives.

HARD RULES:
1. Never use idioms or color/state words for the body (red face, pale, green, black out, gritted teeth, cold sweat, hair standing on end, etc.). Translate into mechanism + locality/degree + preservation clause.
2. Never use collective verbs (everyone, the crowd, some people, they all). Individuate each person by screen position, give each a different action, an onset offset (0.5 to 1.5 s apart), and a different amplitude. Always include at least one person who reacts late or not at all.
3. Every visible person gets a motion verb in every shot. Listeners get specific idle behavior, never 'listens' or 'stands still'.
4. Every environment gets three layers of motion (see template). Name the actual phenomena (rain streaks on glass, flickering neon, steam, dust in the shaft of light).
5. Action Budget: per 5 seconds, one primary action, one secondary action, plus ambient only. No simultaneous multi-limb choreography.
6. All strong actions need anticipation and a settle with a terminal pose.
7. Do not re-describe faces, hair, or outfits that exist in references. State only deltas.
8. Bind every reference with a role-limiting phrase. Props appear only if used in the shot's timeline.
9. One shot, one emotional beat, one camera move. Prefer static, slow push, or slow pan. No whip pans, no orbit during dialogue.
10. Dialogue: short lines, interruptions, pauses, gaze breaks, listener reaction BEFORE reply. Never strict alternating turns of equal length.
11. Use concrete physical language. Emotion is shown through posture, hands, breath, gaze, and object handling, never named as a facial state.
12. Continuity: carry over the final pose, prop location, and light of the previous shot as the starting state of the next.
13. Write prompts in plain, specific English. Avoid metaphor and poetic abstraction inside prompts.
14. Non-Linear Kinetics & Dynamic Cadence: Never allow constant-velocity, floaty motion. Every major physical action must be structured as Anticipation (brief freeze, weight drop, or held breath) -> Sudden Kinetic Impulse (burst) -> Impact Lock & Follow-Through (inertia damping, fabric overshoot, settle). Use variable shot lengths (1.5-3.0s fast vs 4.0-6.0s slow) to create an organic, breathing dramatic rhythm.

OUTPUT FORMAT:
## Scene Analysis (short)
## Phase 1: Asset Requirement Checklist (table: ID | purpose | image prompt)
## Phase 2: Shot List (table: shot | size | duration | beat)
## Shot Prompts (one block per shot, template above)
## Self-Audit (checklist with pass/fix notes)

SELF-AUDIT CHECKLIST:
[ ] No idiom or color-state word describing a body or face
[ ] No collective verbs; every crowd member individuated with offsets
[ ] Every visible person has a verb; listeners have idle behavior
[ ] Three ambient layers present
[ ] Action Budget respected; anticipation and settle present
[ ] Dynamic breathing cadence applied: variable shot durations (1.5–3.0s bursts vs 4.0–6.0s holds)
[ ] Non-linear kinetics present: anticipation micro-freeze, sudden burst impulse, and inertia follow-through
[ ] References role-limited; no face re-description
[ ] One camera move; max 2 dialogue lines
[ ] Dialogue has pauses, listener pre-reaction, natural overlap or gap
[ ] Skin-tone preservation clause wherever the face emotes
[ ] Continuity handoff to the next shot stated
```

## 5. End-to-End Demonstration

**Scene: "The Ticket."** Interior, rainy evening, a small watch-repair workshop. Eli (35) is bent over the bench. His younger sister Nora (32) comes in to confess that she pawned their late father's pocket watch. Tomas, an apprentice, works at the back and overhears.

### 5.1 Scene analysis

- **Nora:** goal is to confess and be forgiven; she is carrying shame about money and about the watch.
- **Eli:** goal is to keep control, so he works with his hands to avoid showing hurt.
- **Tomas:** wants to be invisible; his small reactions are asymmetric to the siblings' beats.
- **Light:** warm bench lamp, cool window light from rain, intermittent neon spill from outside.

### 5.2 Phase 1: Asset Requirement Checklist

| ID | Purpose | Image generation prompt |
| --- | --- | --- |
| **CHR-NORA-TURN** | Identity | Character turnaround sheet, woman about 32, shoulder-length dark-brown wavy hair, olive-toned skin, tired warm eyes, navy wool coat over gray knit sweater, dark jeans, brown leather boots. Four views: front, three-quarter, profile, back. Standing neutral, arms relaxed at sides, **hands empty**. Flat even studio light, plain light-gray background, natural skin tone, photorealistic. |
| **CHR-NORA-EXP** | Emotion anchors | Same woman, head-and-shoulders, four panels: neutral, guarded, guilty-subdued (eyes lowered, lips pressed), tearful-held (glistening eyes, no tears falling). Natural, even skin tone in all panels, soft frontal light. |
| **CHR-NORA-STATE** | Rain state | Same woman, front and three-quarter view, coat shoulders and hair ends damp from rain, no other changes, empty hands, plain background. |
| **CHR-ELI-TURN** | Identity | Character turnaround sheet, man about 35, short black hair with slight graying at the temples, light stubble, brown eyes, lean build, rolled-sleeve charcoal shirt under a worn leather work apron. Front, three-quarter, profile, back, neutral stance, **hands empty**, flat light, plain background, natural skin tone, photorealistic. |
| **CHR-ELI-EXP** | Emotion anchors | Same man, head-and-shoulders: neutral, concentrating, controlled-hurt (jaw set, eyes steady), softened. Natural, even skin tone throughout. |
| **CHR-TOMAS-TURN** | Background identity | Turnaround sheet, young man about 22, curly red-brown hair, thin frame, canvas apron over a green sweater. Front, three-quarter, back, hands empty, plain background. |
| **SCN-SHOP-MASTER** | Layout truth | Empty small watch-repair workshop at evening, wide eye-level view: wooden workbench with a hooded lamp at center-left, wall of antique clocks behind, rain-streaked street window at right with a faint neon sign outside, shelf of small parts drawers at back, a steaming kettle on a hot plate, a door at left. No people, no hands, photorealistic. |
| **SCN-SHOP-ANGLE-B** | Reverse view | Same workshop from behind the bench looking toward the entrance door, same lighting and set dressing, empty. |
| **SCN-SHOP-MAP** | Blocking | Simple top-down plan of the workshop: door (left wall), bench (center), window (right wall), back shelves and Tomas's small table (rear), kettle (rear right). Labelled positions. |
| **PRP-TICKET** | Hero prop | Isolated pawn ticket: cream card, tear-off stub, faded blue ink stamp, handwritten amount, on neutral gray ground, two angles, a coin for scale. |
| **PRP-LOUPE** | Prop | Isolated brass jeweler's loupe with a leather strap, neutral gray ground, two angles. |
| **LIT-SHOP** | Light | Same workshop, key warm lamp at the bench, cool window light from the right, soft neon spill on the glass, natural color temperature on skin tones. |

### 5.3 Shot list (Dynamic Cadence Wave)

| Shot | Size | Dur. | Cadence Type | Beat |
| --- | --- | --- | --- | --- |
| S1 | Wide two-shot | 6.0 s | Inhale / Build | Arrival: Nora enters, Eli keeps working |
| S2 | Medium two-shot | 4.0 s | Compression | Hesitation: she struggles to start, breath tightens |
| S3 | Close-up Nora | 5.0 s | Emotional Deepening | Confession: micro-warmth, unshed tear, silence |
| S4 | Medium Eli with Tomas | 2.5 s | Sharp Impact / Burst | Controlled shock: breath stops, sudden kinetic arrest |
| S5 | Wide two-shot | 6.0 s | Exhale / Follow-through | Aftermath: ticket slides forward, rising with inertia, departure |

Reference table for all shots: `@Image1` = CHR-NORA-TURN, `@Image2` = CHR-NORA-STATE, `@Image3` = CHR-NORA-EXP, `@Image4` = CHR-ELI-TURN, `@Image5` = CHR-ELI-EXP, `@Image6` = CHR-TOMAS-TURN, `@Image7` = SCN-SHOP-MASTER, `@Image8` = SCN-SHOP-ANGLE-B, `@Image9` = PRP-TICKET, `@Image10` = PRP-LOUPE, `@Image11` = LIT-SHOP.

### 5.4 Shot prompts

**S1: Arrival (6.0 s — Atmospheric Inhale)**

- **REFERENCES:** @Image2 is Nora (identity and outfit, rain-damp state; not her pose). @Image4 is Eli (identity and outfit only). @Image6 is Tomas (identity only). @Image7 is the workshop (layout and lighting only). @Image11 is the light mood.
- **SHOT:** Wide eye-level two-shot from inside the shop, 35mm feel, slow push-in over 6 seconds, static horizon.
- **BLOCKING:** Eli seated at the center-left bench facing the camera at a slight angle. Door at far left, Nora entering. Tomas at the small rear table, back three-quarter to camera, left of the clocks.
- **TIMELINE:**
  - 0.0 s: door opens inward; Nora steps in and pauses half a beat on the threshold (anticipation), pulling the door shut behind her.
  - 1.0 s: Eli does not look up; his right hand turns a tiny screwdriver in a watch movement under the lamp with rhythmic precision.
  - 2.0 to 4.0 s: Nora walks four slow steps toward the bench, hands in coat pockets, shoulders slightly raised; settles at the bench's near edge, weight on her left foot, final pose standing close to the bench.
  - 4.5 s: Eli lifts his eyes briefly to her, then lowers them back to the movement.
- **AMBIENT MOTION BUDGET:**
  - Foreground idle: Eli's breath visible in his shoulders; the screwdriver tip makes tiny circular turns.
  - Midground: Tomas sorts small gears into trays with quick small hand movements, glances once toward the door at 1.5 s and returns to work; kettle steam rises and curls sideways in the draft when the door opens.
  - Background: rain runs down the window in uneven streaks; the neon glow outside pulses slowly across the glass; pendulums on two wall clocks swing at slightly different speeds; dust motes drift in the lamp beam.
- **DIALOGUE:** none. Subtle room sound only.
- **LIGHT AND COLOR:** warm bench lamp pools on Eli's hands, cool window light along the right edge. Natural skin tone preserved on both faces.
- **CONSTRAINTS:** Natural, healthy skin tone throughout. Keep each person's identity matched to their reference. Smooth, human-paced movement with clear anticipation and settle. No text on screen. No camera shake.
- **HANDOFF:** Nora ends at the near edge of the bench; Eli still holds the screwdriver.

**S2: Hesitation (4.0 s — Compression Beat)**

- **REFERENCES:** same as S1; also @Image10 is the loupe (prop only), resting on the bench.
- **SHOT:** Medium two-shot from slightly over Nora's left shoulder, 50mm feel, static camera.
- **BLOCKING:** Nora left foreground, partly back to camera, Eli right of center behind the bench, Tomas small and blurred in the right background.
- **TIMELINE:**
  - 0.0 s: Nora draws a sudden breath through her nose, shoulders tensing (anticipation); lips part, then press tight.
  - 1.0 s: her right hand comes out of her pocket and rests on the bench edge, thumb rubbing the side of her index finger.
  - 1.8 s: Eli sets down the screwdriver without looking up, picks up the loupe and tilts it in his fingers, thumb freezing mid-stroke.
  - 3.2 s: Nora lifts her gaze to his face, holds it for a second, then drops it down to the bench (settle).
- **AMBIENT MOTION BUDGET:**
  - Foreground idle: Nora shifts her weight from left to right foot once; Eli's eyes track the movement under the lamp.
  - Midground: Tomas lifts a tray, freezes his hand briefly mid-air at 1.5 s (listening), then places it down slowly.
  - Background: rain continues unevenly; a short gust rattles the window pane; steam from the kettle thins.
- **DIALOGUE:**
  - 1.2 s, Nora, low and breathy: "Eli. About Dad's watch."
  - 2.8 s, Eli, flat, eyes on the loupe: "It's in the drawer."
  - Listener pre-reaction: Eli's thumb freezes on the loupe half a second before speaking.
- **LIGHT AND COLOR:** warm bench lamp as key, cool window fill. Natural skin tone preserved; no tint shift.
- **CONSTRAINTS:** Natural, healthy skin tone throughout. Only two people animate prominently; Tomas stays soft and subdued. Non-linear, breathing human tempo.
- **HANDOFF:** Nora's right hand resting on the bench edge; Eli holds the loupe in his palm.

**S3: Confession (5.0 s — Emotional Deepening)**

- **REFERENCES:** @Image3 is Nora's expression range (guilty-subdued, tearful-held; reference for facial structure and mood only). @Image2 for identity and rain-damp hair. @Image7 for blurred background layout.
- **SHOT:** Close-up on Nora's face and shoulders, 85mm feel, shallow depth of field, very slow push-in.
- **BLOCKING:** Nora centered, Eli's out-of-focus shoulder at the right edge of frame.
- **TIMELINE:**
  - 0.0 s: jaw tightens slightly at the hinge, lips pressed, nostrils flare slightly on an inhale (anticipation).
  - 0.8 s: she shakes her head once, minimally, eyes locking onto Eli off-frame right.
  - 1.2 s: faint, uneven warmth appears high on her cheekbones and ear tips, building slowly; her natural skin tone is otherwise unchanged.
  - 2.5 s: she speaks her line with a slight vocal crack; her lower eyelids glisten; she blinks once; a single tear forms but does not fall.
  - 4.0 s: she exhales through the nose, shoulders dropping two centimeters; settles with eyes lowered to the left.
- **AMBIENT MOTION BUDGET:**
  - Foreground idle: damp hair ends move slightly with her breath; the coat collar shifts as she exhales.
  - Midground: out-of-focus Eli's hand slowly lowers the loupe onto the bench surface.
  - Background: soft bokeh of the neon sign pulses; raindrops slide down the blurred window; dust drifts in the lamp beam.
- **DIALOGUE:** at 2.2 s, Nora, voice cracking slightly: "I pawned it. Three weeks ago." Followed by 1.8 seconds of complete silence save for the clock tick and rain.
- **LIGHT AND COLOR:** warm key from the left, cool rim from the window. Natural skin tone preserved; no color grading shift on skin.
- **CONSTRAINTS:** Subtle, realistic micro-expressions only. Natural skin tone throughout. Eyes stay clear and natural. Mouth shape stays natural while speaking.
- **HANDOFF:** Nora ends looking down-left, tear unshed.

**S4: Controlled Reaction (2.5 s — Sharp Kinetic Impact / Sudden Freeze)**

- **REFERENCES:** @Image5 is Eli's expression range (controlled-hurt; facial structure and mood only). @Image4 identity. @Image6 Tomas (identity only). @Image7 layout.
- **SHOT:** Medium shot on Eli, 50mm, static camera. Tomas visible, softly focused in the rear right.
- **BLOCKING:** Eli center, facing camera; Tomas three meters behind him at the rear table.
- **TIMELINE:**
  - 0.0 s: on hearing the line, Eli's breath instantly cuts off; hand mid-motion freezes solid on the bench (sudden kinetic arrest).
  - 0.6 s: jaw muscle snaps tight with visible tension at the hinge; nostrils flare; he holds dead still for a full second.
  - 1.8 s: right hand abruptly shoves the loupe two centimeters aside with a sharp, controlled click; fingers splay flat onto the wood with an impact lock (settle).
- **AMBIENT MOTION BUDGET:**
  - Foreground idle: vein at his temple pulses once; chest remains rigid without breathing.
  - Midground: Tomas stops hand movement instantly at 0.4 s, keeping his head completely down like a turtle.
  - Background: rain slaps the window pane; clock pendulum swings steadily across the tense silence.
- **DIALOGUE:** at 1.9 s, Eli, quiet, low, hard: "How much?"
- **LIGHT AND COLOR:** lamp light hard on his hands and jaw; cool window light on the opposite cheek. Natural skin tone preserved.
- **CONSTRAINTS:** Sharp contrast between absolute stillness and abrupt hand impulse. Natural skin tone throughout. No exaggerated facial distortion.
- **HANDOFF:** Eli's right hand splayed flat on the bench; his jaw locked.

**S5: Aftermath (6.0 s — Exhale & Departure)**

- **REFERENCES:** @Image2, @Image4, @Image6 identities; @Image8 is the reverse-angle layout; @Image9 is the pawn ticket (prop only); @Image11 light.
- **SHOT:** Wide two-shot from behind the bench toward the door, 35mm feel, very slow push-in.
- **BLOCKING:** Eli center-left behind the bench, Nora right, Tomas in the far background at his table, door at center rear.
- **TIMELINE:**
  - 0.0 s: Nora draws the pawn ticket from her coat, pauses (anticipation), then slides it across the polished wood toward Eli with sudden momentum; fingers withdraw to her side.
  - 1.5 s: Eli picks up the ticket, folds it with a crisp snap, slips it into his apron pocket.
  - 2.8 s: Eli braces his palms on the bench (anticipation), pushes up with an explosive upward thrust, rising tall; apron strings swing forward in inertia, then sway to a rest.
  - 4.2 s: he grabs his heavy wool coat from the hook in one sweeping motion, swings it over his shoulders with momentum, and begins walking toward the door; Nora follows half a step behind; final pose: both stepping through the threshold.
- **AMBIENT MOTION BUDGET:**
  - Foreground idle: apron strings and coat tails settle after the movement; Nora wipes the corner of her eye quickly at 2.0 s.
  - Midground: Tomas glances up at 3.5 s as Eli rises, waits until they take two steps, then slowly reaches for his screwdriver.
  - Background: rain streams across the glass; clock pendulum swings; hot plate kettle gives off a faint hiss.
- **DIALOGUE:**
  - 1.0 s, Nora, small voice: "Two hundred eighty. I'll get it back."
  - 4.8 s, Eli, mid-stride, deep and firm: "We'll get it back."
- **LIGHT AND COLOR:** warm lamp on the bench, cool dim light near the doorway. Natural skin tone preserved.
- **CONSTRAINTS:** Natural, healthy skin tone throughout. Non-linear acceleration with clear inertia damping on coats and apron. Hands show five fingers each.
- **HANDOFF:** Doorway empty as both exit; Tomas remains at rear table.

### 5.5 Self-audit

| Check | Result |
| --- | --- |
| No idiom or color-state words for faces | Pass. "Blush" translated to local, faint warmth with preservation clause (S3). |
| No collective verbs | Pass. Tomas is an individual with his own action and delayed onset. |
| Every visible person has a verb, listeners have idle behavior | Pass. Eli's thumb freezes, Tomas pauses and sorts, Nora's weight shifts. |
| Three ambient layers | Pass in all five shots. |
| Dynamic breathing cadence (Inter-shot) | Pass. Durations wave across 6.0s ➔ 4.0s ➔ 5.0s ➔ 2.5s (burst) ➔ 6.0s. |
| Non-linear kinetics (Intra-shot) | Pass. Anticipation freeze (S2/S4/S5), sudden kinetic burst (S4 shove, S5 stand), inertia follow-through. |
| Action Budget and follow-through | Pass. One primary and one secondary action per shot; terminal poses stated. |
| References role-limited | Pass. No face re-description. |
| Dialogue naturalness | Pass. Pauses, pre-reactions, a 1.8 s silence, one listener who speaks while moving. |
| Continuity handoffs | Pass. |

## 6. Operating Notes

- **A/B test layers.** If a prompt is too long, drop layers one at a time to see which matter. Keep the Motion Budget, Translation Layer, and Kinetic Easing last, since they do the most heavy lifting.
- **Tune amplitudes with a lexicon.** Maintain a studio glossary of motion verbs, kinetic easing phrases (anticipation, burst, impact lock, follow-through), and physiological translations; extend the tables in Section 2 whenever a new idiom or floaty motion causes a failure.
- **Log failures by type.** Tag each bad take as FREEZE, DYE, SYNC, LIMB, KINETIC (floaty/sluggish), CADENCE (flat rhythm), or DRIFT, and fold fixes back into the system prompt.
- **Use the first and last frame.** If the platform supports image-to-video with start and end frames, generate the stable frame from the assets first, then animate toward the settle pose.
