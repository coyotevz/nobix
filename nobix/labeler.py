# -*- coding: utf-8 -*-

import time
from collections import namedtuple


DEBUG = False


LabelSize = namedtuple("LabelSize", "width height gap")

mm_pt = lambda mm: mm*8
pt_mm = lambda pt: int(pt/8)

safe_margin = sm = 10 # points

label_metrics = lm = {
    # points
    'E1': LabelSize(mm_pt(38), mm_pt(20), mm_pt(2)),
    'E2': LabelSize(mm_pt(60), mm_pt(43), mm_pt(3)),
}

# internal fonts
font_metrics = fm = {
    # points
    '2': (203./17, 14),
    '3': (203./14.5, 17),
    '4': (203./12.7, 20),
    '5': (203./5.6, 48),
}


class LabelerError(Exception):
    pass


def center_line(text, char_width, width):
    "Returns left coordinate for centered line"
    return int( (width - (char_width * len(text))) / 2 )

def word_wrap(text, width, sep=' '):
    text = text.strip()

    if len(text) <= width:
        return [text]
    else:
        if isinstance(sep, basestring):
            sep = [sep]
        i = -1
        for s in sep:
            li = text.rfind(s, 0, width)
            i = max([i, li])

        if i < 0:
            i = width
        l = [text[0:i+1].strip()]
        r = text[i+1:].strip()
        l.extend(word_wrap(r, width, sep))
        return l

class Label1(object):

    def __init__(self, code='', desc='', qty=1):
        self._code = code
        self._desc = desc
        self._qty = qty

    def render(self, size):
        height = size.height - (sm*2)
        width = size.width - (sm*2)

        out = ''
        if DEBUG:
            out += 'X%d,%d,2,%d,%d\n' % (sm, sm, size.width-sm, size.height-sm)
            out += 'LO%d,%d,%d,2\n' % (sm, sm+int(height/2), width)
        if self._code:
            out += self.render_code(sm, sm, height/2, width)

        if self._desc:
            out += self.render_desc(sm, sm+height/2, height/2, width)

        if out:
            out += 'P%d\n' % self._qty

        return out

    def render_code(self, x, y, height, width):
        font, vscale = ( ('5',1) if len(self._code) <= 7 else ('4',2) )
        top = int( ( height - fm[font][1]*vscale ) / 2)
        left = center_line(self._code, fm[font][0], width)
        return 'A%d,%d,0,%s,1,%d,N,"%s"\n' % (x+left, y+top, font, vscale, self._code)

    def render_desc(self, x, y, height, width):
        font, vscale = '2', 1
        w = int(width/fm[font][0])
        lines = word_wrap(self._desc, w, sep=[' ', '.'])[:2]
        vsep = int ( ((fm[font][1]*vscale) / 2) * 2 )
        top = int( (height - (fm[font][1]*vscale*len(lines) + (len(lines)-1)*vsep)) / 2 )
        ret = ''
        for l in lines:
            left = center_line(l, fm[font][0], width)
            ret += 'A%d,%d,0,%s,1,%d,N,"%s"\n' % (x+left, y+top, font, vscale, l.replace('"','\\"'))
            y += fm[font][1]*vscale + vsep
        return ret

class Labeler(object):

    def __init__(self, label_size='E1', speed=3, idVendor=0x1664, idProduct=0x013b):
        self._label_size = label_size
        self._size = label_metrics[label_size]
        self._speed = speed

        self._idVendor = idVendor
        self._idProduct = idProduct

        self._labels = []

    def add_label(self, label):
        self._labels.append(label)

    def render_header(self):
        cmd = []
        cmd.append('I8,1,003')
        cmd.append('ZN')
        cmd.append('q%d' % self._size.width)
        cmd.append('S%d' % self._speed)
        cmd.append('OD')
        cmd.append('JF')
        cmd.append('ZT')
        cmd.append('Q%d,%d' % (self._size.height, self._size.gap))
        cmd.append('N')

        return '\n'.join(cmd) + '\n'

    def render(self):
        out = self.render_header()
        for l in self._labels:
            out += l.render(self._size)
        return out

    def printout(self):
        import usb.core
        import usb.util

        dev = usb.core.find(idVendor=self._idVendor, idProduct=self._idProduct)
        if dev is None:
            raise LabelerError('No se encotro el dispositivo')

        try:
            dev.attach_kernel_driver(0)
        except usb.core.USBError as error:
            pass
        # detech current kernel driver
        try:
            dev.detach_kernel_driver(0)
        except usb.core.USBError as error:
            if error.args[0] != 'Entity not found':
                raise LabelerError("Ocurrio un error desconocido en datach_kernel_driver()")

        # set the active configuration. With no arguments, the first
        # configuration will be the active
        dev.set_configuration()

        interface = list(dev[0])[0]

        # get an endpoint instance
        ep = usb.util.find_descriptor(
                interface, # first interface
                # match the first OUT endpoint
                custom_match = \
                    lambda e: \
                        usb.util.endpoint_direction(e.bEndpointAddress) == \
                        usb.util.ENDPOINT_OUT
             )

        assert ep is not None

        ep.write(self.render().encode('cp850', 'ignore'))

if __name__ == '__main__':
    import sys
    text = sys.argv[1]

    l = Labeler()
    l.add_label(Label1(code=sys.argv[1], desc=sys.argv[2].decode('utf-8')))
    print l.render()
    l.printout()
