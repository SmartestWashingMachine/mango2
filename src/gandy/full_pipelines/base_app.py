from abc import ABC, abstractmethod
import os


class BaseApp(ABC):
    def __init__(self, preload=False):
        """
        All apps inherit from BaseApp. This BaseApp will "lazy load" the required model when the process method is called for the first time.

        Make sure to call super().__init__() if inheriting from this class.
        """
        self.loaded = False

        if preload:
            self.load_model()

    def load_model(self):
        """
        All logic to load a model should go in here.
        If the app does not use any model, then this method can be left alone.

        Make sure to call super().__load_model__() at the end of the method if inheriting from this class.
        If not calling super(), then put this line at the end of your code:
            self.loaded = True
        """
        self.loaded = True

    @abstractmethod
    def unload_model(self):
        self.loaded = False

    @abstractmethod
    def process(self, *args, **kwargs):
        raise RuntimeError("App .process method was not implemented.")

    def begin_process(self, *args, **kwargs):
        if not self.loaded:
            self.load_model()

        return self.process(*args, **kwargs)

    def can_load(self, path_exists=""):
        if path_exists == "":
            return True
        return os.path.exists(path_exists)
