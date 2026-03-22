"""Thumbnail generation engine using Pillow."""

import logging
import math
import random
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src.utils import load_config, retry

logger = logging.getLogger("youtube_automation")

# Gradient presets for thumbnails
GRADIENT_PRESETS = [
    ((30, 60, 180), (140, 20, 200)),    # Blue to Purple
    ((200, 50, 50), (250, 150, 0)),      # Red to Orange
    ((0, 150, 100), (0, 60, 180)),       # Green to Blue
    ((180, 0, 180), (60, 0, 120)),       # Magenta to Deep Purple
    ((20, 20, 60), (80, 0, 40)),         # Dark Blue to Dark Red
]


class ThumbnailEngine:
    """Generates eye-catching YouTube thumbnails."""

    def __init__(self, config: dict = None):
        self.config = config or load_config()
        thumb_config = self.config.get("thumbnail", {})
        self.width, self.height = thumb_config.get("resolution", [1280, 720])
        self.font_size = thumb_config.get("font_size", 72)
        self.templates = thumb_config.get("templates", ["gradient_bold", "split_accent", "dark_glow"])
        self._font = self._load_font(self.font_size)
        self._font_large = self._load_font(int(self.font_size * 1.3))
        self._font_small = self._load_font(int(self.font_size * 0.5))

    def _load_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Load a font, falling back to default if custom fonts unavailable."""
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf",
            "assets/fonts/DejaVuSans-Bold.ttf",
        ]
        for path in font_paths:
            if Path(path).exists():
                return ImageFont.truetype(path, size)
        return ImageFont.load_default()

    @retry(max_attempts=2, backoff=1.0)
    def generate_thumbnail(self, title: str, output_path: str, template: str = None) -> str:
        """Generate a thumbnail image.

        Args:
            title: Video title text
            output_path: Output JPEG file path
            template: Template name (gradient_bold, split_accent, dark_glow)

        Returns:
            Path to the created thumbnail
        """
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        if template is None:
            template = random.choice(self.templates)

        if template == "gradient_bold":
            img = self._template_gradient_bold(title)
        elif template == "split_accent":
            img = self._template_split_accent(title)
        elif template == "dark_glow":
            img = self._template_dark_glow(title)
        else:
            img = self._template_gradient_bold(title)

        img.save(str(output), "JPEG", quality=95)
        logger.info(f"Thumbnail created: {output} (template: {template})")
        return str(output)

    def _draw_gradient(self, img: Image.Image, color1: tuple, color2: tuple):
        """Draw a gradient on an image."""
        draw = ImageDraw.Draw(img)
        for y in range(self.height):
            ratio = y / self.height
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            draw.line([(0, y), (self.width, y)], fill=(r, g, b))

    def _draw_text_with_shadow(self, draw: ImageDraw.Draw, text: str, position: tuple,
                                font: ImageFont.FreeTypeFont, fill: str = "white",
                                shadow_color: str = "black", shadow_offset: int = 4):
        """Draw text with a drop shadow."""
        x, y = position
        # Shadow
        draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=shadow_color)
        # Main text
        draw.text((x, y), text, font=font, fill=fill)

    def _template_gradient_bold(self, title: str) -> Image.Image:
        """Bold gradient background with large white text."""
        img = Image.new("RGB", (self.width, self.height))
        colors = random.choice(GRADIENT_PRESETS)
        self._draw_gradient(img, colors[0], colors[1])
        draw = ImageDraw.Draw(img)

        # Add decorative circles
        for _ in range(5):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            r = random.randint(30, 150)
            opacity_color = tuple(c // 3 for c in colors[0])
            draw.ellipse([x - r, y - r, x + r, y + r], fill=None,
                        outline=(*opacity_color, 80), width=3)

        # Draw title
        wrapped = textwrap.fill(title.upper(), width=20)
        lines = wrapped.split("\n")

        total_height = len(lines) * (self.font_size + 20)
        y_start = (self.height - total_height) // 2

        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=self._font_large)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
            y = y_start + i * (self.font_size + 30)
            self._draw_text_with_shadow(draw, line, (x, y), self._font_large,
                                         shadow_offset=5)

        return img

    def _template_split_accent(self, title: str) -> Image.Image:
        """Split design with accent color block."""
        img = Image.new("RGB", (self.width, self.height), (20, 20, 30))
        draw = ImageDraw.Draw(img)

        # Left accent bar
        accent_color = random.choice([(255, 60, 60), (60, 200, 255), (255, 200, 0), (0, 255, 150)])
        draw.rectangle([0, 0, 80, self.height], fill=accent_color)

        # Accent stripe at bottom
        draw.rectangle([0, self.height - 8, self.width, self.height], fill=accent_color)

        # Title text
        wrapped = textwrap.fill(title.upper(), width=22)
        lines = wrapped.split("\n")

        total_height = len(lines) * (self.font_size + 15)
        y_start = (self.height - total_height) // 2

        for i, line in enumerate(lines):
            x = 140
            y = y_start + i * (self.font_size + 20)
            self._draw_text_with_shadow(draw, line, (x, y), self._font,
                                         shadow_offset=3)

        return img

    def _template_dark_glow(self, title: str) -> Image.Image:
        """Dark background with glowing text effect."""
        img = Image.new("RGB", (self.width, self.height), (10, 10, 20))
        draw = ImageDraw.Draw(img)

        # Draw radial glow in center
        glow_color = random.choice([(40, 0, 80), (0, 40, 80), (80, 0, 40)])
        cx, cy = self.width // 2, self.height // 2
        for r in range(300, 0, -2):
            alpha = int(255 * (1 - r / 300) * 0.3)
            color = tuple(min(255, c + alpha) for c in glow_color)
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)

        # Title text with glow effect (drawn multiple times with offset)
        wrapped = textwrap.fill(title.upper(), width=20)
        lines = wrapped.split("\n")

        total_height = len(lines) * (self.font_size + 20)
        y_start = (self.height - total_height) // 2

        glow_text_color = random.choice(["cyan", "magenta", "yellow", "lime"])

        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=self._font_large)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
            y = y_start + i * (self.font_size + 30)

            # Glow layers
            for offset in [6, 4, 2]:
                draw.text((x - offset, y), line, font=self._font_large, fill=glow_text_color)
                draw.text((x + offset, y), line, font=self._font_large, fill=glow_text_color)

            # Main text
            draw.text((x, y), line, font=self._font_large, fill="white")

        return img
