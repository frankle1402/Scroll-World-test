# Pipeline

## 1. Safe preflight

```bash
if test -n "${AI302_API_KEY:-}"; then echo AI302_API_KEY=present; else echo AI302_API_KEY=missing; fi
base=${AI302_BASE_URL:-https://api.302.ai}
curl -sS -o /dev/null -w 'endpoint_http=%{http_code}\n' --connect-timeout 10 --max-time 20 "$base/"
python3 scripts/seedance_302.py --help
ffmpeg -version | head -1
ffprobe -version | head -1
```

Stop if the key is missing. Do not print the key or dump the environment.

## 2. Generate stills

Use Codex `$imagegen` / ChatGPT Image for every still. Save approved inputs as `still_<scene>.png`. Use one shared style preamble and one image backend/model throughout. Generate a separate portrait composition when native mobile is approved; do not rely on a desktop crop.

## 3. Generate scene motion

After the user approves the stated paid call count and settings:

```bash
python3 scripts/seedance_302.py \
  --prompt-file "$WORK/dive_scene.txt" \
  --first-frame "$WORK/still_scene.png" \
  --output "$WORK/dive_scene.mp4" \
  --model doubao-seedance-2-0-260128 \
  --ratio 16:9 --duration 8 --resolution 1080p
```

Use `--ratio 9:16` for the separately composed native portrait chain.

## 4. Extract actual boundary frames

```bash
ffmpeg -v error -y -ss 0 -i "$WORK/dive_next.mp4" -frames:v 1 -q:v 2 "$WORK/first_next.png"
ffmpeg -v error -y -sseof -0.15 -i "$WORK/dive_prev.mp4" -frames:v 1 -q:v 2 "$WORK/last_prev.png"
```

## 5. Generate connectors

```bash
python3 scripts/seedance_302.py \
  --prompt-file "$WORK/conn_1.txt" \
  --first-frame "$WORK/last_prev.png" \
  --last-frame "$WORK/first_next.png" \
  --output "$WORK/conn_1.mp4" \
  --model doubao-seedance-2-0-260128 \
  --ratio 16:9 --duration 5 --resolution 1080p
```

## 6. Encode for responsive scrubbing

```bash
ffmpeg -v error -y -i input.mp4 -an \
  -c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p \
  -g 8 -keyint_min 8 -sc_threshold 0 -movflags +faststart output.mp4
```

For mobile, use the native portrait render, scale to 720 pixels wide if needed, and use GOP 4. Never upscale a smaller source.

## 7. QA

- Run `ffprobe` on every MP4 and confirm codec, dimensions, duration, frame rate, and no unexpected audio.
- Compare adjacent boundary frames and visually inspect every seam.
- Verify connector count equals scene count minus one.
- Scrub slowly and rapidly in a browser; test reverse scrolling and resize/orientation changes.
- Verify poster frame and video frame zero match.
- Keep generated URLs and API responses out of frontend assets; download outputs immediately because provider URLs may expire.
