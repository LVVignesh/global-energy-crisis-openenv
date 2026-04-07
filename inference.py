import os
import json
import re
import asyncio
import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("HF_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Meta-Llama-3-8B-Instruct")
ENV_URL = os.getenv("ENV_URL", "http://127.0.0.1:7860")

client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)


def extract_json(text: str) -> dict:
    """Robustly extract a JSON object from LLM response text."""
    import re
    json_match = re.search(r"\{.*\}", text, re.DOTALL)

    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
            
    return {
        "fuel_to_hospital": 0,
        "fuel_to_emergency": 0,
        "fuel_to_transport": 0,
        "fuel_to_residential": 0
    }


async def run_mission(task_id: str):
    """
    Execute one mission (easy/medium/hard).
    Emits mandatory [START] / [STEP] / [END] log format for automated grading.
    """
    print(f"[START] task={task_id} env=global_crisis_logistics model={MODEL_NAME}")

    # --- Reset ---
    try:
        res = requests.post(f"{ENV_URL}/reset", json={"task_id": task_id}, timeout=10)
        res.raise_for_status()
        obs = res.json()["observation"]
    except Exception as exc:
        print(f"[END] success=false steps=0 rewards= error={exc}")
        return

    rewards = []

    for step in range(1, 6):
        # Dynamically adjust the AI's strategic instructions based on the difficulty mode
        if task_id == "easy":
            strategy = (
                "STRATEGY for EASY MODE: You have PLENTY of fuel (160 total). "
                "However, DO NOT fulfill all demands in a single turn! The city needs a steady supply. "
                "You must carefully pace yourself to spread your allocations across all 5 steps (e.g., 20-30 units per step)."
            )
        elif task_id == "medium":
            strategy = (
                "STRATEGY for MEDIUM MODE: Fuel is restricted (120 total). "
                "Prioritize the Hospital, Transport, and Emergency sectors first. "
                "Only give the leftover fuel to the Residential sector. Be careful not to exceed `fuel_available`."
            )
        else:
            strategy = (
                "STRATEGY for HARD MODE: CRITICAL FUEL SHORTAGE (80 total). "
                "RULE 1: You MUST prioritize the `transport` bottleneck first to unlock supply lines. "
                "RULE 2: Prioritize Hospitals next. "
                "RULE 3: Emergency and Residential sectors only get the scraps. DO NOT exceed `fuel_available`."
            )

        prompt = (
            "You are a Geopolitical Crisis Logistics AI. You have up to 5 steps to stabilize the sectors.\n"
            "CRITICAL RULE: The SUM of fuel you allocate right now MUST NOT exceed `fuel_available`.\n\n"
            f"{strategy}\n\n"
            f"Current observation:\n{json.dumps(obs, indent=2)}\n\n"
            "Respond ONLY with a JSON object:\n"
            '{"fuel_to_hospital": <int>, "fuel_to_emergency": <int>, '
            '"fuel_to_transport": <int>, "fuel_to_residential": <int>}'
        )

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=120,
            )
            action = extract_json(response.choices[0].message.content)
        except Exception as exc:
            print(f"[STEP] step={step} action=null reward=0.00 done=true error={exc}")
            break

        # Use episode_id from the observation
        episode_id = obs.get("episode_id", "")

        try:
            step_res = requests.post(
                f"{ENV_URL}/step",
                json={"action": action, "episode_id": episode_id},
                timeout=10,
            )
            step_res.raise_for_status()
            data = step_res.json()
        except Exception as exc:
            print(f"[STEP] step={step} action={json.dumps(action)} reward=0.00 done=true error={exc}")
            break

        obs = data["observation"]
        reward = float(data["reward"])
        done = bool(data["done"])
        fuel_left = obs.get("fuel_available", 0)
        rewards.append(f"{reward:.2f}")

        print(
            f"[STEP] step={step} action={json.dumps(action)} "
            f"reward={reward:.2f} done={str(done).lower()} "
            f"error=null"
        )

        if done:
            break

    total = sum(float(r) for r in rewards)
    score = round(min(max(total / max(len(rewards), 1), 0.0), 1.0), 4)
    success = score >= 0.5
    print(
        f"[END] success={str(success).lower()} "
        f"steps={len(rewards)} score={score} rewards={','.join(rewards)}"
    )


if __name__ == "__main__":
    for task in ["easy", "medium", "hard"]:
        asyncio.run(run_mission(task))
