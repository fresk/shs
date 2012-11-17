#!/bin/bash
SCRIPTPATH=`dirname $0`
echo $SCRIPTPATH

KIVY_DPI=264 KIVY_METRICS_DENSITY=2 python main.py --size=1024x768
