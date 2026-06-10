from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.database import engine, Base
# Import models to ensure they are registered on metadata before create_all
from app.models import contact, thread, email, action, audit_log, knowledge_chunk, web_intelligence_cache
from app.routes import ingest, threads, dashboard, status as status_route, rag, actions, agent, analytics, intelligence, classification
from app.config import settings

app = FastAPI(
    title="Agentic CRM Intelligence Platform",
    description="Phase 1: Backend foundation, email ingestion and operations system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 1. CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for the local assessment, configurable later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Database Initialization
@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)

# 3. Consistent Error Envelope Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    # Transform Pydantic validation errors into consistent error format
    errors = exc.errors()
    formatted_details = {}
    for err in errors:
        loc = ".".join(str(x) for x in err.get("loc", []))
        formatted_details[loc] = err.get("msg", "Validation error")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_code": "VALIDATION_ERROR",
            "message": "Invalid email payload",
            "details": formatted_details
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    # Map standard HTTP exceptions
    error_code = "API_ERROR"
    if exc.status_code == status.HTTP_404_NOT_FOUND:
        error_code = "NOT_FOUND"
    elif exc.status_code == status.HTTP_401_UNAUTHORIZED:
        error_code = "UNAUTHORIZED"
    elif exc.status_code == status.HTTP_403_FORBIDDEN:
        error_code = "FORBIDDEN"

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": error_code,
            "message": exc.detail,
            "details": {}
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    # Catch-all for unexpected internal errors
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred on the server",
            "details": {"error": str(exc)}
        }
    )

# 4. Route Registration
app.include_router(ingest.router)
app.include_router(threads.router)
app.include_router(dashboard.router)
app.include_router(status_route.router)
app.include_router(rag.router)
app.include_router(actions.router)
app.include_router(agent.router)
app.include_router(analytics.router)
app.include_router(intelligence.router)
app.include_router(classification.router)

# 5. GET /health route
@app.get("/health", status_code=status.HTTP_200_OK, tags=["system"])
def health_check():
    return {
        "status": "healthy",
        "service": "senai-crm-backend"
    }

