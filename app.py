"""Vercel entrypoint: the FastAPI app lives in backend/."""

from backend.app import app

__all__ = ["app"]
