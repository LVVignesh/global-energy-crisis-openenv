from typing import Dict, Optional
from pydantic import ConfigDict, Field
from openenv.core.env_server.types import Action, Observation, State


class TaskAction(Action):
    """Strategic fuel allocation across 4 critical sectors."""
    fuel_to_hospital: int = Field(..., ge=0, description="Fuel to hospitals (Priority 1)")
    fuel_to_emergency: int = Field(..., ge=0, description="Fuel to emergency services (Priority 2)")
    fuel_to_transport: int = Field(..., ge=0, description="Fuel to transport/logistics (Priority 3 - BOTTLENECK)")
    fuel_to_residential: int = Field(..., ge=0, description="Fuel to residential grid (Priority 4)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "fuel_to_hospital": 30,
                "fuel_to_emergency": 20,
                "fuel_to_transport": 20,
                "fuel_to_residential": 10,
            }
        }
    )


class TaskObservation(Observation):
    """
    Environment observation returned to the agent.
    reward and done are inherited from Observation base class
    and populated by step() for the OpenEnv server to serialize.
    """
    episode_id: str = Field(..., description="Active session ID — use this in /step requests")
    fuel_available: int = Field(..., description="Fuel remaining in the strategic reserve")
    hospital_demand: int = Field(..., description="Fuel gap for hospitals")
    emergency_demand: int = Field(..., description="Fuel gap for emergency services")
    transport_demand: int = Field(..., description="Fuel gap for logistics (bottleneck key)")
    residential_demand: int = Field(..., description="Fuel gap for residential grid")
    message: str = Field(..., description="Strategic intelligence report")
    # Explicitly declare inherited fields so Swagger shows them
    reward: float = Field(default=0.0, description="Step reward [0.0, 1.0]")
    done: bool = Field(default=False, description="True when episode is complete")


class TaskState(State):
    """Internal episode state — not exposed to agent."""
    episode_id: str = "uninitialised"
    step_count: int = 0
    task_difficulty: str = "easy"
    total_score: float = 0.0
    fuel_available: float = 0.0
    current_demands: Dict[str, int] = Field(default_factory=dict)
