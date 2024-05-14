from starlette.websockets import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket, role_id):
        await websocket.accept()
        self.active_connections.append({'role': role_id, 'socket': websocket})

    def disconnect(self, websocket: WebSocket):
        for connection in self.active_connections:
            if connection.get('socket') == websocket:
                self.active_connections.remove(connection)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def send_role_message(self, message: str, role_id):
        # for connection in self.active_connections:
        #     if connection.get('role') == role_id:
        #         await connection.get('socket').send_text(message)
        for connection in self.active_connections:
            if str(connection.get('role')) == str(role_id):
                await connection.get('socket').send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.get('socket').send_text(message)


manager = ConnectionManager()
