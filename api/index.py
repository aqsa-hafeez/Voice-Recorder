import os
import sys

# Vercel runs this file from /api, so add the project root to sys.path
# to make the top-level "app" package importable.
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.main import app  # noqa: E402  (Vercel needs a module-level "app" ASGI callable)
