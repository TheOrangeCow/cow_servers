class ChatServer:
    def __init__(self, send_func, broadcast_func):
        self.send = send_func
        self.broadcast = broadcast_func

        self.clients = []
        self.nicknames = []
        self.banned = set()

    def join(self, client, nickname):
        if nickname in self.banned:
            self.send(client, "You are banned.")
            return False

        if nickname == "admin":
            self.send(client, "PASS")
            return "WAITING_FOR_ADMIN_PASS"

        self.nicknames.append(nickname)
        self.clients.append(client)

        self.broadcast(f"{nickname} joined!")
        return True

    def admin_auth(self, client, password):
        if password != "password":
            self.send(client, "GOAWAY")
            return False

        self.nicknames.append("admin")
        self.clients.append(client)

        self.broadcast("admin joined!")
        return True

    def leave(self, client):
        if client in self.clients:
            idx = self.clients.index(client)
            name = self.nicknames[idx]

            self.clients.pop(idx)
            self.nicknames.pop(idx)

            self.broadcast(f"{name} left.")

    def kick_user(self, name):
        if name in self.nicknames:
            idx = self.nicknames.index(name)
            client = self.clients[idx]

            self.send(client, "You were kicked by admin.")
            self.leave(client)
            self.broadcast(f"{name} was kicked.")

    def ban_user(self, name):
        self.kick_user(name)
        self.banned.add(name)

        try:
            with open("bans.txt", "a") as f:
                f.write(name + "\n")
        except:
            pass

    def handle(self, client, msg):
        if client not in self.clients:
            return

        idx = self.clients.index(client)
        name = self.nicknames[idx]

        if msg.startswith("KICK"):
            if name == "admin":
                self.kick_user(msg[5:].strip())
            else:
                self.send(client, "Admin only.")

        elif msg.startswith("BAN"):
            if name == "admin":
                self.ban_user(msg[4:].strip())
            else:
                self.send(client, "Admin only.")

        else:
            self.broadcast(f"{name}: {msg}")