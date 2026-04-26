# the background colour, in the form: #rrggbb - 0 to disable
WINDOW_BACKGROUND = "#000000"
# lateral panel background colour - 0 to disable
PANEL_BACKGROUND = "#888888"
# toolbar or overlay at upper right: 0 use overlay - 1 use toolbar
USE_TOOLBAR = 0
# overlay size
OVERLAY_WIDTH = 100
OVERLAY_HEIGHT = 50
# overlay position: 0 left - 1 right
OVERLAY_POS = 0
# PIL will be used - python list e.g. ["image/gif", "image/ppm"]
# leave empty to not to use PIL at all: no PIL python binding needed
with_pil = ["image/x-tga"]
# depends on with_pil list
PIL_EXT = []
# use glycin: 0 no - 1 version 1 - 2 version 2
with_glycin = 1
# list, e.g.: ["image/avif","image/heif","image/jxl"]
GLICYN_LIST = ["image/avif","image/heif","image/jxl"]
# depends on the GLICYN_LIST
GLICYN_EXT = ["*.avif", "*.heif", "*.heic", "*.jxl"]
# could be animated
# animated_format = ["image/gif", "image/webp"]
# image formats to be skipped
img_skipped = []
# left panel at start: 0 off - 1 on
LEFT_PANEL = 0
# the size of the icons in the left
ICON_SIZE = 64
# tool 1 name
TOOL1NAME = ""
# tool 2 name
TOOL2NAME = ""
# tool 3 name
TOOL3NAME = ""