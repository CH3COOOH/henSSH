def get_and_run(cmd):
	response = ''
	if cmd.lower() in ["exit", "quit"]:
		return -1
	elif cmd.strip() == '':
		return ''
	elif cmd == "hello":
		response = "Hello, User!\n"
	else:
		response = "Command not found\n"
	return response