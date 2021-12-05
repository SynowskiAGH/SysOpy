import socket
import select

# rozmiar "headera" wiadomości
msg_length = 300
usr_length = 30

# IP i PORT na którym stawiamy serwer
IP = "0.0.0.0"
PORT = 42069

# Stworzenie socketa
# socket.AF_INET - rodzina adresów, IPv4, inne przykłady: AF_INET6, AF_BLUETOOTH, AF_UNIX
# socket.SOCK_STREAM - TCP, połączeniowy; socket.SOCK_DGRAM - UDP, bezpołączeniowy, datagramy; socket.SOCK_RAW - surowe pakiety IP
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Adresy sa zwalnianie ASAP


# Bind, żeby serwer powiedział systemowi operacyjnemu, że zajmuje dany adres IP i PORT
# Serwer używający adresu 0.0.0.0 słucha na wszystkich dostępnych interfejsach, przydatne do łączenia się lokalnie i z LAN
server.bind((IP, PORT))

# Przełącza socket w tryb nasłuchiwania, bedzie przyjmowal polaczenia od klientow
server.listen()

# Lista socketów dla select.select()
# select() to Unixowy systemcall do monitorowania wielu plików na raz (wielu socketów w naszym przypadku)
socket_list = [server]

# Słownik połączonych klientów - socket jako klucz, nagłówek i nazwa użytkownika jako dane
clients = {}

print(f'Nasluchuje polaczen na: {IP}:{PORT}...')

# Handler odbierania wiadomości


def receive_message(client_socket, is_user):

    try:
        # Zwracamy obiekt z nagłówkiem i wiadomością (następne "header" danych z socketa)
        if is_user:
            msg = client_socket.recv(usr_length)
        else:
            msg = client_socket.recv(msg_length)
        if not len(msg):
            return False
        return msg

    except:

        # Jeśli tu jesteśmy, to połączenie nie zostało zamknięte poprawnie (np. klient nacisnął ctrl+c)
        # albo zwyczajnie stracił połączenie
        # socket.close() wywołuje również socket.shutdown(socket.SHUT_RDWR) co wysyła informacje o zamknięciu obu połówek połączenia
        # stąd może się pojawić ta pusta wiadomość, której wcześniej szukamy
        return False


while True:

    # Główna pętla programu
    # Wywołuje Unix'owy system call select() albo Windows'owy WinSock call select() z trzema parametrami:
    #   - rlist - lista socketów do monitorowania danych przychodzących
    #   - wlist - sockety, na które możemy coś wysłać (sprawdza, czy bufory nie zawierają danych i socket jest gotowy do wysłania)
    #   - xlist - sockety, na których szukamy wyjątków (chcemy monitorować wszystkie, więc podajemy to samo co do rlist)
    # Zwracane listy:
    #   - reading - sockety, na które otrzymaliśmy dane (żebyśmy nie musieli każdego z osobna pytać w pętli)
    #   - writing - sockety gotowe na nadanie danych (tutaj zmienna zastępcza '_', bo nas to nie obchodzi)
    #   - errors  - sockety z błędami
    # To jest wywołanie blokujące, kod "poczeka" tutaj, aż to zadanie się skończy
    read_sockets, _, exception_sockets = select.select(
        socket_list, [], socket_list)

    # Iterujemy przez sockety, które otrzymały dane
    for notified_socket in read_sockets:

        # Jeśli wybrany socket to nasz główny socket - otrzymaliśmy nowe połączenie, zaakceptujmy je
        if notified_socket == server:

            # Akceptowanie nowego połączenia
            # To daje nam nowy socket - client socket, do niego podłączony jest TYLKO DANY klient, przez niego z nim się komunikujemy
            # Drugi otrzymany obiekt to zestaw IP/PORT
            client_socket, client_address = server.accept()

            # Klient powinien natychmiast nadać swój username, otrzymajmy go i zapiszmy
            user = receive_message(client_socket, True)

            # Jeśli go nie otrzymaliśmy to znaczy, że klient się rozłączył zanim nadał swój username
            if user is False:
                continue

            # Dodajemy nowy socket do listy select.select()
            socket_list.append(client_socket)

            # Zapisujemy username i "header"
            clients[client_socket] = user

            # Wyświetlamy informacje o nowym połączeniu w konsoli
            print('Accepted new connection from {}:{}, username: {}'.format(
                *client_address, user.decode('utf-8').rstrip()))

        # Jeśli istniejący socket kliencki wysłał wiadomość
        else:

            # Pobieramy otrzymaną wiadomość
            message = receive_message(notified_socket, False)

            # Jeśli nie otrzymaliśmy wiadomości, klient się rozłączył, posprzątajmy
            if message is False:
                # Wyświetlamy informacje o utraconym połączeniu w konsoli
                print('Closed connection from: {}'.format(
                    clients[notified_socket].decode('utf-8')))

                # Usuwamy socket z listy socket.socket()
                socket_list.remove(notified_socket)

                # Usuwamy klienta z naszej listy
                del clients[notified_socket]

                continue

            # Wybieramy użytkownika, któremu odpowiada socket, żebyśmy wiedzieli kto nadał wiadomość
            user = clients[notified_socket]

            # Wyświetlamy informacje o otrzymaniu nowej wiadomości
            print(
                f'Received message from {user.decode("utf-8").rstrip()}: {message.decode("utf-8").rstrip()}')

            # Iterujemy po wszystkich połączeniach klienckich i nadajemy na nie otrzymaną wiadomość
            for client_socket in clients:

                # Ale nie wysyłamy jej do nadawcy
                if client_socket != notified_socket:

                    # Wysyłamy username i wiadomość (oba z ich odpowiednimi headerami)
                    # Używamy ponownie headera wiadomości od nawdawcy i zapisany header username'a (z momentu podłączenia klienta)
                    client_socket.send(user + message)

    # Nie jest to potrzebne, ale jakby coś poszło nie tak to rozwiążmy wyjątki
    for notified_socket in exception_sockets:

        # Usuwamy powiadomiony socket z listy socket.socket()
        socket_list.remove(notified_socket)

        # Usuwamy odpowiadającego mu klienta
        del clients[notified_socket]
