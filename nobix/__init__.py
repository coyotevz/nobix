#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pkg_resources import get_distribution, DistributionNotFound

try:
    __version__ = get_distribution("Nobix").version
except DistributionNotFound:
    __version__ = "dev"
