"""Package setup for YouTube Automation Platform."""

from setuptools import setup, find_packages

setup(
    name="youtube-automation-system",
    version="1.0.0",
    description="AI-powered YouTube automation platform - daily videos and shorts on autopilot",
    author="shubh041197-code",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "moviepy>=2.0.0",
        "edge-tts>=6.1.0",
        "Pillow>=10.0.0",
        "google-api-python-client>=2.100.0",
        "google-auth-oauthlib>=1.1.0",
        "google-auth-httplib2>=0.1.1",
        "httpx>=0.25.0",
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "jinja2>=3.1.0",
        "python-multipart>=0.0.6",
        "apscheduler>=3.10.0",
        "pyyaml>=6.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "youtube-auto=src.main:main",
        ],
    },
)
