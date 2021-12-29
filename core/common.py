#!/usr/bin/env python3
# Copyright (c) 2021 Silas Cutler, silas.cutler@gmail.com (https://silascutler.com/)
# See the file 'COPYING' for copying permission.

import logging

log = logging.getLogger("obj_hypervisor")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)    
log.addHandler(handler)
log.setLevel(logging.DEBUG)


class detux(object):
    def __init__(self):
        pass
        
