#Hola, soy un cliente aburrido.

import socket
import json
import threading
import os
import sys
import _thread
import curses
from fileTransfer import receiveFile

def breakInput(l,stdscr):
	x = stdscr.getch()
	l.append(True)
	curses.nocbreak()
	stdscr.keypad(False)
	curses.echo()
	curses.endwin()
	return


def downloadStatus():
	bookList = []
	inputList = []

	for book in transferStatus:
		if (transferStatus[book]!=""):
			bookList.append(book)

	if (len(bookList) == 0):
		print("\nNo hay descargas en curso.\n")
		return

	stdscr = curses.initscr()
	_thread.start_new_thread(breakInput, (inputList,stdscr))

	while True:

		output = "\r"

		for bookName in bookList:

			output += bookName+": "+transferStatus[bookName]+"\t"

		sys.stdout.write(output)
		sys.stdout.flush()

		if (len(inputList) != 0):
			break

def listBooks():
	jsonData = clientSocket.recv(1024).decode()

	bookList = json.loads(jsonData)

	print("\nLista de libros disponibles:")
	for i in range(len(bookList)):
		print(i+1, ": ", bookList[i])

	clientSocket.send("Received".encode())

def getBook():
		
	print("\nIngrese nombre del libro: ")
	bookName = input()
	clientSocket.send(bookName.encode())

	transferPort = clientSocket.recv(1024).decode()
	print("Puerto de transferencia: "+transferPort+"\n")

	isFile = os.path.isfile(bookName)
	isLinesFile = os.path.isfile(bookName+".downloaded")

	if isLinesFile:
		linesFileSize = os.path.getsize(bookName+".downloaded")

		if (linesFileSize == 0):
			os.remove(bookName+".downloaded")
			os.remove(bookName)
			isLinesFile = False
			isFile = False

	if isFile and not isLinesFile:
		opt = input("El libro ya está descargado. ¿Desea reemplazarlo? (y/n)\n")
		if opt == 'n':
			return

	transferThread = receiveFile(bookName, int(transferPort), host, transferStatus, transferStatusLock, dlPerServer, dlPerServerLock, isFile, isLinesFile, isFileInServer, isFileInServerLock)

	transferThread.start()

	#Chequeo de archivo en servidor
	while True:
		if (len(isFileInServer) != 0):
			if isFileInServer[0] == True:
				isFileInServer = []
				return

			elif isFileInServer[0] == False:
				isFileInServer = []
				raise Exception("File not in server.")
				return

def downloadsPerServer():
	for key in dlPerServer:
		print(key+ ": ", dlPerServer[key])

def main(hostname):
	transferStatus = {}
	transferStatusLock = threading.Lock()

	clientSocket = socket.socket()
	#host = socket.gethostname() 
	
	host = hostname #ingresa el nombre del servidor
	port = 2810

	#Conectamos al demonio
	clientSocket.connect((host, port))

	#Obtenemos el puerto del hilo del servidor
	serverPort = int(clientSocket.recv(1024).decode())

	#Desconectamos del demonio
	clientSocket.close()

	#Conectamos al hilo del servidor
	clientSocket = socket.socket()

	clientSocket.connect((host, serverPort))

	#Cargamos la lista de libros descargados
	downloadList = open("downloadedBooks.json").read()

	dlPerServer = json.loads(downloadList)

	dlPerServerLock = threading.Lock()

	#Mostramos mensaje de servidor
	print(clientSocket.recv(1024).decode())

	#Inicializamos lista de revision de transferencia.
	isFileInServer = []
	isFileInServerLock = threading.Lock()

	while True:

		print("\nIngrese una opcion:\n1. Para ver el estado de las descargas\n2. Para ver la lista de libros.\n3. Para descargar un libro.\n4. Para ver los libros descargados por servidor.\n0. Para salir.")
		option = input()

		clientSocket.send(option.encode())

		if (option == '1'):
			downloadStatus()

		elif (option == '2'):
			listBooks()

		elif (option == '3'):
			getBook()

		elif (option == '4'):
			downloadsPerServer()

		elif (option == '0'):
			clientSocket.close()
			break


	clientSocket.close()


if __name__ == "__main__":
	serverList = ["159.90.9.15", "159.90.9.16", "159.90.9.17"]

	i = 0
	while (i < 3):

		try:
			main(serverList[i])
			sys.exit()

		except:
			print("\nConectando con otro Servidor...\n")

			i = i+1
			if (i == 3):
				i = 0
