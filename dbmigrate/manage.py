#!/usr/bin/env python
from migrate.versioning.shell import main

try:
    from nobix.config import load_config
    URL = load_config().database_uri
except ImportError:
    URL = 'postgresql://nobix:nobix@localhost/nobix'

main(url=URL, repository='dbmigrate', debug='False')
