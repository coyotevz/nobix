# -*- coding: utf-8 -*-

import json
import socketserver

import usb.core
import usb.util


class LabelerBridgeError(Exception):
    pass


def _custom_match(e):
    return usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT


def send_to_labeler(idVendor, idProduct, message):

    dev = usb.core.find(idVendor=idVendor, idProduct=idProduct)
    if dev is None:
        raise LabelerBridgeError('No se encontrol el dispositivo')

    reattach = False
    if dev.is_kernel_driver_active(0):
        reattach = True
        dev.detach_kernel_driver(0)

    # set the active configuration. With no arguments, the first configuration
    # will be the active
    dev.set_configuration()

    # get an endpint instance
    cfg = dev.get_active_configuration()
    interface = cfg[(0, 0)]

    # get an endpoint instance
    ep = usb.util.find_descriptor(interface, custom_match=_custom_match)

    if ep is None:
        raise LabelerBridgeError("Error en find_descriptor()")

    try:
        ep.write(message)
    except usb.core.USBError:
        raise LabelerBridgeError("USB Error")
    except:
        raise LabelerBridgeError("write failed")

    usb.util.dispose_resources(dev)

    if reattach:
        dev.attach_kernel_driver(0)


class JSONLabelerHandler(socketserver.BaseRequestHandler):

    def handle(self):
        SIZE = 16384
        e = None
        response = {}
        json_data = self.request.recv(SIZE)

        try:
            data = json.loads(json_data)
        except:
            json_data += self.request.recv(SIZE)
            data = json.loads(json_data)

        try:
            send_to_labeler(**data)
            response['status'] = 'ok'
        except Exception as err:
            response['status'] = 'error'
            response['type'] = err.__class__.__name__
            if err.args[0]:
                response['message'] = err.args[0]
            e = err

            #with open('/home/augusto/error.log', 'w') as out:
            #    out.write("Error:\n")
            #    out.write("len(json_data): {}\n".format(len(json_data)))
            #    out.write("json_data:\n")
            #    out.write(str(json_data) + "\n")


        response_data = json.dumps(response)
        self.request.send(bytes(response_data, 'utf-8'))

        if e is not None:
            raise e


if __name__ == "__main__":
    HOST, PORT = '0.0.0.0', 9999

    try:
        # Create the server binding to localhost:9999
        with socketserver.TCPServer((HOST, PORT), JSONLabelerHandler) as server:
            # Activate the server, this will keep running until you interrupt the
            # program
            server.serve_forever()
    except KeyboardInterrupt:
        pass
