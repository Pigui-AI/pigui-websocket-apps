import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from app.manager import ConnectionManager
import json

app = FastAPI(title="WebSocket Pub/Sub Microservice", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app = FastAPI(title="WebSocket Pub/Sub Microservice", version="1.0.0")
manager = ConnectionManager()


@app.get("/")
async def root():
    return {"message": "WebSocket Pub/Sub Service running", "docs": "/docs"}


@app.get("/topics")
async def get_topics():
    """Lista todos los temas activos y cuántos suscriptores tienen."""
    return {
        "topics": {
            topic: len(subscribers)
            for topic, subscribers in manager.topics.items()
        }
    }


@app.websocket("/ws/{topic}")
async def websocket_endpoint(websocket: WebSocket, topic: str):
    """
    Conéctate a un tema específico.
    
    - Al conectar: te suscribes automáticamente al tema.
    - Para enviar un mensaje a todos en el tema, envía JSON:
        {"action": "publish", "message": "Tu mensaje aquí"}
    - Para cambiarte de tema:
        {"action": "subscribe", "topic": "nuevo-tema"}
    """
    await manager.connect(websocket, topic)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                action = payload.get("action")

                if action == "publish":
                    message = payload.get("message", "")
                    await manager.broadcast(topic, message, sender=websocket)

                elif action == "subscribe":
                    new_topic = payload.get("topic", "").strip()
                    if new_topic:
                        await manager.change_topic(websocket, topic, new_topic)
                        topic = new_topic  # actualiza el tema local del loop
                    else:
                        await websocket.send_json({"error": "Debes indicar un 'topic' válido."})

                else:
                    await websocket.send_json({"error": f"Acción desconocida: '{action}'. Usa 'publish' o 'subscribe'."})

            except json.JSONDecodeError:
                await websocket.send_json({"error": "El mensaje debe ser JSON válido."})

    except WebSocketDisconnect:
        await manager.disconnect(websocket, topic)


@app.get("/test", response_class=HTMLResponse)
async def test_client():
    """Cliente HTML de prueba para el WebSocket."""
    html_path = os.path.join(os.path.dirname(__file__), "test_client.html")
    with open(html_path, encoding="utf-8") as f:
        return f.read()
