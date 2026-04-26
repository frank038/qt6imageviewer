#!/usr/bin/python3
# V. 1.1.0

from qt6imgvrlang import *
from PyQt6.QtCore import Qt, QRect, QMimeDatabase, QIODevice, QByteArray, QBuffer, QEvent, QSize, QThread, pyqtSignal
from PyQt6.QtGui import QGuiApplication, QAction, QImage, QImageReader, QPixmap, QPalette, QPainter, QIcon, QTransform, QMovie, QBrush, QColor
from PyQt6.QtPrintSupport import QPrintDialog, QPrinter
from PyQt6.QtWidgets import QPushButton, QMenu, QColorDialog, QListView, QAbstractItemView, QListWidget, QListWidgetItem, QHBoxLayout, QVBoxLayout, QWidget, QLabel, QSizePolicy, QScrollArea, QMessageBox, QMainWindow, QMenu, QFileDialog
import subprocess, os, time
from cfg_imageviewer import *
import io

skip_pil = 0
if with_pil:
    try:
        from PIL import Image, ImageQt
    except:
        skip_pil = 1
else:
    skip_pil = 1

skip_glycin = 1
if with_glycin == 1:
    try:
        import gi
        gi.require_version("Gly", "1")
        gi.require_version("GlyGtk4", "1")
        from gi.repository import Gly, GlyGtk4, Gio
        skip_glycin = 0
    except:
        skip_glycin = 0
elif with_glycin == 2:
    try:
        import gi
        gi.require_version("Gly", "2")
        gi.require_version("GlyGtk4", "2")
        from gi.repository import Gly, GlyGtk4, Gio
        skip_glycin = 0
    except:
        skip_glycin = 1
        
# home dir
MY_HOME = os.path.expanduser('~')

# this program working directory
main_dir = os.getcwd()

os.chdir(MY_HOME)
# os.chdir(main_dir)

# the image folder
IMAGE_FOLDER = None

# the overlay1 size
OV1W = OVERLAY_WIDTH
OV1H = OVERLAY_HEIGHT

#######
# binary extensions
supportedFormats = QImageReader.supportedImageFormats()
fformats_tmp = ""
for fft in supportedFormats:
    fformats_tmp += "*."+fft.data().decode()+" "

if with_pil:
    for eel in with_pil:
        fft = eel.split("/")[1]
        fformats_tmp += "*."+fft+" "

# extensions
fformats = fformats_tmp[0:-1]

if with_pil != [] and PIL_EXT != []:
    fformats += " "
    fformats += " ".join(PIL_EXT)

if with_glycin > 0 and GLICYN_EXT != []:
    fformats += " "
    fformats += " ".join(GLICYN_EXT)

dialog_filters = '{} ({});;{} (*)'.format(WIMAGES, WALLFILES, fformats)
dialog_filters2 = '{} ({});;{} (*)'.format(WIMAGES, WALLFILES, "*.png *.jpg *.jpeg")

# mimetypes format
SUPPORTED_MIME = []
for el in QImageReader.supportedMimeTypes():
    if el not in img_skipped:
        SUPPORTED_MIME.append(el.data().decode())

for el in with_pil:
    if el not in SUPPORTED_MIME or el not in img_skipped:
        SUPPORTED_MIME.append(el)

for el in GLICYN_LIST:
    if el not in SUPPORTED_MIME or el not in img_skipped:
        SUPPORTED_MIME.append(el)

#######

WW = 800
HH = 600
try:
    with open (os.path.join(main_dir, "winsize.cfg"), "r") as ifile:
        fcontent = ifile.readline()
        WW1, HH1 = fcontent.split(";")
        WW = int(WW1)
        HH = int(HH1.strip())
except:
    try:
        with open(os.path.join(main_dir, "winsize.cfg"), "w") as ifile:
            ifile.write("{};{}".format(WW, HH))
    except:
        pass

# lateral scrollarea thread
class lateralThread(QThread):
    
    lateral1sig = pyqtSignal(list)
    
    def __init__(self, _data, list_widget, ipath):
        super(lateralThread, self).__init__()
        self._data = _data
        self.list_widget = list_widget
        self.ipath = ipath
    
    def run(self):
        data_run = 1
        _list = os.listdir(self._data)
        self.list_widget.setIconSize(QSize(ICON_SIZE,ICON_SIZE))
        while data_run:
            for el in _list:
                fileName = os.path.join(self._data, el)
                image_type = QMimeDatabase().mimeTypeForFile(fileName, QMimeDatabase.MatchMode.MatchDefault).name()
                if image_type in SUPPORTED_MIME:
                    _icon = None
                    _pix = None
                    if (skip_pil == 0) and (image_type in with_pil):
                        try:
                            image = Image.open(fileName)
                            image = image.resize((ICON_SIZE,ICON_SIZE))
                            _pix = ImageQt.toqpixmap(image)
                            if _pix.isNull():
                                continue
                            _icon = QIcon(_pix)
                            if _icon.isNull():
                                del _icon
                                continue
                        except:
                            continue
                    #
                    elif skip_glycin == 0 and image_type in GLICYN_LIST:
                        # seems prevent freezing
                        time.sleep(1)
                        file = Gio.File.new_for_path(fileName)
                        loader = Gly.Loader.new(file=file)
                        loader.set_sandbox_selector(Gly.SandboxSelector.NOT_SANDBOXED)
                        _image = loader.load()
                        _frame = _image.next_frame()
                        _texture = GlyGtk4.frame_get_texture(_frame)
                        gbytes = _texture.save_to_png_bytes()
                        bytesio = gbytes.get_data()
                        _qbytearray = QByteArray(bytesio)
                        _pix = QPixmap()
                        _pix.loadFromData(_qbytearray, None, Qt.ImageConversionFlag.AutoColor)
                        _pix = _pix.scaled(ICON_SIZE,ICON_SIZE,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
                        if _pix.isNull():
                            continue
                        _icon = QIcon(_pix)
                        if _icon.isNull():
                            del _icon
                            continue
                    #
                    else:
                        try:
                        # if (skip_pil == 0) and (image_type not in with_pil):
                            _pix = QPixmap(fileName)#.scaled(QSize(ICON_SIZE,ICON_SIZE), Qt.AspectRatioMode.KeepAspectRatio)
                            if _pix.isNull():
                                continue
                            _pix = _pix.scaled(QSize(ICON_SIZE,ICON_SIZE), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                            if _pix.isNull() or _pix == None:
                                continue
                            _icon = QIcon(_pix)
                            if _icon.isNull():
                                del _icon
                                continue
                        except:
                            continue
                    #
                    if _icon != None:
                        _li = QListWidgetItem(_icon, None)
                        _li.setToolTip(el)
                        _li.setBackground(QBrush(QColor("#E5E5E5")))
                        _li.setSizeHint(QSize(_pix.width(),_pix.height()))
                        self.list_widget.addItem(_li)
            #
            self.lateral1sig.emit(["done", self.ipath])
            data_run = 0

class QImageViewer(QMainWindow):
    def __init__(self, ipath):
        super().__init__()
        #
        self.WW = WW
        self.HH = HH
        self.resize(self.WW, self.HH)
        self.pixel_ratio = self.devicePixelRatio()
        # self.setObjectName("mymainwindow")
        # self.setStyleSheet("QMainWindow#mymainwindow { background-color: "+WINDOW_BACKGROUND+"};")
        self.setContentsMargins(0,0,0,0)
        # wayland or xcb/xorg
        self._platform = QGuiApplication.platformName()
        #
        self.ipath = ipath
        self.curr_dir = None
        # if self.ipath:
            # self.curr_dir = os.path.dirname(self.ipath)
        self.printer = QPrinter()
        # actual scaling factor
        self.scaleFactor = 0.0
        # starting scaling factor
        self.scaleFactorStart = 0.0
        # for key navigation
        self.idx_incr = 0
        #
        self.is_key_nav = 0
        # a gif can be animated
        self.is_animated = False
        self._movie = None
        # multipage but not animated
        self.is_multipage = False
        # # meta+wheel: zoom
        # self.meta_key_pressed = 0
        # the viewer
        self.imageLabel = QLabel()
        self.imageLabel.setBackgroundRole(QPalette.ColorRole.Base)
        self.imageLabel.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.imageLabel.setScaledContents(True)
        self.imageLabel.setContentsMargins(0,0,0,0)
        # central scrollarea
        self.scrollArea = QScrollArea()
        if WINDOW_BACKGROUND != 0:
            self.scrollArea.viewport().setStyleSheet("background-color: {};".format(WINDOW_BACKGROUND))
        self.scrollArea.setContentsMargins(0,0,0,0)
        self.scrollArea.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.scrollArea.setBackgroundRole(QPalette.ColorRole.Dark)
        self.scrollArea.setWidget(self.imageLabel)
        self.imageLabel.setVisible(False)
        self.scrollArea.installEventFilter(self)
        self.scrollArea.viewport().installEventFilter(self)
        self.installEventFilter(self)
        self.last_time_move_h = 0
        self.last_time_move_v = 0
        self.hscrollbar = self.scrollArea.horizontalScrollBar()
        self.vscrollbar = self.scrollArea.verticalScrollBar()
        # the scrollbars height
        self.hbar_height = self.hscrollbar.size().height()
        self.vbar_width = self.vscrollbar.size().height()
        # the widget that contains everything
        self.main_widget = QWidget()
        self.main_widget.setContentsMargins(0,0,0,0)
        self.setCentralWidget(self.main_widget)
        #
        self.main_box = QHBoxLayout()
        self.main_box.setContentsMargins(0,0,0,0)
        self.main_widget.setLayout(self.main_box)
        #
        #### lateral panel
        self.lat_widget = QListWidget()
        self.lat_widget.installEventFilter(self)
        if PANEL_BACKGROUND != 0:
            self.lat_widget.setStyleSheet("background-color: {};".format(PANEL_BACKGROUND))
        _lat_spacing = 1
        self.lat_widget.setSpacing(_lat_spacing)
        _bpad = _lat_spacing+int(self.lat_widget.verticalScrollBar().height()/self.pixel_ratio)
        self.lat_widget.setMaximumWidth(ICON_SIZE+_bpad)
        self.lat_widget.setFixedWidth(ICON_SIZE+_bpad)
        self.lat_widget.setViewMode(QListView.ViewMode.ListMode)
        self.lat_widget.setItemAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lat_widget.setUniformItemSizes(False)
        self.lat_widget.setFlow(QListView.Flow.TopToBottom)
        self.lat_widget.setContentsMargins(0,0,0,0)
        self.lat_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.lat_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.lat_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.lat_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.lat_widget.setVisible(False)
        #
        # self.lat_widget.setGridSize(QSize(ICON_SIZE+2,ICON_SIZE+2))
        self.lat_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.lat_widget.itemClicked.connect(self.on_lat_item_clicked)
        #
        self.main_box.addWidget(self.lat_widget, stretch=1)#, alignment=Qt.AlignmentFlag.AlignCenter)
        ###
        self.main_box.addWidget(self.scrollArea, stretch=10)
        # the folder containing all the images
        self.directory_content = []
        # if self.curr_dir:
            # self.directory_content = os.listdir(self.curr_dir)
        #
        self.lateral1thread = None
        #
        self.directory_current_idx = None
        #
        # 0 use overlay - 1 use toolbar
        self.use_toolbar = USE_TOOLBAR
        #
        self.createActions()
        self.createMenus()
        # overlay1
        if self.use_toolbar == 0:
            self.overlay1_shown = 0
            self.overlay1 = OverlayWidgetBottom(self)
            if OVERLAY_POS == 1:
                self.overlay1.setGeometry(self.WW-10-int(OV1W/self.pixel_ratio),10,int(OV1W/self.pixel_ratio),int(OV1H/self.pixel_ratio))
            elif OVERLAY_POS == 0:
                self.overlay1.setGeometry(10,10,int(OV1W/self.pixel_ratio),int(OV1H/self.pixel_ratio))
            self.overlay1.show()
            # hide at start
            self.overlay1.setVisible(False)
        #
        self.setWindowTitle(WIMAGEVIEWER)
        self.setWindowIcon(QIcon(os.path.join(main_dir, "icons/QImageViewer.svg")))
        #
        self.layout().setContentsMargins(0,0,0,0)
        self.scrollArea.setContentsMargins(0,0,0,0)
        self.imageLabel.setContentsMargins(0,0,0,0)
        #
        self.scrollarea_size = None
        self._is_shown = False
        self._is_resized = False
        #
        self._color_picker = False
        self._color_picker_d = False
        #
        self.original_imageLabel = None
        #
        self.is_rotated = False
        
    
    def showEvent(self, e):
        self._is_shown = True
        self.scrollarea_size = self.scrollArea.size()
        # at start with image name as argument
        if self.ipath:
            if self.curr_dir == os.path.dirname(self.ipath):
                return
            # at start or after opening a new folder
            self.on_on_open()
            ret = self.on_open(self.ipath)
            if ret == -1:
                sys.exit(QApplication.closeAllWindows())
            # the lateral scrollarea
            self.on_lateral1_panel()
        
    
    def resizeEvent(self, e):
        self.WW = self.size().width()
        self.HH = self.size().height()
        if self._is_shown:
            self._is_resized = True
        
    # open from the menu entry
    def open(self):
        options = QFileDialog().options()
        fileName, _ = QFileDialog.getOpenFileName(self, WOPENFILE, self.curr_dir, dialog_filters, options=options)
        if fileName:
            self.is_key_nav = 0
            self.ipath = fileName
            global IMAGE_FOLDER
            IMAGE_FOLDER = os.path.dirname(self.ipath)
            self.on_on_open()
            ret = self.on_open(self.ipath)
            if ret == -1:
                sys.exit(QApplication.closeAllWindows())
            #
            self.on_lateral1_panel()
    
    
    def on_lateral1_panel(self):
        if LEFT_PANEL == 1:
            self.lat_widget.setVisible(True)
            self.pop_list_widget(self.ipath)
        elif LEFT_PANEL == 0:
            if self.lat_widget.isVisible():
                self.lat_widget.setVisible(False)
            if self.lateral1thread != None:
                try:
                    if self.lateral1thread.isRunning():
                        self.lateral1thread.terminate()
                except:
                    pass
    
    def on_leftpanelaction(self):
        global LEFT_PANEL
        LEFT_PANEL = not LEFT_PANEL
        self.on_lateral1_panel()
    
    def pop_list_widget(self, ipath):
        self.lat_widget.clear()
        if os.path.exists(IMAGE_FOLDER):
            self.lateral1thread = lateralThread(IMAGE_FOLDER, self.lat_widget, os.path.basename(ipath))
            self.lateral1thread.lateral1sig.connect(self.on_lateral1)
            self.lateral1thread.finished.connect(self.on_lateral1thread_finished)
            self.lateral1thread.start()
    
    def on_lateral1thread_finished(self):
        self.lateral1thread = None
    
    # _data = ["done", file_name]
    def on_lateral1(self, _data):
        try:
            if self.lateral1thread.isRunning():
                self.lateral1thread.terminate()
        except:
            pass
        #
        if _data[0] == "done":
            self.set_lat_item(_data[1])
    
    def set_lat_item(self, _img_name):
        n_items = self.lat_widget.count()
        for i in range(n_items):
            _item = self.lat_widget.item(i)
            _item_label = _item.toolTip()
            if _item_label == _img_name:
                self.lat_widget.setCurrentItem(_item)
                break
    
    # click the item in the lateral list and set and show this image
    def on_lat_item_clicked(self, _item):
        _image_name = _item.toolTip()
        # find the index
        self.directory_current_idx = self.directory_content.index(_image_name)
        #
        ret = self.on_open(os.path.join(IMAGE_FOLDER,_image_name))
    
    # at start or after opening a new folder
    def on_on_open(self):
        # stop the thread
        if self.lateral1thread != None:
            try:
                if self.lateral1thread.isRunning():
                    self.lateral1thread.terminate()
            except:
                pass
        # set the working dir
        self.curr_dir = os.path.dirname(self.ipath)
        # list the content of the directory
        self.directory_content = os.listdir(self.curr_dir)
    
    
    def on_open(self, fileName):
        self.is_rotated = False
        # update the scrollarea size
        if self._is_resized == True:
            self._is_resized = False
        #
        _WW = self.scrollarea_size.width()
        _HH = self.scrollarea_size.height()
        #
        ppixmap = None
        self.is_animated = False
        self.is_multipage = False
        if self._movie:
            self._movie.stop()
            self._movie = None
        #
        qbuffer = None
        try:
            image_type = QMimeDatabase().mimeTypeForFile(fileName, QMimeDatabase.MatchMode.MatchDefault).name()
            if image_type not in SUPPORTED_MIME:
                return -2
            if image_type in img_skipped:
                if not self.is_key_nav:
                    QMessageBox.information(self, WIMAGEVIEWER, "{} {}.\n{}".format(WCANNOTLOAD, WSKIPPED, fileName))
                return -2
            elif (skip_pil == 0) and (image_type in with_pil):
                image = Image.open(fileName)
                bytesio = io.BytesIO()
                image.save(fp=bytesio, format="PNG")#, save_all=True)#, append_images=imgs, save_all=True, duration=GIF_DELAY, loop=0)
                qbytearray = QByteArray(bytesio.getvalue())
                bytesio.close()
                qbuffer = QBuffer(qbytearray)
            elif skip_glycin == 0 and image_type in GLICYN_LIST:
                file = Gio.File.new_for_path(fileName)
                loader = Gly.Loader.new(file=file)
                loader.set_sandbox_selector(Gly.SandboxSelector.NOT_SANDBOXED)
                _image = loader.load()
                _frame = _image.next_frame()
                _texture = GlyGtk4.frame_get_texture(_frame)
                gbytes = _texture.save_to_png_bytes()
                bytesio = gbytes.get_data()
                qbytearray = QByteArray(bytesio)
                qbuffer = QBuffer(qbytearray)
        except Exception as E:
            QMessageBox.information(self, WIMAGEVIEWER, "{}\n{}.".format(WERROR, str(E)))
            return -1
        # 
        self.ipath = fileName
        # set the picture index in the list
        self.directory_current_idx = self.directory_content.index(os.path.basename(self.ipath))
        #
        self.scaleFactor = 1.0
        #
        if qbuffer == None:
            self._movie = QMovie(fileName)
        else:
            self._movie = QMovie()
            self._movie.setDevice(qbuffer)
            # self._movie.setCacheMode(QMovie.CacheAll)
        #
        #
        if self._movie.frameCount() > 1:
            self.imageLabel.setMovie(self._movie)
            self.original_imageLabel = self.imageLabel
            #
            self._movie.start()
            self._movie.stop()
            ###
            # self.is_animated = True
            ###
            # 0 multipage - -1 animated
            _is_multipage = self._movie.loopCount()
            if _is_multipage == 0:
                self.is_multipage = True
                self._movie.frameChanged.connect(self.on_movie_frame_changed)
                self._movie.finished.connect(self.on_movie_finished)
            if self.is_multipage == False:
                self.is_animated = True
            ###
            ppixmap = self._movie.currentPixmap()
            if ppixmap.isNull():
                QMessageBox.information(self, WIMAGEVIEWER, "{}\n{}\n{}.".format(WERROR, os.path.basename(self.ipath), WIMAGENOTSUPPORTED))
                return -1
            self._movie.stop()
        else:
            if qbuffer:
                self._movie.start()
                ppixmap = self._movie.currentPixmap()
                self._movie.stop()
            else:
                ppixmap = QPixmap(fileName)
            if not ppixmap.isNull():
                self.imageLabel.setPixmap(ppixmap)
                self.imageLabel.rotation = 0
            else:
                QMessageBox.information(self, WIMAGEVIEWER, "{}\n{}\n{}.".format(WERROR, os.path.basename(self.ipath), WIMAGENOTSUPPORTED))
                return -1
        #
        image_width = ppixmap.width()
        image_height = ppixmap.height()
        #
        _a = (_WW-4)/image_width#/self.pixel_ratio
        _b = (_HH-4)/image_height#/self.pixel_ratio
        self.scaleFactor = min(_a, _b)
        #
        self.imageLabel.resize(self.scaleFactor * ppixmap.size())
        self.scaleFactorStart = self.scaleFactor
        #
        if self.is_animated:
            # _frames = self._movie.frameCount()
            # if _frames > 1:
                # self.is_animated = True
            self._movie.start()
        #
        if self.imageLabel.isVisible() == False:
            self.imageLabel.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            self.imageLabel.setVisible(True)
            self.scrollArea.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            self.printAct.setEnabled(True)
            self.updateActions()
            self.infoAct.setEnabled(True)
        #
        self.loopAct.setEnabled(False)
        self.loopAct.setChecked(False)
        if self.is_multipage == True:
            self.setWindowTitle("{} - {} - x{} - {}/{}".format(WIMAGEVIEWER, os.path.basename(self.ipath), round(self.scaleFactor*self.pixel_ratio, 2), self._movie.currentFrameNumber()+1, self._movie.frameCount()))
            self.prevPageAct.setEnabled(True)
            self.nextPageAct.setEnabled(True)
            # self.loopAct.setEnabled(True)
            self.loopAct.setEnabled(False)
            self.loopAct.setChecked(False)
        else:
            self.setWindowTitle("{} - {} - x{}".format(WIMAGEVIEWER, os.path.basename(self.ipath), round(self.scaleFactor*self.pixel_ratio, 2)))
            self.prevPageAct.setEnabled(False)
            self.nextPageAct.setEnabled(False)
        #
        if self.is_animated:
            self.rotateLeftAct.setEnabled(False)
            self.rotateRightAct.setEnabled(False)
            self.loopAct.setEnabled(True)
            self.loopAct.setChecked(True)
        else:
            self.rotateLeftAct.setEnabled(True)
            self.rotateRightAct.setEnabled(True)
    
    def on_movie_frame_changed(self, _n):
        self.setWindowTitle("{} - {} - x{} - {}/{}".format(WIMAGEVIEWER, os.path.basename(self.ipath), round(self.scaleFactor*self.pixel_ratio, 2), _n+1, self._movie.frameCount()))
        
    def on_movie_finished(self):
        if self.loopAct.isChecked():
            self.loopAct.setChecked(False)
    
    def print_(self):
        dialog = QPrintDialog(self.printer, self)
        ret = dialog.exec()
        if ret:
            painter = QPainter(self.printer)
            rect = painter.viewport()
            #
            ppixmap = None
            if self.is_rotated:
                ppixmap = self.imageLabel.pixmap()
            else:
                if self.is_animated:
                    self._movie.stop()
                    _frames = self._movie.frameCount()
                    if _frames > 1:
                        self._movie.jumpToFrame(0)
                ppixmap = self._movie.currentPixmap()
            if self.is_animated:
                self._movie.start()
            #
            size = ppixmap.size()
            size.scale(rect.size(), Qt.AspectRatioMode.KeepAspectRatio)
            painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
            painter.setWindow(ppixmap.rect())
            painter.drawPixmap(0, 0, ppixmap)
        dialog.done(1)
        if ret == 1:
            MyDialog(WIMAGEVIEWER, WIMAGEVIEWER, self)
        # else:
            # MyDialog("Error", "Error.", self)
    
    def info_(self):
        pw = ""
        ph = ""
        pd = ""
        try:
            if self.is_rotated or not self.is_animated:
                ppixmap = self.imageLabel.pixmap()
            else:
                ppixmap = self._movie.currentPixmap()
            pw = ppixmap.width()
            ph = ppixmap.height()
            pd = ppixmap.depth()
        except:
            pw = self._movie.frameRect().width()
            ph = self._movie.frameRect().height()
            pd = WUNKNOWN
        imime = QMimeDatabase().mimeTypeForFile(self.ipath, QMimeDatabase.MatchMode.MatchDefault)
        imime_name = imime.name()
        QMessageBox.information(self, WIMAGEVIEWER, "{} {}\n{} {}\n{} {}\n{} {}\n{} {}".format(WNAME, WWIDTH, WHEIGHT, WDEPTH, WTYPE, os.path.basename(self.ipath), pw, ph, pd, imime_name))
    
    def zoomIn(self):
        self.scaleImage(1.25)
    
    def zoomOut(self):
        self.scaleImage(0.8)
    
    def normalSize(self):
        self.scaleImage(1.0)
    
    def fitSize(self):
        self.scaleImage("fit")
    
    def createActions(self):
        self.openAct = QAction(WOPEN, self, shortcut="Ctrl+o", triggered=self.open)
        self.printAct = QAction(WPRINT, self, shortcut="Ctrl+p", enabled=False, triggered=self.print_)
        self.infoAct = QAction(WINFO, self, shortcut="Ctrl+i", enabled=False, triggered=self.info_)
        self.exitAct = QAction("Exit", self, shortcut="Ctrl+q", triggered=self.close)
        #
        self.zoomInAct = QAction(WZOOMIN, self, shortcut="Ctrl++", enabled=False, triggered=self.zoomIn)
        self.zoomOutAct = QAction(WZOOMOUT, self, shortcut="Ctrl+-", enabled=False, triggered=self.zoomOut)
        self.normalSizeAct = QAction(WNORMALSIZE, self, shortcut="Ctrl+n", enabled=False, triggered=self.normalSize)
        self.fitSizeAct = QAction(WFITWINDOW, self, shortcut="Ctrl+f", enabled=False, triggered=self.fitSize)
        self.rotateLeftAct = QAction(WROTATELEFT, self, shortcut="Ctrl+e", enabled=False, triggered=self.rotateLeft)
        self.rotateRightAct = QAction("Rotate Right", self, shortcut="Ctrl+r", enabled=False, triggered=self.rotateRight)
        self.loopAct = QAction(WLOOP, self, shortcut="ctrl+l", enabled=False, triggered=self.on_loop)
        self.loopAct.setCheckable(True)
        self.prevPageAct = QAction(WPREVPAGE, self, shortcut="ctrl+a", enabled=False, triggered=lambda:self.on_multipage(-1))
        self.nextPageAct = QAction(WNEXTPAGE, self, shortcut="ctrl+z", enabled=False, triggered=lambda:self.on_multipage(1))
        self.leftPanelAct = QAction(WLEFTPANEL, self, shortcut="Ctrl+c", enabled=False, triggered=self.on_leftpanelaction)
        #
        self.tool1Act = QAction("{}".format(TOOL1NAME or "Tool1"), self, shortcut="Ctrl+1", enabled=True, triggered=self.tool1)
        self.tool2Act = QAction("{}".format(TOOL2NAME or "Tool2"), self, shortcut="Ctrl+2", enabled=True, triggered=self.tool2)
        self.tool3Act = QAction("{}".format(TOOL3NAME or "Tool3"), self, shortcut="Ctrl+3", enabled=True, triggered=self.tool3)
        #
        self.tool4Act = QAction("{}".format(WCOLPICKERCLIPBOARD), self, shortcut="Ctrl+4", enabled=True, triggered=self.on_color_picker)
        self.tool5Act = QAction("{}".format(WCOLPICKERDIALOG), self, shortcut="Ctrl+5", enabled=True, triggered=self.on_color_picker_d)
        self.tool6Act = QAction("{}".format(WTESSERACT), self, shortcut="Ctrl+6", enabled=True, triggered=self.on_tesseract)
        #
        self.saveAsPNG = QAction("{}".format(WSAVEPNG), self)
        # self.saveAsPNG.setShortcut("Ctrl+5")
        self.saveAsPNG.setEnabled(True)
        self.saveAsPNG.triggered.connect(lambda:self.on_save_image("png"))
        #
        self.saveAsJPG = QAction("{}".format(WSAVEJPG), self)
        # self.saveAsJPG.setShortcut("Ctrl+6")
        self.saveAsJPG.setEnabled(True)
        self.saveAsJPG.triggered.connect(lambda:self.on_save_image("jpg"))
        
    def on_save_image(self, _code):
        ppixmap = None
        if self.is_rotated or not self.is_animated:
            ppixmap = self.imageLabel.pixmap()
        else:
            _frames = self._movie.frameCount()
            if _frames > 1:
                self._movie.stop()
                self._movie.jumpToFrame(0)
                ppixmap = self._movie.currentPixmap()
                self._movie.start()
            else:
                ppixmap = self._movie.currentPixmap()
        options = QFileDialog().options()
        fileName, _ = QFileDialog.getSaveFileName(self, WSAVEFILE, MY_HOME, dialog_filters2, options=options)
        if fileName:
            if not fileName.split(".")[-1] in ["png","jpg","jpeg"]:
                fileName = fileName+"."+_code
            ret = ppixmap.save(fileName, _code)
            if ret:
                MyDialog(WINFO, WSAVED, self)
            else:
                MyDialog(WERROR1, WERROR2, self)
        
    def createMenus(self):
        self.fileMenu = QMenu(WFILE)#, self)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.printAct)
        self.fileMenu.addSeparator()
        self.subMenuSave = QMenu(WSAVEAS)
        self.subMenuSave.addAction(self.saveAsPNG)
        self.subMenuSave.addAction(self.saveAsJPG)
        self.fileMenu.addMenu(self.subMenuSave)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.infoAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = QMenu(WVIEW)#, self)
        self.viewMenu.addAction(self.zoomInAct)
        self.viewMenu.addAction(self.zoomOutAct)
        self.viewMenu.addAction(self.normalSizeAct)
        self.viewMenu.addAction(self.fitSizeAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.rotateLeftAct)
        self.viewMenu.addAction(self.rotateRightAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.loopAct)
        self.viewMenu.addAction(self.prevPageAct)
        self.viewMenu.addAction(self.nextPageAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.leftPanelAct)
        #
        self.toolMenu = QMenu(WTOOL)#, self)
        self.toolMenu.addAction(self.tool1Act)
        self.toolMenu.addAction(self.tool2Act)
        self.toolMenu.addAction(self.tool3Act)
        self.toolMenu.addAction(self.tool4Act)
        self.toolMenu.addAction(self.tool5Act)
        self.toolMenu.addAction(self.tool6Act)
        #
        if self.use_toolbar == 1:
            self.menuBar().addMenu(self.fileMenu)
            self.menuBar().addMenu(self.viewMenu)
            self.menuBar().addMenu(self.toolMenu)
    
    def on_loop(self):
        if self.sender() != None:
            if self.sender().isChecked() == False:
                self._movie.stop()
            else:
                self._movie.start()
        else:
            if self.loopAct.isChecked() == True:
                self._movie.stop()
                self.loopAct.setChecked(False)
            else:
                self._movie.start()
                self.loopAct.setChecked(True)
    
    def tool1(self):
        if self.ipath == "" or self.ipath == None:
            return
        try:
            subprocess.Popen([os.path.join(main_dir, "tool1.sh"), self.ipath])
        except Exception as E:
            MyDialog(WERROR1, str(E), self)
    
    def tool2(self):
        if self.ipath == "" or self.ipath == None:
            return
        try:
            subprocess.Popen([os.path.join(main_dir, "tool2.sh"), self.ipath])
        except Exception as E:
            MyDialog(WERROR1, str(E), self)
    
    def tool3(self):
        if self.ipath == "" or self.ipath == None:
            return
        try:
            subprocess.Popen([os.path.join(main_dir, "tool3.sh"), self.ipath])
        except Exception as E:
            MyDialog(WERROR1, str(E), self)
    
    def on_color_picker(self):
        self._color_picker = True
        QApplication.setOverrideCursor(Qt.CursorShape.PointingHandCursor)
    
    def on_color_picker_d(self):
        self._color_picker_d = True
        QApplication.setOverrideCursor(Qt.CursorShape.PointingHandCursor)
    
    def on_tesseract(self):
        try:
            if self._platform == "wayland":
                prog = os.path.join(main_dir,"tesseract_clipboard_wayland.sh")
            else:
                prog = os.path.join(main_dir,"tesseract_clipboard_xorg.sh")
            subprocess.Popen([prog])
        except Exception as E:
            MyDialog(WERROR1, str(E), self)
    
    def updateActions(self):
        self.zoomInAct.setEnabled(True)
        self.zoomOutAct.setEnabled(True)
        self.normalSizeAct.setEnabled(True)
        self.fitSizeAct.setEnabled(True)
        self.loopAct.setEnabled(True)
        self.rotateLeftAct.setEnabled(True)
        self.rotateRightAct.setEnabled(True)
        self.leftPanelAct.setEnabled(True)
    
    def scaleImage(self, factor):
        if factor == "fit":
            self.scaleFactor = self.scaleFactorStart
            factor = self.scaleFactor
        elif factor == 1.0:
            self.scaleFactor = 1.0/self.pixel_ratio
        else:
            if (self.scaleFactor/self.pixel_ratio > 3.0) or (self.scaleFactor/self.pixel_ratio < 0.01):
                return
            #
            self.scaleFactor *= factor
        #
        if self.is_animated or self.is_multipage:
            _frames = self._movie.frameCount()
            if _frames > 1 and self.is_animated:
                self._movie.stop()
                self._movie.jumpToFrame(0)
                # ppixmap = self.original_imageLabel.movie().currentPixmap()
                ppixmap = self._movie.currentPixmap()
            # if _frames > 1 and self.is_animated:
                self._movie.start()
            elif _frames > 1 and self.is_multipage:
                self._movie.stop()
                ppixmap = self._movie.currentPixmap()
        # elif self.is_rotated:
        else:
            ppixmap = self.imageLabel.pixmap()
        
        self.imageLabel.resize(self.scaleFactor * ppixmap.size())
        #
        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)
        #
        self.zoomInAct.setEnabled(self.scaleFactor/self.pixel_ratio < 3.0)
        self.zoomOutAct.setEnabled(self.scaleFactor/self.pixel_ratio > 0.01)
        #
        self.setWindowTitle("{} - {} - x{}".format(WIMAGEVIEWER, os.path.basename(self.ipath), round(self.scaleFactor*self.pixel_ratio, 2)))
    
    def adjustScrollBar(self, scrollBar, factor):
        # if self.meta_key_pressed == 1:
            # return
        scrollBar.setValue(int(factor * scrollBar.value()
                               + ((factor - 1) * scrollBar.pageStep() / 2)))
    
    def closeEvent(self, event):
        self.on_close()
    
    def on_close(self):
        new_w = self.size().width()
        new_h = self.size().height()
        if new_w != int(WW) or new_h != int(HH):
            try:
                ifile = open(os.path.join(main_dir, "winsize.cfg"), "w")
                ifile.write("{};{}".format(new_w, new_h))
                ifile.close()
            except Exception as E:
                pass
        QApplication.quit()
    
    # load the next or previous image in the folder
    def keyNav(self, incr_idx):
        self.is_key_nav = 1
        if self._movie:
            self._movie.stop()
            self._movie = None
            self.is_animated = False
        #
        len_folder = len(self.directory_content)
        new_idx = self.directory_current_idx + incr_idx
        # 
        if incr_idx == -1:
            ttype = "d"
        else:
            ttype = "i"
        self.on_open2(new_idx, ttype)
    
    # self.keyNav
    def on_open2(self, new_idx, ttype):
        len_folder = len(self.directory_content)
        if ttype == "i":
            self.idx_incr += 1
            incr_idx = 1
        elif ttype == "d":
            self.idx_incr -= 1
            incr_idx = -1
        #
        if new_idx > len_folder - 1:
            new_idx = 0
            self.idx_incr = 0
        elif new_idx < 0:
            new_idx = len_folder - 1
            self.idx_incr = 0
        #
        nitem = self.directory_content[new_idx]
        fileName = os.path.join(self.curr_dir, nitem)
        ret = self.on_open(fileName)
        # error in reading a file
        if ret == -2:
            if ttype == "i":
                self.on_open2(new_idx+1, ttype)
            elif ttype == "d":
                self.on_open2(new_idx-1, ttype)
        # select the item in the listwidget
        self.set_lat_item(nitem)
    
    #
    def rotateLeft(self):
        self.imageRotate(1)
    
    #
    def rotateRight(self):
        self.imageRotate(-1)
    
    # with up or down keys
    def imageRotate(self, ttype):
        if self.is_animated:
            return
        #
        if ttype == -1:
            image_rotation = 90
        else:
            image_rotation = -90
        #
        if self.is_multipage == False and (self.is_rotated or not self.is_animated):
            ppixmap = self.imageLabel.pixmap()
        elif self.is_multipage:
            self._movie.stop()
            ppixmap = self._movie.currentPixmap()
            if hasattr(self.imageLabel, "rotation"):
                image_rotation += self.imageLabel.rotation
                if image_rotation in [360,-360]:
                    self.imageLabel.rotation = 0
                    image_rotation = 0
                else:
                    self.imageLabel.rotation = image_rotation
            else:
                self.imageLabel.rotation = image_rotation
        #
        transform = QTransform().rotate(image_rotation)
        ppixmap = ppixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
        #
        self.imageLabel.setPixmap(ppixmap)
        self.is_rotated = True
        self.imageLabel.resize(self.scaleFactor * ppixmap.size())
    
    # -1 previous page - 1 next page
    def on_multipage(self, ttype):
        curr_frame_num = self._movie.currentFrameNumber()
        tot_frame_num = self._movie.frameCount()
        if curr_frame_num < tot_frame_num-1:
            curr_frame_num += 1
        else:
            curr_frame_num = 0
        ret = self._movie.jumpToFrame(curr_frame_num)
        ppixmap = self._movie.currentPixmap()
        self.imageLabel.setPixmap(ppixmap)
        self.setWindowTitle("{} - {} - x{} - {}/{}".format(WIMAGEVIEWER, os.path.basename(self.ipath), round(self.scaleFactor*self.pixel_ratio, 2), self._movie.currentFrameNumber()+1, self._movie.frameCount()))
    
    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.HoverMove and isinstance(source, QImageViewer):
            if self.use_toolbar == 0:
                _ex = event.position().x()
                _ey = event.position().y()
                if OVERLAY_POS == 1:
                    if (self.WW-10-int(OV1W/self.pixel_ratio)) < _ex < (self.WW-10) and (10) < _ey < (10+int(OV1H/self.pixel_ratio)):
                        if self.overlay1_shown == 0:
                            self.overlay1.setVisible(True)
                            self.overlay1_shown = 1
                            return True
                    else:
                        self.overlay1.setVisible(False)
                        self.overlay1_shown = 0
                        return True
                elif OVERLAY_POS == 0:
                    if (10) < _ex < (OV1H+10) and (10) < _ey < (10+int(OV1H/self.pixel_ratio)):
                        if self.overlay1_shown == 0:
                            self.overlay1.setVisible(True)
                            self.overlay1_shown = 1
                            return True
                    else:
                        self.overlay1.setVisible(False)
                        self.overlay1_shown = 0
                        return True
        # mouse scrolling
        elif event.type() == QEvent.Type.MouseMove:
            if self.last_time_move_v == 0:
                self.last_time_move_v = int(event.position().y())
            vdistance = self.last_time_move_v - int(event.position().y())
            self.vscrollbar.setValue(self.vscrollbar.value() + vdistance)
            self.last_time_move_v = int(event.position().y())
            #
            if self.last_time_move_h == 0:
                self.last_time_move_h = int(event.position().x())
            hdistance = self.last_time_move_h - int(event.position().x())
            self.hscrollbar.setValue(self.hscrollbar.value() + hdistance)
            self.last_time_move_h = int(event.position().x())
            return True
        elif event.type() == QEvent.Type.MouseButtonRelease:
            self.last_time_move_h = 0
            self.last_time_move_v = 0
            return True
        elif event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                if self._color_picker == True:
                    _pix = self.scrollArea.grab(QRect(int(event.position().x()),int(event.position().y()),1,1))
                    _img = _pix.toImage()
                    _color_picked = _img.pixelColor(0,0).name(QColor.NameFormat.HexRgb)
                    _clipboard = QGuiApplication.clipboard()
                    _clipboard.setText(_color_picked)
                    QApplication.restoreOverrideCursor()
                    self._color_picker = False
                    return True
                elif self._color_picker_d == True:
                    _pix = self.scrollArea.grab(QRect(int(event.position().x()),int(event.position().y()),1,1))
                    _img = _pix.toImage()
                    cdlg = QColorDialog(self)
                    cdlg.setOptions(QColorDialog.ColorDialogOption.ShowAlphaChannel)
                    cdlg.setCurrentColor(_img.pixelColor(0,0))
                    # cdlg.setModal(False)
                    cdlg.show()
                    QApplication.restoreOverrideCursor()
                    self._color_picker_d = False
                    return True
        # key navigation
        elif event.type() == QEvent.Type.KeyPress:
            # overlay1
            if self.use_toolbar == 0:
                if event.modifiers()  == Qt.KeyboardModifier.ControlModifier:
                    if event.key() == Qt.Key.Key_O:
                        self.open()
                    elif event.key() == Qt.Key.Key_P:
                        self.print_()
                    elif event.key() == Qt.Key.Key_I:
                        self.info_()
                    elif event.key() == Qt.Key.Key_Q:
                        self.close()
                    #
                    elif event.key() == Qt.Key.Key_Plus:
                        self.zoomIn()
                    elif event.key() == Qt.Key.Key_Minus:
                        self.zoomOut()
                    elif event.key() == Qt.Key.Key_N:
                        self.normalSize()
                    elif event.key() == Qt.Key.Key_F:
                        self.fitSize()
                    elif event.key() == Qt.Key.Key_E:
                        self.rotateLeft()
                    elif event.key() == Qt.Key.Key_R:
                        self.rotateRight()
                    elif event.key() == Qt.Key.Key_L:
                        self.on_loop()
                    #
                    elif event.key() == Qt.Key.Key_A:
                        self.on_multipage(-1)
                    elif event.key() == Qt.Key.Key_Z:
                        self.on_multipage(1)
                    elif event.key() == Qt.Key.Key_C:
                        self.on_leftpanelaction()
                    #
                    elif event.key() == Qt.Key.Key_1:
                        self.tool1()
                    elif event.key() == Qt.Key.Key_2:
                        self.tool2()
                    elif event.key() == Qt.Key.Key_3:
                        self.tool3()
                    elif event.key() == Qt.Key.Key_4:
                        self.on_color_picker()
                    elif event.key() == Qt.Key.Key_5:
                        self.on_color_picker_d()
                    elif event.key() == Qt.Key.Key_6:
                        self.on_tesseract()
                    return True
            # next or previous file
            if event.key() == Qt.Key.Key_Left:
                self.keyNav(-1)
            elif event.key() == Qt.Key.Key_Right:
                self.keyNav(1)
            # rotate the image
            elif event.key() == Qt.Key.Key_Up:
                self.imageRotate(-1)
            elif event.key() == Qt.Key.Key_Down:
                self.imageRotate(1)
            # colour picker
            elif event.key() == Qt.Key.Key_Escape:
                if self._color_picker == True:
                    QApplication.restoreOverrideCursor()
                    self._color_picker = False
                elif self._color_picker_d == True:
                    QApplication.restoreOverrideCursor()
                    self._color_picker_d = False
            # multipage
            elif event.key() == Qt.Key.Key_PageUp:
                if self.is_multipage:
                    self.on_multipage(-1)
            elif event.key() == Qt.Key.Key_PageDown:
                if self.is_multipage:
                    self.on_multipage(1)
            # elif event.key() == Qt.Key.Key_Meta:
                # self.meta_key_pressed = 1
        # elif event.type() == QEvent.Type.KeyRelease:
            # if event.key() == Qt.Key.Key_Meta:
                # self.meta_key_pressed = 0
        # mouse wheel zoom
        elif event.type() == QEvent.Type.Wheel:
            if isinstance(source, QListWidget):
                return True
            # if self.is_multipage == True:
               # return True
            # if self.is_animated:
                # return True
            # else:
            if self.is_multipage == False:
                ppixmap = self.imageLabel.pixmap()
            else:
                self._movie.stop()
                ppixmap = self._movie.currentPixmap()
            # if self.meta_key_pressed == 1:
            if 1:
                if event.angleDelta().y() < 0:
                    # zoom out
                    self.scaleImage(0.8)
                    _d = (self.scaleFactor-self.scaleFactorStart)
                    _HH = 0
                    if _d > 0:
                        _HH = (ppixmap.width()*self.scaleFactor-ppixmap.width()*self.scaleFactorStart)/(2)
                    _VV = 0
                    if _d > 0:
                        _VV = (ppixmap.height()*self.scaleFactor-ppixmap.height()*self.scaleFactorStart)/(2)
                    self.hscrollbar.setValue(int(_HH))
                    self.vscrollbar.setValue(int(_VV))
                    return True
                elif event.angleDelta().y() > 0:
                    # zoom in
                    self.scaleImage(1.25)
                    _d = (self.scaleFactor-self.scaleFactorStart)
                    _HH = 0
                    if _d > 0:
                        _HH = (ppixmap.width()*self.scaleFactor-ppixmap.width()*self.scaleFactorStart)/(2)
                    _VV = 0
                    if _d > 0:
                        _VV = (ppixmap.height()*self.scaleFactor-ppixmap.height()*self.scaleFactorStart)/(2)
                    self.hscrollbar.setValue(int(_HH))
                    self.vscrollbar.setValue(int(_VV))
                    return True
        #
        return super().eventFilter(source, event)

class OverlayWidgetBottom(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.parent = parent
        self.setContentsMargins(0, 0, 0, 0)
        #
        self.central_layout = QHBoxLayout()
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.central_layout.setSpacing(0)
        self.setStyleSheet("background-color: rgba(128,128,128,0.6); border-width: 1px; border-style: solid; border-color: #ffffff;")
        # self.setWindowOpacity(0.01)
        #
        self.setLayout(self.central_layout)
        #
        self.menu_btn = QPushButton()
        self.menu_btn.setFlat(True)
        _icon = QIcon(os.path.join(main_dir, "icons/menu.svg"))
        self.menu_btn.setIcon(_icon)
        self.central_layout.addWidget(self.menu_btn)
        #
        self.menu0 = QMenu()
        self.menu_btn.setMenu(self.menu0)
        #
        self.menu0.addMenu(self.parent.fileMenu)
        self.menu0.addMenu(self.parent.viewMenu)
        self.menu0.addMenu(self.parent.toolMenu)
        

# type - message - parent
class MyDialog(QMessageBox):
    def __init__(self, *args):
        super(MyDialog, self).__init__(args[-1])
        if args[0] == WINFO:
            self.setIcon(QMessageBox.Icon.Information)
            self.setStandardButtons(QMessageBox.StandardButton.Ok)
        elif args[0] == WERROR1:
            self.setIcon(QMessageBox.Icon.Critical)
            self.setStandardButtons(QMessageBox.StandardButton.Ok)
        elif args[0] == WQUESTION:
            self.setIcon(QMessageBox.Icon.Question)
            self.setStandardButtons(QMessageBox.StandardButton.Ok|QMessageBox.StandardButton.Cancel)
        self.setWindowIcon(QIcon(os.path.join(main_dir,"icons/dialog.png")))
        self.setWindowTitle(args[0])
        self.resize(50,50)
        self.setText(args[1])
        retval = self.exec()


if __name__ == '__main__':
    import sys, os
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    # 
    if len(sys.argv) > 1:
        ipath = sys.argv[1]
        if os.path.dirname(ipath) == '' or ipath[0:2] == "./":
            if ipath[0:2] == "./":
                ipath = ipath[2:]
            ipath = os.path.join(main_dir, ipath)
        if os.path.isfile(ipath):
            if os.path.exists(os.path.dirname(ipath)):
                IMAGE_FOLDER = os.path.dirname(ipath)
            imageViewer = QImageViewer(ipath)
        # elif os.path.isdir(ipath):
            # IMAGE_FOLDER = ipath
        else:
            imageViewer = QImageViewer(None)
    else:
        imageViewer = QImageViewer(None)
    QGuiApplication.setDesktopFileName("qt6imageviewer")
    imageViewer.show()
    sys.exit(app.exec())
