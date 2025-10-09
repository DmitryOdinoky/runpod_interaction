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
from datetime import datetime
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

# MinIO Configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "flux-images")
MINIO_USE_SSL = os.getenv("MINIO_USE_SSL", "false").lower() == "true"

# RunPod URL
RUNPOD_API_URL = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/runsync"

# Default generation settings
DEFAULT_STEPS = 25
DEFAULT_CFG = 4.0
DEFAULT_WIDTH = 1024
DEFAULT_HEIGHT = 1024
DEFAULT_NEGATIVE = "blurry, low quality, distorted, ugly, bad anatomy, low res, poorly drawn"

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


def load_workflow_template() -> dict:
    """Load the FLUX workflow template."""
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
            "inputs": {"width": 1024, "height": 1024, "batch_size": 1},
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
                "steps": 20,
                "cfg": 3.5,
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
    return workflow


def modify_workflow(workflow: dict, prompt: str, negative: str = "",
                    steps: int = 25, cfg: float = 4.0,
                    width: int = 1024, height: int = 1024, seed: int = None) -> dict:
    """Modify workflow with custom parameters."""
    import time

    workflow = json.loads(json.dumps(workflow))  # Deep copy

    # Update prompts (node 6 = positive, node 33 = negative)
    workflow["6"]["inputs"]["text"] = prompt
    workflow["33"]["inputs"]["text"] = negative or DEFAULT_NEGATIVE

    # Update sampling parameters (node 31 = KSampler)
    workflow["31"]["inputs"]["seed"] = seed if seed else int(time.time())
    workflow["31"]["inputs"]["steps"] = steps
    workflow["31"]["inputs"]["cfg"] = cfg

    # Update dimensions (node 27 = EmptySD3LatentImage)
    workflow["27"]["inputs"]["width"] = width
    workflow["27"]["inputs"]["height"] = height

    return workflow


def generate_image(prompt: str, negative: str = "", steps: int = DEFAULT_STEPS,
                   cfg: float = DEFAULT_CFG, width: int = DEFAULT_WIDTH,
                   height: int = DEFAULT_HEIGHT, seed: int = None) -> dict:
    """Generate image via RunPod API."""
    try:
        workflow = load_workflow_template()
        workflow = modify_workflow(workflow, prompt, negative, steps, cfg, width, height, seed)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {RUNPOD_API_KEY}"
        }

        payload = {"input": {"workflow": workflow}}

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
        url = minio_client.presigned_get_object(MINIO_BUCKET, filename, expires=604800)
        logger.info(f"Uploaded to MinIO: {filename}")
        return url

    except S3Error as e:
        logger.error(f"MinIO upload error: {e}")
        return None


# Command Handlers

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    welcome_text = f"""
Hi {user.mention_html()}! 👋

I'm your FLUX Image Generator Bot powered by RunPod!

🎨 **Commands:**
/generate - Generate an image from text
/settings - View current settings
/help - Show detailed help

Just send me a text prompt and I'll generate an image for you!

Example: "a beautiful sunset over mountains, professional photography, 8k"
"""
    await update.message.reply_html(welcome_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    help_text = """
🎨 **FLUX Image Generator Help**

**Basic Usage:**
Just send me a text prompt and I'll generate an image!

**Advanced Options:**
Use /generate with custom settings:
• Steps: 15-35 (default: 25)
• CFG: 1.0-7.0 (default: 4.0)
• Size: Custom dimensions

**Quality Tips:**
• Add "highly detailed, sharp focus, 8k" to prompts
• Use 25-30 steps for best quality
• Try CFG 4.0-5.0 for sharp images

**Examples:**
"cyberpunk city at night, neon lights, highly detailed, 8k"
"portrait of a cat, professional photography, sharp focus"
"fantasy landscape, concept art, intricate details"

Model: FLUX.1-dev-fp8
"""
    await update.message.reply_text(help_text)


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current settings."""
    settings_text = f"""
⚙️ **Current Settings:**

**Default Generation:**
• Steps: {DEFAULT_STEPS}
• CFG Scale: {DEFAULT_CFG}
• Width: {DEFAULT_WIDTH}
• Height: {DEFAULT_HEIGHT}

**Model:** FLUX.1-dev-fp8
**Endpoint:** {RUNPOD_ENDPOINT_ID}
**Storage:** {"MinIO ✓" if minio_client else "Local only"}
"""
    await update.message.reply_text(settings_text)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages as image prompts."""
    prompt = update.message.text
    user = update.effective_user

    logger.info(f"Generating image for user {user.id}: {prompt[:50]}...")

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
            prompt=prompt,
            negative=DEFAULT_NEGATIVE,
            steps=DEFAULT_STEPS,
            cfg=DEFAULT_CFG
        )

        # Check status
        if response.get("status") != "COMPLETED":
            error_msg = response.get("error", "Unknown error")
            await status_msg.edit_text(f"❌ Generation failed: {error_msg}")
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

        # Upload to MinIO (optional)
        minio_url = None
        if minio_client:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"flux_{user.id}_{timestamp}.png"
            minio_url = await asyncio.to_thread(upload_to_minio, image_data, filename)

        # Send image to user as document (preserves quality, no Telegram compression)
        await update.message.reply_document(
            document=BytesIO(image_data),
            filename="flux_generated.png",
            caption=f"✅ Generated!\n\nPrompt: {prompt[:200]}"
        )

        # Delete status message
        await status_msg.delete()

        # Send MinIO URL if available
        if minio_url:
            await update.message.reply_text(
                f"📁 Permanent link (valid 7 days):\n{minio_url}",
                disable_web_page_preview=True
            )

        logger.info(f"Successfully generated image for user {user.id}")

    except Exception as e:
        logger.error(f"Error in handle_text_message: {e}")
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
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    # Add error handler
    application.add_error_handler(error_handler)

    # Start bot
    logger.info("Starting Telegram bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
