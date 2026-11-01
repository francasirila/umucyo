import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from core.exceptions import ServiceError
from routers.users import router as users_router
from routers.auth import router as auth_router
from routers.collection_point import router as collection_point_router
from fastapi import FastAPI
from routers.produce_price import router as produce_price_router
from routers.weighing_device import router as weighing_device_router
from routers.produce_record import router as produce_record_router
from routers.task import router as task_router
from routers import ussd
from database import Base, engine

Base.metadata.create_all(bind=engine)


load_dotenv()



app = FastAPI(
    title="Umucyo API",
    description="API for tea cooperative deliveries, farmer registration and payments.",
    version="1.0.0",
)

cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(produce_price_router)
app.include_router(task_router)
app.include_router(collection_point_router)
app.include_router(weighing_device_router)
app.include_router(produce_record_router)
app.include_router(ussd.router)



@app.exception_handler(ServiceError)
async def service_error_handler(request: Request, exc: ServiceError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.get("/")
def root():
    return {"message": "Umucyo API is running", "docs": "/docs"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
