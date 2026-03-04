"""
api/routes/profile.py
---------------------
User profile management endpoints:
  GET  /api/profile/{user_id}          — retrieve profile
  POST /api/profile/{user_id}          — update name / image path
  POST /api/profile/{user_id}/image    — upload a new avatar image
"""

import logging
import uuid
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.api.models import UserProfile
from app.core.config import UPLOAD_DIR

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/profile")

# In-memory profile store (persists for the lifetime of the server process)
user_profiles: Dict[str, Dict[str, Any]] = {}

# Allowed image MIME types and extensions
_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
_MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB


# ---------------------------------------------------------------------------
# GET profile
# ---------------------------------------------------------------------------

@router.get("/{user_id}")
async def get_profile(user_id: str):
    """Return the stored profile for *user_id*, or sensible defaults."""
    try:
        profile = user_profiles.get(user_id, {"name": "User", "image_path": None})
        return {"status": "success", "profile": profile}
    except Exception as exc:
        logger.error(f"get_profile error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# POST profile (update name / image_path)
# ---------------------------------------------------------------------------

@router.post("/{user_id}")
async def update_profile(user_id: str, profile: UserProfile):
    """Merge *profile* fields into the existing user record."""
    try:
        existing = user_profiles.get(user_id, {})
        existing["name"] = profile.name
        if profile.image_path is not None:
            existing["image_path"] = profile.image_path
        user_profiles[user_id] = existing
        logger.info(f"Profile updated for {user_id}: {existing}")
        return {"status": "success", "profile": existing}
    except Exception as exc:
        logger.error(f"update_profile error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# POST profile image upload
# ---------------------------------------------------------------------------

@router.post("/{user_id}/image")
async def upload_profile_image(user_id: str, file: UploadFile = File(...)):
    """Save an uploaded image as the user's avatar.

    Validates file type (MIME + extension) and size (≤ 5 MB).
    Deletes any previous avatar to avoid orphaned files.
    """
    try:
        # Validate MIME type
        if file.content_type not in _ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(_ALLOWED_CONTENT_TYPES)}",
            )

        content = await file.read()

        # Validate file size
        if len(content) > _MAX_IMAGE_BYTES:
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 5 MB")

        # Determine safe extension
        raw_ext = Path(file.filename).suffix.lower() if file.filename else ".jpg"
        ext = raw_ext if raw_ext in _ALLOWED_EXTENSIONS else ".jpg"

        filename = f"{user_id}_{uuid.uuid4().hex[:8]}{ext}"
        dest_path = UPLOAD_DIR / filename

        # Remove old avatar if present
        existing_profile = user_profiles.get(user_id, {})
        old_image = existing_profile.get("image_path")
        if old_image:
            # old_image is like "/uploads/profiles/filename.ext" — extract just the filename
            old_filename = Path(old_image).name
            old_file = UPLOAD_DIR / old_filename
            if old_file.exists():
                try:
                    old_file.unlink()
                except Exception:
                    pass  # Non-fatal; log only in debug builds

        # Write new avatar
        with open(dest_path, "wb") as fh:
            fh.write(content)

        image_url = f"/uploads/profiles/{filename}"
        user_profiles.setdefault(user_id, {"name": "User"})["image_path"] = image_url

        logger.info(f"Avatar uploaded for {user_id}: {image_url}")
        return {"status": "success", "image_path": image_url, "profile": user_profiles[user_id]}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"upload_profile_image error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))
