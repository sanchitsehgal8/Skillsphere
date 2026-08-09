from __future__ import annotations

from app.integrations.azure_blob_router import router as azure_blob_router
from app.main import app as base_app


base_app.include_router(azure_blob_router)

app = base_app
