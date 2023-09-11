#!/usr/bin/env python3
#-----------------------------------------------------------------------
# checkComponentView.py
#-----------------------------------------------------------------------

import os, sys
import logging

from pmm.componentView import ComponentViewConfig

def check(fname):
    config = ComponentViewConfig()
    x = config.read(fname)
    config.dump()
    
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    check(sys.argv[1])
    
