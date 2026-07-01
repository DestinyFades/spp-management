from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
from app.services.sse_manager import sse_manager
import asyncio

router = APIRouter()

@router.get("/events")
async def sse_events(session_id: str = "default"):
    queue = await sse_manager.subscribe(session_id)
    
    async def event_generator():
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30)
                yield event
            except asyncio.TimeoutError:
                yield {"event": "ping", "data": ""}
            except Exception as e:
                print(f"SSE ошибка: {e}")
                break
    
    return EventSourceResponse(event_generator())
