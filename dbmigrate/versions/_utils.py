#!/usr/bin/env python
# -*- coding: utf-8 -*-

def get_prev_meta(current_filename):
    import os, glob
    orig_wd = os.getcwd()
    os.chdir(os.path.dirname(os.path.abspath(current_filename)))
    current_filename = os.path.basename(current_filename)
    mods = list(reversed(glob.glob('*.py')))
    os.chdir(orig_wd)
    if current_filename.endswith('c'):
        current_filename = current_filename[:-1]
    prev = mods[mods.index(current_filename)-1]
    prev_mod, ext = os.path.splitext(prev)
    module = __import__(prev_mod)
    return module.meta
