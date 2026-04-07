import os
import uvicorn
import gradio as gr
from fastapi.responses import RedirectResponse
from openenv.core.env_server import create_fastapi_app
from .environment import GlobalCrisisEnv
from .models import TaskAction, TaskObservation

# 1. Create the Backend Engine
# This instance will be shared by the API and the UI for consistency.
env_engine = GlobalCrisisEnv()

# 2. Create the OpenEnv FastAPI App
# The factory sets up /reset, /step, /metadata, etc.
app = create_fastapi_app(GlobalCrisisEnv, TaskAction, TaskObservation)

# Metadata for the API
app.title = "Global Energy Crisis Logistics Simulator"
app.version = "1.1.0"  # UI Upgrade
app.description = (
    "A high-stakes Geopolitical Energy Crisis simulating the distribution "
    "of a constrained strategic resource (fuel) across 4 global sectors."
)

# 3. Define the UI Logic (Human Interaction Layer)
def ui_reset(difficulty):
    obs = env_engine.reset(task_id=difficulty.lower())
    return (
        obs.episode_id,
        obs.fuel_available,
        obs.hospital_demand,
        obs.emergency_demand,
        obs.transport_demand,
        obs.residential_demand,
        f"🚨 MISSION COMMENCED\n{obs.message}",
        0.0,
        gr.update(visible=True),
        gr.update(value=0, interactive=True),
        gr.update(value=0, interactive=True),
        gr.update(value=0, interactive=True),
        gr.update(value=0, interactive=True)
    )

def ui_step(ep_id, h, e, t, r):
    if not ep_id or ep_id == "None":
        return None, 0, 0, 0, 0, 0, "❌ Error: Reset the mission first!", 0, gr.update(), 0, 0, 0, 0
    
    action = TaskAction(
        fuel_to_hospital=h,
        fuel_to_emergency=e,
        fuel_to_transport=t,
        fuel_to_residential=r
    )
    obs = env_engine.step(action, episode_id=ep_id)
    
    status = f"📝 STEP UPDATE\n{obs.message}"
    if obs.done:
        status += "\n\n🏁 MISSION COMPLETE. Final report generated."
        return (
            obs.episode_id, obs.fuel_available, obs.hospital_demand, 
            obs.emergency_demand, obs.transport_demand, obs.residential_demand,
            status, obs.reward, gr.update(visible=False), 0, 0, 0, 0
        )
    
    return (
        obs.episode_id, obs.fuel_available, obs.hospital_demand, 
        obs.emergency_demand, obs.transport_demand, obs.residential_demand,
        status, obs.reward, gr.update(visible=True), 0, 0, 0, 0
    )

# 4. Build the "Gold Medal" Command Center Layout
with gr.Blocks(theme=gr.themes.Soft(primary_hue="red", secondary_hue="orange")) as dio:
    gr.Markdown("# 🏙️ GLOBAL ENERGY CRISIS: COMMAND CENTER")
    gr.Markdown("### *Strategic Resource Allocation & Logistics Simulator*")
    
    with gr.Row():
        with gr.Column(scale=1):
            diff_input = gr.Radio(["Easy", "Medium", "Hard"], value="Easy", label="Select Crisis Intensity")
            reset_btn = gr.Button("🚀 INITIALIZE NEW MISSION", variant="primary")
            ep_id_display = gr.Textbox(label="Mission ID", interactive=False)
            
        with gr.Column(scale=3):
            with gr.Group():
                gr.Markdown("### 📡 Real-Time Sector Demand (Lower is Better)")
                with gr.Row():
                    h_gauge = gr.Number(label="🏥 Hospitals", interactive=False)
                    e_gauge = gr.Number(label="🚒 Emergency", interactive=False)
                    t_gauge = gr.Number(label="🚚 Transport", interactive=False)
                    r_gauge = gr.Number(label="🏠 Residential", interactive=False)
            
            fuel_gauge = gr.Slider(0, 200, label="⛽ FUEL RESERVE", interactive=False)
    
    with gr.Row(visible=False) as control_row:
        with gr.Column():
            gr.Markdown("### 🛠️ ALLOCATION PLAN")
            with gr.Row():
                h_in = gr.Number(label="Fuel -> Hospital", value=0)
                e_in = gr.Number(label="Fuel -> Emergency", value=0)
                t_in = gr.Number(label="Fuel -> Transport", value=0)
                r_in = gr.Number(label="Fuel -> Residential", value=0)
            step_btn = gr.Button("⚡ EXECUTE LOGISTICS PLAN", variant="stop")
            
    with gr.Row():
        with gr.Column():
            log_output = gr.Textbox(label="Crisis Log", lines=8, interactive=False)
            reward_display = gr.Number(label="Current Step Efficiency (Reward)", interactive=False)

    # Wire up the events
    reset_btn.click(
        ui_reset, inputs=[diff_input], 
        outputs=[ep_id_display, fuel_gauge, h_gauge, e_gauge, t_gauge, r_gauge, log_output, reward_display, control_row, h_in, e_in, t_in, r_in]
    )
    step_btn.click(
        ui_step, inputs=[ep_id_display, h_in, e_in, t_in, r_in], 
        outputs=[ep_id_display, fuel_gauge, h_gauge, e_gauge, t_gauge, r_gauge, log_output, reward_display, control_row, h_in, e_in, t_in, r_in]
    )

# 5. Mount UI to root and Swagger to /docs
app = gr.mount_gradio_app(app, dio, path="/")

def main():
    port = int(os.getenv("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
