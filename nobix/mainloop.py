#!/usr/bin/env python
# -*- coding: utf-8 -*-

import select
import urwid

_main_loop = None

class NobixSelectEventLoop(urwid.SelectEventLoop):

    def __init__(self, *args, **kwargs):
        super(NobixSelectEventLoop, self).__init__(*args, **kwargs)
        self._keep_running = True

    def run(self):
        try:
            while self._keep_running:
                try:
                    self._loop()
                except select.error, e:
                    if e.args[0] != 4:
                        raise
        except urwid.ExitMainLoop:
            pass

    def quit(self):
        self._keep_running = False

class NobixMainLoop(urwid.MainLoop):

    def __init__(self, widget, palette=[], screen=None, handle_mouse=True,
                 input_filter=None, unhandled_input=None, event_loop=None):
        global _main_loop

        if event_loop is None:
            event_loop = NobixSelectEventLoop()

        self.main_widget = widget

        super(NobixMainLoop, self).__init__(widget, palette, screen,
                handle_mouse, input_filter, unhandled_input, event_loop)

        # keep track of this main loop
        _main_loop = self

def get_main_loop():
    return _main_loop
