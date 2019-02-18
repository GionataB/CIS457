import sys, socket, ssl, json, urllib
from threading import Thread


class Client(Thread):
    def __init__(self, username, gui, address=None, hostname='OpenStream.app', p2pport=2842, debug=False, certlocation=None):
        Thread.__init__(self)
        if not debug and gui is None:
            raise RuntimeError("Standard mode requires a GUI element to work.")
        self.context = ssl.SSLContext()
        self.context.verify_mode = ssl.CERT_REQUIRED
        self.context.check_hostname = True
        if certlocation is None:
            self.context.load_verify_locations("./certificates/selfsigned.crt")
        else:
            self.context.load_verify_locations(certlocation)
        self.gui = gui
        self.port = p2pport
        self.username = username
        self.address = address
        self.hostname = hostname
        self.debug = debug
        self.connected = False
        self.ssl_sock = None
        self.client = None
        self.table_data = {}

    def run(self):
        while True:
            cmd = input("Waiting for a command...\n")
            try:
                self.command(cmd)
            except ConnectionResetError:
                print("The connection has been interrupted from the server side.")
                self.ssl_sock.close()
                self.connected = False

    def command(self, cmd):
        tokens = cmd.split(' ')
        command = tokens[0]
        if command == 'connect' and len(tokens) == 3 and not self.connected:
            self.cnct(tokens[1], tokens[2])
        elif command == 'test':
            self.cnct('35.40.110.232', 2841)
        elif command == 'stream' and len(tokens) == 2 and self.connected:
            self.stream(tokens[1])
        elif command == 'close' and self.connected:
            self.close()
        elif command == 'load' and self.connected:
            self.load()
        elif command == 'info':
            print(f'''Username:     {self.username}
connected:    {self.connected}''')
        elif command == 'cert' and self.connected:
            print(json.dumps(self.ssl_sock.getpeercert(), indent=2))
        elif command == 'dump':
            self.testInfo()
        elif command == 'quit':
            sys.exit()
        elif not self.connected:
            if self.debug:
                print('You are not connected to a server.')
        else:
            if self.debug:
                print(f'The command {command} is not supported.')

    def cnct(self, address, port=2841):
        if not self.connected:
            client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.ssl_sock = self.context.wrap_socket(client_sock, server_hostname=self.hostname)
            self.ssl_sock.connect((address, int(port)))
            self.connected = True

    def stream(self, address=None):
        if address is None:
            address = urllib.request.urlopen('https://ident.me').read().decode('utf8')
        message = bytes('stream ' + self.username + ' ' + address + " \n", 'utf-8')
        self.ssl_sock.send(message)
        with self.ssl_sock.makefile() as stream:
            feedback = stream.readline()
            tokens = feedback.split(' ')
            if tokens[0] == 'OK' and self.debug:
                print('User added')
            elif tokens[0] == 'NO':
                if self.debug:
                    print('The username already exists')
                else:
                    raise UserWarning('The username already exists')

    def close(self):
        message = b'close \n'
        self.ssl_sock.send(message)
        self.ssl_sock.close()
        self.connected = False

    def load(self):
        self.table_data = {}
        message = b'load \n'
        self.ssl_sock.send(message)
        with self.ssl_sock.makefile() as stream:
            for line in stream:
                if self.debug:
                    print(line)
                tokens = line.split(' ')
                if len(tokens) == 1:
                    break
                self.table_data[tokens[0]] = tokens[1]
        return self.table_data

    def getTable(self):
        return self.table_data

    def testInfo(self):
        print(self.table_data)


def main():
    username = input("username: ")
    user = Client(username, None, debug=True)
    user.start()


if __name__ == '__main__':
    main()
