import json
import uuid
from typing import Dict, List
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # Mapping: room_id -> list of active WebSockets
        self.active_rooms: Dict[uuid.UUID, List[WebSocket]] = {}

    async def connect(self, room_id: uuid.UUID, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.active_rooms:
            self.active_rooms[room_id] = []
        self.active_rooms[room_id].append(websocket)

    def disconnect(self, room_id: uuid.UUID, websocket: WebSocket):
        if room_id in self.active_rooms:
            if websocket in self.active_rooms[room_id]:
                self.active_rooms[room_id].remove(websocket)
            if not self.active_rooms[room_id]:
                del self.active_rooms[room_id]

    async def broadcast_to_room(self, room_id: uuid.UUID, event: dict):
        if room_id not in self.active_rooms:
            return

        dead_connections = []
        message = json.dumps(event)
        for connection in self.active_rooms[room_id]:
            try:
                await connection.send_text(message)
            except Exception:
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(room_id, dead)


ws_manager = ConnectionManager()
