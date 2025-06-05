# qt6imageviewer
Image viewer.

Requirements:
- python3
- pyqt6
- PIL for supporting more image formats (optional but recommended)
- config file cfg_imageviewer.py for some application options

Features:
- colour picker - clipboard (the colour in the form #rrggbb will be copied in the clipboard)
- colour picker - dialog (a dialog will appear)
- animated images
- zoom
- rotating (except for animated images)
- lateral panel
- load dialog
- save dialog (image to png or jpg formats)
- can launch three custom command
- basic image info

About the custom actions: from the toolbar can be launched three custom actions. Their names can be changed tin the config file. The bash scripts executed by those actions are: tool1.sh, tool2.sh and tool3.sh. The current visualized image full path will be passed to those bash scripts as argument.

  ![My image](https://github.com/frank038/qt6imageviewer/blob/main/screenshot1.jpg)
