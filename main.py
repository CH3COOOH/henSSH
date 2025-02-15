import socket
import threading
import paramiko

import cmd

HOST = "0.0.0.0"
PORT = 2222
PASSWORD_AUTH = {"user": "password"}
# AUTHORIZED_KEYS = ["ssh-rsa AAAAB3... user@host"]
HOST_KEY = paramiko.RSAKey(filename="server.pem")

class Server(paramiko.ServerInterface):
	def __init__(self):
		self.event = threading.Event()

	# def get_banner(self):
	# 	return ('=== Here is henSSH ===\n', 'en-US')

	def get_allowed_auths(self, username):
		return 'publickey,password'

	def check_auth_password(self, username, password):
		print('Get AUTH from a client.')
		if PASSWORD_AUTH.get(username) == password:
			return paramiko.AUTH_SUCCESSFUL
		return paramiko.AUTH_FAILED

	def check_auth_publickey(self, username, key):
		print('Get a KEY from a client.')
		return paramiko.AUTH_SUCCESSFUL
		# return paramiko.AUTH_FAILED
	
	def check_auth_gssapi_with_mic(username, gss_authenticated=2, cc_file=None):
		return paramiko.AUTH_SUCCESSFUL

	def check_auth_interactive(self, username, submethods):
		return paramiko.AUTH_SUCCESSFUL

	def check_channel_request(self, kind, chanid):
		return paramiko.OPEN_SUCCEEDED
		# if kind == "session":
		# 	return paramiko.OPEN_SUCCEEDED
		# return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

	def check_channel_shell_request(self, channel):
		self.event.set()
		return True

	def check_channel_exec_request(self, channel, command):
		## Usable for Ansible
		print(command)
		try:
			response = cmd.get_and_run(command.decode("utf-8").strip())
			channel.send(response)
			channel.send_exit_status(0)
		except Exception as err:
			print('exception: {}'.format(err))
			channel.send('An error occurred: {}\r\n'.format(err))
			channel.send_exit_status(255)
		finally:
			self.event.set()
		# channel.close()
		return True

	def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
		print(f"{term}, {modes}")
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
		server.event.wait(1000)
		if not server.event.is_set():
			return
		channel.send("Welcome to SSH Server\n$ ")
		# while True:
		# 	## Define your commands here
		# 	command = channel.recv(1024).decode("utf-8").strip()
		# 	print(command)
		# 	response = cmd.get_and_run(command)
		# 	if response == -1:
		# 		channel.send("Goodbye!\n")
		# 		break
		# 	channel.send(response + '$ ')
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
