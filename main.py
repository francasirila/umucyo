from fastapi import FastAPI

from routers.weighing_device import router as weighing_device_router
from routers.produce_record import router as produce_record_router

app = FastAPI(
    title="Umucyo",
    description="Backend API for creating transparency between the farmers and cooperatives",
    version="0.1.0",
)

app.include_router(weighing_device_router)
app.include_router(produce_record_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
