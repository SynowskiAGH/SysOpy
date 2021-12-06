import socket
import select

msg_length = 300
usr_length = 30

IP = "0.0.0.0" # Serwer słucha na wszystkich dostępnych interfejsach
PORT = 42069


# Stworzenie socketa
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # socket.AF_INET - adres IPv4, SOCK_STREAM - TCP (DGRAM - UDP)

server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Adresy sa zwalnianie ASAP

server.bind((IP, PORT)) # Bind, przekazujący OSowi, że zajmuje dane IP i port.

server.listen() # Tryb nasłuchiwania, będzie czekał na klientów


socket_list = [server] # Lista socketów dla select.select() -> select() to Unixowy systemcall do monitorowania wielu plików na raz (wielu socketów w naszym przypadku)

clients = {} # Słownik połączonych użytkowników


print(f'Nasluchuje polaczen na: {IP}:{PORT}...')




def receive_message(client_socket, is_user):

    try:
        # Zwracamy obiekt z wiadomością
        if is_user:
            msg = client_socket.recv(usr_length)
        else:
            msg = client_socket.recv(msg_length)
        if not len(msg):
            return False
        return msg

    except:
        return False #Połączenie nie zostało zamknięte poprawnie


while True:

    # Główna pętla programu
    # Wywołuje Unix'owy system call select() z trzema parametrami:
    #   - input - lista socketów do monitorowania danych przychodzących
    #   - wlist - sockety, na które możemy coś wysłać (sprawdza, czy bufory nie zawierają danych i socket jest gotowy do wysłania)
    #   - error - sockety, na których szukamy wyjątków (chcemy monitorować wszystkie, więc podajemy to samo co do rlist)
    # Zwracane listy:
    #   - reading - sockety, na które otrzymaliśmy dane (żebyśmy nie musieli każdego z osobna pytać w pętli)
    #   - writing - sockety gotowe na nadanie danych (tutaj zmienna zastępcza '_', bo nas to nie obchodzi)
    #   - errors  - sockety z błędami
    # To jest wywołanie blokujące, kod "poczeka" tutaj, aż to zadanie się skończy
    input_socket, _, error_socket = select.select(socket_list, [], socket_list)


    for curr_socket in input_socket: # Iterujemy przez sockety, które otrzymały dane


        if curr_socket == server: # Jeśli wybrany socket to nasz główny socket - otrzymaliśmy nowe połączenie, zaakceptujmy je

            # Akceptowanie nowego połączenia
            # To daje nam nowy socket - client socket, do niego podłączony jest TYLKO DANY klient, przez niego z nim się komunikujemy
            # Drugi otrzymany obiekt to zestaw IP/PORT
            client_socket, client_address = server.accept()

            user = receive_message(client_socket, True) # Otrzymujemy i zapisujemy username klienta

            if user is False: # Jeśli nie, to klient się rozłączył bez podawania swojej nazwy
                continue

            
            socket_list.append(client_socket) # Dodajemy nowy socket do listy select.select()

            clients[client_socket] = user # Zapisujemy username

            print('Zaakceptowano nowe połączenie od: {}:{}, username: {}'.format(
                *client_address, user.decode('utf-8').rstrip()))


        else: # Istniejący socket cliencki wysłał wiadomość

            
            message = receive_message(curr_socket, False) # Pobieramy otrzymaną wiadomość


            if message is False: # Jeśli nie otrzymaliśmy wiadomości to klient musiał się rozłączyć

                print('Utracono połączenie z klientem: {}'.format(
                    clients[curr_socket].decode('utf-8')))

                socket_list.remove(curr_socket) # Usuwamy dany socket z listy socketów

                del clients[curr_socket] # Usuwamy klienta z naszej listy

                continue

            user = clients[curr_socket] # Wybieramy użytkownika, któremu odpowiada socket, żebyśmy wiedzieli kto nadał wiadomość


            print(
                f'Otrzymano wiadomość od: {user.decode("utf-8").rstrip()}: {message.decode("utf-8").rstrip()}') # Informacja o otrzymaniu nowej wiadomości :)


            for client_socket in clients: # Dla każdego klienta w liście klientów:

                if client_socket != curr_socket: # Ale bez klienta, który to wysłał:

                    client_socket.send(user + message) # Wysyłamy username i wiadomość

    for curr_socket in error_socket: # Dla błędów ()

        socket_list.remove(curr_socket) # Usuwamy dany socket z listy socket.socket

        del clients[curr_socket] # Usuwamy tego klienta
