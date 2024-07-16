from typing import List
from gandy.full_pipelines.base_app import BaseApp
from gandy.utils.fancy_logger import logger
from gc import collect


class SwitchApp:
    def __init__(self, apps: List[BaseApp], app_names: List[str], default_idx=0):
        """
        Some of our apps (the individual pipes) in a pipeline will want to be able to be switched around at runtime.

        This class expects an app name for each given app, and provides a util to easily switch between the two as needed.
        """

        if len(app_names) != len(apps):
            raise ValueError(
                f"app_names must be of same length as apps. apps={[str(a) for a in apps]} app_names={[a for a in app_names]}"
            )
        if len(apps) == 0 or len(app_names) == 0:
            raise ValueError("apps and app_names must have at least one item.")

        self.sel_idx = default_idx
        self.apps = apps
        self.app_names = app_names

    def select_app(self, app_name):
        """
        Select the app with the given name. All further process calls on this app will redirect to the newly selected app.
        """
        try:
            idx = self.app_names.index(app_name)
            self.sel_idx = idx

            # Unload the other models to free up memory.
            for other_idx in range(len(self.apps)):
                if other_idx == idx:
                    continue

                try:
                    self.apps[other_idx].unload_model()
                except:
                    pass
            collect()

        except (IndexError, ValueError):
            logger.error(
                f"No app with name {app_name} found. Ignoring the call to select new app."
            )

    def process(self, *args, **kwargs):
        return self.apps[self.sel_idx].begin_process(*args, **kwargs)

    def begin_process(self, *args, **kwargs):
        return self.process(*args, **kwargs)

    def get_sel_app(self):
        return self.apps[self.sel_idx]

    def get_sel_app_name(self):
        return self.app_names[self.sel_idx]

    def set_each_app(self, var_name: str, value):
        """
        Sets a variable on each app.
        """
        for a in self.apps:
            try:
                setattr(a, var_name, value)
            except:
                pass  # In case App is None

    def for_each_app(self):
        return zip(self.apps, self.app_names)
