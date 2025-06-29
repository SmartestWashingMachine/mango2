import os
import json
import io
import base64
from PIL import Image
import requests

class RemoteRouter():
    def __init__(self, socketio_address: str):
        self.socketio_address = socketio_address

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
    
    def post(self, addr: str, data):
        response = requests.post('http://' + self.socketio_address + ':5000' + addr, json=data)
        try:
            response.raise_for_status()
        except Exception as e:
            print('Error:')
            print(e)
            raise e

    def is_remote(self):
        return self.socketio_address is not None and self.socketio_address.strip() != '' and self.socketio_address != '127.0.0.1'
