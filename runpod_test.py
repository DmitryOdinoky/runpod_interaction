#!/usr/bin/env python3
"""
RunPod ComfyUI FLUX Test Script
Tests the RunPod endpoint with FLUX.1-dev-fp8 model
"""

import os
import json
import time
import base64
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# RunPod Configuration
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID")
RUNPOD_API_URL = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync"

# Validate configuration
if not RUNPOD_API_KEY or not ENDPOINT_ID:
    raise ValueError("RUNPOD_API_KEY and RUNPOD_ENDPOINT_ID must be set in .env file")

# Output directory for generated images
OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


def load_workflow(workflow_path: str = "flux_workflow_simple.json") -> dict:
    """Load the ComfyUI workflow JSON file."""
    workflow_file = Path(__file__).parent / workflow_path
    with open(workflow_file, 'r') as f:
        return json.load(f)


def modify_workflow_prompt(workflow: dict, positive_prompt: str, negative_prompt: str = "",
                           seed: int = None, steps: int = 28, cfg: float = 1.0,
                           width: int = 1280, height: int = 1280) -> dict:
    """
    Modify the workflow with custom parameters.

    Args:
        workflow: The base workflow dictionary
        positive_prompt: The positive text prompt
        negative_prompt: The negative text prompt (optional)
        seed: Random seed (None for random)
        steps: Number of sampling steps
        cfg: CFG scale
        width: Image width
        height: Image height

    Returns:
        Modified workflow dictionary
    """
    workflow_copy = json.loads(json.dumps(workflow))  # Deep copy

    # Update prompts (node 6 = positive, node 33 = negative)
    if "6" in workflow_copy:
        workflow_copy["6"]["inputs"]["text"] = positive_prompt
    if "33" in workflow_copy:
        workflow_copy["33"]["inputs"]["text"] = negative_prompt

    # Update sampling parameters (node 31 = KSampler)
    if "31" in workflow_copy:
        if seed is not None:
            workflow_copy["31"]["inputs"]["seed"] = seed
        else:
            workflow_copy["31"]["inputs"]["seed"] = int(time.time())
        workflow_copy["31"]["inputs"]["steps"] = steps
        workflow_copy["31"]["inputs"]["cfg"] = cfg

    # Update dimensions (node 27 = EmptySD3LatentImage)
    if "27" in workflow_copy:
        workflow_copy["27"]["inputs"]["width"] = width
        workflow_copy["27"]["inputs"]["height"] = height

    return workflow_copy


def submit_job(workflow: dict) -> dict:
    """
    Submit a job to RunPod endpoint.

    Args:
        workflow: The ComfyUI workflow to execute

    Returns:
        Response from RunPod API
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {RUNPOD_API_KEY}"
    }

    payload = {
        "input": {
            "workflow": workflow
        }
    }

    print(f"Submitting job to RunPod endpoint: {ENDPOINT_ID}")
    response = requests.post(RUNPOD_API_URL, json=payload, headers=headers)
    response.raise_for_status()

    return response.json()


def save_image_from_base64(base64_data: str, filename: str) -> Path:
    """
    Save base64 encoded image to file.

    Args:
        base64_data: Base64 encoded image data
        filename: Output filename

    Returns:
        Path to saved file
    """
    output_path = OUTPUT_DIR / filename

    # Remove data URI prefix if present
    if "," in base64_data:
        base64_data = base64_data.split(",")[1]

    image_data = base64.b64decode(base64_data)

    with open(output_path, 'wb') as f:
        f.write(image_data)

    print(f"[OK] Image saved to: {output_path}")
    return output_path


def process_response(response: dict) -> list:
    """
    Process RunPod response and save generated images.

    Args:
        response: Response from RunPod API

    Returns:
        List of paths to saved images
    """
    saved_images = []

    if response.get("status") == "COMPLETED":
        output = response.get("output", {})

        # Handle different response formats
        if "images" in output:
            images = output["images"]
            for idx, img_data in enumerate(images):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"flux_output_{timestamp}_{idx}.png"

                # Check if img_data is a dict with base64 data
                if isinstance(img_data, dict):
                    # Try to extract base64 data from dict
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

        elif "message" in output:
            # Handle different output structure
            message = output["message"]
            if isinstance(message, dict) and "images" in message:
                for idx, img_data in enumerate(message["images"]):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"flux_output_{timestamp}_{idx}.png"

                    # Check if img_data is a dict with base64 data
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

        print(f"\n[SUCCESS] Job completed successfully! Generated {len(saved_images)} image(s)")

    elif response.get("status") == "FAILED":
        error_msg = response.get("error", "Unknown error")
        print(f"\n[ERROR] Job failed: {error_msg}")

    else:
        print(f"\n[WARNING] Unexpected status: {response.get('status')}")
        print(f"Response: {json.dumps(response, indent=2)}")

    return saved_images


def run_test(prompt: str, negative_prompt: str = "", steps: int = 28,
             cfg: float = 1.0, width: int = 1280, height: int = 1280, seed: int = None):
    """
    Run a complete test: load workflow, submit job, save results.

    Args:
        prompt: Positive text prompt
        negative_prompt: Negative text prompt
        steps: Number of sampling steps
        cfg: CFG scale
        width: Image width
        height: Image height
        seed: Random seed
    """
    print("=" * 60)
    print("RunPod ComfyUI FLUX Test")
    print("=" * 60)
    print(f"Prompt: {prompt}")
    print(f"Steps: {steps}, CFG: {cfg}, Size: {width}x{height}")
    if seed:
        print(f"Seed: {seed}")
    print("=" * 60)

    try:
        # Load and modify workflow
        workflow = load_workflow()
        workflow = modify_workflow_prompt(
            workflow, prompt, negative_prompt,
            seed=seed, steps=steps, cfg=cfg,
            width=width, height=height
        )

        # Submit job
        response = submit_job(workflow)

        # Process results
        saved_images = process_response(response)

        return saved_images

    except Exception as e:
        print(f"\n[ERROR] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    # Test with a sample prompt
    test_prompt = "a mystical forest with glowing mushrooms and fireflies, magical atmosphere, fantasy art, highly detailed, sharp focus, professional quality, 8k resolution, vibrant colors"
    negative_prompt = "blurry, low quality, distorted, ugly, deformed, pixelated, noise, artifacts"

    images = run_test(
        prompt=test_prompt,
        negative_prompt=negative_prompt,
        steps=28,
        cfg=1.0,
        width=1280,
        height=1280,
        seed=42
    )

    if images:
        print(f"\n[SUCCESS] Generated {len(images)} image(s)")
        for img_path in images:
            print(f"   - {img_path}")
    else:
        print("\n[WARNING] No images generated")
