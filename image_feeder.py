import socket
import numpy as np
import time


class SocketCommunicator:
    def __init__(self, **kwargs):
        self.debug_mode = kwargs.get('debug_mode', True)
        self.ip_address = kwargs.get('ip_address', 'localhost')
        self.port = kwargs.get('port', 6006)
        self.server = kwargs.get('server', True)
        if not self.server:
            self.server_ip = kwargs.get('server_ip', 'localhost')
            self.server_port = kwargs.get('server_port', 6006)
        self.socket = None
        self.connection = None

    def build_server_connection(self):
        while True:
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                address = (self.ip_address, self.port)
                self.socket.bind(address)
                self.socket.listen(5)
            except OSError as e:
                if e.args[0] == 98:
                    print("Port number {} is not available.".format(self.port))
                    self.port -= 1
                    print("Retrying with port number {}.".format(self.port))
                else:
                    self.connection = None
                    break
            else:
                break
        conn, addr = self.socket.accept()
        if self.debug_mode:
            print('[+] Connected with ', addr)
        self.connection = conn
        return conn

    def build_client_connection(self):
        while True:
            try:
                self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                address = (self.ip_address, self.port)
                self.connection.bind(address)
                self.connection.connect((self.server_ip, self.server_port))
            except OSError as e:
                if e.args[0] == 10048:
                    print("Port number {} is not available.".format(self.port))
                    self.port += 1
                    print("Reconnecting with port number {}.".format(self.port))
                else:
                    self.connection = None
                    break
            else:
                break
        return self.connection

    def build_connection(self, server=False):
        if server:
            return self.build_server_connection()
        else:
            return self.build_client_connection()

    def close_connection(self):
        self.connection.close()
        if self.server:
            self.socket.close()

    def receive_string(self, len_string):
        data = self.connection.recv(len_string)
        data = data.decode("UTF-8")
        return data

    def receive_integer(self, len_integer):
        data = self.connection.recv(len_integer)
        data = data.decode("UTF-8")
        data = int(data)
        return data

    def receive_array(self, len_array):
        len_received_data = 0
        received_data = []
        while len_received_data < len_array:
            left_bits = len_array - len_received_data
            data = self.connection.recv(left_bits)
            received_data.extend(data)
            len_received_data = len_received_data + data.__len__()
            if self.debug_mode:
                print("Received data length = {}\n".format(len_received_data))
            if not data:
                break
        return received_data

    def send_string(self, line, length=5):
        self.connection.send(line.zfill(length).encode("UTF-8"))

    def send_integer(self, number, length=5):
        self.connection.send(str(number).zfill(length).encode("UTF-8"))

    def send_array(self, array, length=5):
        if type(array) is not np.ndarray:
            array = np.array(array)
        self.connection.send(array)



import os
import cv2


class ImageFeeder(SocketCommunicator):
    def __init__(self, **kwargs):
        kwargs['server'] = False
        SocketCommunicator.__init__(self, **kwargs)
        self.image_directory = kwargs.get("directory", "data/image/")
        self.image_paths = None
        self.sent_images = dict({})
        self.results = dict({})
        self.received_results = []
        self.ready = False

    def build_connection(self):
        SocketCommunicator.build_connection(self, server=False)

    def get_ready(self):
        self.send_string("ready")
        rd = self.receive_string(5)
        if rd == 'ready':
            self.ready = True
        else:
            self.ready = False

    def scrape_image_file_paths(self):
        image_files = os.listdir(self.image_directory)
        image_file_names = [x for x in image_files if x.endswith(".png")]
        self.image_paths = [os.path.join(self.image_directory, file) for file in image_file_names]
        return self.image_paths

    def send_single_image(self, image_path):
        image = cv2.imread(image_path, 0)  # gray scale image
        image = cv2.resize(image, (50, 50), interpolation=cv2.INTER_AREA)
        if self.debug_mode: print(image[:3])
        self.send_array(image, len(image))
        return image

    def send_images(self):
        if self.connection is None:
            print("Connection not established.")
            return
        self.scrape_image_file_paths()
        self.get_ready()
        if self.ready:
            self.send_integer(len(self.image_paths))
            while len(self.image_paths) > 0:
                image_path = self.image_paths.pop(0)
                image = self.send_single_image(image_path)
                self.sent_images[image_path] = image
        else:
            print("Communication should start with 'ready'.")

    def receive_results(self):
        for key in self.sent_images.keys():
            self.results[key] = self.receive_integer(1)
            message = 'Closed' if self.results[key] == 0 else 'Open'
            image = self.sent_images[key]
            image = cv2.resize(image, (200, 200))
            image = cv2.putText(image, message, (12, 12), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 0, 255), 4)
            self.sent_images[key] = image

        for ik, key in enumerate(self.sent_images.keys()):
            # cv2.imshow(str(ik), self.sent_images[key])
            cv2.imwrite('test.png', self.sent_images[key])
            time.sleep(1)
            print(self.results[key])
        return self.sent_images


if __name__ == "__main__":
    image_feeder = ImageFeeder(port=6007,
                               ip_address='192.168.8.124',
                               server_ip='192.168.8.125',
                               server_port=6006,
                               debug_mode=True,
                               directory="./data/")
    image_feeder.build_connection()
    image_feeder.send_images()
    image_feeder.receive_results()
    image_feeder.close_connection()
