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
