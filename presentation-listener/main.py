import openai
import threading
import pyaudio
import re
import wave
import tempfile
import os
import base64
import json
import asyncio
import websockets     
from src.slide_com import PresentationConnecton
from dotenv import load_dotenv
from multiprocessing import Process
from src.embedding import semantic_search
import uvicorn

def _run_socket_server():
    uvicorn.run(
        "src.slide_server:asgi_app",
        host="0.0.0.0",
        port=5050,
        log_level="info",
    )
class TranscriptStore:
    def __init__(self):
        self._queue   = asyncio.Queue()   # fan-out buffer for new items
        self._archive = []                # complete history

    async def publish(self, text: str):
        """Called by the consumer() in main.py"""
        self._archive.append(text)
        await self._queue.put(text)

    async def subscribe(self):
        """
        Async generator that yields every new transcript.
        Multiple tasks can call it concurrently.
        """
        while True:
            msg = await self._queue.get()
            yield msg

    # convenience accessors
    @property
    def history(self):          # list[str]
        return list(self._archive)

async def listen_and_transcribe_streaming(
        api_key: str,
        model: str = "gpt-4o-mini-transcribe",
        language: str = "en"
    ):
    """
    Continuously send microphone audio to OpenAI’s Realtime ASR endpoint
    and stream the partial / final transcriptions back to the console.
    """
    CHUNK       = 1024               # ≈64 ms of audio @16 kHz
    FORMAT      = pyaudio.paInt16
    CHANNELS    = 1
    RATE        = 16000
    store       = TranscriptStore()
    presentation = PresentationConnecton()

    keywords = {"next slide": presentation.next_slide,
               "previous slide": presentation.previous_slide}
    go_to_slide_pattern = re.compile(r"go to slide (\w+)", re.IGNORECASE)
    # --- microphone ---------------------------------------------------------

    p = pyaudio.PyAudio()
   
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    uri     = "wss://api.openai.com/v1/realtime?intent=transcription"
    headers = {"Authorization": f"Bearer {api_key}",
               "OpenAI-Beta": "realtime=v1",}

    async with websockets.connect(uri, extra_headers=headers, max_size=1_000_000) as ws:
        #  configure / start the transcription session
        await ws.send(json.dumps({
            "type": "transcription_session.update",
            "session": {                         #  ← required wrapper
                "input_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": model,              # eg "gpt-4o-mini-transcribe"
                    "prompt": "This is a presentation and/or a pitch about an OpenAI based product", # eg "This is a presentation about..."
                    "language": language         # eg "en"
        }
    }
        }))

        async def producer():
            """
            Read raw PCM16 data from the mic, base64-encode it,
            and push it up to the WebSocket.
            """
            try:
                while True:
                    data      = stream.read(CHUNK, exception_on_overflow=False)
                    audio_b64 = base64.b64encode(data).decode("ascii")
                    await ws.send(json.dumps({
                        "type": "input_audio_buffer.append",
                        "audio": audio_b64
                    }))
            except asyncio.CancelledError:
                pass

        async def consumer():
            """
            Listen for transcription events and print them.
            The exact event schema can evolve; adapt as needed.
            """
            async for message in ws:
                payload = json.loads(message)

                if payload.get("type") == "conversation.item.input_audio_transcription.completed":
                    text = payload.get('transcript', '')
                    print(f"📝: {text}", )
                    await store.publish(text)
                else:
                    # Uncomment to inspect all message types:
                    # Refresh the line every time we get a new delta
                    # print(f"DEBUG: {payload.get('delta', '')}")
                    pass
            # ----------------------- keyword agent ------------------------

        async def keyword_agent(keywords):
            """
            Waits for every new transcript published to TranscriptStore
            and prints when keywords/phrases are present.
            """
            async for text in store.subscribe():
                # check similarity 
                sim_res = semantic_search(text)
                if sim_res.get('page_number', None) is not None:
                    print(f"🔑 semantic match: {sim_res}")
                    await presentation.go_to_slide(sim_res['page_number'])
                    
                for keyword, func in keywords.items():
                    if keyword.lower() in text.lower():
                        print(f"🔑 keyword match {keyword}: {text}")
                        # Call the function associated with the keyword
                        await func()


        # Run producer & consumer concurrently until Ctrl-C
        await asyncio.gather(producer(), consumer(), keyword_agent(keywords))

    stream.stop_stream()
    stream.close()
    p.terminate()


if __name__ == "__main__":
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Please set the OPENAI_API_KEY environment variable.")
    else:
         asyncio.run(listen_and_transcribe_streaming(api_key))
