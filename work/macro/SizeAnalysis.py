#!/usr/bin/env python3
import os, sys
import argparse
import re
import math
import cv2
import numpy as np
import pickle
#import matplotlib.pyplot as plt
#import math
#import tkinter as tk
#from PIL import Image, ImageTk
import logging

import pmm
import data_pcb
import LinePointPlot
from scipy import linalg
from pmm.model import *

logger = logging.getLogger(__name__)

def lineDiff(self, tag, tag1, tag2, line_vh):
    """tag = tag1 - tag2"""
    key, line1 = f'{tag1}_line', None
    if line1 == None:
        if key in self.outData.keys():
            line1 = self.outData[key]
        elif key in self.inData.keys():
            line1 = self.inData[key]
    key, line2 = f'{tag2}_line', None
    if line2 == None:
        if key in self.outData.keys():
            line2 = self.outData[key]
        elif key in self.inData.keys():
            line2 = self.inData[key]
    #
    if not (line1 and line2):
        self.outData[tag] = None
        logger.warning(f'Cannot calculate the distance between lines')
        logger.warning(f'  Line[{tag1}]={line1}, Line[{tag2}]={line2}')
        return
    
    x, y = 0.0, 0.0
    if line_vh == 'v':
        x, y = line1.xAtY(0.0), 0.0
        x1, y1 = line1.xAtY(20.0), 20.0
        x2, y2 = line1.xAtY(-20.0), -20.0
        dd = abs(x1 - x2)/2.0
    if line_vh == 'h':
        x, y = 0.0, line1.yAtX(0.0)
        x1, y1 = 20.0, line1.xAtY(20.0)
        x2, y2 = -20.0, line1.xAtY(-20.0)
        dd = abs(y1 - y2)/2.0
    p = Point([x, y])
    d = line2.distance(p)
    logger.debug(f' L-P distance ({line2}-{p.position}): {d}')
    dd = 0.0
    self.outData[tag] = MeasuredValue(tag, d, dd)
