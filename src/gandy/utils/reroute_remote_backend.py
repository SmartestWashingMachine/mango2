import os
import json
import io
import base64
from PIL import Image
import requests
from dataclasses import dataclass
import threading
import queue
from time import sleep
from typing import Any
from gandy.utils.try_print import try_print

@dataclass
class ProcessItem():
    addr: str
    data: Any
    files: Any

# Thread-safe.
message_queue = queue.Queue()

class RemoteRouterProcess(threading.Thread):
    def __init__(self):
        super().__init__()
        self.session = requests.Session()

    def make_call(self, item: ProcessItem):
        while True:
            try:
                response = self.session.post(item.addr, data=item.data, files=item.files)
                response.raise_for_status()

                print(f"Request to {item.addr} successful.")
                return
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                self.session = requests.Session()
                print('Session error. Retrying session:')
                try_print(e)

                sleep(1) 
            except Exception as e:
                print('Error FORM POSTING to remote router:')
                try_print(e)
                raise

    def run(self):
        while True:
            item = message_queue.get(block=True)
            self.make_call(item)

    # Not even sure if this is necessary, or can be called. Either way all processes / threads should be stopped when the app closes.
    def stop(self):
        del self.session

class RemoteRouter():
    def __init__(self, socketio_address: str, compress_jpeg: bool):
        self.socketio_address = socketio_address

        self.compress_jpeg = compress_jpeg

        self.session = requests.Session()

        self.remote_router_process = RemoteRouterProcess()
        self.remote_router_process.start()

    def base64_to_pil(self, base64_images):
        images = []
        for b in base64_images:
            img_byte = base64.b64decode(b)
            img_file = io.BytesIO(img_byte)
            img = Image.open(img_file)

            img.load()
            images.append(img)

        return images
    
    def pil_to_base64(self, pils):
        images = []

        for p in pils:
            buffered = io.BytesIO()
            p.save(buffered, format="PNG")
            img_byte = buffered.getvalue()
            images.append(base64.b64encode(img_byte).decode('utf-8'))

        return images

    def form_post(self, addr: str, data, files=None):
        addr = f'http://{self.socketio_address}:5000{addr}'

        message_queue.put(ProcessItem(addr=addr, data=data, files=files))

    def is_remote(self):
        return self.socketio_address is not None and self.socketio_address.strip() != '' and self.socketio_address != '127.0.0.1'
