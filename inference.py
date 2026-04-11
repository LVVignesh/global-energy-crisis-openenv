import sys
import os
import re
import json
from openai import OpenAI
from dotenv import load_dotenv

# Ensure the root directory is in sys.path for robust imports of client.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from client import GlobalCrisisEnv, GlobalCrisisAction

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("HF_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Meta-Llama-3-8B-Instruct")
ENV_URL = os.getenv("ENV_URL", "http://127.0.0.1:7860")

client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)


def extract_json(text: str) -> dict:
    """Robustly extract a JSON object from LLM response text."""
    json_match = re.search(r"\{.*\}", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    # Safe fallback to prevent crashes
    return {
        "fuel_to_hospital": 0,
        "fuel_to_emergency": 0,
        "fuel_to_transport": 0,
        "fuel_to_residential": 0
    }


def run_mission(task_id: str):
    """
    Execute one mission using the professional Client SDK.
    Emits mandatory [START] / [STEP] / [END] log format.
    """
    print(f"[START] task={task_id} env=global_crisis_logistics model={MODEL_NAME}")

    try:
        env = GlobalCrisisEnv(base_url=ENV_URL)
        obs = env.reset(task_id=task_id)
    except Exception as exc:
        print(f"[END] success=false steps=0 rewards= error={exc}")
        return

    rewards = []

    for step_num in range(1, 6):
        # Explicit observation mapping to ensure clean JSON serialization
        obs_summary = {
            "fuel_available": obs.fuel_available,
            "hospital_demand": obs.hospital_demand,
            "emergency_demand": obs.emergency_demand,
            "transport_demand": obs.transport_demand,
            "residential_demand": obs.residential_demand,
            "message": obs.message
        }

        # Strategy context including the new Precision Logistics / Waste Penalty
        if task_id == "easy":
            strategy = (
                "STRATEGY for EASY MODE: You have PLENTY of fuel (160 total). "
                "PRECISION RULE: Do not over-allocate! Sending more fuel than needed results in a WASTE PENALTY. "
                "Pace your allocations across all 5 steps."
            )
        elif task_id == "medium":
            strategy = (
                "STRATEGY for MEDIUM MODE: Fuel is restricted (120 total). "
                "Priority: Hospital > Transport > Emergency. Avoid waste to maximize your score."
            )
        else:
            strategy = (
                "STRATEGY for HARD MODE: CRITICAL FUEL SHORTAGE (80 total). "
                "RULE 1: You MUST clear the `transport` bottleneck (demand > 5) to unlock 100% efficiency. "
                "RULE 2: Avoid sending fuel and wasting it on full sectors (Waste Penalty applies)."
            )

        prompt = (
            "You are a Geopolitical Crisis Logistics AI. You have 5 steps to stabilize the city.\n"
            "RESOURCE OPTIMIZATION: Sending more fuel than the current demand causes an 'Inefficiency Penalty'.\n\n"
            f"{strategy}\n\n"
            f"Current observation:\n{json.dumps(obs_summary, indent=2)}\n\n"
            "Analyze the situation and respond ONLY with a JSON object containing a 'thought_process' and the 4 allocation fields:\n"
            '{"thought_process": "...", "fuel_to_hospital": <int>, "fuel_to_emergency": <int>, '
            '"fuel_to_transport": <int>, "fuel_to_residential": <int>}'
        )

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=250,
            )
            raw_content = response.choices[0].message.content
            action_data = extract_json(raw_content)
            
            # Create a typed action object
            action = GlobalCrisisAction(
                fuel_to_hospital=int(action_data.get("fuel_to_hospital", 0)),
                fuel_to_emergency=int(action_data.get("fuel_to_emergency", 0)),
                fuel_to_transport=int(action_data.get("fuel_to_transport", 0)),
                fuel_to_residential=int(action_data.get("fuel_to_residential", 0))
            )
        except Exception as exc:
            print(f"[STEP] step={step_num} action=null reward=0.00 done=true error={exc}")
            break

        try:
            obs = env.step(action)
            reward_str = f"{obs.reward:.2f}"
            rewards.append(reward_str)

            # Emission of logs including the AI's reasoned action
            clean_action = action.to_dict()
            print(
                f"[STEP] step={step_num} action={json.dumps(clean_action)} "
                f"reward={reward_str} done={str(obs.done).lower()} "
                f"error=null"
            )

            if obs.done:
                break
        except Exception as exc:
            print(f"[STEP] step={step_num} action={json.dumps(action.to_dict())} reward=0.00 done=true error={exc}")
            break

    total = sum(float(r) for r in rewards)
    score = round(min(max(total / 5, 0.0), 1.0), 4)
    success = score >= 0.5
    print(
        f"[END] success={str(success).lower()} "
        f"steps={len(rewards)} rewards={','.join(rewards)}"
    )


if __name__ == "__main__":
    for task in ["easy", "medium", "hard"]:
        run_mission(task)
