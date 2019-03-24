#!/bin/bash

ps aux | grep 'jssrv.py' | grep -v 'grep'

if [ $? -eq 0 ]; then
    MAIN_PID=`ps aux | grep 'jssrv.py' | grep -v 'grep' | awk '{print $2}'`
    kill -9 $(ps -ef | grep $MAIN_PID | grep -v 'grep' | awk '{print $2}')
    if [ $? -eq 0 ]; then
        echo "Kill phantomjs service, done!"
        sleep 3
        sh /sources/python/xxx/phantomjs_service/startup.sh
        echo "Restart phantomjs service, done!"
    else
        echo "Kill operation failed, please check..."
    fi
else
    sh /sources/python/xxx/phantomjs_service/startup.sh
    echo "Restart phantomjs service, done!"
fi
