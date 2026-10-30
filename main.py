from fastapi import FastAPI

from routers.produce_record import router as produce_record_router
from routers import ussd

app = FastAPI(
    title="Umucyo",
    description="Backend API for creating transparency between the farmers and cooperatives",
    version="0.1.0",
)

app.include_router(produce_record_router)
app.include_router(ussd.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
