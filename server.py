from fastapi import FastAPI
from fastapi.websockets import WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connection(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = {
            "websocket": websocket,
        }
        new_client = ClientAccount(client_id, None)
        new_client.set_status("online")
        self.active_connections[client_id]["account"] = new_client
        print(f"Client connected: {self.active_connections[client_id]['account'].show_info()}")
        
    def disconnect(self, websocket: WebSocket, client_id: str):
        self.active_connections.pop(client_id, None)
        print(f"Client disconnected: {client_id}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message:str):
        for conn in self.active_connections:
            await self.active_connections[conn]["websocket"].send_text(message)

    async def private_message(self, message:str, username:str):
        await self.active_connections[username]["websocket"].send_text(message)
    
    async def get_connection_count(self):
        return len(self.active_connections)
    
class ClientAccount:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.status = "offline"
        self.friends = set()
        self.permissions = set()
    
    def add_friend(self, friend_username):
        self.friends.add(friend_username)
    
    def remove_friend(self, friend_username):
        self.friends.discard(friend_username)
    
    def add_permission(self, permission):
        self.permissions.add(permission)

    def remove_permission(self, permission):
        self.permissions.discard(permission)
    
    def set_status(self, status):
        self.status = status

    def show_info(self):
        return {
            "username": self.username,
            "status": self.status,
            "friends": list(self.friends),
            "permissions": list(self.permissions)
        }


manager = ConnectionManager()

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get():
    with open("./templates/client.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/login")
async def get_login():
    with open("./templates/connection.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/client_count")
async def get_client_count():
    return {"count": await manager.get_connection_count()}


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(ws: WebSocket, client_id: str, password: str = None):
    await manager.connection(ws, client_id)
    await manager.broadcast(f"Client {client_id} joined the chat")
    try:
        while True:
            data = await ws.receive_text()
            #await manager.send_personal_message(f"You wrote: {data}", ws)
            if data.startswith("@"):
                target, msg = data[1:].split(" ", 1)
                if target in manager.active_connections:
                    await manager.private_message(f"Private from @{client_id}: {msg}", target)
                    await manager.send_personal_message(f"Private to @{target}: {msg}", ws)
                else:
                    await manager.send_personal_message(f"User @{target} not found.", ws)
            elif data.startswith("/help"):
                help_msg = "Commands:\n"
                help_msg += "@username message - Send private message\n |"
                help_msg += "/help - Show this help message\n |"
                help_msg += "/add_friend @username - Add a friend\n |"
                help_msg += "/show_friends - Show your friends list\n |"
                help_msg += "/show_info - Show your account info\n |"
                await manager.send_personal_message(help_msg, ws)
            elif data.startswith("/add_friend @"):
                friend_username = data.split("@", 1)[1].strip()
                manager.active_connections[client_id]["account"].add_friend(friend_username)
                await manager.send_personal_message(f"Added @{friend_username} as a friend.", ws)
            elif data.startswith("/show_friends"):
                friends = manager.active_connections[client_id]["account"].friends
                await manager.send_personal_message(f"your friends: {','.join(friends)}", ws)
            elif data.startswith("/show_info"):
                info = manager.active_connections[client_id]["account"].show_info()
                await manager.send_personal_message(f"Your account info: {info}", ws)
            elif data.startswith("/"):
                await manager.send_personal_message("Unknown command. Type /help for a list of commands.", ws)
            else:
                await manager.broadcast(f"@{client_id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(ws, client_id)
        await manager.broadcast(f"Client {client_id} left the chat")
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)