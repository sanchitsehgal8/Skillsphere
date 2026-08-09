from __future__ import annotations

from mangum import Mangum

from app.main import app


handler = Mangum(app)
