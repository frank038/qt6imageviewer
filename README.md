# qt6imageviewer
Image viewer.

Requirements:
- python3
- pyqt6
- PIL for supporting more image formats (optional but recommended)
- Glycin version 1 or 2 for supporting more image formats (heic/heif, avif); optional; to be setted in the config file
- tesseract for the ocr text recognition (optional): under wayland slurm and grim are also required; under xorg scrot and xclip are also required
- config file cfg_imageviewer.py for some application options

Features:
- colour picker - clipboard (the colour in the form #rrggbb will be copied in the clipboard)
- colour picker - dialog (a dialog will appear)
- animated images
- zoom (from the menu, with the mouse wheel and with the shortcut)
- rotating (except for animated images)
- lateral panel
- load dialog
- save dialog (image to png or jpg formats)
- can launch three custom command
- basic image info
- fit to window
- original size
- multipage image navigation (page up and down)
- ocr recognition by selection
- autorotation of images, when possible (as option in the config file)
- shortcuts
- language file.

About the custom actions: from the toolbar can be launched three custom actions. Their names can be changed tin the config file. The bash scripts executed by those actions are: tool1.sh, tool2.sh and tool3.sh. The current visualized image full path will be passed to those bash scripts as argument.

  ![My image](https://github.com/frank038/qt6imageviewer/blob/main/screenshot1.png)
