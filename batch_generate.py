#!/usr/bin/env python3
"""
Batch Image Generation Script
Generates multiple images from a list of prompts using RunPod ComfyUI
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from runpod_utils import (
    RunPodClient,
    WorkflowBuilder,
    batch_process_prompts
)

# Load environment variables
load_dotenv()

# RunPod Configuration
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID")

# Validate configuration
if not RUNPOD_API_KEY or not ENDPOINT_ID:
    raise ValueError("RUNPOD_API_KEY and RUNPOD_ENDPOINT_ID must be set in .env file")

# Output directory
OUTPUT_DIR = Path(__file__).parent / "batch_outputs"


def main():
    """Main batch processing function"""
    print("=" * 60)
    print("Batch Image Generation with FLUX.1-dev-fp8")
    print("=" * 60)

    # Initialize client
    client = RunPodClient(api_key=RUNPOD_API_KEY, endpoint_id=ENDPOINT_ID)

    # Load workflow template
    workflow_template = WorkflowBuilder.load_workflow("flux_workflow.json")

    # Define prompts to generate
    prompts = [
        "a serene mountain landscape at sunset, professional photography, 8k, highly detailed",
        "a futuristic cyberpunk city with neon lights, rainy night, cinematic",
        "a magical forest with glowing mushrooms and fireflies, fantasy art",
        "a steampunk airship flying through clouds, detailed mechanical parts",
        "an underwater scene with colorful coral reef and tropical fish, vibrant colors"
    ]

    # Common settings
    negative_prompt = "blurry, low quality, distorted, ugly, bad anatomy"
    steps = 20
    cfg = 3.5
    width = 1024
    height = 1024

    print(f"\nGenerating {len(prompts)} images...")
    print(f"Settings: {steps} steps, CFG {cfg}, {width}x{height}")
    print(f"Output directory: {OUTPUT_DIR}")
    print("\nPrompts:")
    for i, prompt in enumerate(prompts, 1):
        print(f"  {i}. {prompt}")
    print("\n" + "=" * 60)

    # Process prompts
    # Set use_async=True to process in parallel (faster but may hit rate limits)
    # Set use_async=False to process sequentially (slower but more reliable)
    saved_images = batch_process_prompts(
        client=client,
        workflow_template=workflow_template,
        prompts=prompts,
        output_dir=str(OUTPUT_DIR),
        negative_prompt=negative_prompt,
        steps=steps,
        cfg=cfg,
        width=width,
        height=height,
        use_async=False  # Change to True for parallel processing
    )

    print("\n" + "=" * 60)
    print(f"✅ Batch processing complete!")
    print(f"Generated {len(saved_images)} image(s)")
    print("\nSaved images:")
    for img_path in saved_images:
        print(f"  - {img_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
