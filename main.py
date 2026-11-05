import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from core.exceptions import ServiceError
from routers.users import router as users_router
from routers.auth import router as auth_router
from routers.collection_point import router as collection_point_router
from routers import ussd
from routers.produce_price import router as produce_price_router
from routers.weighing_device import router as weighing_device_router
from routers.produce_record import router as produce_record_router
from routers.task import router as task_router




app = FastAPI(
    title="Umucyo API",
    description="API for tea cooperative deliveries, farmer registration and payments.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://192.168.1.15:3000",
        "http://192.168.100.252:3000",
        "http://192.168.100.252:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(collection_point_router)
app.include_router(weighing_device_router)
app.include_router(task_router)
app.include_router(produce_record_router)
app.include_router(ussd.router)
app.include_router(produce_price_router)





@app.get("/")
def root():
    return {"message": "Umucyo API is running", "docs": "/docs"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
