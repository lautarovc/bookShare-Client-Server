import socket
import threading
import json
import sys
import os
from time import sleep

class sendFile(threading.Thread):
	def __init__(self, fileName, transferPort, address):
		threading.Thread.__init__(self)
		self.fileName = fileName
		self.transferPort = transferPort
		self.address = address

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



class receiveFile(threading.Thread):
	def __init__(self, fileName, transferPort, host):
		threading.Thread.__init__(self)
		self.fileName = fileName
		self.transferPort = transferPort
		self.host = host

	def run(self):

		self.createSocket()

		fileExists = int(self.clientSocket.recv(512).decode())

		if not fileExists:
			print("File unavailable in server.")
			self.clientSocket.close()
			return

		self.receive()

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
			movement = int(percentage//2.5)

			sys.stdout.write("\r[" + "=" * movement +  " " * (40-movement) + "]" +  str(percentage) + "%")
			sys.stdout.flush()

			sleep(0.025)

			self.clientSocket.send(("Received "+str(i)).encode())

	def receive(self):
		self.fileSize = int(self.clientSocket.recv(1024).decode())

		isFile = os.path.isfile(self.fileName)
		isLinesFile = os.path.isfile(self.fileName+".downloaded")

		if not isFile and not isLinesFile:

			file = open(self.fileName, 'wb')
			linesFile = open(self.fileName+".downloaded", "wb")
			begin = 0

		elif isFile and isLinesFile:

			file = open(self.fileName, 'ab')
			linesFile = open(self.fileName+".downloaded", "r")

			linesFileLast = int(linesFile.readlines()[-2].rstrip())

			linesFile.close()

			linesFile = open(self.fileName+".downloaded", "ab")

			begin = linesFileLast + 1

		elif isFile and not isLinesFile:

			print("El libro ya está descargado. ¿Desea reemplazarlo? (y/n)\n")
			opt = input()

			if opt[0] == "y":
				file = open(self.fileName, 'wb')
				linesFile = open(self.fileName+".downloaded", "wb")
				begin = 0

			else:
				self.clientSocket.close()
				return

		#Envio begin
		self.clientSocket.send(str(begin).encode())

		self.writeFile(file, linesFile, begin)

		linesFile.close()
		os.remove(self.fileName+".downloaded")

		file.close()