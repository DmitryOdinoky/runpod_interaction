# Image Quality Tips for FLUX.1-dev-fp8

## Why Images May Be Blurry

FLUX.1-dev-fp8 uses 8-bit quantization (fp8), which is faster but can produce slightly softer images than full precision models. Here's how to get the sharpest results:

## Recommended Settings (Updated Defaults)

**New defaults in `generate.py`:**
- Steps: **25** (was 20)
- CFG: **4.0** (was 3.5)
- Better negative prompt with "low res, poorly drawn"

## Settings Guide

### Steps (Most Important for Sharpness)
```bash
--steps 15   # Fast but may be blurry
--steps 20   # Decent quality
--steps 25   # ✓ RECOMMENDED - Good balance
--steps 30   # Maximum quality, slower
```

### CFG Scale (Controls Detail)
```bash
--cfg 2.0    # Very soft, creative
--cfg 3.5    # Balanced
--cfg 4.0    # ✓ RECOMMENDED - Sharper
--cfg 5.0    # Very sharp, high contrast
--cfg 6.0+   # May oversaturate
```

### Prompt Quality Keywords

**Add these to your prompts for sharper images:**
```
highly detailed, sharp focus, 8k, professional photography,
ultra detailed, crisp, clear, photorealistic, high resolution
```

**Examples:**

❌ **Poor (vague):**
```bash
venv/python.exe generate.py "a cat"
```

✓ **Good (detailed):**
```bash
venv/python.exe generate.py "a cat, highly detailed, sharp focus, professional photography"
```

✓ **Best (quality keywords + settings):**
```bash
venv/python.exe generate.py "a majestic cat with detailed fur, sharp focus, professional photography, 8k, highly detailed" --steps 30 --cfg 4.5
```

## Negative Prompt Improvements

**Updated default negative prompt:**
```
blurry, low quality, distorted, ugly, bad anatomy, low res, poorly drawn
```

**For extra sharpness, add:**
```bash
venv/python.exe generate.py "your prompt" --negative "blurry, soft focus, low quality, low res, poorly drawn, distorted, ugly, bad anatomy, out of focus"
```

## Image Size Recommendations

Larger images can look sharper:
```bash
# Standard (1024x1024)
venv/python.exe generate.py "prompt" --width 1024 --height 1024

# Higher resolution (slower but sharper)
venv/python.exe generate.py "prompt" --width 1536 --height 1536 --steps 30

# Ultra high resolution (very slow)
venv/python.exe generate.py "prompt" --width 2048 --height 2048 --steps 35
```

**Note:** Larger images require more VRAM and take longer.

## Comparison Test

Let's compare settings with the same seed:

**Low quality (fast):**
```bash
venv/python.exe generate.py "a beautiful rose" --steps 15 --cfg 2.5 --seed 100
```

**Medium quality (default):**
```bash
venv/python.exe generate.py "a beautiful rose, detailed" --steps 25 --cfg 4.0 --seed 100
```

**High quality (best):**
```bash
venv/python.exe generate.py "a beautiful rose, highly detailed, sharp focus, professional photography, 8k" --steps 30 --cfg 4.5 --seed 100
```

## Style-Specific Tips

### Photography
```bash
venv/python.exe generate.py "portrait of a woman, professional photography, sharp focus, 85mm lens, detailed, 8k" --steps 30 --cfg 4.5
```

### Artwork
```bash
venv/python.exe generate.py "fantasy landscape, concept art, highly detailed, sharp, intricate details" --steps 28 --cfg 4.0
```

### Product Photography
```bash
venv/python.exe generate.py "product shot, studio lighting, sharp focus, clean background, highly detailed, professional" --steps 30 --cfg 5.0
```

## Quick Quality Presets

Create these as shortcuts:

**Fast (testing):**
```bash
--steps 15 --cfg 3.5
```

**Balanced (default):**
```bash
--steps 25 --cfg 4.0
```

**Quality (recommended):**
```bash
--steps 28 --cfg 4.5
```

**Maximum:**
```bash
--steps 35 --cfg 5.0 --width 1536 --height 1536
```

## What NOT to Do

❌ Don't use very low steps (<15)
❌ Don't use vague prompts without quality keywords
❌ Don't forget the negative prompt
❌ Don't use CFG below 2.0 (too soft)
❌ Don't use CFG above 7.0 (oversaturated)

## Example: Perfect Portrait

```bash
venv/python.exe generate.py \
  "portrait of a person, professional photography, sharp focus, detailed face, studio lighting, 85mm lens, bokeh background, highly detailed, 8k" \
  --negative "blurry, soft focus, low quality, low res, poorly drawn, distorted, ugly, bad anatomy, out of focus, oversaturated" \
  --steps 30 \
  --cfg 4.5 \
  --width 1024 \
  --height 1280
```

## Example: Sharp Landscape

```bash
venv/python.exe generate.py \
  "mountain landscape at golden hour, sharp focus, highly detailed, professional photography, vivid colors, 8k, ultra detailed" \
  --negative "blurry, low quality, low res, poorly drawn, soft, hazy" \
  --steps 28 \
  --cfg 4.0 \
  --width 1536 \
  --height 864
```

## Troubleshooting Blurry Images

1. **Increase steps**: Try 28-30
2. **Increase CFG**: Try 4.5-5.0
3. **Add quality keywords**: "sharp focus, highly detailed, 8k"
4. **Improve negative prompt**: Add "blurry, soft focus, low res"
5. **Increase resolution**: Try 1536x1536
6. **Check the model**: Confirm it's using flux1-dev-fp8.safetensors

## File Size Reference

- **Small/blurry** (<500 KB): Usually low quality
- **Medium** (600-900 KB): Decent quality
- **Good** (900 KB - 1.2 MB): Good detail
- **Excellent** (1.2-2 MB+): High detail, sharp

Compare your outputs:
```bash
ls -lh outputs/
```

## Final Recommendation

For best results, always use:
```bash
venv/python.exe generate.py "YOUR_PROMPT, highly detailed, sharp focus, 8k" --steps 28 --cfg 4.5
```

The updated defaults (steps=25, cfg=4.0) should now produce much sharper images by default!
