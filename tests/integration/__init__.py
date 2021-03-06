import threading
import time
from typing import Callable
from gi.repository import GLib


def run_and_join(function: Callable):
	t = run(function)
	t.join()


def run(function: Callable) -> threading.Thread:
	t = threading.Thread(target=function)
	t.start()
	time.sleep(2)
	return t


def run_on_main_loop_and_wait(function):
	run_on_main_loop(function)
	time.sleep(1)


def run_on_main_loop(function):
	GLib.idle_add(function, priority=GLib.PRIORITY_HIGH)
