#!/bin/bash

TMP_FOLDER="/tmp"

sleep 1
cd $TMP_FOLDER
SEL_STR=$(scrot -s -e 'echo $n')

if [ ! -z "${SEL_STR}" ]; then
# # xorg
# tesseract $SEL_STR stdout --psm 12 | xclip -selection clipboard
convert $SEL_STR -threshold 75% - | tesseract stdin stdout --psm 12 | xclip -selection clipboard

rm $SEL_STR
notify-send -e -t 3000 "Selection saved"
else
notify-send -e -t 3000 "No selection"
fi