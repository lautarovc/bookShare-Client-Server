"""
	Redes de Computadoras I
	Enero-Marzo 2018
	Prof. Wilmer Pereira
	Proyecto 1 
	server.py

	Autores:
		Lautaro Villalón 12-10427
		Yarima Luciani 13-10770
"""

import socket
import threading
import json
from fileTransfer import sendFile


##
# class server(threading.Thread)
# Servidor 
class server(threading.Thread):
	def __init__(self, threadId, connection, address, serverPort, clientLock, portLock, transferPorts, dlPerClientLock, clientListLock):
		threading.Thread.__init__(self)
		self.threadId = threadId
		self.connection = connection
		self.address = address
		self.serverPort = serverPort
		self.clientLock = clientLock
		self.portLock = portLock
		self.transferPorts = transferPorts
		self.dlPerClientLock = dlPerClientLock
		self.clientListLock = clientListLock

	##
	# def run(self)
	# Corre el hilo del servidor 
	def run(self):
		connectionSuccess = self.createSocket()

		self.loadDownloadedBooks()
		self.loadHistory()

		#menuThread = menu(self.dlPerClient, self.clientList)
		#menuThread.start()

		if (not connectionSuccess):
			self.connection.close()
			return

		message = 'Hola bienvenido al hilo: '+str(self.threadId)+' Puerto: '+str(self.serverPort)

		self.connection.send(message.encode())

		while True:
			clientOption = self.connection.recv(1024).decode()
			
			if (clientOption == '2'):
				self.sendList()

			elif (clientOption == '3'):
				
				bookName = self.connection.recv(1024).decode()

				# AREA CRITICA PORT LOCK
				self.portLock.acquire()

				transferPort = self.transferPorts[-1] + 1

				self.transferPorts.append(transferPort)

				self.portLock.release()
				# FIN AREA CRITICA PORT LOCK

				transferThread = sendFile(bookName, transferPort, self.address, self.dlPerClient, self.dlPerClientLock)

				transferThread.start()

				self.connection.send(str(transferPort).encode())

			elif (clientOption == '0'):
				self.connection.close()
				break

	##
	# def createSocket(self)
	# Crea el socket del servidor 
	def createSocket(self):
		serverSocket = socket.socket()
		#host = socket.gethostname()
		host = ''

		serverSocket.bind((host, self.serverPort))

		serverSocket.listen(1)

		connection, address = serverSocket.accept()

		if (address[0] != self.address[0]):
			print("Client address thread incompatible.")
			connection.close()
			return 0

		self.connection = connection
		return 1

	##
	# @def sendList(self)s
	# Envía la lista de libros disponibles para descargar 
	def sendList(self):

		bookListData = open("./Data/bookList.json").read()

		self.connection.send(bookListData.encode())

		clientCheck = self.connection.recv(1024).decode()

		if clientCheck == "Received":
			print("Book list sent successfully.\n")
			self.saveHistory()
		else:
			print("Error: Book list not received by client.\n")

	##
	# @def loadDownloadedBooks(self)
	# Carga la lista de libros descargados
	def loadDownloadedBooks(self):
		downloadList = open("./Data/downloadedBooks.json", "r")

		self.dlPerClient = json.loads(downloadList.read())

		downloadList.close()

	##
	# @def loadHistory(self)
	# Carga la lista de los clientes que consultaron la lista de libros para descargar 
	def loadHistory(self):
		file = open("./Data/clientList.json", "r")

		self.clientList = json.loads(file.read())

		file.close()

	##
	# @def saveHistory(self)
	# Guarda la lista de los clientes que consultaron la lista de libros para descargar en un archivo JSON
	def saveHistory(self):

		self.clientListLock.acquire()

		if not (self.address[0] in self.clientList):
			self.clientList.append(self.address[0])
			file = open("./Data/clientList.json", "w")

			json.dump(self.clientList, file)

			file.close()


		self.clientListLock.release()

##
# class menu(threading.Thread)
# Menu del servidor 
class menu(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)

	##
	# @def run(self)
	# Enfectúa las opciones del menú del servidor para visualizar las estadísticas pedidas
	def run(self):

		while True:

			print("\nIngrese una opcion:\n1. Para ver los libros descargados\n2. Para ver los clientes que han consultado.\n3. Para ver el numero de descargas por libro por cliente.\n0. Para salir.")
			option = input()

			if (option == '1'):
				self.loadDownloadedBooks()
				self.showDownloadedBooks()

			elif (option == '2'):
				self.loadHistory()
				self.showClientList()

			elif (option == '3'):
				self.loadDownloadedBooks()
				self.showDownloadsPerClient()

			elif (option == '4'):
				continue
				#self.showCurrentDownloads()

			elif (option == '0'):
				break

	##
	# @def loadDownloadedBooks(self)
	# Carga en el menu la lista de libros descargados 
	def loadDownloadedBooks(self):
		downloadList = open("./Data/downloadedBooks.json", "r")

		self.dlPerClient = json.loads(downloadList.read())

		downloadList.close()


	##
	# @def loadHistory(self)
	# Carga en el menu la lista de clientes que han consultado la lista de libros para descargar
	def loadHistory(self):
		file = open("./Data/clientList.json", "r")

		self.clientList = json.loads(file.read())

		file.close()

	##
	# @def showDownloadedBooks(self)
	# Muestra en pantalla la lista de libros descargados 
	def showDownloadedBooks(self):
		print()
		for key in self.dlPerClient:
			print(key)

	##
	# @def showClientList(self)
	# Muestra en pantalla la lista de clientes que han consultado la lista de libros para descargar 
	def showClientList(self):
		print()
		for client in self.clientList:
			print(client)

	##
	# @def showDownloadsPerClient(self)
	# Muestra en pantalla los libros descargados por cliente 
	def showDownloadsPerClient(self):
		print()
		for book in self.dlPerClient:
			print(book+":\n")
			for client in self.dlPerClient[book]:
				print("\t"+client+": ", self.dlPerClient[book][client])

