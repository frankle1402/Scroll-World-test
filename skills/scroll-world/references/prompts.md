# Prompt contracts

## Intake

Record `SUBJECT`, `BRAND_NAME`, a 4–6 color `PALETTE`, `TONE`, `STYLE`, ordered `SECTIONS`, `CAMERA`, and whether `MOBILE` is required. Each section needs an id, visual subject, eyebrow, title, one-sentence body, and optional tags.

## Shared still preamble

Reuse this text byte-for-byte across all scene prompts, changing bracketed values once before the batch:

```text
A cohesive cinematic [STYLE] world, designed as one continuous environment. Consistent camera language, materials, warm directional lighting, shadows, and palette of [PALETTE]. Centered focal subject with generous travel space around it, rich depth layers for parallax, no text, no letters, no numbers, no captions, no logos, no watermark.
```

Append one scene description:

```text
Scene: [concrete environment, focal point, people/objects, foreground, middle ground, background]. Compose natively for [16:9 landscape | 9:16 portrait]. This is the opening frame of a smooth forward cinematic camera move.
```

Generate all stills with Codex `$imagegen` / ChatGPT Image (GPT Image 2.0 when available). Do not use Higgsfield. Review all stills together before generating video.

## Motion prompt

```text
Single continuous cinematic camera move, no cuts. Start exactly from the supplied first frame. Glide slowly forward and descend toward [FOCAL POINT], with gentle parallax across foreground, middle ground, and background. Preserve the scene's subjects, geometry, palette, materials, and lighting. Finish in a calm stable glide suitable for a seamless handoff. No text, captions, logos, watermark, camera shake, jump cut, morphing, or sudden speed change.
```

## Connector prompt

Supply frames extracted from rendered videos, never original stills.

```text
Single continuous cinematic transition, no cuts. Start exactly at the supplied first frame and finish exactly at the supplied last frame. Move smoothly out of [PREVIOUS SCENE], travel through one visually connected world, then approach [NEXT SCENE]. Preserve camera direction, speed, lighting, palette, geometry, and subject identity. Smooth graceful motion with subtle parallax. No text, captions, logos, watermark, jump cut, flash, morph, or sudden acceleration.
```

## Cohesion checks

Reject or re-roll a still that changes art style, camera angle, palette, lighting direction, character design, or background treatment. Reject a motion clip whose boundary frame contains sideways blur, an unfinished orbit, altered subjects, or a discontinuous camera direction.
