# RunPod ComfyUI Interaction Scripts

Python scripts for interacting with RunPod ComfyUI endpoints using FLUX.1-dev-fp8 model.

## Overview

This repository contains scripts and utilities for generating images using ComfyUI workflows on RunPod serverless infrastructure. It supports both synchronous and asynchronous job submission, batch processing, and flexible workflow customization.

## Features

- **Simple Test Script**: Quick testing with single prompts
- **Utility Module**: Reusable classes and functions for RunPod interactions
- **Batch Processing**: Generate multiple images from a list of prompts
- **Flexible Workflows**: Easy customization of prompts, dimensions, and sampling parameters
- **Async Support**: Process multiple images in parallel
- **Image Handling**: Automatic base64 decoding and file saving

## Prerequisites

- Python 3.8+
- RunPod account with active endpoint
- RunPod API key and endpoint ID

## Installation

1. Clone the repository:
```bash
git clone git@github.com:DmitryOdinoky/runpod_interaction.git
cd runpod_interaction
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Update the API credentials in the scripts:

```python
RUNPOD_API_KEY = "your_api_key_here"
ENDPOINT_ID = "your_endpoint_id_here"
```

Or set them as environment variables:
```bash
export RUNPOD_API_KEY="your_api_key_here"
export ENDPOINT_ID="your_endpoint_id_here"
```

## Files

### Core Files

- **`flux_workflow.json`**: ComfyUI workflow for FLUX.1-dev-fp8 model
- **`runpod_test.py`**: Simple test script for single image generation
- **`runpod_utils.py`**: Utility module with helper classes
- **`batch_generate.py`**: Batch processing script
- **`requirements.txt`**: Python dependencies

### Output Directories

- **`outputs/`**: Generated images from test script
- **`batch_outputs/`**: Generated images from batch processing

## Usage

### 1. Simple Test

Generate a single image with a test prompt:

```bash
python runpod_test.py
```

This will generate an image using the default test prompt and save it to the `outputs/` directory.

### 2. Custom Single Image

Modify `runpod_test.py` or use it as a library:

```python
from runpod_test import run_test

images = run_test(
    prompt="a beautiful sunset over the ocean",
    negative_prompt="blurry, low quality",
    steps=20,
    cfg=3.5,
    width=1024,
    height=1024,
    seed=42
)
```

### 3. Batch Processing

Generate multiple images from a list of prompts:

```bash
python batch_generate.py
```

Edit the `prompts` list in `batch_generate.py` to customize your batch:

```python
prompts = [
    "your first prompt",
    "your second prompt",
    "your third prompt"
]
```

### 4. Using the Utility Module

For advanced usage, import the utility classes:

```python
from runpod_utils import RunPodClient, WorkflowBuilder, ImageHandler

# Initialize client
client = RunPodClient(
    api_key="your_api_key",
    endpoint_id="your_endpoint_id"
)

# Load and modify workflow
workflow = WorkflowBuilder.load_workflow("flux_workflow.json")
WorkflowBuilder.set_prompt(workflow, "your amazing prompt")
WorkflowBuilder.set_sampler_params(workflow, steps=25, cfg=4.0)
WorkflowBuilder.set_dimensions(workflow, width=1280, height=720)

# Submit job synchronously
response = client.submit_sync(workflow)

# Extract and save images
images = ImageHandler.extract_images_from_response(response)
for idx, img_data in enumerate(images):
    ImageHandler.save_base64_image(img_data, f"output_{idx}.png")
```

### 5. Async Processing

For parallel processing of multiple images:

```python
from runpod_utils import RunPodClient, WorkflowBuilder

client = RunPodClient(api_key="...", endpoint_id="...")

# Submit multiple jobs
job_ids = []
for prompt in my_prompts:
    workflow = WorkflowBuilder.load_workflow("flux_workflow.json")
    WorkflowBuilder.set_prompt(workflow, prompt)
    job_id = client.submit_async(workflow)
    job_ids.append(job_id)

# Wait for completion
for job_id in job_ids:
    response = client.wait_for_completion(job_id)
    # Process response...
```

## Workflow Customization

The FLUX workflow supports the following parameters:

### Prompts
- **Positive prompt**: Description of desired image
- **Negative prompt**: What to avoid in the image

### Sampling Parameters
- **Steps**: 15-30 (default: 20)
- **CFG Scale**: 1.0-7.0 (default: 3.5)
- **Seed**: Any integer (None for random)
- **Sampler**: euler (default)
- **Scheduler**: simple (default)

### Image Dimensions
- **Width**: 512-2048 (default: 1024)
- **Height**: 512-2048 (default: 1024)
- Recommended: multiples of 64

### Model Components
- **Model**: flux1-dev-fp8.safetensors
- **VAE**: ae.sft
- **CLIP**: t5xxl_fp8_e4m3fn.safetensors, clip_l.safetensors

## API Classes

### `RunPodClient`

Main client for API interactions:

```python
client = RunPodClient(api_key, endpoint_id)

# Synchronous submission (waits for completion)
response = client.submit_sync(workflow)

# Asynchronous submission (returns job ID)
job_id = client.submit_async(workflow)
status = client.check_status(job_id)
final = client.wait_for_completion(job_id)
```

### `WorkflowBuilder`

Helper for workflow manipulation:

```python
# Load/save workflows
workflow = WorkflowBuilder.load_workflow("path.json")
WorkflowBuilder.save_workflow(workflow, "output.json")

# Modify workflow
WorkflowBuilder.set_prompt(workflow, positive, negative)
WorkflowBuilder.set_sampler_params(workflow, seed, steps, cfg)
WorkflowBuilder.set_dimensions(workflow, width, height)
```

### `ImageHandler`

Image processing utilities:

```python
# Decode base64
image_bytes = ImageHandler.decode_base64_image(base64_string)

# Save images
path = ImageHandler.save_image(image_bytes, "output.png")
path = ImageHandler.save_base64_image(base64_string, "output.png")

# Extract from response
images = ImageHandler.extract_images_from_response(response)
```

## Troubleshooting

### Common Issues

1. **Timeout errors**: Increase timeout in `submit_sync()` or use async mode
2. **Rate limits**: Use sequential processing or add delays between requests
3. **Out of memory**: Reduce image dimensions or batch size
4. **Invalid workflow**: Verify workflow JSON structure and node IDs

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Examples

### Generate with Custom Seed

```python
images = run_test(
    prompt="a mystical forest",
    seed=12345,  # Reproducible results
    steps=25,
    cfg=4.0
)
```

### Landscape vs Portrait

```python
# Landscape
run_test(prompt="...", width=1280, height=720)

# Portrait
run_test(prompt="...", width=720, height=1280)
```

### High Quality Settings

```python
images = run_test(
    prompt="masterpiece, best quality, ultra detailed, 8k",
    negative_prompt="low quality, blurry, distorted, bad anatomy",
    steps=30,
    cfg=5.0,
    width=1536,
    height=1536
)
```

## Performance Tips

1. **Async vs Sync**: Use async for multiple images, sync for single images
2. **Batch Size**: Process 3-5 images in parallel to balance speed and reliability
3. **Dimensions**: Larger images take longer (1024x1024 is a good default)
4. **Steps**: 20-25 steps usually sufficient, more doesn't always mean better
5. **CFG Scale**: 3.0-4.0 works well for FLUX, higher can oversaturate

## License

This project is provided as-is for use with RunPod services.

## Support

For issues with:
- **Scripts**: Open an issue in this repository
- **RunPod API**: Contact RunPod support
- **ComfyUI**: Check ComfyUI documentation

## Version History

- **v1.0**: Initial release with FLUX.1-dev-fp8 support
  - Single image generation
  - Batch processing
  - Sync/async modes
  - Comprehensive utilities

## Credits

- **ComfyUI**: Stable Diffusion workflow interface
- **RunPod**: Serverless GPU infrastructure
- **FLUX.1**: Advanced image generation model
