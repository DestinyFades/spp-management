import asyncio
from typing import Dict, List

class SSEManager:
    def __init__(self):
        self.connections: Dict[str, List[asyncio.Queue]] = {}
    
    async def subscribe(self, session_id: str):
        queue = asyncio.Queue()
        if session_id not in self.connections:
            self.connections[session_id] = []
        self.connections[session_id].append(queue)
        return queue
    
    async def publish(self, calc_id: str, data: dict):
        for session_queues in self.connections.values():
            for queue in session_queues:
                await queue.put({
                    "event": "new_calculation",
                    "data": {"calc_id": calc_id, "tree": data}
                })
    
    async def notify_session(self, session_id: str, calc_id: int):
        if session_id in self.connections:
            for queue in self.connections[session_id]:
                await queue.put({
                    "event": "saved_calculation",
                    "data": {"saved_id": calc_id}
                })

sse_manager = SSEManager()
