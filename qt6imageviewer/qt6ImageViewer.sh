#!/bin/bash

thisdir=$(dirname "$0")
cd $thisdir
if [[ $# -eq 0 ]]; then
  python3 qt6ImageViewer.py &
else
  python3 qt6ImageViewer.py "$1" &
fi
cd $HOME
