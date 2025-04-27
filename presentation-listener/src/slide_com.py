import socketio
import asyncio

SERVER_URL = "http://localhost:5050"      # same host/port your uvicorn runs on

class PresentationConnecton:
    """
    Connects as a Socket.IO *client* and emits control events that the
    browser is listening to.
    """

    def __init__(self):
        # Re-use the global asyncio loop in main.py
        self.sio = socketio.AsyncClient(reconnection=True)

        @self.sio.event
        async def connect():
            print("📡  Presentation client connected to server")

        @self.sio.event
        async def disconnect():
            print("📡  Presentation client disconnected")

        # connect asynchronously; store the task so that import-time
        # instantiation doesn’t block
        self._connect_task = asyncio.create_task(self.sio.connect(SERVER_URL))

    # helper to ensure we’re connected before emitting
    async def _ready(self):
        await self._connect_task

    # API the rest of your code already calls
    async def next_slide(self):
        await self._ready()
        await self.sio.emit("nextSlide")

    async def previous_slide(self):
        await self._ready()
        await self.sio.emit("previousSlide")

    async def go_to_slide(self, slide_number: int):
        await self._ready()
        await self.sio.emit("changeSlide", slide_number)