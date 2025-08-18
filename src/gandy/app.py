__version__ = "2.0.0"

import threading
from gevent.pywsgi import WSGIServer
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
import os
from eliot.stdlib import EliotHandler
from gandy.utils.fancy_logger import logger
from time import sleep
import json
from gandy.utils.reroute_remote_backend import RemoteRouter
from gandy.state.dangerous_config import DangerousConfig
from gandy.state.debug_state import debug_state
from gandy.socket_process import SocketProcess, SocketWrapper

dangerous_config = DangerousConfig()
logger.do_print = dangerous_config.do_print or dangerous_config.debug

remote_router = RemoteRouter(dangerous_config.socketio_address, dangerous_config.compress_jpeg)

debug_state.debug = dangerous_config.debug

app = Flask(__name__)
web_app = Flask(__name__, template_folder=os.getcwd() + '/templates', static_folder=os.getcwd() + '/static')

# ONNX seems to be funky with asynchronous logick magick. With the default ping timeout (5000ms), it's likely that the client will drop the connection midway through the process.
# Of course, a long ping timeout is not ideal either.
# socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True, ping_timeout=100000)

# Just adds future emits to a message queue. Another thread will handle the actual emitting.
socketio = SocketWrapper()

legacy_logger = logging.getLogger("Gandy")
legacy_logger.setLevel(logging.DEBUG)

console = logging.StreamHandler()
legacy_logger.addHandler(console)

legacy_logger.addHandler(EliotHandler())

legacy_logger.info("Running app.")

if dangerous_config.enable_web_ui or remote_router.is_remote():

    @app.before_request
    def before_request():
        timestamp = strftime("[%Y-%b-%d %H:%M]")
        logger.log(
            f"{timestamp} {request.remote_addr} {request.method} {request.scheme} {request.full_path}"
        )


def run_server():
    socketio_thread = SocketProcess(remote_router.socketio_address, logger)
    socketio_thread.start()

    if dangerous_config.enable_web_ui:
        logic_thread = threading.Thread(target=lambda: WSGIServer(('0.0.0.0', 5000), app).serve_forever())
        web_thread = threading.Thread(target=lambda: WSGIServer(('0.0.0.0', 5200), app).serve_forever())

        logic_thread.start()
        web_thread.start()
    else:
        # serve(app, host='0.0.0.0', port=5000, threads=1)
        WSGIServer(('0.0.0.0', 5000), app).serve_forever()
    # app.run(host="0.0.0.0", debug=False)


import gandy.book_routes
import gandy.tasks.task1.task1_routes
import gandy.tasks.task2.task2_routes
import gandy.tasks.task3.task3_routes
import gandy.tasks.task3.server_side_box_key_capture
import gandy.tasks.task4.task4_routes
import gandy.tasks.task5.task5_routes
import gandy.tasks.task6.task6_routes
import gandy.tasks.task7.task7_routes
import gandy.tasks.task8.task8_routes
import gandy.web_routes
import gandy.config_routes
import gandy.dev_routes

import gandy.webui.load_html
