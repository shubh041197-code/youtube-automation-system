"""SEO optimization engine — generates titles, descriptions, tags, and hashtags."""

import json
import logging
import os
import random

import httpx

from src.utils import load_config, retry

logger = logging.getLogger("youtube_automation")

# Fallback SEO templates
TITLE_TEMPLATES = [
    "{topic} - Everything You Need to Know",
    "The Ultimate Guide to {topic}",
    "{topic} Explained in Simple Terms",
    "Why {topic} Matters More Than You Think",
    "{topic}: What Nobody Tells You",
]

DESCRIPTION_TEMPLATE = """🔥 {title}

In this video, we dive deep into {topic} and explore everything you need to know.

📌 Key Topics Covered:
{key_points}

👍 If you found this helpful, please LIKE and SUBSCRIBE for more content!
🔔 Turn on notifications so you never miss a video.

📱 Follow us on social media for daily updates.

#technology #learning #education

⏰ Timestamps:
{timestamps}
"""

DEFAULT_TAGS = [
    "technology", "tutorial", "explained", "guide", "tips",
    "how to", "2024", "best", "top", "learn"
]


class SEOEngine:
    """Generates SEO-optimized metadata for YouTube videos."""

    def __init__(self, config: dict = None):
        self.config = config or load_config()
        ai_config = self.config.get("ai", {})
        self.api_key = ai_config.get("api_key", os.getenv("AI_API_KEY", ""))
        self.api_base = ai_config.get("api_base_url", "https://api.openai.com/v1")
        self.model = ai_config.get("model", "gpt-4o-mini")
        self.youtube_config = self.config.get("youtube", {})
        self.default_tags = self.youtube_config.get("default_tags", DEFAULT_TAGS)

    def _call_ai(self, prompt: str) -> str:
        """Call AI API for SEO generation."""
        if not self.api_key:
            raise ValueError("AI_API_KEY not set")

        with httpx.Client(timeout=30) as client:
            response = client.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are a YouTube SEO expert. Optimize content for maximum discoverability and click-through rate."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 1024,
                    "temperature": 0.7
                }
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

    @retry(max_attempts=3, backoff=2.0)
    def generate_seo(self, topic: str, script: dict, video_type: str = "long") -> dict:
        """Generate complete SEO metadata for a video.

        Args:
            topic: Video topic
            script: Script dict with sections
            video_type: 'long' or 'short'

        Returns:
            Dict with title, description, tags
        """
        try:
            return self._generate_ai_seo(topic, script, video_type)
        except Exception as e:
            logger.warning(f"AI SEO generation failed: {e}. Using fallback.")
            return self._generate_fallback_seo(topic, script, video_type)

    def _generate_ai_seo(self, topic: str, script: dict, video_type: str) -> dict:
        """Generate SEO metadata using AI."""
        sections = script.get("sections", [])
        section_titles = [s.get("title", "") for s in sections]

        prompt = (
            f"Generate YouTube SEO metadata for a {'short-form' if video_type == 'short' else 'long-form'} "
            f"video about: '{topic}'\n\n"
            f"{'Sections: ' + ', '.join(section_titles) if section_titles else ''}\n\n"
            f"Return ONLY valid JSON:\n"
            f'{{"title": "Catchy title (max 70 chars)",'
            f' "description": "Full description with emojis, sections, CTA (max 5000 chars)",'
            f' "tags": ["tag1", "tag2", ...] (15-20 relevant tags)'
            f"}}\n\n"
            f"Rules:\n"
            f"- Title: catchy, under 70 characters, includes main keyword\n"
            f"- Description: includes hook, key points, CTA, relevant hashtags\n"
            f"- Tags: mix of broad and specific keywords\n"
            f"{'- Add #Shorts in title and description' if video_type == 'short' else ''}"
        )

        result = self._call_ai(prompt)
        cleaned = result.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]

        seo = json.loads(cleaned)

        # Enforce limits
        seo["title"] = seo.get("title", topic)[:100]
        seo["description"] = seo.get("description", "")[:5000]
        seo["tags"] = (seo.get("tags", []) + self.default_tags)[:30]

        if video_type == "short" and "#Shorts" not in seo["title"]:
            seo["title"] = seo["title"][:90] + " #Shorts"

        return seo

    def _generate_fallback_seo(self, topic: str, script: dict, video_type: str) -> dict:
        """Generate SEO metadata using templates."""
        title_template = random.choice(TITLE_TEMPLATES)
        title = title_template.format(topic=topic)

        sections = script.get("sections", [])
        key_points = "\n".join(f"• {s.get('title', '')}" for s in sections if s.get("title"))
        timestamps = ""
        current_time = 0
        for s in sections:
            minutes = current_time // 60
            seconds = current_time % 60
            timestamps += f"{minutes:02d}:{seconds:02d} - {s.get('title', 'Section')}\n"
            current_time += s.get("duration_hint", 60)

        description = DESCRIPTION_TEMPLATE.format(
            title=title,
            topic=topic,
            key_points=key_points or "• " + topic,
            timestamps=timestamps or "00:00 - Start"
        )

        tags = list(self.default_tags) + [
            topic.lower(),
            topic.split()[0].lower() if topic.split() else "video",
        ]

        if video_type == "short":
            title = title[:90] + " #Shorts"
            tags.append("shorts")

        return {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags[:30]
        }

    def generate_shorts_seo(self, shorts_scripts: list, topic: str) -> list:
        """Generate SEO metadata for multiple shorts."""
        results = []
        for script in shorts_scripts:
            seo = self.generate_seo(
                topic=script.get("title", topic),
                script={"sections": [script]},
                video_type="short"
            )
            results.append(seo)
        return results
