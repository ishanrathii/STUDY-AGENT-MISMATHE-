"""MISMATHE web entry point — runs the FastAPI app via uvicorn."""
from __future__ import annotations

import logging

import uvicorn

from config import settings


logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)


def main() -> None:
    uvicorn.run(
        "mismathe.web.server:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
