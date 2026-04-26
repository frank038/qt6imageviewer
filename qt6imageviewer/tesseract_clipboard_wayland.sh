#!/bin/bash

sleep 1
SEL_STR=$(grim -g "$(slurp)" -t png /tmp/tcw.png)

if [ ! -z "/tmp/tcw.png" ]; then
convert /tmp/tcw.png -threshold 75% - | tesseract stdin stdout --psm 12 | wl-copy
rm /tmp/tcw.png
notify-send -e -t 3000 "Selection saved"
else
notify-send -e -t 3000 "No selection"
fi