#Hola, soy un cliente aburrido.

import socket
import json
from fileTransfer import receiveFile

def listBooks():
	jsonData = clientSocket.recv(1024).decode()

	bookList = json.loads(jsonData)

	print("\nLista de libros disponibles:")
	for i in range(len(bookList)):
		print(i+1, ": ", bookList[i])

	clientSocket.send("Received".encode())



clientSocket = socket.socket()
host = socket.gethostname() #ingresa el nombre del servidor
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

print(clientSocket.recv(1024).decode())

while True:

	print("\nIngrese una opcion:\n1. Para pedir lista de libros.\n2. Para descargar un libro.\n0. Para salir.")
	option = input()

	clientSocket.send(option.encode())

	if (option == '1'):
		listBooks()

	elif (option == '2'):
		
		print("\nIngrese nombre del libro: ")
		bookName = input()
		clientSocket.send(bookName.encode())

		transferPort = clientSocket.recv(1024).decode()
		print("Puerto de transferencia: "+transferPort+"\n")

		transferThread = receiveFile(bookName, int(transferPort), host)

		transferThread.start()

	elif (option == '0'):
		clientSocket.close()
		break

