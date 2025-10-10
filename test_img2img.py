#!/usr/bin/env python3
"""
Simple img2img test script using the same workflow as telegram_bot.py
"""

import os
import json
import time
import base64
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# RunPod Configuration
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID")
RUNPOD_API_URL = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync"

# FLUX optimal settings
DEFAULT_STEPS = 28
DEFAULT_CFG = 1.0  # FLUX works best with CFG=1.0
DEFAULT_DENOISE = 0.75
DEFAULT_NEGATIVE = "blurry, low quality, distorted, ugly, deformed, pixelated, noise, artifacts"

# Output directory
OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


def load_image_as_base64(image_path: str) -> str:
    """Load an image file and convert to base64 string."""
    with open(image_path, 'rb') as f:
        image_data = f.read()
    return base64.b64encode(image_data).decode('utf-8')


def create_img2img_workflow(prompt: str, negative: str, denoise: float, steps: int, cfg: float, seed: int = None):
    """Create img2img workflow matching telegram_bot.py structure."""
    if seed is None:
        seed = int(time.time())

    workflow = {
        "6": {
            "inputs": {"text": prompt, "clip": ["30", 1]},
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "CLIP Text Encode (Prompt)"}
        },
        "8": {
            "inputs": {"samples": ["31", 0], "vae": ["30", 2]},
            "class_type": "VAEDecode",
            "_meta": {"title": "VAE Decode"}
        },
        "9": {
            "inputs": {"filename_prefix": "flux", "images": ["8", 0]},
            "class_type": "SaveImage",
            "_meta": {"title": "Save Image"}
        },
        "10": {
            "inputs": {"image": "input_image.png", "upload": "image"},  # Just filename, not base64!
            "class_type": "LoadImage",
            "_meta": {"title": "Load Image"}
        },
        "11": {
            "inputs": {"pixels": ["10", 0], "vae": ["30", 2]},
            "class_type": "VAEEncode",
            "_meta": {"title": "VAE Encode"}
        },
        "30": {
            "inputs": {"ckpt_name": "flux1-dev-fp8.safetensors"},
            "class_type": "CheckpointLoaderSimple",
            "_meta": {"title": "Load Checkpoint"}
        },
        "31": {
            "inputs": {
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": denoise,
                "model": ["30", 0],
                "positive": ["6", 0],
                "negative": ["33", 0],
                "latent_image": ["11", 0]  # From VAEEncode
            },
            "class_type": "KSampler",
            "_meta": {"title": "KSampler"}
        },
        "33": {
            "inputs": {"text": negative, "clip": ["30", 1]},
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "CLIP Text Encode (Negative)"}
        }
    }

    return workflow


def generate_img2img(prompt: str, image_path: str, denoise: float = DEFAULT_DENOISE,
                     steps: int = DEFAULT_STEPS, cfg: float = DEFAULT_CFG,
                     negative: str = DEFAULT_NEGATIVE, seed: int = None):
    """Generate img2img using RunPod API."""

    print(f"Loading image: {image_path}")
    image_base64 = load_image_as_base64(image_path)

    print(f"Creating workflow...")
    print(f"  Prompt: {prompt}")
    print(f"  Denoise: {denoise}")
    print(f"  Steps: {steps}, CFG: {cfg}")

    workflow = create_img2img_workflow(prompt, negative, denoise, steps, cfg, seed)

    # Build payload - send base64 in images array, NOT in workflow!
    payload = {
        "input": {
            "workflow": workflow,
            "images": [
                {
                    "name": "input_image.png",
                    "image": image_base64
                }
            ]
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {RUNPOD_API_KEY}"
    }

    print(f"\nSubmitting to RunPod...")
    response = requests.post(RUNPOD_API_URL, json=payload, headers=headers, timeout=300)
    response.raise_for_status()

    result = response.json()
    print(f"Status: {result.get('status')}")

    if result.get("status") == "COMPLETED":
        output = result.get("output", {})
        images = output.get("images", [])

        if images:
            img_data = images[0]

            # Handle dict or string format
            if isinstance(img_data, dict):
                img_str = img_data.get("image") or img_data.get("data")
            else:
                img_str = img_data

            # Remove data URI prefix if present
            if "," in img_str:
                img_str = img_str.split(",")[1]

            # Save image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"img2img_test_{timestamp}.png"
            output_path = OUTPUT_DIR / filename

            image_bytes = base64.b64decode(img_str)
            with open(output_path, 'wb') as f:
                f.write(image_bytes)

            print(f"\n✅ SUCCESS! Image saved to: {output_path}")
            return output_path
        else:
            print("❌ No images in response")
            return None
    else:
        error = result.get("error", "Unknown error")
        print(f"❌ Failed: {error}")
        return None


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python test_img2img.py <prompt> <image_path> [denoise]")
        print("Example: python test_img2img.py \"cyberpunk style\" outputs/test.png 0.75")
        sys.exit(1)

    prompt = sys.argv[1]
    image_path = sys.argv[2]
    denoise = float(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_DENOISE

    if not Path(image_path).exists():
        print(f"❌ Image not found: {image_path}")
        sys.exit(1)

    print("=" * 60)
    print("FLUX img2img Test")
    print("=" * 60)

    generate_img2img(prompt, image_path, denoise=denoise)
