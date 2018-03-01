"""
	Redes de Computadoras I
	Enero-Marzo 2018
	Prof. Wilmer Pereira
	Proyecto 1 
	fileTransfer.py

	Autores:
		Lautaro Villalón 12-10427
		Yarima Luciani 13-10770
"""

import socket
import threading
import json
import sys
import os
from time import sleep

##
# @class sendFile(self)
# Hilo para enviar libros 
class sendFile(threading.Thread):
	def __init__(self, fileName, transferPort, address, dlPerClient, dlPerClientLock):
		threading.Thread.__init__(self)
		self.fileName = fileName
		self.transferPort = transferPort
		self.address = address
		self.dlPerClient = dlPerClient
		self.dlPerClientLock = dlPerClientLock

	##
	# @def run(self)
	# Corre el hilo para enviar libros 
	def run(self):
		connectionSuccess = self.createSocket()

		if(not connectionSuccess):
			print("Connection Unsuccessful on port: ", self.transferPort)
			self.connection.close()
			return

		try:
			file = open("./Books/"+self.fileName, 'rb')
		except:
			self.connection.send('0'.encode())
			self.connection.close()
			return

		self.connection.send('1'.encode())

		fileLines = file.readlines()

		self.connection.send(str(len(fileLines)).encode())

		begin = int(self.connection.recv(512).decode())
		
		for i in range(begin, len(fileLines)):
			self.connection.send(fileLines[i])
			arrived = self.connection.recv(1024).decode()
			if (arrived != ("Received "+str(i))):
				print("File Transfer Error in line %d", i)
				self.connection.close()
				return

		file.close()

		self.saveHistory()

		self.connection.close()

	##
	# @def createSocket(self)
	# Crea el socket para enviar libros
	def createSocket(self):
		serverSocket = socket.socket()
		#host = socket.gethostname()
		host = ''

		serverSocket.bind((host, self.transferPort))

		serverSocket.listen(1)

		connection, address = serverSocket.accept()

		if (address[0] != self.address[0]):
			print("Client address thread incompatible.")
			connection.close()
			return 0

		self.connection = connection
		return 1

	##
	# @def saveHistory(self)
	# Guarda los libros descargados en un archivo JSON 
	def saveHistory(self):
		self.dlPerClientLock.acquire()

		if (not self.fileName in self.dlPerClient):
			self.dlPerClient[self.fileName] = {self.address[0]:0}

		elif (not self.address[0] in self.dlPerClient[self.fileName]): 
			self.dlPerClient[self.fileName][self.address[0]] = 0


		self.dlPerClient[self.fileName][self.address[0]] += 1

		file = open("./Data/downloadedBooks.json", "w")

		json.dump(self.dlPerClient, file)

		file.close()

		self.dlPerClientLock.release()


##
# @class receive(self)
# Hilo para recibir libros 
class receiveFile(threading.Thread):
	def __init__(self, fileName, transferPort, host, transferStatus, transferStatusLock, dlPerServer, dlPerServerLock, isFile, isLinesFile):
		threading.Thread.__init__(self)
		self.fileName = fileName
		self.transferPort = transferPort
		self.host = host
		self.transferStatus = transferStatus
		self.transferStatusLock = transferStatusLock
		self.dlPerServer = dlPerServer
		self.dlPerServerLock = dlPerServerLock
		self.isFile = isFile
		self.isLinesFile = isLinesFile

	##
	# @def run(self)
	# Corre el hilo para recibir libros 
	def run(self):
		self.createSocket()

		fileExists = int(self.clientSocket.recv(512).decode())

		if not fileExists:
			print("Archivo no conseguido en este servidor, por favor cambie de servidor.")
			self.clientSocket.close()
			return

		self.receive()

		self.saveHistory()

		self.clientSocket.close()

	##
	# @def createSocket(self)
	# Crea el socket para recibir libros
	def createSocket(self):
		self.clientSocket = socket.socket()
		#host = socket.gethostname()
		#host = ''

		self.clientSocket.connect((self.host, self.transferPort))

	##
	# @def writeFile(self)
	# Escribe el libro que está siendo descargado, línea por línea
	def writeFile(self, file, linesFile, begin):
		for i in range(begin, self.fileSize):
			file.write(self.clientSocket.recv(4096))
			linesFile.write((str(i)+"\n").encode())

			percentage = ((i+1)*100)//self.fileSize
			#movement = int(percentage//2.5)

			self.transferStatusLock.acquire()

			#self.transferStatus[self.fileName] = "[" + "=" * movement +  " " * (40-movement) + "]" +  str(percentage) + "%"
			self.transferStatus[self.fileName] = str(percentage) + "%"

			self.transferStatusLock.release()

			sleep(0.025)

			self.clientSocket.send(("Received "+str(i)).encode())

	##
	# @def createSocket(self)
	# Recibe el libro
	def receive(self):
		self.fileSize = int(self.clientSocket.recv(1024).decode())

		if not self.isFile and not self.isLinesFile:

			file = open(self.fileName, 'wb')
			linesFile = open(self.fileName+".downloaded", "wb")
			begin = 0

		elif self.isFile and self.isLinesFile:

			file = open(self.fileName, 'ab')
			linesFile = open(self.fileName+".downloaded", "r")

			linesFileLast = int(linesFile.readlines()[-2].rstrip())

			linesFile.close()

			linesFile = open(self.fileName+".downloaded", "ab")

			begin = linesFileLast + 1

		elif self.isFile and not self.isLinesFile:

			os.remove(self.fileName)
			file = open(self.fileName, 'wb')
			linesFile = open(self.fileName+".downloaded", "wb")
			begin = 0

		#Envio begin
		self.clientSocket.send(str(begin).encode())

		self.writeFile(file, linesFile, begin)

		linesFile.close()
		os.remove(self.fileName+".downloaded")

		file.close()
	
	##
	# @def saveHistory(self)
	# Guarda los libros descargados en un archivo JSON 
	def saveHistory(self):
		if (self.fileName in self.dlPerServer[self.host]):
			return

		self.dlPerServerLock.acquire()

		file = open("downloadedBooks.json", "w")

		self.dlPerServer[self.host].append(self.fileName)

		json.dump(self.dlPerServer, file)

		file.close()

		self.dlPerServerLock.release()