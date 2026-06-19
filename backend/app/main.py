import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

# Error monitoring — activates only when SENTRY_DSN is configured
if os.getenv("SENTRY_DSN"):
    try:
        import sentry_sdk

        sentry_sdk.init(
            dsn=os.getenv("SENTRY_DSN"),
            environment=os.getenv("ENVIRONMENT", "development"),
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        )
    except ImportError:
        logging.getLogger(__name__).warning("SENTRY_DSN set but sentry-sdk is not installed")

from app.db import connect_to_postgres, close_postgres_connection
from app.auth.config import auth_settings
from app.auth.router import router as auth_router
from app.video_analysis.router import router as video_router
from app.interviews.router import router as interviews_router
from app.resume_parser.router import router as resume_parser_router
from app.middlewares.auth_context import attach_auth_context
from app.voice.websocket_handler import router as voice_router
from app.interview_agent.realtime_router import router as interview_agent_realtime_router
from app.meeting_room.router import router as meeting_router, team_fit_router
from app.meeting_room.realtime_router import router as meeting_room_realtime_router
from app.group_interview.router import router as group_interview_router
from app.results.router import router as results_router

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI()
app.middleware("http")(attach_auth_context)

app.add_middleware(
    SessionMiddleware,
    secret_key=auth_settings.secret_key,
    same_site="lax",
    https_only=auth_settings.cookie_secure,
)

allowed_origins = [origin.strip() for origin in auth_settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(video_router)
app.include_router(interviews_router)
app.include_router(interview_agent_realtime_router)
app.include_router(resume_parser_router)
app.include_router(voice_router)
app.include_router(meeting_router)
app.include_router(team_fit_router)
app.include_router(meeting_room_realtime_router)
app.include_router(group_interview_router)
app.include_router(results_router)


@app.on_event("startup")
async def startup_event():
    logger.info("Application startup initiated")
    # All tables/indexes are created via Alembic migrations (run `alembic upgrade head`
    # before starting the app, NOT here). We only verify connectivity at startup.
    await connect_to_postgres()
    logger.info("Application startup completed")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown initiated")
    await close_postgres_connection()
    logger.info("Application shutdown completed")


@app.get("/")
def read_root():
    return {"Hello": "World"}