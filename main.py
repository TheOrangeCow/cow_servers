import socket
import threading

from server_types.chat_server import ChatServer
from server_types.terminal_server import TerminalServer

HOST = "0.0.0.0"
PORT = 6000
PASSWORD = "1234"

SERVER_TYPES = {
    "chat": ChatServer,
    "terminal": TerminalServer
}

servers = {}
server_types = {}
clients = {}

def send_to_client(conn, message):
    try:
        conn.send((message + "\n").encode())
    except:
        pass

def broadcast(server_id, message):
    for c, info in clients.items():
        if info["server"] == server_id:
            send_to_client(c, message)

def handle_client(conn, addr):
    try:
        send_to_client(conn, "SERVER_ID:")
        server_id = conn.recv(1024).decode().strip()

        send_to_client(conn, "TYPE (chat/terminal):")
        server_type = conn.recv(1024).decode().strip()

        send_to_client(conn, "PASSWORD:")
        password = conn.recv(1024).decode().strip()

        if password != PASSWORD:
            send_to_client(conn, "WRONG PASSWORD")
            conn.close()
            return

        send_to_client(conn, "NAME:")
        name = conn.recv(1024).decode().strip()

        if server_id not in servers:
            if server_type not in SERVER_TYPES:
                send_to_client(conn, "INVALID SERVER TYPE")
                conn.close()
                return

            print(f"Creating server '{server_id}' ({server_type})")

            servers[server_id] = SERVER_TYPES[server_type](
                send_func=lambda c, msg: send_to_client(c, msg),
                broadcast_func=lambda msg: broadcast(server_id, msg)
            )

            server_types[server_id] = server_type

        server = servers[server_id]

        clients[conn] = {
            "server": server_id,
            "name": name
        }

        result = server.join(conn, name)

        if result == "WAITING_FOR_ADMIN_PASS":
            password = conn.recv(1024).decode().strip()
            if not server.admin_auth(conn, password):
                conn.close()
                return
        elif result is False:
            conn.close()
            return

        while True:
            data = conn.recv(1024)
            if not data:
                break

            msg = data.decode().strip()
            server.handle(conn, msg)

    except Exception as e:
        print("Error:", e)

    if conn in clients:
        info = clients.pop(conn)
        server_id = info["server"]

        if server_id in servers:
            servers[server_id].leave(conn)

    conn.close()

def start():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen()

    print(f"Controller running on {HOST}:{PORT}")

    while True:
        conn, addr = s.accept()
        print(f"Connected: {addr}")
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

start()
