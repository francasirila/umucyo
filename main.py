from fastapi import FastAPI

app = FastAPI(title="Umucyo",
description="Backend API for creating transparency between the farmers and cooperatives",
version="0.1.0"
)


@app.get("/health")
def health() -> dict[str, str]:
    """Let deployment verification confirm that the API is responding."""
    return {"status": "ok"}
