# WebSocket Pub/Sub Microservice

Microservicio FastAPI con WebSockets que permite suscribirse a temas y publicar mensajes.

## Estructura

```
ws-pubsub/
├── app/
│   ├── __init__.py
│   ├── main.py          # Rutas FastAPI y endpoints WebSocket
│   ├── manager.py       # Lógica de pub/sub (ConnectionManager)
│   └── test_client.html # Cliente HTML de prueba
├── main.py              # Entry point
├── requirements.txt
└── Dockerfile
```

## Instalación y ejecución

```bash
pip install -r requirements.txt
python main.py
```

O con uvicorn directamente:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Con Docker:
```bash
docker build -t ws-pubsub .
docker run -p 8000:8000 ws-pubsub
```

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Info del servicio |
| GET | `/docs` | Swagger UI |
| GET | `/topics` | Temas activos y número de suscriptores |
| GET | `/test` | Cliente HTML de prueba |
| WS | `/ws/{topic}` | Conectar y suscribirse a un tema |

## Protocolo WebSocket

Conectarse a `ws://localhost:8000/ws/{nombre-del-tema}`.

### Publicar un mensaje
```json
{ "action": "publish", "message": "Hola a todos!" }
```

### Cambiar de tema
```json
{ "action": "subscribe", "topic": "otro-tema" }
```

### Eventos que recibirás
| Evento | Descripción |
|--------|-------------|
| `subscribed` | Confirmación de suscripción al tema |
| `message` | Nuevo mensaje de otro usuario |
| `published` | Confirmación de tu publicación |
| `user_joined` | Alguien se unió al tema |
| `user_left` | Alguien salió del tema |

## Ejemplo con JavaScript (cliente)

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/noticias");

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};

// Publicar
ws.send(JSON.stringify({ action: "publish", message: "¡Hola mundo!" }));

// Cambiar tema
ws.send(JSON.stringify({ action: "subscribe", topic: "deportes" }));
```

## Ejemplo con Python (cliente)

```python
import asyncio
import websockets
import json

async def main():
    async with websockets.connect("ws://localhost:8000/ws/noticias") as ws:
        # Recibir confirmación de suscripción
        print(await ws.recv())

        # Publicar un mensaje
        await ws.send(json.dumps({"action": "publish", "message": "Hola desde Python!"}))
        print(await ws.recv())

asyncio.run(main())
```
