#!/usr/bin/env python3

import os
import argparse
import pmm

def parseArgs():
    parser = argparse.ArgumentParser()
    return parser.parse_args()

def showModuleDesign():
    m = pmm.Rd53aModule()
    m.dump()

if __name__ == '__main__':
    args = parseArgs()
    showModuleDesign()
