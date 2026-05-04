import asyncio
from typing import Callable, Awaitable, Dict
from agents.plugins.orbit.axl_client import AXLClient
from agents.plugins.orbit.messages import decode_message, AXLMessage

Handler = Callable[[AXLMessage], Awaitable[None]]

class AXLListener:
    def __init__(self, axl_client: AXLClient):
        self.axl = axl_client
        self.handlers: Dict[str, Handler] = {}
        self.running = False

    def on(self, msg_type: str, handler: Handler):
        self.handlers[msg_type] = handler

    async def start(self):
        self.running = True
        while self.running:
            try:
                messages = self.axl.recv()
                for raw_msg in messages:
                    msg = decode_message(raw_msg)
                    handler = self.handlers.get(msg.type)
                    if handler:
                        await handler(msg)
            except Exception as e:
                print(f"Listener error: {e}")
            await asyncio.sleep(1)  # Poll interval (GAP: not specified in blueprint)

    async def stop(self):
        self.running = False
