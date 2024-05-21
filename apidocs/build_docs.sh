#!/bin/bash

echo $BASH_SOURCE

HERE_DIR=`dirname "$BASH_SOURCE"`
ROOT_DIR=`realpath $HERE_DIR/../..`

echo $ROOT_DIR

cd $ROOT_DIR/apidocs


sphinx-build -a -b html $ROOT_DIR/apidocs $ROOT_DIR/public/
