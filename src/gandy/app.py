__version__ = "2.0.0"

from waitress import serve
from time import strftime
import logging
from flask import Flask, request
from gandy.model_apps import (
    TEXT_DETECTION_APP,
    TEXT_RECOGNITION_APP,
    TRANSLATION_APP,
    SPELL_CORRECTION_APP,
    IMAGE_CLEANING_APP,
    IMAGE_REDRAWING_APP,
    RERANKING_MODEL_APP,
    TEXT_LINE_MODEL_APP,
    translate_pipeline,
)
from gandy.get_envs import ENABLE_WEB_UI
import os
from eliot.stdlib import EliotHandler
from gandy.utils.fancy_logger import logger
import socketio as socketio_pkg
from time import sleep

app = Flask(__name__)

# ONNX seems to be funky with asynchronous logick magick. With the default ping timeout (5000ms), it's likely that the client will drop the connection midway through the process.
# Of course, a long ping timeout is not ideal either.
# socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True, ping_timeout=100000)

socketio = socketio_pkg.Client()

def try_socket_conn(is_reconn = False):
    while True:
        try:
            print('Connecting...')
            # By default SocketIO client does not reconnect on the initial connection attempt...
            socketio.connect('ws://127.0.0.1:5100', transports=['websocket'])
            break
        except Exception as e:
            print(e)
            print('Gonna retry connection.')
            sleep(1)
            continue

    if is_reconn:
        sleep(2) # In case of reconnection BS. Actually, this turned out to be buffer size limit - maybe we don't need this reconnection stuff.

try_socket_conn()

legacy_logger = logging.getLogger("Gandy")
legacy_logger.setLevel(logging.DEBUG)

console = logging.StreamHandler()
legacy_logger.addHandler(console)

legacy_logger.addHandler(EliotHandler())

legacy_logger.info("Running app.")

def patched_emit(*args, **kwargs):
    try:
        socketio.emit(*args, **kwargs)
    except Exception as e:
        try:
            socketio.disconnect()
        except Exception as ee:
            print(ee)

        logger.info('Socket error (reconnecting?):')
        logger.error(e)

        try_socket_conn(is_reconn=True)
        patched_emit(*args, **kwargs)

socketio.patched_emit = patched_emit

socketio.sleep = lambda *args, **kwargs: None
socketio.start_background_task = lambda fn, *args: fn(*args)

if ENABLE_WEB_UI:

    @app.before_request
    def before_request():
        timestamp = strftime("[%Y-%b-%d %H:%M]")
        logger.error(
            f"{timestamp} {request.remote_addr} {request.method} {request.scheme} {request.full_path}"
        )


def run_server():
    serve(app, host='0.0.0.0', port=5000)
    # app.run(host="0.0.0.0", debug=False)


import gandy.book_routes
import gandy.tasks.task1.task1_routes
import gandy.tasks.task2.task2_routes
import gandy.tasks.task3.task3_routes
import gandy.tasks.task4.task4_routes
import gandy.tasks.task5.task5_routes
import gandy.tasks.task6.task6_routes
import gandy.tasks.task7.task7_routes
import gandy.web_routes
import gandy.config_routes
import gandy.dev_routes

import gandy.webui.load_html
