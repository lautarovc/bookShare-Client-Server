import socket
import threading
import json
import sys
import os
from time import sleep

class sendFile(threading.Thread):
	def __init__(self, fileName, transferPort, address, dlPerClient, dlPerClientLock):
		threading.Thread.__init__(self)
		self.fileName = fileName
		self.transferPort = transferPort
		self.address = address
		self.dlPerClient = dlPerClient
		self.dlPerClientLock = dlPerClientLock

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

	def createSocket(self):
		serverSocket = socket.socket()
		host = socket.gethostname()
		#host = ''

		serverSocket.bind((host, self.transferPort))

		serverSocket.listen(1)

		connection, address = serverSocket.accept()

		if (address[0] != self.address[0]):
			print("Client address thread incompatible.")
			connection.close()
			return 0

		self.connection = connection
		return 1

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


class receiveFile(threading.Thread):
	def __init__(self, fileName, transferPort, host, transferStatus, transferStatusLock, dlPerServer, dlPerServerLock, isFile, isLinesFile, isFileInServer, isFileInServerLock):
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
		self.isFileInServer = isFileInServer
		self.isFileInServerLock = isFileInServerLock

	def run(self):

		self.createSocket()

		fileExists = int(self.clientSocket.recv(512).decode())

		if not fileExists:
			print("\nEl archivo no se encuentra en el servidor, probando con el siguiente...\n")
			self.clientSocket.close()

			# ENVIA MENSAJE A PAPA
			self.isFileInServerLock.acquire()
			self.isFileInServer.append(False)
			self.isFileInServerLock.release()
			return



		self.receive()

		self.saveHistory()

		self.clientSocket.close()

	def createSocket(self):
		self.clientSocket = socket.socket()
		#host = socket.gethostname()
		#host = ''

		self.clientSocket.connect((self.host, self.transferPort))

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

		#self.transferStatusLock.acquire()		

		#self.transferStatus[self.fileName] = ""

		#self.transferStatusLock.release()

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


		#ENVIO MENSAJE A PAPA, SI ESTA ARCHIVO
		self.isFileInServerLock.acquire()
		self.isFileInServer.append(True)
		self.isFileInServerLock.release()


		#Envio begin
		self.clientSocket.send(str(begin).encode())

		self.writeFile(file, linesFile, begin)

		linesFile.close()
		os.remove(self.fileName+".downloaded")

		file.close()

	def saveHistory(self):
		if (self.fileName in self.dlPerServer[self.host]):
			return

		self.dlPerServerLock.acquire()

		file = open("downloadedBooks.json", "w")

		self.dlPerServer[self.host].append(self.fileName)

		json.dump(self.dlPerServer, file)

		file.close()

		self.dlPerServerLock.release()