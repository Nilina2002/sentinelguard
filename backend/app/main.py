from fastapi import FastAPI, Request
from app.api import auth, users, images, reports, matching, system
from app.core.logger import setup_logger
import time
from fastapi.middleware.cors import CORSMiddleware

# logger setup
logger = setup_logger()
logger.info("Starting SentinelGuard API")

app = FastAPI(title="SentinelGuard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(images.router)
app.include_router(reports.router)
app.include_router(matching.router)
app.include_router(system.router)

# middleware for logging requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(f"{request.method} {request.url} {response.status_code} {duration:.3f}s")
    return response

# root endpoint
@app.get("/")
def root():
    return {"message": "Welcome to SentinelGuard API!"}
