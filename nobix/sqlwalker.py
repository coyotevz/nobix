#!/usr/bin/env python
# -*- coding: utf-8 -*-

# patch
import nobix._pickle_methods

from queue import Empty as QueueEmpty
from multiprocessing import Process, Queue, Event

from urwid import ListWalker

def _consume_queue(queue, timeout=0.1):
    while True:
        try:
            queue.get(timeout=timeout)
        except QueueEmpty:
            break

class SQLWorker(Process):

    def __init__(self, query, qoutput, qaccum):
        super(SQLWorker, self).__init__()
        self.query = query
        self.qoutput = qoutput
        self.qaccum = qaccum
        self.stop = Event()

    def run(self):
        query = iter(self.query.yield_per(100))
        while not self.stop.is_set():
            try:
                item = next(query)
                self.qoutput.put(item)
                self.qaccum.put(item)
            except StopIteration:
                self.qoutput.put('STOP')
                self.qaccum.put('STOP')
                break
        self.qoutput.close()
        self.qaccum.close()

    def end(self):
        self.stop.set()

class FormatterWorker(Process):

    def __init__(self, formatter, qinput, qoutput):
        super(FormatterWorker, self).__init__()
        self.formatter = formatter
        self.qinput = qinput
        self.qoutput = qoutput
        self.stop = Event()

    def run(self):
        while not self.stop.is_set():
            try:
                item = self.qinput.get(timeout=1)
            except QueueEmpty:
                continue
            if item == 'STOP':
                break
            self.qoutput.put(self.formatter(item))

        if self.stop.is_set():
            # Consume the rest of queue
            _consume_queue(self.qinput)

        self.qinput.close()
        self.qoutput.close()
        self.qoutput.join_thread()

    def end(self):
        self.stop.set()

class QueryWalker(ListWalker):

    def __init__(self, query, formatter, max_rows=None, row_adapter=None, result_cb=None):
        if max_rows is None:
            max_rows = query.count()
        self.max_rows = max_rows
        self.row_adapter = row_adapter or (lambda x: x)
        self.result_callback = result_cb or (lambda x: None)

        self.focus = 0
        self.processed = []
        self.accumulator = []

        self.fmt_input = Queue()
        self.fmt_output = Queue()
        self.qaccum = Queue()

        self.sql_worker = SQLWorker(query, self.fmt_input, self.qaccum)
        self.fmt_worker = FormatterWorker(formatter, self.fmt_input, self.fmt_output)

        self.sql_worker.start()
        self.fmt_worker.start()

    def stop_workers(self):

        if self.sql_worker.is_alive():
            self.sql_worker.end()
            if not self.qaccum._reader.closed:
                _consume_queue(self.qaccum)
            self.fmt_input.close()
            self.qaccum.close()
            self.fmt_input.join_thread()
        if self.fmt_worker.is_alive():
            self.fmt_worker.end()

            # Consume the rest of queue
            _consume_queue(self.fmt_output)

            self.fmt_output.close()

    def _fetch_results(self):
        while True:
            try:
                row = self.qaccum.get_nowait()
            except QueueEmpty:
                break
            if row == 'STOP':
                self.result_callback(self.accumulator)
                # Remove watcher handle before close queue
                self._remove_watcher()
                self.qaccum.close()
                self.qaccum.join_thread()
                return
            self.accumulator.append(self.row_adapter(row))

    def _remove_watcher(self):
        self._loop.event_loop.remove_watch_file(self._handle)
        self._loop.draw_screen()

    def connect_watcher(self, loop):
        self._loop = loop
        self._handle = loop.event_loop.watch_file(self.qaccum._reader, self._fetch_results)

    def _get_at_pos(self, pos):
        # Short circuit
        if pos < 0 or pos > (self.max_rows - 1):
            return None, None

        if pos < len(self.processed):
            # We have that line so return it
            return self.processed[pos], pos

        if pos < 30:
            # Force first 30 lines loaded
            p = self.fmt_output.get()
            if p:
                self.processed.append(p)
            else:
                return self._get_at_pos(pos)
            return self.processed[-1], pos

        try:
            p = self.fmt_output.get(timeout=0.2)
            if p:
                self.processed.append(p)
            else:
                return self._get_at_pos(pos)
            #self.processed.append(self.fmt_output.get(timeout=0.2))
        except QueueEmpty:
            return None, None

        return self.processed[-1], pos

    ## ListWalker interface

    def get_focus(self):
        return self._get_at_pos(self.focus)

    def set_focus(self, focus):
        self.focus = focus
        self._modified()

    def get_next(self, start_from):
        return self._get_at_pos(start_from + 1)

    def get_prev(self, start_from):
        return self._get_at_pos(start_from - 1)
