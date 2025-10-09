#!/usr/bin/env python3
"""
RunPod Utilities Module
Provides helper functions for interacting with RunPod ComfyUI endpoints
"""

import os
import json
import time
import base64
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class RunPodConfig:
    """Configuration for RunPod API"""
    api_key: str
    endpoint_id: str

    @property
    def runsync_url(self) -> str:
        """Get the synchronous endpoint URL"""
        return f"https://api.runpod.ai/v2/{self.endpoint_id}/runsync"

    @property
    def run_url(self) -> str:
        """Get the asynchronous endpoint URL"""
        return f"https://api.runpod.ai/v2/{self.endpoint_id}/run"

    def status_url(self, job_id: str) -> str:
        """Get the status check URL for a job"""
        return f"https://api.runpod.ai/v2/{self.endpoint_id}/status/{job_id}"


class RunPodClient:
    """Client for interacting with RunPod ComfyUI endpoints"""

    def __init__(self, api_key: str, endpoint_id: str):
        """
        Initialize RunPod client.

        Args:
            api_key: RunPod API key
            endpoint_id: RunPod endpoint ID
        """
        self.config = RunPodConfig(api_key=api_key, endpoint_id=endpoint_id)
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}"
        })

    def submit_sync(self, workflow: dict, timeout: int = 300) -> dict:
        """
        Submit a synchronous job (waits for completion).

        Args:
            workflow: ComfyUI workflow dictionary
            timeout: Request timeout in seconds

        Returns:
            Response dictionary from RunPod
        """
        payload = {"input": {"workflow": workflow}}

        response = self.session.post(
            self.config.runsync_url,
            json=payload,
            timeout=timeout
        )
        response.raise_for_status()

        return response.json()

    def submit_async(self, workflow: dict) -> str:
        """
        Submit an asynchronous job (returns immediately with job ID).

        Args:
            workflow: ComfyUI workflow dictionary

        Returns:
            Job ID string
        """
        payload = {"input": {"workflow": workflow}}

        response = self.session.post(
            self.config.run_url,
            json=payload,
            timeout=30
        )
        response.raise_for_status()

        result = response.json()
        return result.get("id")

    def check_status(self, job_id: str) -> dict:
        """
        Check the status of an async job.

        Args:
            job_id: Job ID to check

        Returns:
            Status response dictionary
        """
        response = self.session.get(
            self.config.status_url(job_id),
            timeout=30
        )
        response.raise_for_status()

        return response.json()

    def wait_for_completion(self, job_id: str, poll_interval: int = 5,
                           max_wait: int = 600) -> dict:
        """
        Wait for an async job to complete.

        Args:
            job_id: Job ID to wait for
            poll_interval: Seconds between status checks
            max_wait: Maximum time to wait in seconds

        Returns:
            Final status response dictionary
        """
        start_time = time.time()

        while time.time() - start_time < max_wait:
            status = self.check_status(job_id)
            job_status = status.get("status")

            if job_status in ["COMPLETED", "FAILED"]:
                return status

            print(f"Status: {job_status}, waiting {poll_interval}s...")
            time.sleep(poll_interval)

        raise TimeoutError(f"Job {job_id} did not complete within {max_wait} seconds")


class WorkflowBuilder:
    """Helper class for building and modifying ComfyUI workflows"""

    @staticmethod
    def load_workflow(workflow_path: str) -> dict:
        """Load workflow from JSON file."""
        with open(workflow_path, 'r') as f:
            return json.load(f)

    @staticmethod
    def save_workflow(workflow: dict, output_path: str):
        """Save workflow to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(workflow, f, indent=2)

    @staticmethod
    def set_prompt(workflow: dict, positive: str, negative: str = "",
                  positive_node: str = "2", negative_node: str = "7") -> dict:
        """
        Set prompt text in workflow.

        Args:
            workflow: Workflow dictionary
            positive: Positive prompt text
            negative: Negative prompt text
            positive_node: Node ID for positive prompt
            negative_node: Node ID for negative prompt

        Returns:
            Modified workflow
        """
        if positive_node in workflow:
            workflow[positive_node]["inputs"]["text"] = positive
        if negative_node in workflow:
            workflow[negative_node]["inputs"]["text"] = negative
        return workflow

    @staticmethod
    def set_sampler_params(workflow: dict, seed: Optional[int] = None,
                          steps: int = 20, cfg: float = 3.5,
                          sampler_node: str = "6") -> dict:
        """
        Set sampling parameters in workflow.

        Args:
            workflow: Workflow dictionary
            seed: Random seed (None for timestamp-based)
            steps: Number of sampling steps
            cfg: CFG scale
            sampler_node: Node ID for sampler

        Returns:
            Modified workflow
        """
        if sampler_node in workflow:
            if seed is not None:
                workflow[sampler_node]["inputs"]["seed"] = seed
            else:
                workflow[sampler_node]["inputs"]["seed"] = int(time.time())
            workflow[sampler_node]["inputs"]["steps"] = steps
            workflow[sampler_node]["inputs"]["cfg"] = cfg
        return workflow

    @staticmethod
    def set_dimensions(workflow: dict, width: int, height: int,
                      latent_node: str = "1") -> dict:
        """
        Set image dimensions in workflow.

        Args:
            workflow: Workflow dictionary
            width: Image width
            height: Image height
            latent_node: Node ID for latent image

        Returns:
            Modified workflow
        """
        if latent_node in workflow:
            workflow[latent_node]["inputs"]["width"] = width
            workflow[latent_node]["inputs"]["height"] = height
        return workflow


class ImageHandler:
    """Helper class for handling image data"""

    @staticmethod
    def decode_base64_image(base64_data: str) -> bytes:
        """
        Decode base64 image data.

        Args:
            base64_data: Base64 encoded string (with or without data URI prefix)

        Returns:
            Raw image bytes
        """
        # Remove data URI prefix if present
        if "," in base64_data:
            base64_data = base64_data.split(",")[1]

        return base64.b64decode(base64_data)

    @staticmethod
    def save_image(image_data: bytes, output_path: str) -> Path:
        """
        Save image data to file.

        Args:
            image_data: Raw image bytes
            output_path: Path to save image

        Returns:
            Path object of saved file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'wb') as f:
            f.write(image_data)

        return output_path

    @staticmethod
    def save_base64_image(base64_data: str, output_path: str) -> Path:
        """
        Decode and save base64 image.

        Args:
            base64_data: Base64 encoded image
            output_path: Path to save image

        Returns:
            Path object of saved file
        """
        image_data = ImageHandler.decode_base64_image(base64_data)
        return ImageHandler.save_image(image_data, output_path)

    @staticmethod
    def extract_images_from_response(response: dict) -> List[str]:
        """
        Extract base64 image data from RunPod response.

        Args:
            response: RunPod API response dictionary

        Returns:
            List of base64 image strings
        """
        images = []

        if response.get("status") != "COMPLETED":
            return images

        output = response.get("output", {})

        # Try different response formats
        if "images" in output:
            images = output["images"]
        elif "message" in output:
            message = output["message"]
            if isinstance(message, dict) and "images" in message:
                images = message["images"]

        return images


def create_timestamped_filename(prefix: str = "output", extension: str = "png") -> str:
    """
    Create a timestamped filename.

    Args:
        prefix: Filename prefix
        extension: File extension (without dot)

    Returns:
        Timestamped filename string
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{extension}"


def batch_process_prompts(client: RunPodClient, workflow_template: dict,
                         prompts: List[str], output_dir: str,
                         negative_prompt: str = "", steps: int = 20,
                         cfg: float = 3.5, width: int = 1024, height: int = 1024,
                         use_async: bool = False) -> List[Path]:
    """
    Process multiple prompts in batch.

    Args:
        client: RunPodClient instance
        workflow_template: Base workflow to use
        prompts: List of prompts to process
        output_dir: Directory to save outputs
        negative_prompt: Negative prompt for all images
        steps: Sampling steps
        cfg: CFG scale
        width: Image width
        height: Image height
        use_async: Use async submission (process in parallel)

    Returns:
        List of saved image paths
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    saved_images = []

    if use_async:
        # Submit all jobs asynchronously
        job_ids = []
        for prompt in prompts:
            workflow = json.loads(json.dumps(workflow_template))
            WorkflowBuilder.set_prompt(workflow, prompt, negative_prompt)
            WorkflowBuilder.set_sampler_params(workflow, steps=steps, cfg=cfg)
            WorkflowBuilder.set_dimensions(workflow, width, height)

            job_id = client.submit_async(workflow)
            job_ids.append((job_id, prompt))
            print(f"Submitted job {job_id} for prompt: {prompt[:50]}...")

        # Wait for all jobs to complete
        for job_id, prompt in job_ids:
            print(f"\nWaiting for job {job_id}...")
            response = client.wait_for_completion(job_id)

            images = ImageHandler.extract_images_from_response(response)
            for idx, img_data in enumerate(images):
                filename = create_timestamped_filename(f"batch_{job_id}")
                filepath = output_path / filename
                saved_path = ImageHandler.save_base64_image(img_data, str(filepath))
                saved_images.append(saved_path)
                print(f"✅ Saved: {saved_path}")

    else:
        # Submit jobs synchronously (one at a time)
        for idx, prompt in enumerate(prompts):
            print(f"\nProcessing prompt {idx + 1}/{len(prompts)}: {prompt[:50]}...")

            workflow = json.loads(json.dumps(workflow_template))
            WorkflowBuilder.set_prompt(workflow, prompt, negative_prompt)
            WorkflowBuilder.set_sampler_params(workflow, steps=steps, cfg=cfg)
            WorkflowBuilder.set_dimensions(workflow, width, height)

            response = client.submit_sync(workflow)

            images = ImageHandler.extract_images_from_response(response)
            for img_idx, img_data in enumerate(images):
                filename = create_timestamped_filename(f"batch_{idx:03d}")
                filepath = output_path / filename
                saved_path = ImageHandler.save_base64_image(img_data, str(filepath))
                saved_images.append(saved_path)
                print(f"✅ Saved: {saved_path}")

    return saved_images
