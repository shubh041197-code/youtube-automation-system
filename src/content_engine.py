"""AI-powered content generation: topics, scripts, and short-form content."""

import json
import os
import random
import logging

import httpx

from src.utils import load_config, retry

logger = logging.getLogger("youtube_automation")

# Fallback script templates when AI API is unavailable
FALLBACK_TEMPLATES = [
    {
        "topic": "Top 5 Tech Innovations",
        "sections": [
            {"title": "Introduction", "narration": "Welcome back to the channel! Today we're diving into the top 5 tech innovations that are changing the world as we know it. Stay tuned because number one will blow your mind!", "duration_hint": 15},
            {"title": "Innovation 5: Quantum Computing", "narration": "Starting at number 5, quantum computing is making massive strides. Companies like IBM and Google are pushing the boundaries of what's computationally possible. Quantum computers can solve problems in minutes that would take traditional computers thousands of years.", "duration_hint": 60},
            {"title": "Innovation 4: AI Assistants", "narration": "At number 4, AI assistants have evolved beyond simple voice commands. They can now write code, create art, and even help with scientific research. The implications for productivity are enormous.", "duration_hint": 60},
            {"title": "Innovation 3: Renewable Energy Tech", "narration": "Number 3 is renewable energy technology. Solar panels are now more efficient than ever, and new battery storage solutions are making clean energy available around the clock.", "duration_hint": 60},
            {"title": "Innovation 2: Brain-Computer Interfaces", "narration": "At number 2, brain-computer interfaces are becoming reality. These devices can help paralyzed patients communicate and may eventually allow us to interact with technology using just our thoughts.", "duration_hint": 60},
            {"title": "Innovation 1: Space Technology", "narration": "And the number one innovation is reusable space technology! Companies are making space more accessible than ever, with plans for satellite internet coverage worldwide and even civilian space travel.", "duration_hint": 60},
            {"title": "Conclusion", "narration": "Those are the top 5 tech innovations shaping our future. If you found this helpful, smash that like button and subscribe for more tech content. See you in the next video!", "duration_hint": 15}
        ]
    },
    {
        "topic": "How AI is Changing Everything",
        "sections": [
            {"title": "Hook", "narration": "Artificial intelligence isn't just a buzzword anymore. It's fundamentally changing how we work, create, and live. Let me show you exactly how.", "duration_hint": 15},
            {"title": "AI in Healthcare", "narration": "In healthcare, AI algorithms can now detect diseases from medical images with accuracy that rivals experienced doctors. Early detection of cancer, heart disease, and other conditions is saving lives every single day.", "duration_hint": 90},
            {"title": "AI in Education", "narration": "Education is being transformed by personalized AI tutors that adapt to each student's learning pace and style. No more one-size-fits-all education. Every student gets a customized learning experience.", "duration_hint": 90},
            {"title": "AI in Creative Work", "narration": "Creative professionals are using AI as a powerful collaborator. From generating initial designs to composing music, AI tools are amplifying human creativity rather than replacing it.", "duration_hint": 90},
            {"title": "The Future", "narration": "The future of AI is incredibly exciting. As these systems become more capable, they'll help us solve problems we haven't even imagined yet. The key is ensuring this technology benefits everyone.", "duration_hint": 60},
            {"title": "Call to Action", "narration": "What area of AI excites you the most? Let me know in the comments below. Don't forget to like and subscribe for more content like this!", "duration_hint": 15}
        ]
    }
]

FALLBACK_SHORTS = [
    {"title": "Did You Know?", "narration": "Did you know that the first computer bug was an actual bug? In 1947, a moth was found stuck in a relay of the Harvard Mark II computer. Engineers literally had to debug the machine! The term 'debugging' stuck around ever since. Follow for more tech facts!"},
    {"title": "Mind-Blowing Tech Fact", "narration": "Here's something wild: your smartphone has more computing power than all of NASA had during the 1969 moon landing. That tiny device in your pocket is literally more powerful than the technology that put humans on the moon. Like and follow for more!"},
    {"title": "Quick Tech Tip", "narration": "Want to speed up your computer instantly? Close unnecessary browser tabs. Each open tab uses RAM and CPU resources. Having 50 tabs open is like trying to read 50 books at once. Your computer will thank you! Follow for more tips!"},
]


class ContentEngine:
    """Generates topics, scripts, and content using AI."""

    def __init__(self, config: dict = None):
        self.config = config or load_config()
        ai_config = self.config.get("ai", {})
        self.api_key = ai_config.get("api_key", os.getenv("AI_API_KEY", ""))
        self.api_base = ai_config.get("api_base_url", "https://api.openai.com/v1")
        self.model = ai_config.get("model", "gpt-4o-mini")
        self.max_tokens = ai_config.get("max_tokens", 4096)
        self.temperature = ai_config.get("temperature", 0.8)
        self.content_config = self.config.get("content", {})

    def _call_ai(self, system_prompt: str, user_prompt: str) -> str:
        """Call the AI API (OpenAI-compatible)."""
        if not self.api_key:
            raise ValueError("AI_API_KEY not set. Set it in .env or config.yaml")

        with httpx.Client(timeout=60) as client:
            response = client.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature
                }
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

    @retry(max_attempts=3, backoff=2.0)
    def generate_topic(self, used_topics: list = None) -> str:
        """Generate a unique video topic."""
        niche = self.content_config.get("niche", "technology")
        topics_pool = self.content_config.get("topics", [])
        used = used_topics or []

        try:
            avoid_str = ", ".join(used[-20:]) if used else "none"
            result = self._call_ai(
                system_prompt="You are a YouTube content strategist. Generate engaging, trending video topics.",
                user_prompt=(
                    f"Generate ONE unique, engaging YouTube video topic about '{niche}'. "
                    f"The topic should be specific, clickable, and trending. "
                    f"Avoid these recently used topics: {avoid_str}. "
                    f"Return ONLY the topic title, nothing else."
                )
            )
            return result.strip().strip('"').strip("'")
        except Exception as e:
            logger.warning(f"AI topic generation failed: {e}. Using fallback.")
            available = [t for t in topics_pool if t not in used]
            if not available:
                available = topics_pool or ["Technology Tips and Tricks"]
            return random.choice(available)

    @retry(max_attempts=3, backoff=2.0)
    def generate_script(self, topic: str) -> dict:
        """Generate a full video script with sections."""
        target_duration = self.content_config.get("long_video_target_duration", 480)

        try:
            result = self._call_ai(
                system_prompt=(
                    "You are an expert YouTube scriptwriter. Write engaging, informative scripts "
                    "that keep viewers watching. Use a conversational, energetic tone."
                ),
                user_prompt=(
                    f"Write a complete YouTube video script about: '{topic}'\n\n"
                    f"Target total duration: ~{target_duration // 60} minutes.\n\n"
                    f"Return ONLY valid JSON in this exact format:\n"
                    f'{{"sections": [\n'
                    f'  {{"title": "Hook/Introduction", "narration": "...", "duration_hint": 15}},\n'
                    f'  {{"title": "Section Title", "narration": "Full narration text...", "duration_hint": 90}},\n'
                    f'  ...\n'
                    f'  {{"title": "Conclusion & CTA", "narration": "...", "duration_hint": 15}}\n'
                    f"]}}\n\n"
                    f"Rules:\n"
                    f"- Start with a compelling 15-second hook\n"
                    f"- Include 4-6 main content sections (~60-90 seconds each)\n"
                    f"- End with a conclusion + call to action\n"
                    f"- Write the full narration text (what will be spoken)\n"
                    f"- duration_hint is approximate seconds for that section\n"
                    f"- Make it engaging, informative, and natural-sounding"
                )
            )
            # Parse JSON from response (handle markdown code blocks)
            cleaned = result.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
            script = json.loads(cleaned)

            if "sections" not in script or len(script["sections"]) < 3:
                raise ValueError("Invalid script format")

            return script

        except Exception as e:
            logger.warning(f"AI script generation failed: {e}. Using fallback template.")
            template = random.choice(FALLBACK_TEMPLATES)
            return {"sections": template["sections"]}

    @retry(max_attempts=3, backoff=2.0)
    def generate_shorts_scripts(self, topic: str) -> list:
        """Generate scripts for 3 YouTube Shorts."""
        count = self.config.get("shorts", {}).get("count", 3)

        try:
            result = self._call_ai(
                system_prompt=(
                    "You are a viral YouTube Shorts scriptwriter. Write punchy, "
                    "attention-grabbing scripts that hook viewers in the first 3 seconds."
                ),
                user_prompt=(
                    f"Write {count} YouTube Shorts scripts related to: '{topic}'\n\n"
                    f"Each short should be 30-60 seconds when spoken.\n\n"
                    f"Return ONLY valid JSON in this format:\n"
                    f'{{"shorts": [\n'
                    f'  {{"title": "Short Title", "narration": "Full script text..."}},\n'
                    f"  ...\n"
                    f"]}}\n\n"
                    f"Rules:\n"
                    f"- Each script must hook the viewer in the first 3 seconds\n"
                    f"- Keep each narration to 50-100 words\n"
                    f"- Make them shareable and interesting\n"
                    f"- End each with a quick CTA (follow, like, etc.)\n"
                    f"- Each short should cover a different angle of the topic"
                )
            )
            cleaned = result.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
            data = json.loads(cleaned)

            shorts = data.get("shorts", [])
            if len(shorts) < count:
                raise ValueError(f"Expected {count} shorts, got {len(shorts)}")
            return shorts[:count]

        except Exception as e:
            logger.warning(f"AI shorts generation failed: {e}. Using fallback.")
            return FALLBACK_SHORTS[:count]
