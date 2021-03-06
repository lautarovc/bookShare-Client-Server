"""
	Redes de Computadoras I
	Enero-Marzo 2018
	Prof. Wilmer Pereira
	Proyecto 1 
	client.py

	Autores:
		Lautaro Villalón 12-10427
		Yarima Luciani 13-10770
"""

import socket
import json
import threading
import os
import sys
import _thread
import curses
from fileTransfer import receiveFile



def main(serverName):

	# Funciones ayudantes 

	##
	# def breakInput(l, stdscr)
	# param l, stdscr
	# Capta cualquier tecla para salir de las descargas 
	def breakInput(l,stdscr):
		x = stdscr.getch()
		l.append(True)
		curses.nocbreak()
		stdscr.keypad(False)
		curses.echo()
		curses.endwin()
		return

	##
	# def downloadStatus()
	# Muestra en pantalla el estado de la descarga de cada libro 
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

	##
	# def listBooks()
	# Muestra en pantalla la lista de libros disponible para descargar 
	def listBooks():
		jsonData = clientSocket.recv(1024).decode()

		bookList = json.loads(jsonData)

		print("\nLista de libros disponibles:")
		for i in range(len(bookList)):
			print(i+1, ": ", bookList[i])

		clientSocket.send("Received".encode())

	##
	# def getBook()
	# Descarga un libro 
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

		transferThread = receiveFile(bookName, int(transferPort), host, transferStatus, transferStatusLock, dlPerServer, dlPerServerLock, isFile, isLinesFile)

		transferThread.start()

	##
	# def downloadPerServer()
	# Muestra en pantalla los libros que han sido descargados por servidor 
	def downloadsPerServer():
		for key in dlPerServer:
			print(key+ ": ", dlPerServer[key])

	transferStatus = {}
	transferStatusLock = threading.Lock()

	clientSocket = socket.socket()
	#host = socket.gethostname() #ingresa el nombre del servidor
	host = serverName
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

	while True:

		print("\nIngrese una opcion:\n1. Para ver el estado de las descargas\n2. Para ver la lista de libros.\n3. Para descargar un libro.\n4. Para ver los libros descargados por servidor.\n5. Para cambiar de servidor.\n0. Para salir.")
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

		elif (option == '5'):
			raise Exception("Opcion de cambio de servidor")

		elif (option == '0'):
			clientSocket.close()
			break


	clientSocket.close()


if __name__ == '__main__':

	serverList = ['159.90.9.17', '159.90.9.19', '159.90.9.20']

	i=0
	while (i < 3):
		try:
			main(serverList[i])
			sys.exit()
		except Exception as e:
			if str(e) == "Opcion de cambio de servidor":
				i += 1
				if i == 3:
					i = 0

			else:
				i += 1
				print("Error de conexion, intentando con Servidor ", i)


	print("Imposible conectar a todos los servidores.")