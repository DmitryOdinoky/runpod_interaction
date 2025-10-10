#!/usr/bin/env python3
"""
Simple command-line image generator for RunPod ComfyUI
Usage:
    python generate.py "your prompt here"
    python generate.py "your prompt here" --negative "bad quality, blurry"
    python generate.py "your prompt here" --steps 30 --cfg 4.0
    python generate.py "your prompt here" --width 1280 --height 720
    python generate.py "your prompt here" --seed 12345
"""

import argparse
import sys
from runpod_test import run_test


def main():
    parser = argparse.ArgumentParser(
        description='Generate images with FLUX.1-dev-fp8 via RunPod',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate.py "a beautiful sunset over the ocean"
  python generate.py "cyberpunk city" --negative "blurry, ugly" --steps 25
  python generate.py "fantasy dragon" --width 1280 --height 720 --cfg 4.0
  python generate.py "portrait of a cat" --seed 42
        """
    )

    # Required argument
    parser.add_argument(
        'prompt',
        type=str,
        help='The text prompt for image generation'
    )

    # Optional arguments
    parser.add_argument(
        '--negative', '-n',
        type=str,
        default='blurry, low quality, distorted, ugly, bad anatomy, low res, poorly drawn, deformed, pixelated, noise, artifacts',
        help='Negative prompt (default: "blurry, low quality, distorted, ugly, bad anatomy, low res, poorly drawn, deformed, pixelated, noise, artifacts")'
    )

    parser.add_argument(
        '--steps', '-s',
        type=int,
        default=28,
        help='Number of sampling steps (default: 28, recommended: 25-30 for quality)'
    )

    parser.add_argument(
        '--cfg', '-c',
        type=float,
        default=1.0,
        help='CFG scale (default: 1.0, FLUX works best with CFG=1.0)'
    )

    parser.add_argument(
        '--width', '-w',
        type=int,
        default=1280,
        help='Image width (default: 1280)'
    )

    parser.add_argument(
        '--height',
        type=int,
        default=1280,
        help='Image height (default: 1280)'
    )

    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help='Random seed for reproducibility (default: random)'
    )

    args = parser.parse_args()

    # Display settings
    print("=" * 60)
    print("RunPod FLUX Image Generator")
    print("=" * 60)
    print(f"Prompt: {args.prompt}")
    print(f"Negative: {args.negative}")
    print(f"Steps: {args.steps}, CFG: {args.cfg}")
    print(f"Size: {args.width}x{args.height}")
    if args.seed:
        print(f"Seed: {args.seed}")
    print("=" * 60)
    print()

    # Generate image
    images = run_test(
        prompt=args.prompt,
        negative_prompt=args.negative,
        steps=args.steps,
        cfg=args.cfg,
        width=args.width,
        height=args.height,
        seed=args.seed
    )

    if images:
        print("\n" + "=" * 60)
        print("Image(s) saved successfully!")
        for img_path in images:
            print(f"  {img_path}")
        print("=" * 60)
        return 0
    else:
        print("\n[ERROR] Failed to generate images")
        return 1


if __name__ == "__main__":
    sys.exit(main())
