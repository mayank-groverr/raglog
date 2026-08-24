import os
import time

import json
from log_parser import parse_line_to_log
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
            self.callback(changed_content, path)


def get_log_change(changed_content, source_path=None):
    """
    Called whenever new lines are appended to a watched .log file.
    Splits the new content into lines and parses each one with log_parser.
    """
    for line in changed_content.splitlines():
        line = line.strip()
        if not line:
            continue

        record = parse_line_to_log(line)  # tag which file this came from

        # For now: just print the parsed result as JSON.
        # Replace this with DB insert / alerting / forwarding / etc.
        print(json.dumps(record))


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
