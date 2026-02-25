import time
from fastapi import WebSocket, WebSocketDisconnect

from models.user import ClientAccount

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, dict] = {}

   
    async def connection(self, websocket: WebSocket, client_id: str) -> bool:
        await websocket.accept()

        first_connection = False

        if client_id not in self.active_connections:
            account = ClientAccount(client_id, None)
            account.set_status("online")

            self.active_connections[client_id] = {
                "account": account,
                "sockets": []
            }

            first_connection = True
            print(f"{client_id} connected (first session)")

        self.active_connections[client_id]["sockets"].append(websocket)

        print(f"{client_id} opened socket ({len(self.active_connections[client_id]['sockets'])})")

        return first_connection   
    def disconnect(self, client_id: str, websocket: WebSocket) -> bool:
        if client_id not in self.active_connections:
            return False

        sockets = self.active_connections[client_id]["sockets"]

        if websocket in sockets:
            sockets.remove(websocket)

        print(f"{client_id} closed socket ({len(sockets)} remaining)")

        if not sockets:
            self.active_connections[client_id]["account"].set_status("offline")
            del self.active_connections[client_id]
            print(f"{client_id} fully disconnected")

            return True  # dernière session fermée

        return False
              
    async def send_personal_message(self, message: str, websocket: WebSocket):
        time_stramp = time.strftime("%H:%M")
        try:
            await websocket.send_text(f"{time_stramp} - {message}")
        except:
            pass

    async def broadcast(self, message: str):
        time_stramp = time.strftime("%H:%M")

        for client_id, data in self.active_connections.items():
            for ws in data["sockets"]:
                try:
                    await ws.send_text(f"{time_stramp} - {message}")
                except:
                    pass  # socket mort → ignoré

    async def private_message(self, message: str, username: str):
        if username not in self.active_connections:
            return

        time_stramp = time.strftime("%H:%M")

        for ws in self.active_connections[username]["sockets"]:
            await ws.send_text(f"{time_stramp} - {message}")
    
    async def get_connection_count(self):
        return len(self.active_connections)
    
    def get_command_list(self):
        return [
            "@username message - Send private message",
            "/help - Show this help message",
            "/add_friend @username - Add a friend",
            "/show_friends - Show your friends list",
            "/show_info - Show your account info"
        ]


from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware

class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        return response

