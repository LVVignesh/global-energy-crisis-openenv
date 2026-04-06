import random
from typing import Any, Dict, Optional

from openenv.core.env_server.interfaces import Environment
from .models import TaskAction, TaskObservation, TaskState

_DIFFICULTY_CONFIG = {
    "easy":   {"fuel": 160, "hospital": 40, "emergency": 30, "transport": 20, "residential": 15},
    "medium": {"fuel": 120, "hospital": 40, "emergency": 30, "transport": 20, "residential": 15},
    "hard":   {"fuel": 80,  "hospital": 40, "emergency": 30, "transport": 20, "residential": 15},
}
_WEIGHTS = {"hospital": 0.40, "emergency": 0.30, "transport": 0.20, "residential": 0.10}


def _compute_reward(effective_gains: Dict[str, float], initial_fuel: int) -> float:
    """Proportional reward in [0.0, 1.0]. No magic thresholds."""
    if initial_fuel <= 0:
        return 0.0
    weighted = sum(effective_gains[k] * _WEIGHTS[k] for k in _WEIGHTS)
    return float(min(1.0, weighted / initial_fuel))


class GlobalCrisisEnv(Environment):

    _episodes: Dict[str, TaskState] = {}

    def __init__(self):
        super().__init__()
        self._current_episode_id: Optional[str] = None

    @property
    def state(self) -> TaskState:
        if self._current_episode_id and self._current_episode_id in GlobalCrisisEnv._episodes:
            return GlobalCrisisEnv._episodes[self._current_episode_id]
        return TaskState()

    def reset(self, seed: Optional[int] = None, episode_id: Optional[str] = None, **kwargs) -> TaskObservation:
        diff = kwargs.get("task_id", "easy")
        if diff not in _DIFFICULTY_CONFIG:
            diff = "easy"

        ep_id = episode_id or str(random.randint(10000, 99999))
        self._current_episode_id = ep_id
        cfg = _DIFFICULTY_CONFIG[diff]
        noise = random.randint(-2, 2) if seed is None else 0

        demands = {
            "hospital":    cfg["hospital"] + noise,
            "emergency":   cfg["emergency"],
            "transport":   cfg["transport"],
            "residential": cfg["residential"],
        }
        state = TaskState(
            episode_id=ep_id,
            step_count=0,
            task_difficulty=diff,
            total_score=0.0,
            fuel_available=float(cfg["fuel"]),
            current_demands=demands,
        )
        GlobalCrisisEnv._episodes[ep_id] = state

        return TaskObservation(
            episode_id=ep_id,
            fuel_available=cfg["fuel"],
            hospital_demand=demands["hospital"],
            emergency_demand=demands["emergency"],
            transport_demand=demands["transport"],
            residential_demand=demands["residential"],
            message=f"CRISIS MISSION COMMENCED: [{diff.upper()}] Mode. Reserve: {cfg['fuel']} units.",
            reward=0.0,
            done=False,
        )

    async def reset_async(self, seed=None, episode_id=None, **kwargs) -> TaskObservation:
        return self.reset(seed=seed, episode_id=episode_id, **kwargs)

    def step(self, action: Any, timeout_s: Optional[float] = None, **kwargs) -> TaskObservation:
        ep_id = kwargs.get("episode_id")
        if ep_id:
            self._current_episode_id = ep_id

        state = self.state

        # Guard — no valid session
        if state.episode_id == "uninitialised":
            return TaskObservation(
                episode_id="none", fuel_available=0,
                hospital_demand=0, emergency_demand=0,
                transport_demand=0, residential_demand=0,
                message="ERROR: No active episode. Call /reset with a task_id first.",
                reward=0.0, done=True,
            )

        act = TaskAction(**action) if isinstance(action, dict) else action
        h, e, t, r = (act.fuel_to_hospital, act.fuel_to_emergency,
                      act.fuel_to_transport, act.fuel_to_residential)
        total_alloc = h + e + t + r
        demands = state.current_demands
        initial_fuel = _DIFFICULTY_CONFIG[state.task_difficulty]["fuel"]
        msg = "Strategic distribution complete."

        if total_alloc > state.fuel_available:
            # Over-allocation penalty
            msg = "LOGISTICS OVERLOAD: Allocation exceeds reserves. No fuel shipped."
            effective_gains = {"hospital": 0.0, "emergency": 0.0, "transport": 0.0, "residential": 0.0}
        else:
            state.fuel_available -= total_alloc

            # 🚨 Logistics Bottleneck — hard mode only
            multiplier = 1.0
            if state.task_difficulty == "hard" and demands.get("transport", 0) > 5:
                multiplier = 0.1
                msg = "LOGISTICS BOTTLENECK ACTIVE: Transport must be prioritised first."

            effective_gains = {
                "hospital":    h * multiplier,
                "emergency":   e * multiplier,
                "transport":   float(t),
                "residential": float(r),
            }
            for k in demands:
                demands[k] = max(0, demands[k] - int(effective_gains[k]))

        reward = _compute_reward(effective_gains, initial_fuel)
        state.step_count += 1
        state.total_score += reward

        done = state.step_count >= 5

        return TaskObservation(
            episode_id=state.episode_id,
            fuel_available=int(state.fuel_available),
            hospital_demand=demands["hospital"],
            emergency_demand=demands["emergency"],
            transport_demand=demands["transport"],
            residential_demand=demands["residential"],
            message=msg,
            reward=float(reward),
            done=bool(done),
        )

    async def step_async(self, action: Any, timeout_s: Optional[float] = None, **kwargs) -> TaskObservation:
        return self.step(action, timeout_s=timeout_s, **kwargs)

    def get_metadata(self) -> Any:
        from openenv.core.env_server.types import EnvironmentMetadata
        return EnvironmentMetadata(
            name="global_energy_crisis_logistics",
            description="Geopolitical fuel crisis simulator with bottleneck mechanics.",
            version="1.0.0",
        )
