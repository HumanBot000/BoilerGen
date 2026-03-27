class ObservableList(list):
    def __init__(self, *args, callback=None):
        super().__init__(*args)
        self._callback = callback

    def _notify(self, action, *args):
        if self._callback:
            self._callback(self,action, *args)

    def append(self, item):
        super().append(item)
        self._notify("append", item)

    def remove(self, item):
        super().remove(item)
        self._notify("remove", item)

    def __setitem__(self, index, value):
        old = self[index]
        super().__setitem__(index, value)
        self._notify("set", value)

    def extend(self, iterable):
        super().extend(iterable)
        self._notify("extend", iterable)