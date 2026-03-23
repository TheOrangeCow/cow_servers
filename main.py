from flask import Flask, jsonify, request
import socket
import threading
import random
import os

app = Flask(__name__)

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD_SOKETS").encode()


servers = {}



class ChatServer:
    def __init__(self, server_id, password):
        self.server_id = server_id
        self.password = password
        self.clients = []
        self.nicknames = []
        self.banned = set()

    def broadcast(self, message):
        for client in self.clients[:]:
            try:
                client.send(message)
            except:
                self.remove_client(client)

    def remove_client(self, client):
        if client in self.clients:
            idx = self.clients.index(client)
            name = self.nicknames[idx]
            self.clients.pop(idx)
            self.nicknames.pop(idx)
            self.broadcast(f"{name} left.".encode())
            client.close()

    def kick_user(self, name):
        if name in self.nicknames:
            idx = self.nicknames.index(name)
            client = self.clients[idx]

            client.send("You were kicked.".encode())
            client.close()

            self.clients.pop(idx)
            self.nicknames.pop(idx)

            self.broadcast(f"{name} was kicked.".encode())

    def handle(self, client):
        while True:
            try:
                msg = client.recv(1024)
                if not msg:
                    break

                text = msg.decode()

                if text.startswith("KICK"):
                    if self.nicknames[self.clients.index(client)] == 'admin':
                        self.kick_user(text[5:].strip())
                    else:
                        client.send("Admin only.".encode())

                elif text.startswith("BAN"):
                    if self.nicknames[self.clients.index(client)] == 'admin':
                        name = text[4:].strip()
                        self.banned.add(name)
                        self.kick_user(name)
                    else:
                        client.send("Admin only.".encode())

                else:
                    self.broadcast(msg)

            except:
                break

        self.remove_client(client)

    def join(self, client):
        client.send(b"NICK")
        nickname = client.recv(1024).decode()

        if nickname in self.banned:
            client.send(b"BANNED")
            client.close()
            return

        if nickname == 'admin':
            client.send(b"PASS")
            if client.recv(1024).decode() != self.password:
                client.send(b"GOAWAY")
                client.close()
                return

        self.nicknames.append(nickname)
        self.clients.append(client)

        self.broadcast(f"{nickname} joined!".encode())

        threading.Thread(target=self.handle, args=(client,), daemon=True).start()



class EchoServer:
    def __init__(self, server_id, password):
        self.password = password

    def join(self, client):
        while True:
            try:
                data = client.recv(1024)
                if not data:
                    break
                client.send(b"Echo: " + data)
            except:
                break
        client.close()


SERVER_TYPES = {
    "chat": ChatServer,
    "echo": EchoServer
}


def start_controller():
    host = '0.0.0.0'
    port = 6000

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()

    print(f"[+] Controller running on {port}")

    while True:
        client, addr = server.accept()
        threading.Thread(target=handle_client, args=(client,), daemon=True).start()


def handle_client(client):
    try:
        client.send(b"SERVER_ID")
        server_id = client.recv(1024).decode().strip()

        client.send(b"PASS")
        password = client.recv(1024).decode().strip()

        if server_id not in servers:
            client.send(b"NO_SERVER")
            client.close()
            return

        server = servers[server_id]

        if password != server.password:
            client.send(b"WRONG_PASS")
            client.close()
            return

        client.send(b"OK")

        server.join(client)

    except:
        client.close()



@app.route("/cow_servers/create", methods=["POST"])
def create_server():
    data = request.json or {}
    server_type = data.get("type", "chat")

    server_id = f"server{len(servers)+1}"
    password = str(random.randint(1000, 9999))

    server_class = SERVER_TYPES[server_type]
    instance = server_class(server_id, password)

    servers[server_id] = instance

    return jsonify({
        "server_id": server_id,
        "type": server_type,
        "connect": f"{request.host.split(':')[0]}:6000"
    })

@app.route("/cow_servers/delete", methods=["POST"])
def delete_server():
    if request.headers.get("admin") != ADMIN_PASSWORD:
        return "Unauthorized", 403

    sid = request.json.get("id")

    if sid in servers:
        del servers[sid]

    return "OK"
 


@app.route("/cow_servers/")
def home():
    html = "<h1>Servers</h1><ul>"

    for sid, s in servers.items():
        html += f"""
        <li>
        ID: {sid}<br>
        Type: {type(s).__name__}<br>
        Connect: {request.host.split(':')[0]}:6000<br><br>
        </li>
        """

    html += "</ul>"
    return html

SECRET = os.environ.get("WEBHOOK_SECRET_SOCKETS").encode()

@app.route('/cow_servers/update', methods=['POST'])
def update():
    signature = request.headers.get('X-Hub-Signature-256')
    if not signature:
        return "Forbidden", 403

    sha_name, received_sig = signature.split('=')

    mac = hmac.new(SECRET, msg=request.data, digestmod=hashlib.sha256)

    if not hmac.compare_digest(mac.hexdigest(), received_sig):
        return "Forbidden", 403

    subprocess.Popen(["/bin/bash", "/var/www/sockets/update_app.sh"])
    return "OK", 200


@app.route("/cow_servers/admin")
def admin():
    pw = request.args.get("pw")

    if pw != ADMIN_PASSWORD:
        return "Wrong password"

    rows = ""
    for sid, s in servers.items():
        rows += f"""
        <tr>
            <td>{sid}</td>
            <td>{type(s).__name__}</td>
            <td>{s.password}</td>
            <td>{len(getattr(s, 'clients', []))}</td>
            <td><button onclick="del('{sid}')">Delete</button></td>
        </tr>
        """

    return f"""
    <h1>Admin Panel</h1>

    <h2>Create Server</h2>
    <select id="type">
        <option value="chat">Chat</option>
        <option value="echo">Echo</option>
    </select>
    <button onclick="create()">Create</button>

    <h2>Servers</h2>
    <table border="1">
        <tr>
            <th>ID</th>
            <th>Type</th>
            <th>Password</th>
            <th>Users</th>
            <th>Action</th>
        </tr>
        {rows}
    </table>

    <script>
    async function create() {{
        let type = document.getElementById("type").value;

        await fetch("/create", {{
            method: "POST",
            headers: {{"Content-Type": "application/json"}},
            body: JSON.stringify({{type}})
        }});

        location.reload();
    }}

    async function del(id) {{
        await fetch("/delete", {{
            method: "POST",
            headers: {{
                "Content-Type": "application/json",
                "admin": "{ADMIN_PASSWORD}"
            }},
            body: JSON.stringify({{id}})
        }});

        location.reload();
    }}
    </script>
    """


threading.Thread(target=start_controller, daemon=True).start()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=6001)