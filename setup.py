#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from os.path import join
from glob import glob
from setuptools import setup, find_packages

NAME = "Nobix"
VERSION = "0.0.9"
DB_REPO = "dbmigrate"

def check_noegg_dependencies():
    from pkg_resources import parse_version

    mod_not_installed = u"El módulo '%s' es necesario para el funcionamiento del programa, hay que instalarlo"
    mod_old_version = u"Encontré el módulo '%s' pero la version minima requerida es %s"

    pycups_version = "1.9.49"
    try:
        mod = __import__('cups')
        mod.require(pycups_version)
    except ImportError:
        print mod_not_installed % ('cups',)
        sys.exit(1)
    except RuntimeError:
        print mod_old_version % ('cups', pycups_version)
        sys.exit(1)

    # rsvg
    gtk_version = (2, 20, 1)
    try:
        mod = __import__('gtk')
    except ImportError:
        print mod_not_installed % ('gtk',)
        sys.exit(1)
    if mod.gtk_version < gtk_version:
        print mod_old_version % ('gtk', ".".join(gtk_version))

    pycairo_version = '1.8.10'
    try:
        mod = __import__('cairo')
    except ImportError:
        print mod_not_installed % ('cairo',)
        sys.exit(1)
    if parse_version(pycairo_version) > parse_version(mod.cairo_version_string()):
        print mod_old_version % ('cairo', pycairo_version)


def datafiles(df):
    ret = []
    for dest, path in df:
        if not dest.startswith("/"):
            dest = join(sys.prefix, dest)
        if isinstance(path, (list, tuple)):
            paths = []
            for p in path:
                paths.extend(glob(p))
        else:
            paths = glob(path)
        ret.append((dest, paths))
    return ret

def get_config_db_uri(location):
    import imp
    try:
        fp, filename, description = imp.find_module('nobix', [location])
        nobix_mod = imp.load_module('nobix', fp, filename, description)
        fp, filename, description = imp.find_module('config', nobix_mod.__path__)
        config_mod = imp.load_module('nobix.config', fp, filename, description)
    except ImportError:
        return None
    try:
        config = config_mod.load_config()
    except SystemExit:
        return None
    return config.database_uri

def upgrade_db(uri):
    from migrate.versioning import api
    from migrate.exceptions import DatabaseNotControlledError, InvalidRepositoryError
    try:
        current_db_version = api.db_version(uri, DB_REPO)
        current_repo_version = api.version(DB_REPO)
    except DatabaseNotControlledError:
        api.version_control(uri, DB_REPO, version='1')
        current_db_version = api.db_version(uri, DB_REPO)
        current_repo_version = api.version(DB_REPO)
    except InvalidRepositoryError:
        raise SystemExit(
            u"WARNING: Existe un error en el repositorio de la base de datos (%s)" % DB_REPO
        )

    if current_db_version <= current_repo_version:
        api.upgrade(uri, DB_REPO)
        print u"done"
    else:
        raise SystemExit(
            u"\n"
            u"WARNING: La base de datos parece más nueva que de lo que debería ser"
            u"WARNING: mmm ....  que raro, esto no debería suceder"
        )

def try_upgrade_db():
    "This must be run at 'install' time and after setup() function"
    import os.path
    from copy import copy
    from pkg_resources import Requirement, WorkingSet, get_distribution, DistributionNotFound

    try:
        migrate_dist = get_distribution('sqlalchemy-migrate>=0.6')
        migrate = __import__('migrate')
    except DistributionNotFound, ImportError:
        raise SystemExit(
            u"\n"
            u"WARNING: 'sqlalchemy-migrate' not found, this is a bug in setup.py file!\n"
            u"WARNING:  El sistema se ha actualizado pero NO la base de datos. :("
        )

    cwd = os.path.dirname(os.path.abspath(__file__))
    sys_path = copy(sys.path)
    if cwd in sys_path:
        sys_path.remove(cwd)
    req = Requirement.parse(NAME)
    ws = WorkingSet(sys_path)
    old_nobix = ws.find(req)
    new_nobix = get_distribution(NAME)

    if not old_nobix:
        return

    if old_nobix.parsed_version < new_nobix.parsed_version:
        database_uri = get_config_db_uri(old_nobix.location)
        if database_uri:
            print u"\nUpgrading Nobix database %s -> %s ..." % (old_nobix.version, new_nobix.version),
            upgrade_db(uri=database_uri)
        else:
            raise SystemExit(
                u"\n"
                u"WARNING: No se puede obtener el nombre de la base de datos.\n"
                u"WARNING: El sistema se ha actualizado pero NO la base de datos. :("
            )

    elif old_nobix.parsed_version == new_nobix.parsed_version:
        print u"Reinstalling Nobix %s" % (new_nobix.version)
    else:
        print u"We don't handle Nobix downgrade (installed %s)" % old_nobix.version

if 'install' in sys.argv:
    check_noegg_dependencies()

setup(
    name = NAME,
    version = VERSION,
    url = u"http://www.rocctech.com.ar/nobix",
    author = u"Augusto Roccasalva",
    author_email = u"augusto@rocctech.com.ar",
    license = u"GPL",
    packages = find_packages(),

    entry_points = {
        'console_scripts': [
            'nobix = nobix.main:main',
        ],
    },

    data_files = datafiles([
        ('share/nobix', 'data/config.py'),
        ('share/nobix/templates', ['data/templates/*.mako', 'data/templates/README']),
        ('share/nobix/scripts', 'scripts/*'),
        ('share/nobix/icons', 'data/icons/*'),
    ]),

    install_requires = [
        #'distribute>=0.6.10',
        'python-dateutil>=1.4.1',
        'SQLAlchemy>=0.7.0',
        'Elixir>=0.7.0',
        #'sqlalchemy-migrate>=0.7',
        'urwid==0.9.9.1',
        'Mako>=0.3.2',
        'Unidecode>=0.04.1',
        'pyusb',
    ],
)

if 'install' in sys.argv:
    try_upgrade_db()
