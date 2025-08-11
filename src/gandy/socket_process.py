import threading
import queue
from time import sleep
import socketio as socketio_pkg

# Thread-safe. Used to queue up messages to be sent via web sockets.
message_queue = queue.Queue()

class SocketProcess(threading.Thread):
    def __init__(self, socketio_address: str, logger):
        super().__init__()

        self.socketio_address = socketio_address

        self.socketio = socketio_pkg.Client()

        self.logger = logger

    def try_socket_conn(self):
        while not self.socketio.connected:
            try:
                log_msg = f"Connecting to {self.socketio_address}..."
                print(log_msg)
                self.logger.info(log_msg)

                # By default SocketIO client does not reconnect on the initial connection attempt...
                self.socketio.connect(
                    f"ws://{self.socketio_address}:5100", transports=["websocket"]
                )
                break
            except Exception as e:
                print(e)
                print("Gonna retry connection.")
                self.logger.info(
                    "Failed connecting to Socket server - retrying soon..."
                )

                sleep(1)
                continue

    def patched_emit(self, event, data, *args, **kwargs):
        while True:
            self.try_socket_conn() # Returns right away if already connected.

            try:
                self.socketio.emit(event, data, *args, **kwargs)
                return None
            except Exception as e:
                print("--- SOCKET ERROR:")
                print(e)
                self.logger.error(e)

                # Just in case...
                if self.socketio.connected:
                    err = "SocketIO was 'connected' yet the error was still raised! This should NEVER happen."
                    print(err)
                    self.logger.error(err)
                    sleep(3)

    def run(self):
        self.try_socket_conn()

        while True:
            try:
                message = message_queue.get(block=False)

                self.patched_emit(message[0], message[1], *message[2], **message[3])
            except queue.Empty:
                pass
            except Exception as e:
                print(f"Error in socket process: {e}")
                self.logger.error(f"Error in socket process: {e}")

            self.socketio.sleep(0.01) # Allows time for heartbeats I hope.

    # Not even sure if this is necessary, or can be called. Either way all processes / threads should be stopped when the app closes.
    def stop(self):
        if self.socketio.connected:
            self.socketio.disconnect()
            print("Socket disconnected.")
            self.logger.info("Socket disconnected.")
        else:
            print("Socket was not connected.")
            self.logger.info("Socket was not connected.")

class SocketWrapper():
    def patched_emit(self, event, data, *args, **kwargs):
        message_queue.put((event, data, args, kwargs))

    def sleep(self, *args, **kwargs):
        pass # For legacy compatibility.

    def start_background_task(self, fn, *args):
        fn(*args) # For legacy compatibility.