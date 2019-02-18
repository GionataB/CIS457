from threading import Thread
import socket, sys, cv2
import numpy as np


class P2PClient(Thread):
    def __init__(self, address, maingui=None, port=2842, debug=False):
        Thread.__init__(self)
        self.debug = debug
        self.gui = maingui
        self.port = port
        self.address = address
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((address, int(port)))
        if self.debug:
            print("Connected")

    def run(self):
        running = True
        first = True
        h = 0
        w = 0
        while running:
            chunks = []
            templen = []
            bytes_recv = 0
            # Execute it only once at the very beginning
            if first:
                # Get the height of the video
                while bytes_recv < 4:
                    chunk = self.sock.recv(4)
                    if chunk == b'':
                        running = False
                        break
                    templen.append(chunk)
                    bytes_recv += len(chunk)
                h = b''.join(templen)
                h = int.from_bytes(h, sys.byteorder)

                bytes_recv = 0
                chunk = b''
                templen = []

                # Get the width of the video
                while bytes_recv < 4:
                    chunk = self.sock.recv(4)
                    if chunk == b'':
                        running = False
                        break
                    templen.append(chunk)
                    bytes_recv += len(chunk)
                w = b''.join(templen)
                w = int.from_bytes(w, sys.byteorder)

                bytes_recv = 0
                chunk = b''
                templen = []
                first = False

            # Get the total length
            while bytes_recv < 4:
                chunk = self.sock.recv(4)
                if chunk == b'':
                    running = False
                    break
                templen.append(chunk)
                bytes_recv += len(chunk)
            else:
                if self.debug:
                    print(chunk)
            if not running:
                break
            MSGLEN = b''.join(templen)
            MSGLEN = int.from_bytes(MSGLEN, sys.byteorder)
            if self.debug:
                print(f'len: {MSGLEN}')
            bytes_recv = 0
            chunk = b''
            while bytes_recv < MSGLEN:
                chunk = self.sock.recv(min(MSGLEN - bytes_recv, 2048))
                if self.debug:
                    print(f'data: {chunk}')
                if chunk == b'':
                    running = False
                    break
                chunks.append(chunk)
                bytes_recv += len(chunk)
            if not running:
                break
            message = b''.join(chunks)
            if self.debug:
                self.testprint(MSGLEN, message)
            else:
                frame = np.fromstring(message, dtype=np.uint8)
                frame = frame.reshape(h, w, 3)
                cv2.imshow("video", frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        cv2.destroyWindow("video")
        self.sock.close()
        if self.debug:
            print('Received all data')

    def testprint(self, size, message):
        print(f'''Length: {size}
{message}''')


def main():
    address = '35.40.110.232'
    debug = P2PClient(address, debug=True)
    debug.start()


if __name__ == '__main__':
    main()
