#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
from hashlib import md5
import time
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from decimal import Decimal, DecimalException

from urwid import Edit, Text, Button, Divider, SolidFill, Overlay, Pile,\
                  Columns, SimpleListWalker, ListBox, Padding, Filler,\
                  LineBox, AttrMap, WidgetWrap, MainLoop, ExitMainLoop,\
                  WidgetDecoration,\
                  connect_signal, command_map
from urwid.widget import EditError
from urwid.util import MetaSuper

from nobix.exc import NobixBadDateError
from nobix.config import get_current_config

class InputBox(Edit):#{{{
    "Rich input text box"
    signals = ['focus-in', 'focus-out', 'edit-done', 'edit-cancel']
    _highlight_attr = 'inputbox.highlight'

    def __init__(self, *args, **kwargs):#{{{
        self.max_length = kwargs.pop('max_length', None)
        self.set_highlight_attr(kwargs.pop('highlight_attr', self._highlight_attr))
        d = {'edit_text': kwargs.pop('edit_text', '')}
        kwargs.update(d)
        self.has_focus = False
        self.__super.__init__(*args, **kwargs)
        connect_signal(self, 'focus-in', self.on_focus_in)
        connect_signal(self, 'focus-out', self.on_focus_out)
        connect_signal(self, 'edit-cancel', self.on_edit_cancel)
#}}}
    def filter_input(self, text):#{{{
        "Filter input text at insert_text_result() time."
        return text
#}}}
    def insert_text(self, text):#{{{
        result_text, result_pos = self.insert_text_result(text)

        if self.max_length is not None and len(result_text) > self.max_length:
            # Don't insert and emit
            self._emit('edit-done', self.get_edit_text())
            return None

        self.highlight = None
        self.set_edit_text(result_text)
        self.set_edit_pos(result_pos)
#}}}
    def insert_text_result(self, text):#{{{
        text = self.filter_input(text)
        if self.highlight:
            start, stop = self.highlight
            btext, etext = self.edit_text[:start], self.edit_text[stop:]
            result_text = btext + etext
            result_pos = start
        else:
            result_text = self.edit_text
            result_pos = self.edit_pos

        result_text = result_text[:result_pos] + text + result_text[result_pos:]
        result_pos += len(text)
        return (result_text, result_pos)
#}}}
    def render(self, size, focus=False):#{{{
        if self.has_focus and not focus:
            self._emit('focus-out')
        elif focus and not self.has_focus:
            self._emit('focus-in')
        self.has_focus = focus

        return self.__super.render(size, focus=focus)
#}}}
    def keypress(self, size, key):#{{{

        unhandled = key
        if key == "enter" and not self.multiline:
            unhandled = self._emit('edit-done', self.get_edit_text())
        elif key == "esc":
            unhandled = self._emit('edit-cancel')

        if unhandled:
            return self.__super.keypress(size, key)
#}}}
    def on_focus_in(self, widget):#{{{
        self._prev_value = self.edit_text
#}}}
    def on_focus_out(self, widget):#{{{
        self.set_edit_text(self.edit_text)
#}}}
    def on_edit_cancel(self, widget):#{{{
        self.set_edit_text(self._prev_value or '')
#}}}

    def set_highlight_attr(self, attr):
        self._highlight_attr = attr

    # Always return unicode
    def set_edit_text(self, text):
        self.__super.set_edit_text(text)
    def get_edit_text(self):
        return str(self.__super.get_edit_text())
    edit_text = property(get_edit_text, set_edit_text)

    def _get_highlight(self):
        return self._highlight
    def _set_highlight(self, val):
        self._highlight = val
        self._invalidate()
    highlight = property(_get_highlight, _set_highlight)

    # Highlight support FIXME: Testing phase
    def get_text(self):
        attrib = []
        if self.highlight:
            s, e = self.highlight
            if e-s > 0:
                if s != 0:
                    attrib.append((None, s))
                attrib.append((self._highlight_attr, e-s))
        return self._caption + self._edit_text, attrib
#}}}

class IntegerInputBox(InputBox):#{{{

    def __init__(self, caption="", value=None, default=None,#{{{
                 min_value=None, max_value=None, **kwargs):
        self._min = int(min_value) if min_value else None
        self._max = int(max_value) if max_value else None
        self._default = int(default) if default else None
        self.__super.__init__(caption, **kwargs)
        self.set_value(value)
        connect_signal(self, 'focus-out', self.on_focus_out)
#}}}
    def valid_charkey(self, ch):#{{{
        return len(ch) == 1 and ch in "0123456789-+"
#}}}
    def valid_char(self, ch):#{{{
        ch = self.filter_input(ch)
        if not self.valid_charkey(ch):
            return False

        future_result, _ = self.insert_text_result(ch)

        try:
            result = int(future_result)
            if self._min and result < self._min:
                return False
            if self._max and result > self._max:
                return False
        except ValueError:
            return False

        # if the result if fully valid integer, return true:
        if re.match(r'[\+\-]?(0|[1-9]\d*)?$', future_result):
            return True
        return False
#}}}
    def set_value(self, val):#{{{
        if isinstance(val, int):
            v = val
        else:
            try:
                v = int(str(val))
            except (ValueError, TypeError):
                return
        self.set_edit_text(str(v))
#}}}
    def get_value(self):#{{{
        if self.edit_text:
            return int(self.edit_text)
        else:
            return self._default or 0
#}}}
    value = property(get_value, set_value)

    def on_focus_out(self, widget):#{{{
        if self.edit_text:
            self.set_value(self.edit_text)
        else:
            self.set_value(self._default)
        self.set_value(self.get_value())
#}}}
#}}}

class NumericInputBox(InputBox):#{{{

    def __init__(self, caption="", value=None, default=None, digits=2, sep=".",#{{{
                 min_value=None, max_value=None, max_digits=4, **kwargs):
        self._sep = sep
        self._min = Decimal(str(min_value)) if min_value is not None else None
        self._max = Decimal(str(max_value)) if max_value is not None else None
        self._max_digits = max_digits
        self._default = Decimal(str(default)) if default else None
        self._q = Decimal((0, (1,), -digits))

        self.__super.__init__(caption, **kwargs)
        self.set_value(value)

        connect_signal(self, 'focus-out', self.on_focus_out)
#}}}
    def filter_input(self, text):#{{{
        return text.replace(".", self._sep)
#}}}
    def valid_charkey(self, ch):#{{{
        _valids = "+-0123456789" + self._sep
        return len(ch) == 1 and ch in _valids
#}}}
    def valid_char(self, ch):#{{{
        ch = self.filter_input(ch)
        if not self.valid_charkey(ch):
            return False

        future_result, _ = self.insert_text_result(ch)

        # Single sign
        if future_result in ('-', '+'):
            if self._max is not None or self._min is not None:
                if future_result == '-' and self._min >= Decimal(0):
                    return False
                elif future_result == '+' and self._max <= Decimal(0):
                    return False
            return True

        sep = r'\%s' % self._sep

        # leading zeroes
        if re.match(r'[+-]?0\d+%s?\d*$' % sep, future_result):
            return False

        # excesive digits
        if re.match(r'[+-]?\d*%s\d{%d,}\d+' % (sep, self._max_digits), future_result):
            return False

        if future_result.startswith(('+', '-')):
            future_result = future_result[0] + '0' + future_result[1:]
        else:
            future_result = '0' + future_result

        try:
            result = Decimal(future_result.replace(self._sep, "."))
            if self._min is not None and result < self._min:
                return False
            if self._max is not None and result > self._max:
                return False
            return True
        except DecimalException as e:
            return False
#}}}
    def get_value(self):#{{{
        if self.edit_text:
            try:
                return Decimal(self.edit_text.replace(self._sep, "."))
            except DecimalException:
                return self._default
        else:
            return self._default
#}}}
    def set_value(self, val):#{{{
        if isinstance(val, Decimal):
            v = val
        else:
            try:
                v = Decimal(str(val).replace(self._sep, "."))
            except DecimalException:
                self.set_edit_text("")
                return
        self.set_edit_text(str(v.quantize(self._q)).replace(".", self._sep))
#}}}
    value = property(get_value, set_value)

    def on_focus_out(self, widget):#{{{
        if self.edit_text:
            self.set_value(self.edit_text)
        else:
            self.set_value(self._default)
#}}}
#}}}

class DateInputBox(InputBox):#{{{

    signals = ['bad-date-error']

    def __init__(self, caption="", out_fmt="%d/%m/%y", in_fmt=(), **kwargs):#{{{

        if not in_fmt:
            in_fmt = ('%d%m%y', '%d%m%Y', '%d/%m/%y', '%d/%m/%Y',
                      '%d-%m-%y', '%d-%m-%Y', '%d.%m.%y', '%d.%m.%y')
        if not isinstance(in_fmt, (tuple, list)):
            in_fmt = (in_fmt,)
        self.in_fmt = in_fmt
        self.out_fmt = out_fmt

        opts = {
            'align': kwargs.pop('align', 'right'),
            'max_length': kwargs.pop('max_length', 8),
        }
        kwargs.update(opts)
        self.__super.__init__(caption, **kwargs)

        connect_signal(self, 'edit-done', self._check_date)
        connect_signal(self, 'focus-out', self._check_date)
#}}}
    def valid_char(self, ch):#{{{
        return len(ch) == 1 and ch in '0123456789/-.'
#}}}
    def set_value(self, val):#{{{
        d = self._parse_date(val)
        self.set_edit_text(self._format_date(d))
#}}}
    def get_value(self):#{{{
        if self.edit_text:
            return self._parse_date(self.edit_text)
        return None
#}}}
    value = property(get_value, set_value)

    def _parse_date(self, val):#{{{
        if isinstance(val, (datetime, date)):
            d = val
        elif isinstance(val, str):
            d = None
            for fmt in self.in_fmt:
                try:
                    d = datetime.strptime(val, fmt)
                    break
                except ValueError:
                    pass
            if val == '':
                return None
            if d is None:
                raise NobixBadDateError("Fecha malformada: %s" % val)
        else:
            raise ValueError("%r must be a string or datetime/date object not %s" % (val, type(val)))
        return d.date() if isinstance(d, datetime) else d
#}}}
    def _format_date(self, val):#{{{
        if val is not None:
            try:
                return val.strftime(self.out_fmt)
            except ValueError:
                raise NobixBadDateError("Fecha malformada: %s" % val)
        return ''
#}}}
    def _check_date(self, *args):#{{{
        if self.edit_text:
            try:
                d = self._parse_date(self.edit_text)
                self.set_value(d)
            except NobixBadDateError as e:
                self._emit('bad-date-error', str(e))
                return False
        return True
#}}}
    def keypress(self, size, key):#{{{
        p = self.edit_pos
        _check = False
        if command_map[key] == 'cursor left':
            if p == 0: _check = True
        elif command_map[key] == 'cursor right':
            if p >= len(self.edit_text): _check = True
        elif command_map[key] in ('cursor up', 'cursor down'):
            _check = True
        elif key in ('H', 'h'):
            self.set_value(date.today())
            self._emit('edit-done', self.get_edit_text())
            return

        if _check:
            if self._check_date():
                return self.__super.keypress(size, key)
            return None
        else:
            return self.__super.keypress(size, key)
#}}}
#}}}

class DateSelectorBox(DateInputBox):#{{{

    def __init__(self, *args, **kwargs):#{{{
        self.min_date = kwargs.pop('min_date', get_current_config().min_date)
        self.max_date = kwargs.pop('max_date', get_current_config().max_date)
        self.__super.__init__(*args, **kwargs)
#}}}
    def keypress(self, size, key):#{{{
        if key in ('+', '-', 'ctrl up', 'ctrl down', 'ctrl left', 'ctrl right',
                   'q', 'a', 'w', 's', 'e', 'd'):
            current = self.get_value() or date.today()
            if key in ('+', 'q'): m = {'days': +1}
            elif key in ('-', 'a'): m = {'days': -1}
            elif key in ('ctrl up', 'w'): m = {'months': +1}
            elif key in ('ctrl down', 's'): m = {'months': -1}
            elif key in ('ctrl right', 'e'): m = {'years': +1}
            elif key in ('ctrl left', 'd'): m = {'years': -1}
            self.set_value(current+relativedelta(**m))
            return key
        return self.__super.keypress(size, key)
#}}}
    def _check_date(self, *args):#{{{
        if self.edit_text == '0': self.set_value(self.min_date)
        elif self.edit_text == '9': self.set_value(self.max_date)
        else: return self.__super._check_date(self, *args)
#}}}
#}}}

class NumericText(Text):#{{{

    def __init__(self, value=None, digits=2, sep=".", **kwargs):#{{{
        self._value = None
        self._sep = sep
        self._q = Decimal((0, (1,), -digits))
        opts = {
            'align': kwargs.get('align', 'right'),
            'wrap': kwargs.get('wrap', 'clip'),
        }
        kwargs.update(opts)
        self.__super.__init__("", **kwargs)
        self.set_value(value)
#}}}
    def set_value(self, val):#{{{
        if isinstance(val, Decimal):
            self._value = val
        else:
            try:
                self._value = Decimal(str(val).replace(self._sep, "."))
            except DecimalException:
                return
        self.set_text(str(self._value.quantize(self._q)).replace(".", self._sep))
#}}}
    def get_value(self):#{{{
        if self._value is not None:
            return self._value
        return Decimal()
#}}}
    value = property(get_value, set_value)
#}}}

class Border(WidgetDecoration, WidgetWrap):#{{{

    def __init__(self, original_widget, title=None, title_attr=None, attr=None):#{{{

        self.title = title
        self.title_attr = title_attr
        self.attr = attr
        self._attr = attr

        def _get_attr(w):
            if attr is not None:
                return AttrMap(w, attr)
            return w

        self.tline = _get_attr(Divider("─"))
        self.bline = _get_attr(Divider("─"))
        self.lline = _get_attr(SolidFill("│"))
        self.rline = _get_attr(SolidFill("│"))

        self.tlcorner = _get_attr(Text("┌"))
        self.trcorner = _get_attr(Text("┐"))
        self.blcorner = _get_attr(Text("└"))
        self.brcorner = _get_attr(Text("┘"))

        self._title_text = Text(" %s " % self.title, 'center')
        self._title = AttrMap(self._title_text, self.title_attr)

        top = Columns([('fixed', 1, self.tlcorner),
                       self.tline,
                       ('fixed', len(self.title)+2, self._title),
                       self.tline,
                       ('fixed', 1, self.trcorner)])

        middle = Columns([('fixed', 1, self.lline),
                         original_widget,
                         ('fixed', 1, self.rline)],
                         box_columns=[0,2],
                         focus_column=1)

        bottom = Columns([('fixed', 1, self.blcorner),
                          self.bline,
                          ('fixed', 1, self.brcorner)])

        pile = Pile([('flow', top), middle, ('flow', bottom)], focus_item=1)

        WidgetDecoration.__init__(self, original_widget)
        WidgetWrap.__init__(self, pile)
#}}}
    def set_title_attr(self, attr):#{{{
        self.title_attr = attr
        self._invalidate()
#}}}
    def set_title(self, text):#{{{
        self._title_text.set_text(text)
        self._invalidate()
#}}}
#}}}

# used in dialog interfaces
from nobix.mainloop import get_main_loop

### Dialog objects ###

class Dialog(object, metaclass=MetaSuper):#{{{
    def __init__(self, content, buttons_and_results=[], title=None, subtitle=None,#{{{
                 focus_button=None, keypress=None, input_filter=None, **kwargs):

        self.dialog_result = None
        self._callback = None
        self.align = kwargs.pop('align', 'center')
        self.valign = kwargs.pop('valign', 'middle')
        self.width = kwargs.pop('width', ('relative', 60))
        self.min_width = kwargs.pop('min_width', None)
        self.height = kwargs.pop('height', ('relative', 60))
        self.min_height = kwargs.pop('min_height', None)
        self._compact_header = kwargs.pop('compact_header', False)
        self.attr_style = kwargs.pop('attr_style', 'dialog')
        self.title_attr_style = kwargs.pop('title_attr_style', 'dialog.title')
        self.subtitle_attr_style = kwargs.pop('subtitle_attr_style', 'dialog.subtitle')
        self.with_border = kwargs.pop('with_border', True)
        self.must_quit = kwargs.pop('must_quit', False)
        self._content = content
        self.title = title
        self.subtitle = subtitle
        self.top_widget = get_main_loop().main_widget
        self.screen = get_main_loop().screen
        self._title_widget = Text("")
        self._focus_button = focus_button
        self._keypress = keypress
        self._input_filter = input_filter

        button_normal_attr = kwargs.pop('button_normal_attr', 'dialog.button')
        button_focus_attr = kwargs.pop('button_focus_attr', 'dialog.button.focus')

        self._keep_running = True

        class ResultSetter(object):
            def __init__(subself, res):
                subself.res = res
            def __call__(subself, btn):
                if callable(subself.res):
                    self.dialog_result = subself.res(btn)
                else:
                    self.dialog_result = subself.res
                #from nobix.utils import show_error
                #show_error("%s\n%s\nself._keep_running: %s\nself.dialog_result: %r" % (type(self), btn, self._keep_running, self.dialog_result))
                if self.must_quit:
                    self.quit()

        self.button_widgets = []
        for btn_descr in buttons_and_results:
            if btn_descr is None:
                self.button_widgets.append(Text(""))
            elif isinstance(btn_descr, Button):
                self.button_widgets.append(AttrMap(btn_descr, button_normal_attr, button_focus_attr))
            elif isinstance(btn_descr, AttrMap):
                seff.button_widgets.append(btn_descr)
            else:
                btn_text, btn_result = btn_descr
                self.button_widgets.append(
                    AttrMap(Button(btn_text, ResultSetter(btn_result)),
                            button_normal_attr, button_focus_attr)
                )
#}}}
    def run(self, alarm=None):#{{{
        pile_widgets = [self._content]
        if self.button_widgets:
            pile_widgets.append(("flow", Columns(self.button_widgets, dividechars=1)))
        self._pile = w = Pile(pile_widgets)

        header = []
        if self.title is not None:
            self._title_widget = Text(self.title, align='center')
            header.append(('flow', AttrMap(self._title_widget, self.title_attr_style)))
        if self.subtitle is not None:
            header.append(('flow', AttrMap(Text(self.subtitle, align='center'), self.subtitle_attr_style)))

        if header:
            if not self._compact_header:
                header.append(("fixed", 1, SolidFill()))
            header.append(w)
            w = Pile(header)

        if self.with_border:
            w = LineBox(w)
#            w = Border(w, title=self.title, title_attr=self.title_attr_style, attr=self.attr_style)
        overlay = Overlay(w, self.top_widget, align=self.align, valign=self.valign,
                          width=self.width, height=self.height, min_width=self.min_width,
                          min_height=self.min_height)

        self.w = w = AttrMap(overlay, self.attr_style)

        if isinstance(self._focus_button, int):
            self.focus_button(self._focus_button)

        mainloop = get_main_loop()
        old_widget = mainloop.widget
        old_unhandled_input = mainloop._unhandled_input
        old_input_filter = mainloop._input_filter

        mainloop.widget = w
        mainloop._unhandled_input = self.keypress
        mainloop._input_filter = self.input_filter
        mainloop.draw_screen()

        self._keep_running = True

        if alarm is not None and isinstance(alarm, tuple) and len(alarm) in (2, 3):
            mainloop.set_alarm_in(*alarm)

        self.configure_subloop(mainloop)

        # run event_loop in controlled/modal form
        while self._keep_running and mainloop.event_loop._keep_running:
            mainloop.event_loop._loop()

        if self._callback:
            self._callback(*self._args)

        # restore main loop
        #mainloop.widget = self.top_widget
        mainloop.widget = old_widget
        mainloop._unhandled_input = old_unhandled_input
        mainloop._input_filter = old_input_filter
        mainloop.draw_screen()
        return self.dialog_result
#}}}
    def configure_subloop(self, subloop):#{{{
        pass
#}}}
    def keypress(self, key):#{{{
        if self._keypress is not None:
            return self._keypress(key)
#}}}
    def input_filter(self, key, raw):#{{{
        if self._input_filter is not None:
            return self._input_filter(key, raw)
        return key
#}}}
    def quit(self, *args):#{{{
        self._keep_running = False
#        raise ExitMainLoop()
#}}}
    def _quit(self, *args):#{{{
        # To connect as button callback
        self.quit()
        #self.must_quit = True
#}}}
    def install_callback(self, callback, args=()):#{{{
        self._callback = callback
        self._args = args
#}}}
    def remove_callback(self):#{{{
        self._callback = None
#}}}
    def focus_button(self, index):#{{{
        if self.button_widgets:
            self._pile.set_focus(self._pile.widget_list[-1])
            self._pile.widget_list[-1].set_focus_column(index)
#}}}
#}}}

class _MsgDialog(Dialog):#{{{

    def keypress(self, key):
        if key in ('enter', 'escape', ' '):
            self.quit()
#}}}
class ErrorDialog(_MsgDialog):#{{{

    def __init__(self, message):
        self.__super.__init__(Text(message, align='center'), title="ERROR")
        self.height = None
        self.attr_style = "dialog.error"
        self.title_attr_style = "dialog.error.title"

#}}}
class WarningDialog(_MsgDialog):#{{{

    def __init__(self, message, buttons=[], **kwargs):
        title = kwargs.pop('title', "CUIDADO")
        self.__super.__init__(
                Text(message, align='center'),
                title=title,
                buttons_and_results=buttons,
                must_quit=True,
                height=None,
                attr_style="dialog.warning",
                title_attr_style="dialog.warning.title",
                button_normal_attr="dialog.warning.button",
                button_focus_attr="dialog.warning.button.focus",
                **kwargs
            )
#}}}

class SingleMessageDialog(_MsgDialog):#{{{

    def __init__(self, message, message_width=False):
        self.__super.__init__(Text(message, align='center'))
        self.height = None
        if message_width:
            self.width = len(message) + 2
        self.attr_style = "dialog.singlemessage"
#}}}
class PasswordInputBox(InputBox):#{{{

    def get_text(self):
        return self._caption, self._attrib

    # Hide password in object representation
    # like in exceptions 
    def _repr_words(self):
        return self.__super._repr_words()[:-1] + [
            repr('*'*len(self._edit_text))] + [
            'multiline'] * (self.multiline is True)
#}}}
class PasswordDialog(Dialog):#{{{

    def __init__(self, for_action=None):#{{{
        self.user_input = InputBox(align="right", max_length=3)
        connect_signal(self.user_input, 'edit-done', lambda w,c: self.pile.set_focus(1))
        connect_signal(self.user_input, 'edit-cancel', self.cancel)
        self.pass_input = PasswordInputBox(align="right")
        connect_signal(self.pass_input, 'edit-done', lambda w,c: self.quit())
        connect_signal(self.pass_input, 'edit-cancel', self.cancel)

        self.pile = Pile([
            Columns([Text(("dialog.password.label", "Vendedor: "), align="right"),
                     ('fixed', 3, AttrMap(self.user_input, "dialog.password.value",
                                          "dialog.password.value.focus"))]),
            Columns([Text(("dialog.password.label", "Clave: "), align="right"),
                     ('fixed', 3, AttrMap(self.pass_input, "dialog.password.value",
                                          "dialog.password.value.focus"))]),
        ])

        w = Padding(self.pile, align='center', width=13)

        self.__super.__init__(w, [None],
                              title="PERMISO DE SUPERVISOR",
                              subtitle=for_action,
                              height=None,
                              width=25)
        self.attr_style = "dialog.password"
        self.title_attr_style = "dialog.password.title"
        self.subtitle_attr_style = "dialog.password.action"
#}}}
    def cancel(self, *w):#{{{
        self.dialog_result = '<cancelled>'
        self.quit()
#}}}
    def run(self):#{{{
        retval = self.__super.run()
        if retval is not None:
            return retval
        codigo_vendedor = self.user_input.get_edit_text()
        vendedor = get_current_config().vendedores.get(codigo_vendedor)
        if vendedor and 'pass' in vendedor:
            passwd = self.pass_input.get_edit_text()
            return vendedor.get('pass') == md5(codigo_vendedor+'|'+passwd).hexdigest()
        return False#}}}
#}}}

class MenuItem(WidgetWrap):#{{{

    def __init__(self, label, callback=None, args=()):
        self.cb = callback
        self.args = args
        if not isinstance(label, Text):
            label = Text(label)
        self.__super.__init__(label)

    def selectable(self):
        return self.cb is not None

    def keypress(self, size, key):
        if key == "enter":
            self.activate()
        return key

    def activate(self):
        return self.cb(*self.args)
#}}}
class Menu(Dialog):#{{{

    def __init__(self, menu_items, focus_item=0, **kwargs):#{{{
        # menu items: ( (text, attr), (callback, args), shortcut )
        self.item_list = SimpleListWalker([])
        listbox = ListBox(self.item_list)
        self.__super.__init__(listbox, keypress=self.on_keypress, **kwargs)

        self.attr_style = 'dialog.menu'
        self.title_attr_style = 'dialog.menu.title'
        self.shortcuts = {}

        def wrap(callback):
            if callback:
                def w(*args):
                    self.install_callback(callback, args)
                    self.quit()
                w.__name__ = callback.__name__
                w.__doc__ = callback.__doc__
                return w
            return None


        for item in menu_items:
            tag_attr = item[0]
            if len(item) > 1:
                ca = item[1]
                if isinstance(ca, tuple):
                    if len(ca) == 2:
                        cb, args = ca
                    else:
                        cb, args = ca, ()
                else:
                    cb = ca
                    args = ()
                if not callable(cb):
                    raise ValueError("You must pass a callable callback")
            else:
                cb, args = None, ()
            self.item_list.append(AttrMap(MenuItem(tag_attr, wrap(cb), args),
                                  'dialog.menu.item', 'dialog.menu.item.focus'))
            if len(item) > 2:
                self.shortcuts[item[2]] = len(self.item_list) - 1

        self.item_list.set_focus(focus_item)
#}}}
    def on_keypress(self, key):#{{{
        if key == "esc":
            self.quit()
        elif key in self.shortcuts:
            self.item_list[self.shortcuts[key]].original_widget.activate()
        return key
#}}}
#}}}

class SearchBox(InputBox):#{{{

    def selectable(self):
        return False

    def on_edit_cancel(self, widget):
        pass

    def filter_input(self, text):
        return text.upper()
#}}}
class SearchListItem(Columns, metaclass=MetaSuper):#{{{

    _search_box = None
    selected = False

    def set_search_box(self, search_box):
        self._search_box = search_box

    def selectable(self):
        return True

    def keypress(self, size, key):
        if self._search_box:
            if command_map[key] not in ('cursor up', 'cursor down',\
                'cursor page up', 'cursor page down'):
                return self._search_box.keypress(size, key)
        return key
#}}}
class SearchDialog(Dialog):#{{{
    title = "SearchDialog"
    subtitle = "GenericWindow"
    _items = []

    def __init__(self, **kwargs):#{{{

        self.search_box = SearchBox()
        self.items_count = Text("", align='right')

        self.search_items = SimpleListWalker(self._null_list_item())
        connect_signal(self.search_items, "modified", self._update_items_count)
        self.search_list = ListBox(self.search_items)

        connect_signal(self.search_box, "edit-done", self.on_edit_done)
        connect_signal(self.search_box, "edit-cancel", lambda w: self.quit())
        connect_signal(self.search_box, "change", lambda sb, term: self.set_search_term(term))

        self._constr = self.get_item_constructor()

        self.multiple_selection = kwargs.pop('multiple_selection', False)
        self._selected_items = OrderedSet([])

        opts = {
            'height': kwargs.get('height', None),
            'width': kwargs.get('width', ('relative', 90)),
            'title': kwargs.get('title', self.title),
            'subtitle': kwargs.get('subtitle', self.subtitle),
            'compact_header': kwargs.get('compact_header', True),
        }
        kwargs.update(opts)

        self.pile = Pile([
            ('fixed', 15, AttrMap(self.search_list, 'dialog.search.item')),
            Columns([
                AttrMap(self.search_box, 'dialog.search.input'),
                ('fixed', 1, AttrMap(Divider(), 'dialog.search.input')),
                ('fixed', 4, AttrMap(self.items_count, 'dialog.search.input')),
                ]),
            ], focus_item=0)

        self.__super.__init__(self.pile, **kwargs)

        self.attr_style = "dialog.search"
        self.title_attr_style = "dialog.search.title"
        self.subtitle_attr_style = "dialog.search.subtitle"
#}}}
    def keypress(self, key):#{{{
        if key == 'insert' and self.multiple_selection:
            if self.pile.get_focus().original_widget is self.search_list:
                wid, pos = self.search_list.get_focus()
            else:
                pos = 0
            current_item = self.search_items[pos]
            article = self.get_data_for(pos)
            current_item.original_widget.selected = not current_item.original_widget.selected
            if current_item.original_widget.selected:
                current_item.attr_map = {None: 'dialog.search.item.selected'}
                current_item.focus_map = {None: 'dialog.search.item.focus.selected'}
                self._selected_items.add(article)
            else:
                current_item.attr_map = {None: 'dialog.search.item'}
                current_item.focus_map = {None: 'dialog.search.item.focus'}
                self._selected_items.discard(article)

            self.search_list.set_focus(pos+1)
            self._update_items_count()
#}}}
    def on_edit_done(self, widget, text):#{{{
        result = []
        if self.pile.get_focus().original_widget is self.search_list:
            wid, pos = self.search_list.get_focus()
        else:
            pos = 0
        if self.multiple_selection:
            result = list(self._selected_items)
        if len(result) < 1:
            if self.get_data_for(pos):
                result = [self.get_data_for(pos)]
        self.dialog_result = result
        self.quit()
#}}}
    def set_search_term(self, term):#{{{
        self._clear_search_items()
        query = self.get_query(term)
        if query is not None:
            self._items = tuple(query[:150])
            if len(self._items) > 0:
                l_items = list(map(self._constr, self._items))
                for i in l_items:
                    i.set_search_box(self.search_box)
                self.search_items.extend([AttrMap(i, 'dialog.search.item',\
                    'dialog.search.item.focus') for i in l_items])
                if self.multiple_selection:
                    for a in (self._selected_items & set(self._items)):
                        idx = self._items.index(a)
                        self.search_items[idx].attr_map = {None: 'dialog.search.item.selected'}
                        self.search_items[idx].focus_map = {None: 'dialog.search.item.focus.selected'}
                        self.search_items[idx].original_widget.selected = True
                return
        self.search_items.extend(self._null_list_item())
#}}}
    def _clear_search_items(self):#{{{
        self.search_items[:] = []
        self._update_items_count()
#}}}
    def _null_list_item(self):#{{{
        null = SearchListItem([Text("")])
        null.set_search_box(self.search_box)
        return [null]
#}}}
    def _update_items_count(self):#{{{
        if len(self.search_items) > 149:
            self.items_count.set_text("+150")
        else:
            self.items_count.set_text("")
        selected_count = len(self._selected_items)
        if selected_count > 0:
            self._title_widget.set_text(self.title + (" (+%d)" % selected_count))
        else:
            self._title_widget.set_text(self.title)

#}}}
    def get_data_for(self, index):#{{{
        try:
            return self._items[index]
        except IndexError as e: # index out of range
            return None
#}}}
    def get_query(self, term):#{{{
        raise NotImplementedError("This must be implemented by subclass")
#}}}
    def get_item_constructor(self):#{{{
        return None
#}}}
#}}}

class WaitFiscalAnswer(Dialog):#{{{

    def __init__(self, filename, title=None, timeout=10, interval=0.1):#{{{
        self.filename = filename
        self.interval = interval
        self.timeout = timeout

        if title is None:
            title = "IMPRIMIENDO"

        msg = Text("Esperando la respuesta de la Impresora Fiscal ...", align='left')
        self.eta = Text("", align='left')

        self.dummy = Text("")
        self.dummy._selectable = True
        self.dummy.keypress = lambda s,k : None

        self.buttons = Columns([
            AttrMap(Button("Seguir esperando", on_press=self.remove_buttons),'dialog.button', 'dialog.button.focus'),
            AttrMap(Button("Cancelar Impresion", on_press=lambda *w: self.quit()), 'dialog.button', 'dialog.button.focus'),
        ], dividechars=1)

        self.content = Pile([
            msg,
            Divider(),
            self.eta,
            self.dummy,
        ])

        self.__super.__init__(
            self.content,
            title=title,
            attr_style='dialog.waitfiscal',
            title_attr_style='dialog.waitfiscal.title',
            height=None,
            width=60,
        )
#}}}
    def run(self):#{{{
        self._start_time = datetime.now()
        self._last_option = time.time()
        return self.__super.run(alarm=(self.interval, self._alarm))
#}}}
    def _alarm(self, main_loop, user_data=None):#{{{
        if not os.path.exists(self.filename):
            self.update_status()
            main_loop.set_alarm_in(self.interval, self._alarm)
            return
        else:
            self.dialog_result = True
            self.quit()
#}}}
    def update_status(self):#{{{
        self.eta.set_text("Tiempo: %s" % get_elapsed_time(self._start_time))
        if type(self.content.widget_list[-1]) is Text:
            if (time.time() - self._last_option) > self.timeout:
                self.add_buttons()
#}}}
    def add_buttons(self):#{{{
        self.content.widget_list[-1] = self.buttons
        self.content.set_focus(self.buttons)
#}}}
    def remove_buttons(self, *btn):#{{{
        self._last_option = time.time()
        self.content.widget_list[-1] = self.dummy
        self.content.set_focus(self.dummy)
#}}}
#}}}

class SingleMessageWaiter(_MsgDialog):#{{{

    def __init__(self, message, message_width=False):#{{{
        self.__super.__init__(Text(message, align='center'))
        self.height = None
        if message_width:
            self.width = len(message) + 2
        self.attr_style = 'dialog.singlemessage'
#}}}
    def run(self):#{{{
        pile_widgets = [self._content]
        if self.button_widgets:
            pile_widgets.append(("flow", Columns(self.button_widgets, dividechars=1)))
        self._pile = w = Pile(pile_widgets)

        header = []
        if self.title is not None:
            self._title_widget = Text(self.title, align='center')
            header.append(('flow', AttrMap(self._title_widget, self.title_attr_style)))
        if self.subtitle is not None:
            header.append(('flow', AttrMap(Text(self.subtitle, align='center'), self.subtitle_attr_style)))

        if header:
            if not self._compact_header:
                header.append(("fixed", 1, SolidFill()))
            header.append(w)
            w = Pile(header)

        if self.with_border:
            w = LineBox(w)
#            w = Border(w, title=self.title, title_attr=self.title_attr_style, attr=self.attr_style)
        w = Overlay(w, self.top_widget,
                    align=self.align,
                    valign=self.valign,
                    width=self.width,
                    height=self.height,
                    min_width=self.min_width,
                    min_height=self.min_height)

        w = AttrMap(w, self.attr_style)

        loop = get_main_loop()
        loop.widget = w
        loop.draw_screen()
        loop.widget = self.top_widget
#}}}
#}}}

# FIXME: Circular dependencies
from nobix.utils import get_elapsed_time, OrderedSet

# vim:foldenable:foldmethod=marker
