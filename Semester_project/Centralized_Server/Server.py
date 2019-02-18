import threading
from threading import Thread
import socket, ssl, urllib.request, sys, os


class _ClientThread(Thread):
    hosts_list = {}
    lock = threading.Lock()

    def __init__(self, server, client_socket=None, address=None):
        if client_socket is None or address is None:
            raise UnboundLocalError('The client does not exist')
        else:
            Thread.__init__(self)
            self.server = server
            self.host_name = ""
            self.address = address
            self.sock = client_socket
            self.stream = self.sock.makefile()
            self.running = True

    def run(self):
        while self.running:
            sentence = self.stream.readline()
            self.stream.flush()
            tokens = sentence.split(" ")
            print(f""" -- USER {self.address[0]} OPERATION --""")
            print(f"[{self.address[0]}] received: {tokens}")
            print(f"[{self.address[0]}] command: {tokens[0]}")
            command = tokens[0]
            if command == 'stream' and len(tokens) == 4:
                if self.add_host(tokens[1], tokens[2]):
                    if self.sock.send(b"OK \n") == 0:
                        print(f"[{self.address[0]}] Connection broken")
                        self.disconnect()
                else:
                    if self.sock.send(b"NO \n") == 0:
                        print(f"[{self.address[0]}] Connection broken")
                        self.disconnect()
            elif command == 'close':
                self.disconnect()
            elif command == 'load':
                self.send_hosts()
            elif len(command) == 0:
                print(f"[{self.address[0]}] Received an empty string, closing connection.")
                self.disconnect()
            else:
                print(f"[{self.address[0]}] Request {tokens} Unknown")

    def add_host(self, host_name, address):
        self.host_name = host_name
        success = True
        if not len(self.host_name) > 0:
            success = False
        if success:
            with _ClientThread.lock:
                if host_name not in _ClientThread.hosts_list:
                    _ClientThread.hosts_list[host_name] = address
                    self.server.streamers += 1
                else:
                    success = False
        return success

    def send_hosts(self):
        with _ClientThread.lock:
            keys = list(_ClientThread.hosts_list)
            running = True
            while len(keys) > 0 and running:
                bytessent = 0
                key = keys.pop()
                message = bytes(key + ' ' + _ClientThread.hosts_list[key] + ' \n', 'utf-8')
                msglen = len(message)
                while bytessent < msglen:
                    sent = self.sock.send(message[bytessent:])
                    if sent == 0:
                        print(f"[{self.address[0]}] Connection broken")
                        running = False
                        break
                    bytessent += sent
            else:
                sent = self.sock.send(b'\n')
                if sent == 0:
                    self.disconnect()

    def disconnect(self):
        with _ClientThread.lock:
            if self.host_name in _ClientThread.hosts_list:
                del _ClientThread.hosts_list[self.host_name]
                self.server.streamers -= 1
        self.sock.close()
        self.server.connections -= 1
        self.running = False


class Server:
    def __init__(self, address=None, port=2841, certificate='selfsigned'):
        self.context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        crtfile = './certificates/' + certificate + '.crt'
        keyfile = './certificates/' + certificate + '.key'
        self.context.load_cert_chain(certfile=crtfile, keyfile=keyfile)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if address is None:
            # self.ext_ip = socket.gethostbyname(socket.getfqdn()) used on Linux systems
            self.ext_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')
        else:
            self.ext_ip = address
        self.port = port
        try:
            self.server_socket.bind((self.ext_ip, self.port))
        except socket.gaierror:
            self.ext_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')
            self.server_socket.bind((self.ext_ip, self.port))
        self.server_socket.listen(5)
        self.connections = 0
        self.streamers = 0
        self.connection_handler = _Loop(self, self.server_socket)
        self.connection_handler.start()
        print(f"""      -- SERVER RUNNING --
IP:     {self.ext_ip}
Port:   {self.port}""")
        self.acceptcmds()

    def acceptcmds(self):
        run = True
        while run:
            cmd = input('Waiting for command...\n')
            size = len(cmd.split(' '))
            if size is not 1:
                print('Format not valid')
            elif cmd == 'stats':
                print(f'''Users connected:                {self.connections}
Streaming users available:      {self.streamers}''')
            elif cmd == 'stop':
                self.connection_handler.running = False
                print('The server will not accept new connections.')
            elif cmd == 'test':
                self.fakeit()
            elif cmd == 'dump':
                self.dbdump()
            elif cmd == 'quit' and not self.connection_handler.running:
               os._exit(0)
            elif cmd == 'quit':
                print('The server has to be stopped before you can kill the process.')
            else:
                print('Command unknown')

    def fakeit(self):
        _ClientThread.hosts_list['test0'] = '127.0.0.1'
        _ClientThread.hosts_list['test2'] = '127.0.0.7'
        _ClientThread.hosts_list['test3'] = '127.0.0.86'
        _ClientThread.hosts_list['test4'] = '127.0.0.143'

    def dbdump(self):
        print(_ClientThread.hosts_list)


class _Loop(Thread):
    def __init__(self, server, server_socket, running=True):
        Thread.__init__(self)
        self.server = server
        self.server_socket = server_socket
        self.running = running

    def run(self):
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                ssl_socket = self.server.context.wrap_socket(client_socket, server_side=True)
            except ssl.SSLError:
                print(f'Connection with [{address[0]}] has been refused due failing of the SSL authentication')
            else:
                self.server.connections += 1
                thread = _ClientThread(self.server, ssl_socket, address)
                thread.start()
        self.server_socket.close()


def main():
    print("""Welcome to the centralized server.
To work, the server needs your current IP address.
You can either provide one, or let the server get your current IP.
To select the IP automatically, please enter an empty value.""")
    switcher = {
        0:  "selfsigned",
        1:  "selfsignedExpired",
        2:  "selfsignedWrongName"
    }
    addr = input("IP Address: ")
    opt = -1
    while opt not in switcher.keys():
        opt = int(input('''Select which certificate to load:
0:      Default certificate
1:      Expired certificate
2:      Different hostname certificate\n'''))
    name = switcher[opt]
    if len(addr) == 0:
        Server(certificate=name)
    else:
        Server(addr, certificate=name)


if __name__ == '__main__':
    main()
