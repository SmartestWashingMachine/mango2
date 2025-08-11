import os
import json
import io
import base64
from PIL import Image
import requests
from time import sleep

class RemoteRouter():
    def __init__(self, socketio_address: str):
        self.socketio_address = socketio_address

        self.session = requests.Session()

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
    
    def form_post(self, addr: str, data, files = None):
        addr = 'http://' + self.socketio_address + ':5000' + addr

        try:
            response = self.session.post(addr, data=data, files=files)
            response.raise_for_status()
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            print('Session error. Retrying session:')
            print(e)
            sleep(3)

            self.form_post(addr, data, files)
        except Exception as e:
            print('Error FORM POSTING to remote router:')
            print(e)
            raise e

    def post(self, addr: str, data):
        addr = 'http://' + self.socketio_address + ':5000' + addr

        response = requests.post(addr, json=data)
        try:
            response.raise_for_status()
        except Exception as e:
            print('Error JSON POSTING to remote router:')
            print(e)
            raise e

    def is_remote(self):
        return self.socketio_address is not None and self.socketio_address.strip() != '' and self.socketio_address != '127.0.0.1'
