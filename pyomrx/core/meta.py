from pyomrx.core.exceptions import *
from threading import Event


class Abortable:
    def __init__(self, abort_event=None):
        self.abort_event = abort_event or Event()
        if not abort_event:
            print(f'new abort event for {self} with id {id(self.abort_event)}')

    def raise_for_abort(self):
        if self.abort_event.is_set():
            print(f'{self} got abort event set')
            raise AbortException()

    def abort(self):
        print(f'{self} setting abort event {id(self.abort_event)}')
        self.abort_event.set()
