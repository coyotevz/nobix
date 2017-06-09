# -*- coding: utf-8 -*-

import json
import socketserver


class LabelerBridgeError(Exception):
    pass


def _custom_match(e):
    return usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT


def send_to_labeler(idVendor, idProduct, message):
    import usb.core
    import usb.util

    dev = usb.core.find(idVendor=idVendor, idProduct=idProduct)
    if dev is None:
        raise LabelerBridgeError('No se encontrol el dispositivo')

    try:
        dev.attach_kernel_driver(0)
    except usb.core.USBError as error:
        pass
    # detach current kernel driver
    try:
        dev.detach_kernel_driver(0)
    except usb.core.USBError as error:
        if error.args[0] != 'Entity not found':
            raise LabelerBridgeError("Ocurrio un error desconocido en detach_kernel_driver()")

    # set the active configuration. With no arguments, the first configuration
    # will be the active
    dev.set_configuration()

    interface = list(dev[0])[0]

    # get an endpoint instance
    ep = usb.util.find_descriptor(interface, custom_match=_custom_match)

    if ep is None:
        raise LabelerBridgeError("Error en find_descriptor()")

    ep.write(message)


class JSONLabelerHandler(socketserver.BaseRequestHandler):

    def handle(self):
        response = {}
        json_data = self.request.recv(1024)

        try:
            data = json.loads(json_data)
            send_to_labeler(**data)
            response['status'] = 'ok'
        except Exception as err:
            response['status'] = 'error'
            response['type'] = err.__class__.__name__
            if err.args[0]:
                response['message'] = err.args[0]

        response_data = json.dumps(response)
        self.request.send(bytes(response_data, 'utf-8'))


if __name__ == "__main__":
    HOST, PORT = 'localhost', 9999

    # Create the server binding to localhost:9999
    with socketserver.TCPServer((HOST, PORT), JSONLabelerHandler) as server:
        # Activate the server, this will keep running until you interrupt the
        # program
        server.serve_forever()
