import os
import logging

import uvicorn
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from promotion_agent.agent import root_agent

AGENT_DIR = os.path.dirname(os.path.abspath(__file__))

SESSION_SERVICE_URI = "sqlite:///./sessions.db"
ALLOWED_ORIGINS = ["http://localhost", "http://localhost:8080", "*"]
# Set web=True if you intend to serve a web interface, False otherwise
SERVE_WEB_INTERFACE = True

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    session_service_uri=SESSION_SERVICE_URI,
    allow_origins=ALLOWED_ORIGINS,
    web=SERVE_WEB_INTERFACE,
)


if __name__ == "__main__":
    mode = os.environ.get("APP_MODE", "a2a")
    port = int(os.environ.get("PORT", "8080"))
    logger.info(f"Mode: {mode}, Port: {port}")
    if mode == "a2a":
        a2a_app = to_a2a(root_agent, host="promotion-agent", port=port)
        logger.info("🔄 Starting A2A app...")
        uvicorn.run(a2a_app, host="0.0.0.0", port=port)
    else:
        uvicorn.run(app, host="0.0.0.0", port=port)