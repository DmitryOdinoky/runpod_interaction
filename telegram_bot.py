#!/usr/bin/env python3
"""
Telegram Bot for FLUX Image Generation via RunPod
Dockerized version with MinIO storage support
"""

import os
import sys
import logging
import asyncio
import json
import base64
from datetime import datetime, timedelta
from pathlib import Path
from io import BytesIO

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import requests
from minio import Minio
from minio.error import S3Error

# Load environment variables
load_dotenv()

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
RUNPOD_ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID")
HUGGING_FACE_TOKEN = os.getenv("HUGGING_FACE_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# MinIO Configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "flux-images")
MINIO_USE_SSL = os.getenv("MINIO_USE_SSL", "false").lower() == "true"

# RunPod URL
RUNPOD_API_URL = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/runsync"

# Default generation settings
DEFAULT_STEPS = 28
DEFAULT_CFG = 1.0  # FLUX works best with CFG=1.0, not 3.5-4.0!
DEFAULT_WIDTH = 1280
DEFAULT_HEIGHT = 1280
DEFAULT_NEGATIVE = "blurry, low quality, distorted, ugly, deformed, pixelated, noise, artifacts"
DEFAULT_DENOISE = 0.75  # For img2img: 0.5 = subtle, 0.75 = moderate, 0.9 = strong changes

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# MinIO client
minio_client = None


def init_minio():
    """Initialize MinIO client and create bucket if it doesn't exist."""
    global minio_client
    try:
        minio_client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_USE_SSL
        )

        # Create bucket if it doesn't exist
        if not minio_client.bucket_exists(MINIO_BUCKET):
            minio_client.make_bucket(MINIO_BUCKET)
            logger.info(f"Created MinIO bucket: {MINIO_BUCKET}")
        else:
            logger.info(f"MinIO bucket exists: {MINIO_BUCKET}")

    except Exception as e:
        logger.error(f"Failed to initialize MinIO: {e}")
        minio_client = None


def load_workflow_template(mode: str = "txt2img") -> dict:
    """Load the FLUX workflow template from JSON file.

    Args:
        mode: "txt2img" or "img2img"
    """
    # For img2img, always use embedded workflow (JSON file is txt2img only)
    if mode == "img2img":
        logger.info("Using embedded img2img workflow")
    else:
        # Load txt2img workflow from JSON file
        workflow_file = Path(__file__).parent / "flux_workflow_simple.json"

        try:
            with open(workflow_file, 'r') as f:
                workflow = json.load(f)
            logger.info(f"Loaded workflow from {workflow_file}")
            return workflow
        except Exception as e:
            logger.error(f"Failed to load workflow from file: {e}, using fallback")

    # Fallback: embedded workflow (txt2img only)
    if mode == "txt2img":
        workflow = {
            "6": {
                "inputs": {"text": "", "clip": ["30", 1]},
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
            "27": {
                "inputs": {"width": 1280, "height": 1280, "batch_size": 1},
                "class_type": "EmptySD3LatentImage",
                "_meta": {"title": "EmptySD3LatentImage"}
            },
            "30": {
                "inputs": {"ckpt_name": "flux1-dev-fp8.safetensors"},
                "class_type": "CheckpointLoaderSimple",
                "_meta": {"title": "Load Checkpoint"}
            },
            "31": {
                "inputs": {
                    "seed": 42,
                    "steps": 28,
                    "cfg": 1.0,
                    "sampler_name": "euler",
                    "scheduler": "simple",
                    "denoise": 1,
                    "model": ["30", 0],
                    "positive": ["6", 0],
                    "negative": ["33", 0],
                    "latent_image": ["27", 0]
                },
                "class_type": "KSampler",
                "_meta": {"title": "KSampler"}
            },
            "33": {
                "inputs": {"text": "", "clip": ["30", 1]},
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode (Negative)"}
            }
        }
    else:  # img2img
        workflow = {
            "6": {
                "inputs": {"text": "", "clip": ["30", 1]},
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
                "inputs": {"image": "", "upload": "image"},
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
                    "seed": 42,
                    "steps": 28,
                    "cfg": 1.0,
                    "sampler_name": "euler",
                    "scheduler": "simple",
                    "denoise": 0.75,
                    "model": ["30", 0],
                    "positive": ["6", 0],
                    "negative": ["33", 0],
                    "latent_image": ["11", 0]  # From VAEEncode
                },
                "class_type": "KSampler",
                "_meta": {"title": "KSampler"}
            },
            "33": {
                "inputs": {"text": "", "clip": ["30", 1]},
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode (Negative)"}
            }
        }
    return workflow


def enhance_prompt_quality(prompt: str) -> str:
    """Add quality-enhancing keywords to the prompt if not already present.

    Args:
        prompt: Original user prompt

    Returns:
        Enhanced prompt with quality keywords
    """
    quality_keywords = [
        "highly detailed", "sharp focus", "professional quality",
        "8k resolution", "masterpiece", "best quality"
    ]

    # Check if prompt already has quality keywords
    prompt_lower = prompt.lower()
    has_quality_keywords = any(kw.lower() in prompt_lower for kw in quality_keywords)

    # If no quality keywords found, add them
    if not has_quality_keywords:
        # Add quality suffix
        enhanced = f"{prompt}, highly detailed, sharp focus, professional quality, 8k resolution"
        return enhanced

    return prompt


def modify_workflow(workflow: dict, prompt: str, negative: str = "",
                    steps: int = 28, cfg: float = 1.0,
                    width: int = 1280, height: int = 1280, seed: int = None,
                    denoise: float = 1.0, image_base64: str = None) -> dict:
    """Modify workflow with custom parameters.

    Args:
        workflow: The workflow dict to modify
        prompt: Positive prompt
        negative: Negative prompt
        steps: Number of sampling steps
        cfg: CFG scale
        width: Image width (txt2img only)
        height: Image height (txt2img only)
        seed: Random seed
        denoise: Denoise strength (0.0-1.0, for img2img)
        image_base64: Base64-encoded input image (for img2img)
    """
    import time

    workflow = json.loads(json.dumps(workflow))  # Deep copy

    # Update prompts (node 6 = positive, node 33 = negative)
    workflow["6"]["inputs"]["text"] = prompt
    workflow["33"]["inputs"]["text"] = negative or DEFAULT_NEGATIVE

    # Update sampling parameters (node 31 = KSampler)
    workflow["31"]["inputs"]["seed"] = seed if seed else int(time.time())
    workflow["31"]["inputs"]["steps"] = steps
    workflow["31"]["inputs"]["cfg"] = cfg
    workflow["31"]["inputs"]["denoise"] = denoise

    # Update dimensions for txt2img (node 27 = EmptySD3LatentImage)
    if "27" in workflow:
        workflow["27"]["inputs"]["width"] = width
        workflow["27"]["inputs"]["height"] = height

    # Update image for img2img (node 10 = LoadImage)
    if "10" in workflow and image_base64:
        workflow["10"]["inputs"]["image"] = image_base64

    return workflow


def generate_image(prompt: str, negative: str = "", steps: int = DEFAULT_STEPS,
                   cfg: float = DEFAULT_CFG, width: int = DEFAULT_WIDTH,
                   height: int = DEFAULT_HEIGHT, seed: int = None,
                   mode: str = "txt2img", image_base64: str = None,
                   denoise: float = DEFAULT_DENOISE) -> dict:
    """Generate image via RunPod API.

    Args:
        prompt: Positive prompt
        negative: Negative prompt
        steps: Number of sampling steps
        cfg: CFG scale
        width: Image width (txt2img only)
        height: Image height (txt2img only)
        seed: Random seed
        mode: "txt2img" or "img2img"
        image_base64: Base64-encoded input image (for img2img)
        denoise: Denoise strength (for img2img, 0.0-1.0)
    """
    try:
        workflow = load_workflow_template(mode=mode)

        # For img2img, set the image filename in workflow
        if mode == "img2img" and image_base64:
            image_filename = "input_image.png"
            workflow = modify_workflow(
                workflow, prompt, negative, steps, cfg, width, height, seed,
                denoise=denoise, image_base64=image_filename
            )
        else:
            # For txt2img, denoise MUST be 1.0 (full denoise)
            workflow = modify_workflow(
                workflow, prompt, negative, steps, cfg, width, height, seed,
                denoise=1.0, image_base64=None
            )

        # Log the actual workflow parameters being sent
        logger.info(f"Generating {mode} - Steps: {workflow['31']['inputs']['steps']}, CFG: {workflow['31']['inputs']['cfg']}, Size: {workflow.get('27', {}).get('inputs', {}).get('width', 'N/A')}x{workflow.get('27', {}).get('inputs', {}).get('height', 'N/A')}")

        # Debug: Log full workflow for troubleshooting
        logger.info(f"Full workflow being sent: {json.dumps(workflow, indent=2)}")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {RUNPOD_API_KEY}"
        }

        # Build payload with images array for img2img
        payload = {"input": {"workflow": workflow}}

        if mode == "img2img" and image_base64:
            payload["input"]["images"] = [
                {
                    "name": "input_image.png",
                    "image": image_base64
                }
            ]

        response = requests.post(RUNPOD_API_URL, json=payload, headers=headers, timeout=300)
        response.raise_for_status()

        return response.json()

    except Exception as e:
        logger.error(f"Error generating image: {e}")
        return {"status": "FAILED", "error": str(e)}


def extract_image_from_response(response: dict) -> bytes:
    """Extract base64 image data from RunPod response."""
    if response.get("status") != "COMPLETED":
        return None

    output = response.get("output", {})
    images = output.get("images", [])

    if not images:
        return None

    img_data = images[0]

    # Handle dict or string format
    if isinstance(img_data, dict):
        img_str = img_data.get("image") or img_data.get("data")
    else:
        img_str = img_data

    if not img_str:
        return None

    # Remove data URI prefix if present
    if "," in img_str:
        img_str = img_str.split(",")[1]

    return base64.b64decode(img_str)


def upload_to_minio(image_data: bytes, filename: str) -> str:
    """Upload image to MinIO and return URL."""
    if not minio_client:
        logger.warning("MinIO not available, skipping upload")
        return None

    try:
        # Upload to MinIO
        minio_client.put_object(
            MINIO_BUCKET,
            filename,
            BytesIO(image_data),
            len(image_data),
            content_type="image/png"
        )

        # Generate presigned URL (valid for 7 days)
        url = minio_client.presigned_get_object(MINIO_BUCKET, filename, expires=timedelta(days=7))
        logger.info(f"Uploaded to MinIO: {filename}")
        return url

    except S3Error as e:
        logger.error(f"MinIO upload error: {e}")
        return None


def describe_image_gemini(image_bytes: bytes) -> str:
    """Describe image using Google Gemini Vision API.

    Uses Gemini 2.5 Flash model for image understanding.
    """
    try:
        if not GEMINI_API_KEY:
            return "Gemini API key not configured. Please add GEMINI_API_KEY to .env file."

        # Convert to base64 for Gemini API
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')

        # Gemini API endpoint
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={GEMINI_API_KEY}"

        # Prompt for detailed image description
        prompt = """Analyze this image and provide a detailed description suitable for AI image generation. Include:
1. Main subject and composition
2. Visual style, colors, and lighting
3. Artistic techniques or photography style
4. Mood and atmosphere

Format as a single descriptive paragraph that could be used as an image generation prompt."""

        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_b64
                        }
                    }
                ]
            }]
        }

        headers = {"Content-Type": "application/json"}

        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()

        # Extract text from Gemini response
        if "candidates" in result and len(result["candidates"]) > 0:
            candidate = result["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                parts = candidate["content"]["parts"]
                if len(parts) > 0 and "text" in parts[0]:
                    description = parts[0]["text"].strip()
                    logger.info("Successfully got description from Gemini")
                    return description

        logger.warning(f"Unexpected Gemini response format: {result}")
        return "Unable to generate description from the image."

    except requests.exceptions.HTTPError as e:
        logger.error(f"Gemini API error: {e.response.status_code} - {e.response.text[:200]}")
        return f"API error: {e.response.status_code}. Please check your API key."
    except Exception as e:
        logger.error(f"Error describing image with Gemini: {e}")
        return f"Error processing image. Please try again later."


# Command Handlers

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    welcome_text = f"""
Hi {user.mention_html()}! 👋

I'm your FLUX Image Generator Bot powered by RunPod!

🎨 **How to use:**
• Send a text prompt to generate an image from scratch
• Send a photo with a caption to transform it (img2img)

📝 **Commands:**
/describe - Describe an image with AI
/settings - View current settings
/help - Show detailed help

**Examples:**
Text: "a beautiful sunset over mountains, professional photography, 8k"
Photo + Caption: "make it cyberpunk style with neon lights"
/describe + Photo: Get AI description of your image
"""
    await update.message.reply_html(welcome_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    help_text = """
🎨 **FLUX Image Generator Help**

**Two Modes:**

1️⃣ **Text-to-Image**
Send a text prompt to generate an image.
Example: "cyberpunk city, neon lights, 8k"

2️⃣ **Image-to-Image**
Upload a photo with a caption to transform it.
Examples:
• "watercolor painting style"
• "add neon cyberpunk lighting"
• "anime style"

3️⃣ **Describe Image**
Use /describe then send a photo to get AI description.
Perfect for reverse engineering prompts!

**Tips:**
• Denoise 0.75 = moderate changes
• Add "detailed, sharp, 8k" for quality
• Model: FLUX.1-dev-fp8
• CFG: 1.0, Steps: 20
"""
    await update.message.reply_text(help_text)


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current settings."""
    settings_text = f"""
⚙️ **Current Settings:**

**Text-to-Image (txt2img):**
• Steps: {DEFAULT_STEPS}
• CFG Scale: {DEFAULT_CFG}
• Width: {DEFAULT_WIDTH}
• Height: {DEFAULT_HEIGHT}

**Image-to-Image (img2img):**
• Steps: {DEFAULT_STEPS}
• CFG Scale: {DEFAULT_CFG}
• Denoise: {DEFAULT_DENOISE}

**Model:** FLUX.1-dev-fp8
**Endpoint:** {RUNPOD_ENDPOINT_ID}
**Storage:** {"MinIO ✓" if minio_client else "Local only"}
"""
    await update.message.reply_text(settings_text)


async def describe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /describe command - ask user to send an image."""
    # Set flag in user context
    context.user_data['awaiting_describe_image'] = True

    help_text = """
📝 **Image Description**

Send me a photo now and I'll describe what's in it!

This uses AI vision models to generate:
• Detailed description of the image content
• Style and artistic elements
• Suitable prompt for image generation
"""
    await update.message.reply_text(help_text)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages as image prompts."""
    prompt = update.message.text
    user = update.effective_user

    logger.info(f"Generating image for user {user.id}: {prompt[:50]}...")

    # Enhance prompt with quality keywords
    enhanced_prompt = enhance_prompt_quality(prompt)

    logger.info(f"Original prompt: {prompt}")
    logger.info(f"Enhanced prompt: {enhanced_prompt}")

    # Send initial response
    status_msg = await update.message.reply_text(
        "🎨 Generating your image...\n"
        f"Prompt: {prompt[:100]}...\n\n"
        "This may take 30-60 seconds..."
    )

    try:
        # Generate image
        response = await asyncio.to_thread(
            generate_image,
            prompt=enhanced_prompt,
            negative=DEFAULT_NEGATIVE,
            steps=DEFAULT_STEPS,
            cfg=DEFAULT_CFG
        )

        # Check status
        if response.get("status") != "COMPLETED":
            error_msg = response.get("error", "Unknown error")
            # Truncate error message to avoid Telegram's "Text too long" error
            error_msg = error_msg[:200] if len(error_msg) > 200 else error_msg
            await status_msg.edit_text(f"❌ Failed: {error_msg}")
            return

        # Extract image
        image_data = extract_image_from_response(response)

        if not image_data:
            await status_msg.edit_text("❌ No image data received")
            return

        # Debug: Save to outputs directory to compare quality
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_path = Path(__file__).parent / "outputs" / f"telegram_bot_{timestamp}.png"
        debug_path.parent.mkdir(exist_ok=True)
        with open(debug_path, 'wb') as f:
            f.write(image_data)
        logger.info(f"Debug: Saved image to {debug_path}")

        # Upload to MinIO (background storage, no user notification)
        if minio_client:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"flux_{user.id}_{timestamp}.png"
            await asyncio.to_thread(upload_to_minio, image_data, filename)

        # Send image to user as photo (with preview)
        await update.message.reply_photo(
            photo=BytesIO(image_data),
            caption=f"✅ Generated!\n\nPrompt: {prompt[:200]}"
        )

        # Delete status message
        await status_msg.delete()

        logger.info(f"Successfully generated image for user {user.id}")

    except Exception as e:
        logger.error(f"Error in handle_text_message: {e}")
        await status_msg.edit_text(f"❌ Error: {str(e)}")


async def handle_photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo messages - either describe or img2img."""
    user = update.effective_user

    # Check if user is in "describe mode"
    is_describe = context.user_data.get('awaiting_describe_image', False)

    # If it's a describe request, describe the image
    if is_describe:
        # Clear the flag
        context.user_data['awaiting_describe_image'] = False
        logger.info(f"Describing image for user {user.id}")

        status_msg = await update.message.reply_text("🔍 Analyzing your image...")

        try:
            # Get the largest photo
            photo = update.message.photo[-1]

            # Download photo
            file = await context.bot.get_file(photo.file_id)
            photo_bytes = await file.download_as_bytearray()

            # Describe image
            description = await asyncio.to_thread(describe_image_gemini, bytes(photo_bytes))

            # Send description
            await update.message.reply_text(
                f"📝 **Image Description:**\n\n{description}\n\n"
                f"💡 You can use this as a prompt for image generation!"
            )

            await status_msg.delete()
            logger.info(f"Successfully described image for user {user.id}")

        except Exception as e:
            logger.error(f"Error in describe mode: {e}")
            await status_msg.edit_text(f"❌ Error: {str(e)[:100]}")

        return

    # Otherwise, do img2img
    prompt = update.message.caption or "enhance this image, professional quality, highly detailed"
    logger.info(f"Img2img generation for user {user.id}: {prompt[:50]}...")

    # Enhance prompt with quality keywords
    enhanced_prompt = enhance_prompt_quality(prompt)

    # Send initial response
    status_msg = await update.message.reply_text(
        "🎨 Processing your image...\n"
        f"Prompt: {prompt[:100]}...\n\n"
        "This may take 30-60 seconds..."
    )

    try:
        # Get the largest photo
        photo = update.message.photo[-1]

        # Download photo
        file = await context.bot.get_file(photo.file_id)
        photo_bytes = await file.download_as_bytearray()

        # Convert to base64
        image_base64 = base64.b64encode(bytes(photo_bytes)).decode('utf-8')

        # Generate image
        response = await asyncio.to_thread(
            generate_image,
            prompt=enhanced_prompt,
            negative=DEFAULT_NEGATIVE,
            steps=DEFAULT_STEPS,
            cfg=DEFAULT_CFG,
            mode="img2img",
            image_base64=image_base64,
            denoise=DEFAULT_DENOISE
        )

        # Check status
        if response.get("status") != "COMPLETED":
            error_msg = response.get("error", "Unknown error")
            # Truncate error message to avoid Telegram's "Text too long" error
            error_msg = error_msg[:200] if len(error_msg) > 200 else error_msg
            await status_msg.edit_text(f"❌ Failed: {error_msg}")
            return

        # Extract image
        image_data = extract_image_from_response(response)

        if not image_data:
            await status_msg.edit_text("❌ No image data received")
            return

        # Debug: Save to outputs directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_path = Path(__file__).parent / "outputs" / f"telegram_bot_img2img_{timestamp}.png"
        debug_path.parent.mkdir(exist_ok=True)
        with open(debug_path, 'wb') as f:
            f.write(image_data)
        logger.info(f"Debug: Saved img2img result to {debug_path}")

        # Upload to MinIO (background storage, no user notification)
        if minio_client:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"flux_img2img_{user.id}_{timestamp}.png"
            await asyncio.to_thread(upload_to_minio, image_data, filename)

        # Send image to user as photo (with preview)
        await update.message.reply_photo(
            photo=BytesIO(image_data),
            caption=f"✅ Transformed!\n\nPrompt: {prompt[:200]}\nDenoise: {DEFAULT_DENOISE}"
        )

        # Delete status message
        await status_msg.delete()

        logger.info(f"Successfully generated img2img for user {user.id}")

    except Exception as e:
        logger.error(f"Error in handle_photo_message: {e}")
        await status_msg.edit_text(f"❌ Error: {str(e)}")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors caused by updates."""
    logger.error(f"Update {update} caused error {context.error}")


def main():
    """Start the bot."""
    # Validate configuration
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        sys.exit(1)

    if not RUNPOD_API_KEY or not RUNPOD_ENDPOINT_ID:
        logger.error("RunPod credentials not set!")
        sys.exit(1)

    # Initialize MinIO
    init_minio()

    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("describe", describe_command))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    # Add error handler
    application.add_error_handler(error_handler)

    # Start bot
    logger.info("Starting Telegram bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
