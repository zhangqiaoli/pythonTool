#!/bin/sh
rm tmp -rf
mkdir tmp
svn export . tmp/alwayson
rm tmp/alwayson/publish.sh -f
cd tmp
tar -zcvf alwayson.tar.gz alwayson
mv alwayson.tar.gz ..
cd ..
rm tmp -rf
echo "OK"
