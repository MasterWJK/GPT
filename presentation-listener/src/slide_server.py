# src/slide_server.py
#
# – Starts an ASGI Socket.IO server on http://localhost:5000
# –  Exposes helpers next_slide(), previous_slide(), change_slide()
#    that *any* other module can import and call.

import asyncio
from typing import Optional

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware 
import uvicorn

# ------------------------------------------------------------------ #
# Socket.IO plumbing
# ------------------------------------------------------------------ #
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # or ["http://localhost:5173"] etc.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
asgi_app = socketio.ASGIApp(sio, other_asgi_app=app)   # <<< THIS is what uvicorn must run

# ------------------------------------------------------------------ #
#  Utility to ensure coroutines are executed on the server’s loop
# ------------------------------------------------------------------ #

    
@sio.event
async def connect(sid, environ):
    print(f"✅  client connected: {sid}")
    await sio.emit("nextSlide", sid) 


@sio.event
async def disconnect(sid):
    print(f"❌  client disconnected: {sid}")


# ------------------------------------------------------------------ #
# Helper API that other Python modules can call
# ------------------------------------------------------------------ #
async def _emit(event: str, data: Optional[object] = None):
    """Internal helper always schedule on the running loop. Emits to all connected users."""
    await sio.emit(event, data) 
    print(f"🔔  emitted  {event}  -> {data}")

@sio.on("nextSlide")
def next_slide(*data):
    print(f"🔔  received nextSlide  -> {data}")
    sio.start_background_task(_emit, "nextSlide")

@sio.on("previousSlide")
def previous_slide(*data):
    print(f"🔔  received previousSlide  -> {data}")
    sio.start_background_task(_emit, "previousSlide")

@sio.on("changeSlide")
def change_slide(sid, slide_number: int):
    sio.start_background_task(_emit, "changeSlide", slide_number)


# ------------------------------------------------------------------ #
# If you want to run this file directly (`python -m src.slide_server`)
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    uvicorn.run(
        "src.slide_server:asgi_app",
        host="0.0.0.0",
        port=5050,
        log_level="info",
        reload=False,
    )