import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Set
from app.core.task_queue import task_queue


router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        """Accept and store new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        self.active_connections.discard(websocket)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time task updates"""
    await manager.connect(websocket)
    
    try:
        # Send initial data
        tasks = await task_queue.get_all_tasks(limit=100)
        stats = await task_queue.get_stats()
        
        await websocket.send_json({
            "type": "initial_data",
            "tasks": [json.loads(task.model_dump_json()) for task in tasks],
            "stats": stats
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                
                # Handle ping/pong for keepalive
                if data == "ping":
                    await websocket.send_text("pong")
                    
            except WebSocketDisconnect:
                break
            except Exception:
                break
    
    finally:
        manager.disconnect(websocket)


async def broadcast_task_update(task_id: str):
    """Broadcast task update to all connected clients"""
    task = await task_queue.get_task(task_id)
    stats = await task_queue.get_stats()
    
    if task:
        await manager.broadcast({
            "type": "task_update",
            "task": json.loads(task.model_dump_json()),
            "stats": stats
        })


async def broadcast_stats():
    """Broadcast statistics update to all connected clients"""
    stats = await task_queue.get_stats()
    await manager.broadcast({
        "type": "stats_update",
        "stats": stats
    })

