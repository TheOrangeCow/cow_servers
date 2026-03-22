class TerminalServer:
    def __init__(self, send_func, broadcast_func):
        self.send = send_func
        self.broadcast = broadcast_func
        self.clients = {}

    def join(self, client, name):
        self.clients[client] = name
        self.send(client, f"Welcome {name} to terminal")

    def leave(self, client):
        if client in self.clients:
            self.clients.pop(client)

    def handle(self, client, msg):
        if msg == "ping":
            self.send(client, "pong")
        else:
            self.send(client, f"Executed: {msg}")