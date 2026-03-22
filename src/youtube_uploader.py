"""YouTube upload engine using YouTube Data API v3 with OAuth2."""

import logging
import os
import time
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from src.utils import load_config, retry

logger = logging.getLogger("youtube_automation")

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
YOUTUBE_API_SERVICE = "youtube"
YOUTUBE_API_VERSION = "v3"


class YouTubeUploader:
    """Handles YouTube video uploads via the Data API v3."""

    def __init__(self, config: dict = None):
        self.config = config or load_config()
        self.youtube_config = self.config.get("youtube", {})
        self.category_id = self.youtube_config.get("category_id", "28")
        self.privacy_status = self.youtube_config.get("privacy_status", "private")
        self.notify_subscribers = self.youtube_config.get("notify_subscribers", False)
        self._service = None

    def _get_credentials(self) -> Credentials:
        """Get or refresh OAuth2 credentials."""
        creds = None
        token_path = "token.json"
        client_secret_path = "client_secret.json"

        # Load existing token
        if Path(token_path).exists():
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        # Refresh or create new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not Path(client_secret_path).exists():
                    # Check alternate locations
                    alt_paths = [
                        f for f in Path(".").glob("client_secret*.json")
                    ]
                    if alt_paths:
                        client_secret_path = str(alt_paths[0])
                    else:
                        raise FileNotFoundError(
                            "client_secret.json not found. Download it from Google Cloud Console: "
                            "https://console.cloud.google.com/apis/credentials"
                        )

                flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
                creds = flow.run_local_server(port=0)

            # Save token for next run
            with open(token_path, "w") as f:
                f.write(creds.to_json())

        return creds

    def _get_service(self):
        """Get or create YouTube API service."""
        if self._service is None:
            creds = self._get_credentials()
            self._service = build(YOUTUBE_API_SERVICE, YOUTUBE_API_VERSION, credentials=creds)
        return self._service

    @retry(max_attempts=3, backoff=5.0)
    def upload_video(self, video_path: str, metadata: dict,
                     thumbnail_path: str = None) -> str:
        """Upload a video to YouTube.

        Args:
            video_path: Path to the MP4 video file
            metadata: Dict with 'title', 'description', 'tags'
            thumbnail_path: Optional path to thumbnail image

        Returns:
            YouTube video ID
        """
        if not Path(video_path).exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        service = self._get_service()

        body = {
            "snippet": {
                "title": metadata.get("title", "Untitled Video")[:100],
                "description": metadata.get("description", "")[:5000],
                "tags": metadata.get("tags", [])[:30],
                "categoryId": self.category_id,
            },
            "status": {
                "privacyStatus": self.privacy_status,
                "selfDeclaredMadeForKids": False,
                "notifySubscribers": self.notify_subscribers,
            }
        }

        # Use resumable upload for reliability
        media = MediaFileUpload(
            video_path,
            mimetype="video/mp4",
            resumable=True,
            chunksize=10 * 1024 * 1024  # 10MB chunks
        )

        request = service.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        logger.info(f"Uploading video: {metadata.get('title', 'Untitled')}")
        response = self._resumable_upload(request)
        video_id = response["id"]

        logger.info(f"Video uploaded: https://youtube.com/watch?v={video_id}")

        # Upload thumbnail
        if thumbnail_path and Path(thumbnail_path).exists():
            self._upload_thumbnail(service, video_id, thumbnail_path)

        return video_id

    def _resumable_upload(self, request) -> dict:
        """Execute a resumable upload with retry logic."""
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                logger.info(f"Upload progress: {progress}%")

        return response

    def _upload_thumbnail(self, service, video_id: str, thumbnail_path: str):
        """Upload a custom thumbnail for a video."""
        try:
            media = MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
            service.thumbnails().set(
                videoId=video_id,
                media_body=media
            ).execute()
            logger.info(f"Thumbnail uploaded for video: {video_id}")
        except Exception as e:
            logger.warning(f"Failed to upload thumbnail: {e}")

    def upload_short(self, video_path: str, metadata: dict,
                     thumbnail_path: str = None) -> str:
        """Upload a YouTube Short. Ensures #Shorts tag is present."""
        # Ensure #Shorts in title and description
        title = metadata.get("title", "")
        if "#Shorts" not in title:
            title = title[:90] + " #Shorts"
        metadata["title"] = title

        desc = metadata.get("description", "")
        if "#Shorts" not in desc:
            metadata["description"] = desc + "\n\n#Shorts"

        return self.upload_video(video_path, metadata, thumbnail_path)

    def check_quota(self) -> dict:
        """Check remaining API quota (approximate)."""
        try:
            service = self._get_service()
            # Simple API call to check if we can communicate
            service.channels().list(part="id", mine=True).execute()
            return {"status": "ok", "message": "API accessible"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
