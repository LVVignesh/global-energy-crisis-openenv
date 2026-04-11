import requests
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass

@dataclass
class GlobalCrisisAction:
    fuel_to_hospital: int
    fuel_to_emergency: int
    fuel_to_transport: int
    fuel_to_residential: int

    def to_dict(self):
        return {
            "fuel_to_hospital": self.fuel_to_hospital,
            "fuel_to_emergency": self.fuel_to_emergency,
            "fuel_to_transport": self.fuel_to_transport,
            "fuel_to_residential": self.fuel_to_residential
        }

@dataclass
class GlobalCrisisObservation:
    episode_id: str
    fuel_available: int
    hospital_demand: int
    emergency_demand: int
    transport_demand: int
    residential_demand: int
    message: str
    reward: float
    done: bool

class GlobalCrisisEnv:
    def __init__(self, base_url: str = "http://127.0.0.1:7860"):
        self.base_url = base_url.rstrip("/")
        self.episode_id: Optional[str] = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def reset(self, task_id: str = "easy", seed: Optional[int] = None) -> GlobalCrisisObservation:
        payload = {"task_id": task_id}
        if seed is not None:
            payload["seed"] = seed
            
        res = requests.post(f"{self.base_url}/reset", json=payload, timeout=10)
        res.raise_for_status()
        data = res.json()["observation"]
        
        self.episode_id = data["episode_id"]
        return self._map_obs(data)

    def step(self, action: Union[GlobalCrisisAction, Dict[str, int]]) -> GlobalCrisisObservation:
        if isinstance(action, GlobalCrisisAction):
            action_dict = action.to_dict()
        else:
            action_dict = action
            
        payload = {"action": action_dict}
        if self.episode_id:
            payload["episode_id"] = self.episode_id
            
        res = requests.post(f"{self.base_url}/step", json=payload, timeout=10)
        res.raise_for_status()
        data = res.json()
        
        obs_data = data["observation"]
        obs_data["reward"] = data["reward"]
        obs_data["done"] = data["done"]
        
        return self._map_obs(obs_data)

    def _map_obs(self, data: Dict[str, Any]) -> GlobalCrisisObservation:
        return GlobalCrisisObservation(
            episode_id=data["episode_id"],
            fuel_available=int(data["fuel_available"]),
            hospital_demand=int(data["hospital_demand"]),
            emergency_demand=int(data["emergency_demand"]),
            transport_demand=int(data["transport_demand"]),
            residential_demand=int(data["residential_demand"]),
            message=data["message"],
            reward=float(data.get("reward", 0.0)),
            done=bool(data.get("done", False))
        )
