"""FastAPI application for event streaming API."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from llm_sim.api.routers import events

app = FastAPI(
    title="LLM Simulation Event Stream API",
    description="API for querying simulation event streams",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(events.router, prefix="", tags=["events"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


def run_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    output_root: Path = Path("output"),
):
    """Run the FastAPI server.

    Args:
        host: Host to bind to
        port: Port to bind to
        output_root: Root directory containing simulation outputs
    """
    import uvicorn

    # Store output_root in app state
    app.state.output_root = output_root

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
