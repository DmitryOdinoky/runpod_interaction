#!/usr/bin/env python3
"""
Image-to-Image Generator for RunPod ComfyUI
Generates images based on a text prompt and optional source image

Usage:
    python generate_img2img.py "your prompt" --image source.png
    python generate_img2img.py "cyberpunk style" --image photo.jpg --strength 0.7
"""

import os
import json
import time
import base64
import argparse
import sys
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

# Output directory
OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


def load_image_as_base64(image_path: str) -> str:
    """Load an image file and convert to base64 string."""
    with open(image_path, 'rb') as f:
        image_data = f.read()
    return base64.b64encode(image_data).decode('utf-8')


def create_img2img_workflow(prompt: str, negative_prompt: str, image_base64: str,
                            strength: float = 0.75, steps: int = 20, cfg: float = 3.5,
                            width: int = 1024, height: int = 1024, seed: int = None) -> dict:
    """
    Create an image-to-image workflow.

    Note: This is a simplified workflow. For full img2img support, the RunPod worker
    needs to have the appropriate nodes installed (LoadImage, VAEEncode, etc.)
    """
    if seed is None:
        seed = int(time.time())

    workflow = {
        "3": {
            "inputs": {
                "image": image_base64,
                "upload": "image"
            },
            "class_type": "LoadImage",
            "_meta": {"title": "Load Image"}
        },
        "6": {
            "inputs": {
                "text": prompt,
                "clip": ["30", 1]
            },
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "CLIP Text Encode (Prompt)"}
        },
        "8": {
            "inputs": {
                "samples": ["31", 0],
                "vae": ["30", 2]
            },
            "class_type": "VAEDecode",
            "_meta": {"title": "VAE Decode"}
        },
        "9": {
            "inputs": {
                "filename_prefix": "flux_img2img",
                "images": ["8", 0]
            },
            "class_type": "SaveImage",
            "_meta": {"title": "Save Image"}
        },
        "10": {
            "inputs": {
                "pixels": ["3", 0],
                "vae": ["30", 2]
            },
            "class_type": "VAEEncode",
            "_meta": {"title": "VAE Encode"}
        },
        "30": {
            "inputs": {
                "ckpt_name": "flux1-dev-fp8.safetensors"
            },
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
                "denoise": strength,
                "model": ["30", 0],
                "positive": ["6", 0],
                "negative": ["33", 0],
                "latent_image": ["10", 0]
            },
            "class_type": "KSampler",
            "_meta": {"title": "KSampler"}
        },
        "33": {
            "inputs": {
                "text": negative_prompt,
                "clip": ["30", 1]
            },
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "CLIP Text Encode (Negative)"}
        }
    }

    return workflow


def submit_job(workflow: dict) -> dict:
    """Submit job to RunPod endpoint."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {RUNPOD_API_KEY}"
    }

    payload = {"input": {"workflow": workflow}}

    print(f"Submitting job to RunPod endpoint: {ENDPOINT_ID}")
    response = requests.post(RUNPOD_API_URL, json=payload, headers=headers, timeout=300)
    response.raise_for_status()

    return response.json()


def save_image_from_base64(base64_data: str, filename: str) -> Path:
    """Save base64 encoded image to file."""
    output_path = OUTPUT_DIR / filename

    if "," in base64_data:
        base64_data = base64_data.split(",")[1]

    image_data = base64.b64decode(base64_data)

    with open(output_path, 'wb') as f:
        f.write(image_data)

    print(f"[OK] Image saved to: {output_path}")
    return output_path


def process_response(response: dict) -> list:
    """Process RunPod response and save images."""
    saved_images = []

    if response.get("status") == "COMPLETED":
        output = response.get("output", {})

        if "images" in output:
            images = output["images"]
            for idx, img_data in enumerate(images):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"flux_img2img_{timestamp}_{idx}.png"

                if isinstance(img_data, dict):
                    if "image" in img_data:
                        img_str = img_data["image"]
                    elif "data" in img_data:
                        img_str = img_data["data"]
                    else:
                        print(f"[WARNING] Unknown image dict format: {list(img_data.keys())}")
                        continue
                else:
                    img_str = img_data

                saved_path = save_image_from_base64(img_str, filename)
                saved_images.append(saved_path)

        print(f"\n[SUCCESS] Job completed! Generated {len(saved_images)} image(s)")

    elif response.get("status") == "FAILED":
        error_msg = response.get("error", "Unknown error")
        print(f"\n[ERROR] Job failed: {error_msg}")

    else:
        print(f"\n[WARNING] Unexpected status: {response.get('status')}")
        print(f"Response: {json.dumps(response, indent=2)}")

    return saved_images


def main():
    parser = argparse.ArgumentParser(
        description='Image-to-Image generation with FLUX.1-dev-fp8',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_img2img.py "cyberpunk style" --image photo.jpg
  python generate_img2img.py "oil painting" --image sketch.png --strength 0.6
  python generate_img2img.py "anime style" --image portrait.jpg --steps 30 --cfg 5.0

Note: Image-to-image requires LoadImage and VAEEncode nodes on the RunPod worker.
If you get validation errors, the worker may not support img2img operations.
        """
    )

    parser.add_argument('prompt', type=str, help='Text prompt for image generation')
    parser.add_argument('--image', '-i', type=str, required=True, help='Path to source image')
    parser.add_argument('--negative', '-n', type=str, default='blurry, low quality, distorted', help='Negative prompt')
    parser.add_argument('--strength', type=float, default=0.75, help='Denoising strength 0.0-1.0 (default: 0.75)')
    parser.add_argument('--steps', '-s', type=int, default=20, help='Sampling steps (default: 20)')
    parser.add_argument('--cfg', '-c', type=float, default=3.5, help='CFG scale (default: 3.5)')
    parser.add_argument('--seed', type=int, default=None, help='Random seed')

    args = parser.parse_args()

    # Validate image path
    if not Path(args.image).exists():
        print(f"[ERROR] Image file not found: {args.image}")
        return 1

    # Display settings
    print("=" * 60)
    print("RunPod FLUX Image-to-Image Generator")
    print("=" * 60)
    print(f"Source Image: {args.image}")
    print(f"Prompt: {args.prompt}")
    print(f"Negative: {args.negative}")
    print(f"Strength: {args.strength}")
    print(f"Steps: {args.steps}, CFG: {args.cfg}")
    if args.seed:
        print(f"Seed: {args.seed}")
    print("=" * 60)
    print()

    try:
        # Load source image
        print("Loading source image...")
        image_base64 = load_image_as_base64(args.image)

        # Create workflow
        print("Creating workflow...")
        workflow = create_img2img_workflow(
            prompt=args.prompt,
            negative_prompt=args.negative,
            image_base64=image_base64,
            strength=args.strength,
            steps=args.steps,
            cfg=args.cfg,
            seed=args.seed
        )

        # Submit job
        response = submit_job(workflow)

        # Process results
        images = process_response(response)

        if images:
            print("\n" + "=" * 60)
            print("Image(s) saved successfully!")
            for img_path in images:
                print(f"  {img_path}")
            print("=" * 60)
            return 0
        else:
            print("\n[ERROR] No images generated")
            return 1

    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
