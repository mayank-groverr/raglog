import time
import os

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class MyHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.last_position = {}
        self.callback = callback

    def on_modified(self, event):
        if event.is_directory or not event.src_path.endswith(".log"):
            return
        path = event.src_path

        if path not in self.last_position:
            self.last_position[path] = os.path.getsize(path)
            return
        with open(path, "r") as f:
            f.seek(self.last_position[path])
            changed_content = f.read()
            self.last_position[path] = f.tell()
        if changed_content:
            self.callback(changed_content)


def get_log_change(changed_content):
    ...
    # to Implent after Log parser is created


if __name__ == "__main__":
    paths = ["."]  # Watch the current directory
    event_handler = MyHandler(get_log_change)
    observer = Observer()
    for path in paths:
        observer.schedule(event_handler, path, recursive=False)

    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        observer.join()
