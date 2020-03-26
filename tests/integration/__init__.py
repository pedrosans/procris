import threading
import time
from typing import Callable


def run_and_join(function: Callable):
	t = run(function)
	t.join()


def run(function: Callable) -> threading.Thread:
	t = threading.Thread(target=function)
	t.start()
	time.sleep(2)
	return t


def run_on_main_loop_and_wait(function):
	GLib.idle_add(function, priority=GLib.PRIORITY_HIGH)
	time.sleep(1)