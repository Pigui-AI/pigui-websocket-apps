from fastapi import WebSocket
from typing import Dict, Set
import json
from datetime import datetime


class ConnectionManager:
    def __init__(self):
        # topic -> set of WebSocket connections
        self.topics: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, topic: str):
        await websocket.accept()
        self._add_to_topic(websocket, topic)
        await websocket.send_json({
            "event": "subscribed",
            "topic": topic,
            "subscribers": len(self.topics[topic]),
            "timestamp": self._now()
        })
        await self._notify_topic(topic, {
            "event": "user_joined",
            "topic": topic,
            "subscribers": len(self.topics[topic]),
            "timestamp": self._now()
        }, exclude=websocket)

    async def disconnect(self, websocket: WebSocket, topic: str):
        self._remove_from_topic(websocket, topic)
        await self._notify_topic(topic, {
            "event": "user_left",
            "topic": topic,
            "subscribers": len(self.topics.get(topic, [])),
            "timestamp": self._now()
        })

    async def broadcast(self, topic: str, message: str, sender: WebSocket):
        if topic not in self.topics:
            return
        payload = {
            "event": "message",
            "topic": topic,
            "message": message,
            "timestamp": self._now()
        }
        for connection in list(self.topics[topic]):
            if connection != sender:
                try:
                    await connection.send_json(payload)
                except Exception:
                    self._remove_from_topic(connection, topic)
        # Confirmar al sender
        await sender.send_json({
            "event": "published",
            "topic": topic,
            "message": message,
            "delivered_to": len(self.topics.get(topic, [])),
            "timestamp": self._now()
        })

    async def change_topic(self, websocket: WebSocket, old_topic: str, new_topic: str):
        # Salir del tema anterior
        self._remove_from_topic(websocket, old_topic)
        await self._notify_topic(old_topic, {
            "event": "user_left",
            "topic": old_topic,
            "subscribers": len(self.topics.get(old_topic, [])),
            "timestamp": self._now()
        })
        # Entrar al nuevo tema
        self._add_to_topic(websocket, new_topic)
        await websocket.send_json({
            "event": "subscribed",
            "topic": new_topic,
            "subscribers": len(self.topics[new_topic]),
            "timestamp": self._now()
        })
        await self._notify_topic(new_topic, {
            "event": "user_joined",
            "topic": new_topic,
            "subscribers": len(self.topics[new_topic]),
            "timestamp": self._now()
        }, exclude=websocket)

    def _add_to_topic(self, websocket: WebSocket, topic: str):
        if topic not in self.topics:
            self.topics[topic] = set()
        self.topics[topic].add(websocket)

    def _remove_from_topic(self, websocket: WebSocket, topic: str):
        if topic in self.topics:
            self.topics[topic].discard(websocket)
            if not self.topics[topic]:
                del self.topics[topic]

    async def _notify_topic(self, topic: str, payload: dict, exclude: WebSocket = None):
        if topic not in self.topics:
            return
        for connection in list(self.topics[topic]):
            if connection != exclude:
                try:
                    await connection.send_json(payload)
                except Exception:
                    self._remove_from_topic(connection, topic)

    def _now(self) -> str:
        return datetime.utcnow().isoformat() + "Z"
