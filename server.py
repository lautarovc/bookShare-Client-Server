# HOLA! Soy el hilo del servidor.

import socket
import threading
import json
from fileTransfer import sendFile


class server(threading.Thread):
	def __init__(self, threadId, connection, address, serverPort, clientLock, portLock, transferPorts):
		threading.Thread.__init__(self)
		self.threadId = threadId
		self.connection = connection
		self.address = address
		self.serverPort = serverPort
		self.clientLock = clientLock
		self.portLock = portLock
		self.transferPorts = transferPorts

	def run(self):

		connectionSuccess = self.createSocket()
		if (not connectionSuccess):
			self.connection.close()
			return

		message = 'Hola bienvenido al hilo: '+str(self.threadId)+' Puerto: '+str(self.serverPort)

		self.connection.send(message.encode())

		while True:
			clientOption = self.connection.recv(1024).decode()
			
			if (clientOption == '1'):
				self.sendList()

			elif (clientOption == '2'):
				
				bookName = self.connection.recv(1024).decode()

				# AREA CRITICA PORT LOCK
				self.portLock.acquire()

				transferPort = self.transferPorts[-1] + 1

				self.transferPorts.append(transferPort)

				self.portLock.release()
				# FIN AREA CRITICA PORT LOCK

				self.connection.send(str(transferPort).encode())


				transferThread = sendFile(bookName, transferPort, self.address)


				transferThread.start()

			elif (clientOption == '0'):
				self.connection.close()
				break

	def createSocket(self):
		serverSocket = socket.socket()
		host = socket.gethostname()
		#host = ''

		serverSocket.bind((host, self.serverPort))

		serverSocket.listen(1)

		connection, address = serverSocket.accept()

		if (address[0] != self.address[0]):
			print("Client address thread incompatible.")
			connection.close()
			return 0

		self.connection = connection
		return 1

	def sendList(self):
		bookListData = open("bookList.json").read()

		self.connection.send(bookListData.encode())

		clientCheck = self.connection.recv(1024).decode()

		if clientCheck == "Received":
			print("Book list sent successfully.\n")
		else:
			print("Error: Book list not received by client.\n")


