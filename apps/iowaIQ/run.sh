#!/bin/bash
SCRIPTPATH=`dirname $0`
echo $SCRIPTPATH

KIVY_DPI=320 KIVY_METRICS_DENSITY=2 python main.py --size=1024x768
