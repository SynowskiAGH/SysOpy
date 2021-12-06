import socket
import select
import sys


msg_length = 300
usr_length = 30

IP = input("IPv4 serwera: ")
PORT = 42069


my_ussr = input("Podaj swoja nazwe UWU: ")[:usr_length] # Pobieram username, string zostanie skrócony do 30 znaków
print()

# Stworzenie socketa klienta
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # socket.AF_INET - adres IPv4, SOCK_STREAM - TCP (DGRAM - UDP)


client.connect((IP, PORT)) # Łączymy się z danym ip i portem



username = my_ussr.ljust(usr_length).encode('utf-8') # Musimy zakodować username na bajty, potem policzyć te bajty

client.send(username) # Nadajemy username



while True:

    sockets_list = [sys.stdin, client] # lista możliwych źródeł danych - terminal i socket

    read_sockets, write_socket, error_socket = select.select( # analogiczne jak na serwerze
        sockets_list, [], [])


    for socks in read_sockets:   # iterujemy po źródłach danych
        # jeżeli otrzymaliśmy dane na socket:
        if socks == client:
            # pobieramy username nadawcy:
            username = client.recv(usr_length).decode('utf-8').rstrip()

            # jeżeli go nie otrzymaliśmy, to znaczy, że serwer zakończył działanie (będzie otrzymywał w kółko dane)
            if not len(username):
                print('Połączenie zamknięte przez serwer')

                sys.exit()


            message = client.recv(msg_length).decode('utf-8').rstrip() # Pobieranie treści wiadomości

            print(f'\r{username} > {message}')

        else: # Własna wiadomość, którą napisaliśmy
            
            message = sys.stdin.readline().rstrip() # Zczytujemy wiadomość z terminala i usuwamy znak zakończenia linii z jej końca

            message = message.ljust(msg_length).encode('utf-8') # Kodujemy wiadomość na bajty

            client.send(message) # Nadajemy do serwera naszą wiadomość
