# HOLA, SOY EL SERVIDOR DAEMON.

import socket
import threading
from server import *

daemonSocket = socket.socket()
host = socket.gethostname()
#host = ''

port = 2810
transferPorts = [9474]
daemonSocket.bind((host, port))

daemonSocket.listen(10)

#Inicializacion de variables
threadId = 0
threadList = []

serverPort = port

while True:

	connection, address = daemonSocket.accept()

	#Lock para area critica
	clientLock = threading.Lock()

	portLock = threading.Lock()

	#Creacion de hilo de servidor con Id y puerto
	threadId += 1
	serverPort += 1

	thread = server(threadId, connection, address, serverPort, clientLock, portLock, transferPorts)

	thread.start()

	#Envio de puerto de hilo de servidor al cliente
	connection.send(str(serverPort).encode())

	threadList.append(thread)

