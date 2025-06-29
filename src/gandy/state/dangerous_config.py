import os
import json

class DangerousConfig():
    def __init__(self):
        try:
            with open(os.path.expanduser("~/Documents/Mango/dangerousConfig.json"), 'r') as f:
                dangerous_config = json.load(f)

                self.socketio_address = dangerous_config['remoteAddress']
                self.enable_web_ui = dangerous_config['enableWebUi']
                self.debug = dangerous_config['debug']
        except Exception as e: # Can happen due to race conditions.
            print(e)

            # Actual config file created in ElectronJS see 'readDangerousConfig()'
            self.socketio_address = '127.0.0.1'
            self.enable_web_ui = False
            self.debug = False
