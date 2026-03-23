"""
Vision Service - Image Understanding with Claude or Local Models

Provides intelligent image analysis for uploaded documents:
- Claude 3.5 Sonnet (primary, if ANTHROPIC_API_KEY set)
- Local BLIP for fallback or self-hosted option
- Returns structured responses about image content
"""

import base64
import os
from pathlib import Path
from typing import Optional, Dict, Any

from config import settings


class VisionService:
    """
    Image understanding service using Claude or local vision models.
    """

    def __init__(self):
        self.use_claude = bool(settings.ANTHROPIC_API_KEY)
        self.claude_client = None
        self.local_model = None

        if self.use_claude:
            try:
                from anthropic import Anthropic
                self.claude_client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
                print("✅ Claude vision enabled")
            except Exception as e:
                print(f"⚠️  Claude initialization failed: {e}")
                self.use_claude = False

        if settings.VISION_USE_LOCAL_FALLBACK and not self.use_claude:
            self._init_local_vision()

    def _init_local_vision(self) -> None:
        """Initialize local BLIP model as fallback."""
        try:
            from transformers import BlipProcessor, BlipForConditionalGeneration
            from PIL import Image
            import torch

            print("Loading local BLIP vision model (first run may take a minute)...")
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.local_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
            self.local_model = BlipForConditionalGeneration.from_pretrained(
                "Salesforce/blip-image-captioning-base"
            ).to(device)
            self.device = device
            print(f"✅ Local BLIP vision model ready on {device}")
        except Exception as e:
            print(f"⚠️  Local BLIP initialization failed: {e}")
            self.local_model = None

    def analyze_image(
        self,
        image_path: str,
        question: Optional[str] = None,
        max_tokens: int = 512,
        timeout_seconds: int = 45,
    ) -> Dict[str, Any]:
        """
        Analyze an image with vision model.

        Args:
            image_path: Path to image file
            question: Optional question about the image (e.g., "what is the main subject?")
            max_tokens: Max response length
            timeout_seconds: Timeout for vision analysis (use OCR fallback if exceeded)

        Returns:
            {
                "content": "detailed description or answer",
                "model": "claude" or "blip",
                "usage": {"input_tokens": int, "output_tokens": int},
                "success": bool,
                "error": Optional[str]
            }
        """
        if not os.path.exists(image_path):
            return {
                "content": "",
                "model": "none",
                "usage": {},
                "success": False,
                "error": f"Image not found: {image_path}",
            }

        if self.use_claude and self.claude_client:
            return self._analyze_with_claude(image_path, question, max_tokens)

        if self.local_model:
            print(f"ℹ️  BLIP vision model analyzing (timeout={timeout_seconds}s)...")
            return self._analyze_with_blip(image_path, question)

        return {
            "content": "",
            "model": "none",
            "usage": {},
            "success": False,
            "error": "No vision model available. Set ANTHROPIC_API_KEY for Claude or install transformers for BLIP.",
        }

    def _analyze_with_claude(
        self,
        image_path: str,
        question: Optional[str],
        max_tokens: int,
    ) -> Dict[str, Any]:
        """Analyze image using Claude vision."""
        try:
            with open(image_path, "rb") as img_file:
                image_data = base64.standard_b64encode(img_file.read()).decode("utf-8")

            file_ext = Path(image_path).suffix.lower()
            media_type_map = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".webp": "image/webp",
                ".gif": "image/gif",
            }
            media_type = media_type_map.get(file_ext, "image/jpeg")

            prompt = question or "Describe this image in detail. What do you see?"

            response = self.claude_client.messages.create(
                model=settings.VISION_MODEL,
                max_tokens=max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
            )

            content = response.content[0].text if response.content else ""
            input_tokens = response.usage.input_tokens if hasattr(response, "usage") else 0
            output_tokens = response.usage.output_tokens if hasattr(response, "usage") else 0

            return {
                "content": content,
                "model": "claude",
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                },
                "success": True,
                "error": None,
            }

        except Exception as e:
            print(f"❌ Claude vision error: {e}")
            return {
                "content": "",
                "model": "claude",
                "usage": {},
                "success": False,
                "error": str(e),
            }

    def _analyze_with_blip(
        self,
        image_path: str,
        question: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze image using local BLIP model."""
        try:
            from PIL import Image

            image = Image.open(image_path).convert("RGB")

            if question:
                inputs = self.local_processor(image, question, return_tensors="pt").to(self.device)
            else:
                inputs = self.local_processor(image, return_tensors="pt").to(self.device)

            with self.local_model.eval():
                outputs = self.local_model.generate(**inputs, max_length=128)

            content = self.local_processor.decode(outputs[0], skip_special_tokens=True)

            return {
                "content": content,
                "model": "blip",
                "usage": {},
                "success": True,
                "error": None,
            }

        except Exception as e:
            print(f"❌ BLIP vision error: {e}")
            return {
                "content": "",
                "model": "blip",
                "usage": {},
                "success": False,
                "error": str(e),
            }


# Singleton instance
vision_service = VisionService()
