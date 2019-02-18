from threading import Thread
import socket, urllib.request, sys, cv2
import numpy as np


class P2PServer(Thread):
    def __init__(self, filename, maingui=None, port=2842, address=None, numpeers=1, debug=False):
        Thread.__init__(self)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.filename = filename
        if address is None:
            self.ext_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')
        else:
            self.ext_ip = address
        self.debug = debug
        self.port = port
        if self.debug:
            self.printdebuginfo()
        self.server_socket.bind((self.ext_ip, self.port))
        self.server_socket.listen(5)
        self.connections = 0
        self.peers = []
        self.gui = maingui
        if numpeers < 1:
            numpeers = 1
        self.numpeers = numpeers
        self.connection_handler = _Loop(self, self.server_socket)
        self.connection_handler.start()

    def run(self):
        cap = cv2.VideoCapture(self.filename)
        buffer = []
        end = False
        running = True
        first = True
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = h.to_bytes(4, sys.byteorder)
        w = w.to_bytes(4, sys.byteorder)
        while running:
            ret, frame = cap.read()
            if frame is not None:
                data = frame.flatten()
                message = data.tostring()
                size = len(message)
                if self.debug:
                    print('Initial Size: ' + str(size))
                size = size.to_bytes(4, sys.byteorder)
                if self.debug:
                    print(size)
                message = size + b'' + message
                if first:
                    message = h + b'' + w + b'' + message
                    first = False
                if self.debug:
                    print('Total Size: ' + str(len(message)))
                buffer.append(message)
            else:
                end = True
            for peer in self.peers:
                if not end:
                    try:
                        peer.senddata(message)
                    except BrokenPipeError:
                        if self.debug:
                            print('The client disconnected')
                        peer.discnct()
                else:
                    peer.senddisconnect()
            else:
                try:
                    buffer.pop(0)
                except:
                    if self.debug:
                        print('Sent All data')
                    running = False

    def askdata(self):
        if self.debug:
            inpt = input('Insert the message:\n')
            length = len(inpt)
            byteslength = length.to_bytes(4, sys.byteorder)
            print(f'Length: {length}')
            text = byteslength + bytes(inpt, 'utf-8')
            return text

    def printdebuginfo(self):
        print(f'''   -- P2P Server started --
IP:     {self.ext_ip}
port:   {self.port}''')

    def stopConnection(self):
        self.server_socket.close()


class _Loop(Thread):
    def __init__(self, server, server_socket, running=True):
        Thread.__init__(self)
        self.server = server
        self.server_socket = server_socket
        self.running = running
        self.first = True

    def run(self):
        while True:
            if self.running:
                client_socket, address = self.server_socket.accept()
                self.server.connections += 1
                self.running = self.server.connections < self.server.numpeers
                peer = _P2PConnection(self.server, client_socket, address)
                self.server.peers.append(peer)
                if self.server.connections > 0 and self.first:
                    self.first = False
                    self.server.start()


class _P2PConnection:
    def __init__(self, server, sock, address):
        self.server = server
        self.sock = sock
        self.address = address

    def senddata(self, bytes):
        bytessent = 0
        msglen = len(bytes)
        while bytessent < msglen:
            sent = self.sock.send(bytes[bytessent:])
            if sent == 0:
                self.server.peers.remove(self)
            bytessent += sent

    def senddisconnect(self):
        msg = b''
        self.sock.send(msg)
        self.server.peers.remove(self)
        self.sock.close()

    def discnct(self):
        self.sock.close()
        self.server.peers.remove(self)

def main():
    debug = P2PServer(debug=True)
    debug.start()


if __name__ == '__main__':
    main()
