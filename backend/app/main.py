import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import engine, Base
from app.api import auth, children, parent_settings, story, reports

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(children.router)
app.include_router(parent_settings.router)
app.include_router(story.router)
app.include_router(reports.router)


@app.on_event("startup")
async def startup():
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created.")

    logger.info("Initializing RAG knowledge base...")
    try:
        from app.rag.knowledge_base import get_vectorstore
        get_vectorstore()
        logger.info("RAG knowledge base initialized.")
    except Exception as e:
        logger.warning(f"RAG initialization skipped: {e}")


@app.get("/")
def root():
    return {"message": f"{settings.APP_NAME} v{settings.APP_VERSION}", "status": "running"}


@app.get("/health")
def health():
    return {"status": "ok"}
