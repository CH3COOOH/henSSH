import socket
import threading
import paramiko

HOST = "0.0.0.0"
PORT = 2222
PASSWORD_AUTH = {"user": "password"}
AUTHORIZED_KEYS = ["ssh-rsa AAAAB3... user@host"]
HOST_KEY = paramiko.RSAKey(filename="server.pem")

class Server(paramiko.ServerInterface):
	def __init__(self):
		self.event = threading.Event()

	def get_allowed_auths(self, username):
		return 'publickey'

	def check_auth_password(self, username, password):
		if PASSWORD_AUTH.get(username) == password:
			return paramiko.AUTH_SUCCESSFUL
		return paramiko.AUTH_FAILED

	def check_auth_publickey(self, username, key):
		return paramiko.AUTH_SUCCESSFUL
		# return paramiko.AUTH_FAILED

	def check_channel_request(self, kind, chanid):
		if kind == "session":
			return paramiko.OPEN_SUCCEEDED
		return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

	def check_channel_shell_request(self, channel):
		self.event.set()
		return True


def handle_connection(client):
	transport = paramiko.Transport(client)
	# transport.add_server_key(paramiko.RSAKey.generate(2048))
	transport.add_server_key(HOST_KEY)
	server = Server()
	try:
		transport.start_server(server=server)
		channel = transport.accept(20)
		if channel is None:
			return
		server.event.wait(10)
		if not server.event.is_set():
			return
		channel.send("Welcome to SSH Server\n$ ")
		while True:
			## Define your commands here
			command = channel.recv(1024).decode("utf-8").strip()
			if command.lower() in ["exit", "quit"]:
				channel.send("Goodbye!\n")
				break
			elif command == "hello":
				response = "Hello, User!\n"
			else:
				response = "Command not found\n"
			channel.send(response + "$ ")
	finally:
		transport.close()
		client.close()


def start_server():
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.bind((HOST, PORT))
	sock.listen(5)
	print(f"[*] SSH Server started on {HOST}:{PORT}")
	while True:
		client, addr = sock.accept()
		threading.Thread(target=handle_connection, args=(client,)).start()


if __name__ == "__main__":
	start_server()
