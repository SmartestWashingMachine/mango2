from typing import List


class CacheOption:
    def __init__(self, name: str, max: int, is_column=False) -> None:
        self.name = name
        self.max = max
        self.is_column = is_column


class BasicCache:
    def __init__(self, options: List[CacheOption]) -> None:
        self.options_info = {}

        self.data = {}
        for o in options:
            self.options_info[o.name] = o

            if o.is_column:
                # Python dicts remember key order insertion as of 3.7+
                self.data[o.name] = {}
            else:
                self.data[o.name] = []

    def index(self, key: str, index: int):
        if self.options_info[key].is_column:
            raise RuntimeError("Requires row data.")
        return self.data[key][index]

    def index_of_value(self, key: str, value):
        if self.options_info[key].is_column:
            raise RuntimeError("Requires row data.")
        try:
            return self.data[key].index(value)
        except:
            return None

    def get(self, key: str, value):
        if not self.options_info[key].is_column:
            raise RuntimeError("Requires column data")
        return self.data[key][value]

    def push(self, key: str, value):
        max_count = self.options_info[key].max

        if self.options_info[key].is_column:
            count = len(self.data[key].keys())

            if count >= max_count:
                self.data[key].pop(next(iter(self.data[key])))
            self.data[key][value] = ""  # TODO: Use better data format, like set.
        else:
            count = len(self.data[key])

            if count >= max_count:
                self.data[key] = self.data[key][1:]
            self.data[key].append(value)

    def iterate(self, key: str):
        if self.options_info[key].is_column:
            raise RuntimeError("Requires row data.")
        return [i for i in self.data[key]]

    def enumerate(self, key: str):
        if self.options_info[key].is_column:
            raise RuntimeError("Requires row data.")
        return enumerate(self.data[key])


def make_image_cache():
    max_items = 3 # Since images are taken frame-by-frame, second-by-second, let's assume only nearby frames should be similar.

    return BasicCache(
        [
            CacheOption(name="source_texts", max=max_items),
            CacheOption(name="images", max=max_items),
            CacheOption(name="cropped_images", max=max_items),
            CacheOption(name="seconds", max=max_items),
        ]
    )


def make_translation_cache():
    max_items = 100

    return BasicCache(
        [
            CacheOption(name="source_texts", max=max_items),
            CacheOption(name="target_texts", max=max_items),
            CacheOption(name="seconds", max=max_items),
        ]
    )
