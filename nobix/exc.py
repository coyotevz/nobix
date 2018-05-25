#!/usr/bin/env python
# -*- coding: utf-8 -*-

class NobixError(Exception):
    pass

class NobixPrinterError(NobixError):
    pass

class NobixPrintError(NobixPrinterError):
    pass

class NobixModelError(NobixError):
    pass

class NobixBadDateError(NobixError):
    pass

class NobixBadCuitError(NobixError):
    pass
