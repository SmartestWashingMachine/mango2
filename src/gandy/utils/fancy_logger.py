import logging
from dataclasses import dataclass
from contextlib import contextmanager
from datetime import datetime
from eliot import start_action, to_file, log_message
from time import strftime
import os
import traceback
import contextlib
import functools

@dataclass
class FancyTimeMetric:
    correlation_id: str
    code: str
    begin_time: datetime
    end_time: datetime

# Thank you PyInstaller. I love print statements that do not work across machines.
def try_print(msg: str):
    try:
        print(msg)
    except Exception as e:
        print("Failed to print...")

class FancyLogger:
    def __init__(self) -> None:
        self.do_print = False # Set to True by app.py when the config is loaded if DEBUG is enabled.

        self.logger = logging.getLogger("Gandy")

        self.cached_metrics = []

        self.cur_event_id = None

        save_folder_path = os.path.expanduser("~/Documents/Mango/logs")
        if not os.path.exists(save_folder_path):
            os.makedirs(save_folder_path, exist_ok=True)
        to_file(
            open(
                f'{save_folder_path}/backend_logs_{strftime("%d_%m_%Y")}.txt',
                encoding="utf-8",
                mode="a",
            )
        )

    def make_msg(self, msg: str):
        if self.cur_event_id is not None:
            return f"[{self.cur_event_id}] {msg}"

        return msg

    def log(self, msg: str):
        # log_obj = FancyLog(correlation_id=self.cur_event_id, code=code, message=msg, timestamp=d)
        new_msg = self.make_msg(msg)
        self.logger.debug(new_msg)

    def info(self, msg: str):
        # log_obj = FancyLog(correlation_id=self.cur_event_id, code=code, message=msg, timestamp=d)
        new_msg = self.make_msg(msg)
        self.logger.info(new_msg)

    def debug(self, msg: str):
        new_msg = self.make_msg(msg)
        self.logger.debug(new_msg)

    def exception(self, msg: str):
        new_msg = self.make_msg(msg)
        self.logger.exception(new_msg)

    def error(self, msg: str):
        new_msg = self.make_msg(msg)
        self.logger.error(new_msg)

    @contextlib.contextmanager
    def begin_event(self, event_name: str, **fields):
        with start_action(action_type=event_name, **fields) as ctx:
            try:
                if self.do_print:
                    try_print(f'>>>> {event_name}')
                    for f in fields.items():
                        try_print(f'^^ {f[0]}:')
                        try_print(f[1])

                old_log = ctx.log

                @functools.wraps(old_log)
                def wrapped_log(message_type, do_print = self.do_print, **fields):
                    if do_print:
                        try_print(f'>>>>>> {message_type}')
                        for f in fields.items():
                            try_print(f'^^^ {f[0]}:')
                            try_print(f[1])

                    try:
                        return old_log(message_type, **fields)
                    except Exception as e:
                        try_print('ERROR LOGGING:')
                        try_print(e)

                ctx.log = wrapped_log

                yield ctx
            except:
                self.event_exception(ctx)
                raise
    
    def log_message(self, msg: str, **fields):
        try:
            return log_message(msg, **fields)
        except Exception as e: # Thanks Eliot. What an absolutely miserable logging library you are. A logging library that doesn't work with unicode. wtf?
            try_print('ERROR LOGGING MESSAGE:')
            try_print(msg)
            for f in fields.items():
                try_print(f'^^ {f[0]}:')
                try_print(f[1])
    
    def debug_message(self, msg: str, **fields):
        return log_message(f'DEBUG: {msg}', debug=True, **fields)

    def event_exception(self, ctx):
        try_print('An error has occurred:')
        try_print(traceback.format_exc())
        if ctx is not None:
            return ctx.log(traceback.format_exc())
        else:
            self.log_message(traceback.format_exc())


logger = FancyLogger()
