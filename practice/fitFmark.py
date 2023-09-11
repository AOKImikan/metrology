#!/usr/bin/env python3
import os
import argparse
import cv2

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-file', dest='inputFile',
                        type=str, default='', 
                        help='Input file name (*.jpg)')
    parser.add_argument('-b', '--black-and-white', dest='blackAndWhite',
                        action='store_true', default=False, 
                        help='Convert to black-and-whilte')
    return parser.parse_args()

def run(args):
    image = None
    if os.path.exists(args.inputFile):
        wname = 'window1'
        cv2.namedWindow(wname, cv2.WINDOW_NORMAL)
        image = cv2.imread(args.inputFile, cv2.IMREAD_COLOR)
        if args.blackAndWhite:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        cv2.imshow(wname, image)
        cv2.waitKey(0)
    else:
        print(f'File {args.inputFile} does not exist')
    cv2.destroyAllWindows()

if __name__ == '__main__':
    args = parseArgs()
    run(args)
    
