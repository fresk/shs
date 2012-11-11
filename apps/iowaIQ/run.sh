#!/bin/bash
SCRIPTPATH=`dirname $0`
echo $SCRIPTPATH
python ${SCRIPTPATH}/main.py --size=1024x768
