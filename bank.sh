#!/bin/bash
if [ $# !=  1 ]
then
        echo "Need enter 1 parameter: ./script dir"
else
    appdir=$1
    # get file
    cd $appdir
    /usr/bin/wget -O bank.xml http://www.cbr.ru/scripts/XML_daily.asp
    # update file
    /usr/bin/python manage.py bankupdate
fi
