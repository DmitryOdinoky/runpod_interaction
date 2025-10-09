# Quick Usage Guide

## Text-to-Image Generation

### Basic Usage
```bash
venv/python.exe generate.py "your prompt here"
```

### Examples

**Simple prompt:**
```bash
venv/python.exe generate.py "a serene mountain landscape at sunset"
```

**With negative prompt:**
```bash
venv/python.exe generate.py "cyberpunk city at night" --negative "blurry, ugly, distorted"
```

**High quality settings:**
```bash
venv/python.exe generate.py "fantasy dragon in mountains" --steps 30 --cfg 4.5
```

**Portrait format:**
```bash
venv/python.exe generate.py "portrait of an elegant woman" --width 768 --height 1024
```

**Landscape format:**
```bash
venv/python.exe generate.py "wide ocean view" --width 1280 --height 720
```

**Reproducible (with seed):**
```bash
venv/python.exe generate.py "magical forest" --seed 42
```

### All Options
```bash
venv/python.exe generate.py "prompt" [OPTIONS]

Options:
  --negative, -n TEXT    Negative prompt (default: "blurry, low quality...")
  --steps, -s INTEGER    Sampling steps (default: 20)
  --cfg, -c FLOAT        CFG scale (default: 3.5)
  --width, -w INTEGER    Image width (default: 1024)
  --height, -h INTEGER   Image height (default: 1024)
  --seed INTEGER         Random seed for reproducibility
```

## Image-to-Image Generation

### Basic Usage
```bash
venv/python.exe generate_img2img.py "your prompt" --image source.jpg
```

### Examples

**Transform photo to art style:**
```bash
venv/python.exe generate_img2img.py "oil painting style" --image photo.jpg
```

**With custom strength:**
```bash
venv/python.exe generate_img2img.py "cyberpunk style" --image city.jpg --strength 0.6
```

**High quality transformation:**
```bash
venv/python.exe generate_img2img.py "anime style" --image portrait.jpg --steps 30 --cfg 5.0
```

### Strength Parameter
- `0.0-0.3`: Subtle changes, keeps most of original
- `0.4-0.6`: Moderate changes, balanced transformation
- `0.7-0.9`: Strong changes, mostly new image
- `1.0`: Complete regeneration (like text-to-image)

### All Options
```bash
venv/python.exe generate_img2img.py "prompt" --image PATH [OPTIONS]

Required:
  --image, -i PATH       Source image file

Options:
  --negative, -n TEXT    Negative prompt
  --strength FLOAT       Denoising strength 0.0-1.0 (default: 0.75)
  --steps, -s INTEGER    Sampling steps (default: 20)
  --cfg, -c FLOAT        CFG scale (default: 3.5)
  --seed INTEGER         Random seed
```

**Note:** Image-to-image requires additional nodes (LoadImage, VAEEncode) on the RunPod worker. If you get validation errors, the worker may not support img2img operations yet.

## Tips for Best Results

### Prompting
- Be specific and descriptive
- Include style keywords: "professional photography", "oil painting", "anime", "photorealistic"
- Add quality modifiers: "8k", "highly detailed", "masterpiece", "best quality"
- Use negative prompts to avoid unwanted elements

### Parameters
- **Steps (15-30)**: More steps = more detail, but slower
  - 15-20: Fast, good for testing
  - 20-25: Balanced quality/speed
  - 25-30: High quality, slower

- **CFG Scale (1.0-7.0)**: How closely to follow the prompt
  - 1.0-2.0: Very creative, loose interpretation
  - 3.0-4.0: Balanced (recommended for FLUX)
  - 5.0-7.0: Strict adherence to prompt

- **Dimensions**: Should be multiples of 64
  - Common: 512, 768, 1024, 1280, 1536
  - Standard: 1024x1024
  - Portrait: 768x1024 or 720x1280
  - Landscape: 1280x720 or 1536x864

### Good Prompt Examples

**Landscape:**
```
"a serene mountain landscape at golden hour, professional photography,
highly detailed, 8k, atmospheric lighting, volumetric fog"
```

**Portrait:**
```
"portrait of a woman with flowing hair, elegant, soft lighting,
professional photo, detailed face, bokeh background, high quality"
```

**Fantasy:**
```
"epic fantasy dragon perched on mountain peak, detailed scales,
dramatic lighting, cinematic, highly detailed, concept art style"
```

**Sci-fi:**
```
"futuristic cyberpunk city street at night, neon signs, rain reflections,
cinematic composition, highly detailed, blade runner style"
```

## Output Files

All generated images are saved to the `outputs/` directory with timestamps:
- Text-to-image: `flux_output_YYYYMMDD_HHMMSS_0.png`
- Image-to-image: `flux_img2img_YYYYMMDD_HHMMSS_0.png`

## Troubleshooting

**"Module not found" error:**
```bash
venv/python.exe -m pip install -r requirements.txt
```

**"Required input is missing" or validation errors:**
- The workflow may not be compatible with the worker
- Try text-to-image first (always works)
- Image-to-image may not be supported by all workers

**Images are blurry:**
- Increase steps to 25-30
- Adjust CFG to 4.0-5.0
- Add quality keywords to prompt
- Use stronger negative prompt

**Images don't match prompt:**
- Increase CFG scale
- Be more specific in prompt
- Try different seed values
- Add style keywords

**Timeout errors:**
- Reduce image size
- Decrease steps
- Check RunPod worker status

## Quick Reference

### Fast test:
```bash
venv/python.exe generate.py "test prompt"
```

### High quality:
```bash
venv/python.exe generate.py "your prompt" --steps 30 --cfg 4.5 --width 1536 --height 1536
```

### Reproducible:
```bash
venv/python.exe generate.py "your prompt" --seed 12345
```

### Portrait:
```bash
venv/python.exe generate.py "portrait prompt" --width 768 --height 1024
```

### Batch (edit batch_generate.py for multiple prompts):
```bash
venv/python.exe batch_generate.py
```
