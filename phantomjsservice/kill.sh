#!/bin/bash

MAIN_PID=`ps aux | grep 'jssrv.py' | grep -v 'grep' | awk '{print $2}'`

kill -9 $(ps -ef | grep $MAIN_PID | grep -v 'grep' | awk '{print $2}')

if [ $? -eq 0 ]; then
    echo "Kill phantomjs service, done!"
else
    echo "Kill operation failed, please check..."
fi
