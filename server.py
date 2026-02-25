from unittest import case

from fastapi import FastAPI, Request
from fastapi.websockets import WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import time
from services.connectionManager import ConnectionManager, NoCacheMiddleware
from services.security import hash_password
from fastapi import Form
from fastapi.responses import RedirectResponse
from fastapi import status


from models.user import ClientAccount
class Server:
    def __init__(self, manager: ConnectionManager, app: FastAPI= FastAPI()):
        self.manager = manager
        self.app = app
        self.app.mount("/static", StaticFiles(directory="static"), name="static")

    def run(self):
        self.setup_routes()
        import uvicorn
        self.app.add_middleware(NoCacheMiddleware)
        uvicorn.run(self.app, host="0.0.0.0", port=8000)
    
    
    def setup_routes(self):
        @self.app.get("/register")
        async def get_register():
            with open("./templates/register.html", "r") as f:
                html_content = f.read()
            return HTMLResponse(content=html_content, status_code=200)
        
        @self.app.post("/register")
        async def post_register(username: str = Form(...), password: str = Form(...)):
            print(f"Registered new user: {username}")

            if username in self.manager.active_connections:
                return HTMLResponse("<h3>Username already taken</h3>", status_code=400)


            response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

            # on stocke la session
            response.set_cookie(
                key="username",
                value=username,
                httponly=True,  # important (sécurité)
                samesite="lax",
                path="/"
            )

            return response
        @self.app.get("/")
        async def get(request: Request):
            username = request.cookies.get("username")

            with open("./templates/client.html", "r") as f:
                html_content = f.read()

            # injecter le username dans la page
            html_content = html_content.replace("{{username}}", username if username else "")

            return HTMLResponse(content=html_content, status_code=200)
        
        @self.app.get("/client_count")
        async def get_client_count():
            return {"count": await self.manager.get_connection_count()}


        @self.app.websocket("/ws")
        async def websocket_endpoint(ws: WebSocket):
            print("Cookies reçus:", ws.cookies)
            cookie_username = ws.cookies.get("username")

            if not cookie_username:
                await ws.close(code=1008, reason="Username cookie is required")
                return
                
                
            
            first = await self.manager.connection(ws, cookie_username)

            if first:
                await self.manager.broadcast(f"Client {cookie_username} joined the chat")
            try:
                while True:
                    data = await ws.receive_text()
                    #await manager.send_personal_message(f"You wrote: {data}", ws)

                    match data:
                        case _ if data.startswith("@"):
                            target, msg = data[1:].split(" ", 1)
                            if target in self.manager.active_connections:
                                await self.manager.private_message(f"Private from @{cookie_username}: {msg}", target)
                                await self.manager.send_personal_message(f"Private to @{target}: {msg}", ws)
                            else:
                                await self.manager.send_personal_message(f"User @{target} not found.", ws)
                        case _ if data.startswith("/help"):
                            help_msg = "\n".join(self.manager.get_command_list())
                            await self.manager.send_personal_message(help_msg, ws)

                        case _ if data.startswith("/add_friend @"):
                            friend_username = data.split("@", 1)[1].strip()
                            self.manager.active_connections[cookie_username]["account"].add_friend(friend_username)
                            await self.manager.send_personal_message(f"Added @{friend_username} as a friend.", ws)
                        case _ if data.startswith("/show_friends"):
                            friends = self.manager.active_connections[cookie_username]["account"].friends
                            await self.manager.send_personal_message(f"your friends: {','.join(friends)}", ws)
                        case _ if data.startswith("/show_info"):
                            info = self.manager.active_connections[cookie_username]["account"].show_info()
                            await self.manager.send_personal_message(f"Your account info: {info}", ws)
                        case _ if data.startswith("/"):
                            await self.manager.send_personal_message("Unknown command. Type /help for a list of commands.", ws)
                        case _:
                            await self.manager.broadcast(f"@{cookie_username}: {data}")
                
            except WebSocketDisconnect:
                await self.manager.broadcast(f"Client {cookie_username} left the chat")
                self.manager.disconnect(cookie_username, ws)
                await self.manager.broadcast(f"{cookie_username} left the chat")
        return self.app  

    
if __name__ == "__main__":
    manager = ConnectionManager()
    server = Server(manager)
    server.run()