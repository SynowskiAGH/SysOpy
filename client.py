import socket
import select
import sys

# rozmiar "headera" wiadomości
msg_length = 300
usr_length = 30

# IP i PORT serwera
IP = input("IPv4 serwera: ")
PORT = 42069

# pobieramy od użytkownika username
my_ussr = input("Podaj swoja nazwe UWU: ")[:usr_length] # Przytnie string do 30 znakow
print()

# Stworzenie socketa
# socket.AF_INET - rodzina adresów, IPv4, inne przykłady: AF_INET6, AF_BLUETOOTH, AF_UNIX
# socket.SOCK_STREAM - TCP, połączeniowy; socket.SOCK_DGRAM - UDP, bezpołączeniowy, datagramy; socket.SOCK_RAW - surowe pakiety IP
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Łączymy się z podanym IP i PORTem
client.connect((IP, PORT))

# Przygotowujemy username i jego header
# Musimy zakodować username na bajty, potem policzyć te bajty i przygotować header wiadomości (o stałym rozmiarze), który też zakodujemy
username = my_ussr.ljust(usr_length).encode('utf-8')
# nadajemy header i username w postaci zakodowanej wiadomości
client.send(username)

# sockets_list = [sys.stdin, client] # lista możliwych źródeł danych - terminal i socket

while True:

    sockets_list = [sys.stdin, client] # lista możliwych źródeł danych - terminal i socket

    # analogiczne jak na serwerze wykorzystanie select(), tylko tym razem nie sprawdzamy wyjątków
    read_sockets, write_socket, error_socket = select.select(
        sockets_list, [], [])

    # iterujemy po źródłach danych
    for socks in read_sockets:
        # jeżeli otrzymaliśmy dane na socket (ktoś inny nadał wiadomość i serwer ją podał dalej)
        if socks == client:
            # pobieramy username nadawcy
            username = client.recv(usr_length).decode('utf-8').rstrip()

            # jeżeli go nie otrzymaliśmy, to znaczy, że serwer zakończył działanie
            if not len(username):
                # wypisujemy informacje o tym na konsolę (:P)
                print('Connection closed by the server')

                # kończymy program
                sys.exit()


            # pobieramy treść wiadomości
            message = client.recv(msg_length).decode('utf-8').rstrip()

            # Wypisujemy wiadomość na chacie
            print(f'\r{username} > {message}')

        # Jeżeli nie otrzymaliśmy wiadomości z zewnątrz, to musieliśmy ją napisać na terminalu
        else:
            # zczytujemy wiadomość z terminala i usuwamy znak zakończenia linii z jej końca
            message = sys.stdin.readline().rstrip()

            # # przesuwamy kursor na początek poprzedniej linii, żeby nadpisać wiadomość
            # print(f'\r(YOU) > {message}')
            
            # kodujemy wiadomość na bajty
            message = message.ljust(msg_length).encode('utf-8')
            # nadajemy do serwera naszą wiadomość z jej nagłówkiem
            client.send(message)
