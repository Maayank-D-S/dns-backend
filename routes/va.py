# routes/voice_agent.py
from flask import Blueprint, request, jsonify
import asyncio, json
from livekit import api
from livekit.api import CreateAgentDispatchRequest

voice_agent_bp = Blueprint("voice_agent", __name__)

async def dispatch_agent(room_name, user_id, session_id):
    lk = api.LiveKitAPI()  # Uses env vars like LIVEKIT_API_KEY
    req = CreateAgentDispatchRequest(
        agent_name="my-agent",  # same as in WorkerOptions
        room=room_name,
        metadata=json.dumps({
            "user_id": user_id,
            "session_id": session_id
        })
    )
    dispatch = await lk.agent_dispatch.create_dispatch(req)
    print("dispatch",dispatch)
    await lk.aclose()
    return dispatch

@voice_agent_bp.route("/dispatch", methods=["POST"])
def handle_dispatch():
    data = request.json
    room = data.get("room")
    user_id = data.get("user_id")
    session_id = data.get("session_id")

    if not room or not user_id or not session_id:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        result = asyncio.run(dispatch_agent(room, user_id, session_id))
        return jsonify({"status": "ok", "dispatch_id": result.id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
