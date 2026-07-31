---
name: scroll-world
description: Build immersive scroll-scrubbed continuous-camera websites from cohesive AI scene stills and frame-locked video clips. Use for scroll cinematics, fly-through worlds, diorama landing pages, or native desktop 16:9 and optional mobile 9:16 camera chains. Generate every still with Codex/ChatGPT image generation and every motion or connector clip with 302.AI Seedance 2.0; never use Higgsfield or Monid.
---

# Scroll World

Build a landing page where scrolling scrubs a pre-rendered continuous camera flight through ordered scenes. Use Codex/ChatGPT image generation for stills and the bundled 302.AI adapter for all video.

## Non-negotiable backends and security

- Generate all scene stills with Codex's `$imagegen` tool (ChatGPT Image / GPT Image 2.0 when available). Keep one image model/source for the full chain.
- Generate all scene motion and connector videos through `scripts/seedance_302.py` using 302.AI model `doubao-seedance-2-0-260128` by default.
- Never invoke Higgsfield or Monid.
- Read the API key only from `AI302_API_KEY`; optionally read the base URL from `AI302_BASE_URL` (default `https://api.302.ai`). Never echo the key, place it in prompts, source files, frontend files, committed `.env` files, or logs.
- Before any paid generation, state the number of calls, model, duration, resolution, ratio, audio/watermark settings, and expected cost impact; wait for explicit approval.
- On HTTP 400, inspect the single response, correct the payload against current 302.AI documentation, and ask before another paid attempt. Do not retry paid creation errors automatically.

## Workflow

1. Confirm `AI302_API_KEY` is present without printing it. Check the public endpoint and a non-creating authenticated query.
2. Interview for subject, brand/palette, art direction, camera style, 5–7 ordered scenes, and desktop-only versus native mobile. Propose sensible defaults but obtain approval before generating.
3. Make a byte-identical style preamble and one prompt per still. Read `references/prompts.md`.
4. Generate stills through `$imagegen`, usually 16:9 for desktop. Save PNG files locally. Review the full set for composition, palette, angle, lighting, and style cohesion before video spend.
5. Generate one Seedance motion clip per still. Read `references/pipeline.md` and use `scripts/seedance_302.py`.
6. Extract each rendered motion clip's actual first and last frames with FFmpeg.
7. Generate every connector with the previous rendered clip's actual last frame as `first_frame` and the next rendered clip's actual first frame as `last_frame`.
8. Encode seek-friendly H.264 MP4 assets and wire them into `references/scrub-engine.js` or `references/index-template.html`.
9. Run seam, duration, decoding, browser, and mobile QA. Never describe a chain as seamless without inspecting every boundary.

## Critical seam rule

A connector's first frame **must equal the previous generated motion clip's actual last frame**, and its last frame **must equal the next generated motion clip's actual first frame**. Never connect the original scene stills directly.

```bash
ffmpeg -v error -y -sseof -0.15 -i dive_prev.mp4 -frames:v 1 -q:v 2 last_prev.png
ffmpeg -v error -y -ss 0 -i dive_next.mp4 -frames:v 1 -q:v 2 first_next.png
```

## Desktop and mobile

- Default desktop chain: native `16:9`.
- Ask before producing mobile. A true mobile version is a separately generated native `9:16` chain with its own still compositions, motion clips, extracted seam frames, connectors, posters, and QA.
- Do not silently label a center crop as the native mobile version. Offer a crop only as an explicitly approved fallback.

## Bundled resources

- `scripts/seedance_302.py`: create, poll, and download Seedance tasks without third-party Python dependencies.
- `references/prompts.md`: still, motion, and connector prompt contracts.
- `references/pipeline.md`: command sequence, encoding, and QA.
- `references/scrub-engine.js`: portable vanilla JavaScript scroll engine.
- `references/index-template.html`: minimal integration template.
- `references/knockout.py`: optional flat-background knockout.
