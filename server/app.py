import os
import uvicorn
from fastapi.responses import RedirectResponse
from openenv.core.env_server import create_fastapi_app
from .environment import GlobalCrisisEnv
from .models import TaskAction, TaskObservation

# Create the FastAPI app via OpenEnv factory
app = create_fastapi_app(GlobalCrisisEnv, TaskAction, TaskObservation)

# Metadata
app.title = "Global Energy Crisis Logistics Simulator"
app.version = "1.0.0"
app.description = (
    "A high-stakes Geopolitical Energy Crisis simulating the distribution "
    "of a constrained strategic resource (fuel) across 4 global sectors."
)


@app.get("/", include_in_schema=False)
async def root_redirect():
    return RedirectResponse(url="/docs")


def main():
    """CLI entry point — used by pyproject.toml [project.scripts]."""
    port = int(os.getenv("PORT", 7860))
    uvicorn.run("app:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
