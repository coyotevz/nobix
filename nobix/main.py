#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import signal
import os
from hashlib import md5
from getpass import getpass
import traceback
from datetime import datetime
import xmlrpc.client
import socket

import urwid
from sqlalchemy.exc import SQLAlchemyError

from nobix.config import load_config
from nobix.models import db
#from nobix.db import setup_db, Session
from nobix.ui import MainFrame
from nobix.mainloop import NobixMainLoop
from nobix.utils import get_hostname, get_username
from nobix import __version__

def run_nobix(database_uri=None):

    config = load_config()
    if database_uri:
        config.database_uri = database_uri

    #setup_db(config.database_uri)
    db.configure(config.database_uri)
    sout = open(os.path.expanduser("~/.nobix.log"), "a")

    top = MainFrame()

    loop = NobixMainLoop(
        top,
        handle_mouse=None,
        unhandled_input=quit_on_f10,
        palette=[(k,) + v for k, v in config.color_palette.items()],
    )
    loop.set_alarm_in(1, top.doc_footer.update_date)

    def _try_save_current_document(signum=None, frame=None):
        try:
            top.doc_header.save_current_document()
        except SQLAlchemyError as db_error:
            print(str(datetime.now()), file=sout)
            print("Error in save_current_document()", file=sout)
            print("".join(traceback.format_exc()), file=sout)
            print("\n\nOriginal Exception was:", file=sout)

    try:
        old = loop.screen.tty_signal_keys('undefined', 'undefined',
                'undefined', 'undefined', 'undefined')
        signal.signal(signal.SIGTERM, _try_save_current_document)
        loop.run()
    except Exception as e:
        exc_info = sys.exc_info()
        print(str(datetime.now()), file=sout)
        print("".join(traceback.format_exception(*exc_info)), file=sout)
        raise exc_info[0](exc_info[1]).with_traceback(exc_info[2])
    finally:
        _try_save_current_document()
        loop.screen.tty_signal_keys(*old)
        sout.close()

def quit_on_f10(key):
    if key == 'f10':
        quit()

def quit():
    raise urwid.ExitMainLoop()

def create_password(code=None, password=None):
    """Create md5sum for a salesman-code/password key."""
    if not code:
        code = input('Código Vendedor: ')
    if not password:
        password = getpass('Contraseña: ')
    if password == '':
        sys.exit("ERROR: La contraseña debe contener almenos un digito")
    password2 = getpass('Repetir contraseña: ')
    if password == password2:
        print("md5:", md5(code+'|'+password).hexdigest())
        sys.exit(0)
    sys.exit("ERROR: Las contraseñas no coinciden")

def _make_ns(database_uri=None):
    from nobix.config import load_config
    from nobix.db import setup_db, Session
    from nobix.models import Cliente, Articulo, ItemDocumento, Documento,\
                             Cache, Tasa

    config = load_config()
    if database_uri:
        config.database_uri = database_uri
    setup_db(config.database_uri)
    session = Session()

    del load_config, setup_db, Session
    return locals()

def run_shell(database_uri=None):
    banner = "Interactive Nobix(%s) Shell" % __version__
    namespace = _make_ns(database_uri)
    try:
        import IPython
    except ImportError:
        pass
    else:
        if IPython.__version__ >= '0.11':
            from IPython.frontend.terminal.embed import InteractiveShellEmbed
            sh = InteractiveShellEmbed(banner1=banner)
        else:
            sh = IPython.Shell.IPShellEmbed(banner=banner, argv=[])
        sh(global_ns={}, local_ns=namespace)
        return
    from code import interact
    interact(banner, local=namespace)
    session.commit()

def usage():
    print("""
    Uso: nobix [comando]

    Si [comando] no se especifica se lanza en programa normalmente.

    [comando] puede se uno de los siguientes:

    create_password   -- Genera la contraseña md5 para un vendedor.
    shell             -- Abre una consola con algunos modulos pre-cargados.
    usage,-h,--help   -- Muestra este mensaje de ayuda.

    --database-uri    -- URI de la base de datos como la recibe SQLAlchemy
    """)

def main(args=None):
    if args is None:
        args = sys.argv[1:]

    os.umask(0o002)

    if '--database-uri' in args:
        idx = args.index('--database-uri')
        database_uri = args.pop(idx+1)
        args.pop(idx)
    else:
        database_uri = None

    if len(args) == 0:
        return run_nobix(database_uri)
    elif args[0] == "create_password":
        return create_password()
    elif args[0] == "shell":
        return run_shell(database_uri)
    elif args[0] in ("usage", "-h", "--help"):
        usage()
    else:
        print("ERROR: Argumentos incorrectos")
        usage()

if __name__ == '__main__':
    main()
