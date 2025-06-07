#!/usr/bin/python3
# V. 0.9.1

from PyQt6.QtCore import Qt, QRect, QMimeDatabase, QIODevice, QByteArray, QBuffer, QEvent, QSize, QThread, pyqtSignal
from PyQt6.QtGui import QGuiApplication, QAction, QImage, QImageReader, QPixmap, QPalette, QPainter, QIcon, QTransform, QMovie, QBrush, QColor
from PyQt6.QtPrintSupport import QPrintDialog, QPrinter
from PyQt6.QtWidgets import QColorDialog, QListView, QAbstractItemView, QListWidget, QListWidgetItem, QHBoxLayout, QVBoxLayout, QWidget, QLabel, QSizePolicy, QScrollArea, QMessageBox, QMainWindow, QMenu, QFileDialog
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

# home dir
MY_HOME = os.path.expanduser('~')

# this program working directory
main_dir = os.getcwd()

os.chdir(MY_HOME)
# os.chdir(main_dir)

# the image folder
IMAGE_FOLDER = None

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

dialog_filters = 'Images ({});;All files (*)'.format(fformats)
dialog_filters2 = 'Images ({});;All files (*)'.format("*.png *.jpg *.jpeg")

# mimetypes format
SUPPORTED_MIME = []
for el in QImageReader.supportedMimeTypes():
    if not el in img_skipped:
        SUPPORTED_MIME.append(el.data().decode())

for el in with_pil:
    if el not in SUPPORTED_MIME:
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
                    try:
                        if (skip_pil == 0) and (image_type in with_pil):
                            image = Image.open(fileName)
                            _pix = ImageQt.toqpixmap(image)
                            if _pix.isNull():
                                continue
                            _pix.scaled(QSize(ICON_SIZE,ICON_SIZE), Qt.AspectRatioMode.KeepAspectRatio)
                            if _pix.isNull():
                                continue
                            _icon = QIcon(_pix)
                            if _icon.isNull():
                                del _icon
                                continue
                    except:
                        continue
                    #
                    try:
                        if (skip_pil == 0) and (image_type not in with_pil):
                            _pix = QPixmap(fileName).scaled(QSize(ICON_SIZE,ICON_SIZE), Qt.AspectRatioMode.KeepAspectRatio)
                            if _pix.isNull():
                                continue
                            _icon = QIcon(_pix)
                            if _icon.isNull():
                                del _icon
                                continue
                    except:
                        continue
                    #
                    _li = QListWidgetItem(_icon, None)
                    _li.setToolTip(el)
                    _li.setBackground(QBrush(QColor("#E5E5E5")))
                    _li.setSizeHint(QSize(ICON_SIZE,ICON_SIZE))
                    self.list_widget.addItem(_li)
                    # time.sleep(0.001)
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
        #
        self.ipath = ipath
        self.curr_dir = None
        if self.ipath:
            self.curr_dir = os.path.dirname(self.ipath)
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
        #
        # the viewer
        self.imageLabel = QLabel()
        self.imageLabel.setBackgroundRole(QPalette.ColorRole.Base)
        self.imageLabel.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.imageLabel.setScaledContents(True)
        # central scrollarea
        self.scrollArea = QScrollArea()
        self.scrollArea.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.scrollArea.setBackgroundRole(QPalette.ColorRole.Dark)
        self.scrollArea.setWidget(self.imageLabel)
        self.imageLabel.setVisible(False)
        self.scrollArea.installEventFilter(self)
        self.last_time_move_h = 0
        self.last_time_move_v = 0
        self.hscrollbar = self.scrollArea.horizontalScrollBar()
        self.vscrollbar = self.scrollArea.verticalScrollBar()
        # the scrollbars height
        self.hbar_height = self.hscrollbar.size().height()
        self.vbar_width = self.vscrollbar.size().height()
        # the widget that contains everything
        self.main_widget = QWidget()
        self.main_widget.setContentsMargins(2,2,2,2)
        self.setCentralWidget(self.main_widget)
        #
        self.main_box = QHBoxLayout()
        self.main_box.setContentsMargins(0,0,0,0)
        self.main_widget.setLayout(self.main_box)
        #
        #### lateral scrollarea
        self.lat_scrollarea = QScrollArea()
        self.lat_scrollarea.setContentsMargins(0,0,0,0)
        self.lat_scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.lat_scrollarea.setVisible(False)
        self.lat_scrollarea.setWidgetResizable(True)
        self.lat_scrollarea.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.lat_scrollarea.setFixedWidth(ICON_SIZE+10)
        #
        self.lat_widget = QListWidget()
        # self.lat_widget.setFixedWidth(ICON_SIZE+10)
        # self.lat_widget.setViewMode(QListView.ViewMode.IconMode)
        self.lat_widget.setContentsMargins(0,0,0,0)
        self.lat_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.lat_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.lat_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.lat_scrollarea.setWidget(self.lat_widget)
        #
        self.lat_widget.setGridSize(QSize(ICON_SIZE+2,ICON_SIZE+2))
        self.lat_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.lat_widget.itemClicked.connect(self.on_lat_item_clicked)
        #
        self.main_box.addWidget(self.lat_scrollarea, stretch=1, alignment=Qt.AlignmentFlag.AlignLeft)
        ###
        self.main_box.addWidget(self.scrollArea, stretch=10)
        # the folder containing all the images
        self.directory_content = []
        if self.curr_dir:
            self.directory_content = os.listdir(self.curr_dir)
        #
        self.lateral1thread = None
        #
        self.directory_current_idx = None
        #
        self.createActions()
        self.createMenus()
        #
        self.setWindowTitle("Image Viewer")
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
        fileName, _ = QFileDialog.getOpenFileName(self, 'Open File', self.curr_dir, dialog_filters, options=options)
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
            # the lateral scrollarea
            self.lat_scrollarea.setVisible(True)
            self.pop_list_widget(self.ipath)
        elif LEFT_PANEL == 0:
            if self.lat_scrollarea.isVisible():
                self.lat_scrollarea.setVisible(False)
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
    
    # 
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
                    QMessageBox.information(self, "Image Viewer", "Cannot load {}.\nSkipped by user.".format(fileName))
                return -2
            elif (skip_pil == 0) and (image_type in with_pil):
                image = Image.open(fileName)
                bytesio = io.BytesIO()
                image.save(fp=bytesio, format="PNG")#, save_all=True)#, append_images=imgs, save_all=True, duration=GIF_DELAY, loop=0)
                qbytearray = QByteArray(bytesio.getvalue())
                bytesio.close()
                qbuffer = QBuffer(qbytearray)
        except Exception as E:
            QMessageBox.information(self, "Image Viewer", "Error {}.".format(str(E)))
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
        self.imageLabel.setMovie(self._movie)
        self.original_imageLabel = self.imageLabel
        #
        self._movie.start()
        ppixmap = self._movie.currentPixmap()
        if ppixmap.isNull():
            QMessageBox.information(self, "Image Viewer", "Error:\n{}\n{}.".format(os.path.basename(self.ipath), "Image type not supported"))
            return -1
        self._movie.stop()
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
        _frames = self._movie.frameCount()
        if _frames > 1:
            self.is_animated = True
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
        self.setWindowTitle("Image Viewer - {} - x{}".format(os.path.basename(self.ipath), round(self.scaleFactor*self.pixel_ratio, 2)))
        #
        if self.is_animated:
            self.rotateLeftAct.setEnabled(False)
            self.rotateRightAct.setEnabled(False)
        else:
            self.rotateLeftAct.setEnabled(True)
            self.rotateRightAct.setEnabled(True)
    
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
            MyDialog("Info", "Printed.", self)
        else:
            MyDialog("Error", "Error.", self)
    
    def info_(self):
        pw = ""
        ph = ""
        pd = ""
        try:
            if self.is_rotated:
                ppixmap = self.imageLabel.pixmap()
            else:
                ppixmap = self._movie.currentPixmap()
            pw = ppixmap.width()
            ph = ppixmap.height()
            pd = ppixmap.depth()
        except:
            pw = self._movie.frameRect().width()
            ph = self._movie.frameRect().height()
            pd = "Unknown"
        imime = QMimeDatabase().mimeTypeForFile(self.ipath, QMimeDatabase.MatchMode.MatchDefault)
        imime_name = imime.name()
        QMessageBox.information(self, "Image Info", "Name: {}\nWidth: {}\nHeight: {}\nDepth: {}\nType: {}".format(os.path.basename(self.ipath), pw, ph, pd, imime_name))
    
    def zoomIn(self):
        self.scaleImage(1.25)
    
    def zoomOut(self):
        self.scaleImage(0.8)
    
    def normalSize(self):
        self.scaleImage(1.0)
    
    def fitSize(self):
        self.scaleImage("fit")
    
    def createActions(self):
        self.openAct = QAction("&Open...", self, shortcut="Ctrl+o", triggered=self.open)
        self.printAct = QAction("&Print...", self, shortcut="Ctrl+p", enabled=False, triggered=self.print_)
        self.infoAct = QAction("&Info", self, shortcut="Ctrl+i", enabled=False, triggered=self.info_)
        self.exitAct = QAction("E&xit", self, shortcut="Ctrl+q", triggered=self.close)
        #
        self.zoomInAct = QAction("Zoom In (25%)", self, shortcut="Ctrl++", enabled=False, triggered=self.zoomIn)
        self.zoomOutAct = QAction("Zoom Out (25%)", self, shortcut="Ctrl+-", enabled=False, triggered=self.zoomOut)
        self.normalSizeAct = QAction("Normal Size", self, shortcut="Ctrl+n", enabled=False, triggered=self.normalSize)
        self.fitSizeAct = QAction("Fit to window", self, shortcut="Ctrl+f", enabled=False, triggered=self.fitSize)
        self.rotateLeftAct = QAction("Rotate Left", self, shortcut="Ctrl+e", enabled=False, triggered=self.rotateLeft)
        self.rotateRightAct = QAction("Rotate Right", self, shortcut="Ctrl+r", enabled=False, triggered=self.rotateRight)
        self.leftPanelAct = QAction("Left Panel", self, shortcut="Ctrl+p", enabled=False, triggered=self.on_leftpanelaction)
        #
        self.tool1Act = QAction("{}".format(TOOL1NAME or "Tool1"), self, shortcut="Ctrl+1", enabled=True, triggered=self.tool1)
        self.tool2Act = QAction("{}".format(TOOL2NAME or "Tool2"), self, shortcut="Ctrl+2", enabled=True, triggered=self.tool2)
        self.tool3Act = QAction("{}".format(TOOL3NAME or "Tool3"), self, shortcut="Ctrl+3", enabled=True, triggered=self.tool3)
        #
        self.tool4Act = QAction("{}".format("Color picker - clipboard"), self, shortcut="Ctrl+4", enabled=True, triggered=self.on_color_picker)
        self.tool5Act = QAction("{}".format("Color picker - dialog"), self, shortcut="Ctrl+5", enabled=True, triggered=self.on_color_picker_d)
        #
        self.saveAsPNG = QAction("{}".format("Save as PNG"), self)
        # self.saveAsPNG.setShortcut("Ctrl+5")
        self.saveAsPNG.setEnabled(True)
        self.saveAsPNG.triggered.connect(lambda:self.on_save_image("png"))
        #
        self.saveAsJPG = QAction("{}".format("Save as JPG"), self)
        # self.saveAsJPG.setShortcut("Ctrl+6")
        self.saveAsJPG.setEnabled(True)
        self.saveAsJPG.triggered.connect(lambda:self.on_save_image("jpg"))
        
    def on_save_image(self, _code):
        ppixmap = None
        if self.is_rotated:
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
        fileName, _ = QFileDialog.getSaveFileName(self, 'Save File', MY_HOME, dialog_filters2, options=options)
        if fileName:
            if not fileName.split(".")[-1] in ["png","jpg","jpeg"]:
                fileName = fileName+"."+_code
            ret = ppixmap.save(fileName, _code)
            if ret:
                MyDialog("Info", "Saved.", self)
            else:
                MyDialog("Error", "Some errors occoured.", self)
        
    def createMenus(self):
        self.fileMenu = QMenu("&File", self)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.printAct)
        self.fileMenu.addSeparator()
        self.subMenuSave = QMenu("&Save as...")
        self.subMenuSave.addAction(self.saveAsPNG)
        self.subMenuSave.addAction(self.saveAsJPG)
        self.fileMenu.addMenu(self.subMenuSave)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.infoAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = QMenu("&View", self)
        self.viewMenu.addAction(self.zoomInAct)
        self.viewMenu.addAction(self.zoomOutAct)
        self.viewMenu.addAction(self.normalSizeAct)
        self.viewMenu.addAction(self.fitSizeAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.rotateLeftAct)
        self.viewMenu.addAction(self.rotateRightAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.leftPanelAct)
        #
        self.toolMenu = QMenu("&Tool", self)
        self.toolMenu.addAction(self.tool1Act)
        self.toolMenu.addAction(self.tool2Act)
        self.toolMenu.addAction(self.tool3Act)
        self.toolMenu.addAction(self.tool4Act)
        self.toolMenu.addAction(self.tool5Act)
        #
        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.viewMenu)
        self.menuBar().addMenu(self.toolMenu)
    
    def tool1(self):
        if self.ipath == "" or self.ipath == None:
            return
        try:
            subprocess.Popen([os.path.join(main_dir, "tool1.sh"), self.ipath])
        except Exception as E:
            MyDialog("Error", str(E), self)
    
    def tool2(self):
        if self.ipath == "" or self.ipath == None:
            return
        try:
            subprocess.Popen([os.path.join(main_dir, "tool2.sh"), self.ipath])
        except Exception as E:
            MyDialog("Error", str(E), self)
    
    def tool3(self):
        if self.ipath == "" or self.ipath == None:
            return
        try:
            subprocess.Popen([os.path.join(main_dir, "tool3.sh"), self.ipath])
        except Exception as E:
            MyDialog("Error", str(E), self)
    
    def on_color_picker(self):
        self._color_picker = True
        QApplication.setOverrideCursor(Qt.CursorShape.PointingHandCursor)
    
    def on_color_picker_d(self):
        self._color_picker_d = True
        QApplication.setOverrideCursor(Qt.CursorShape.PointingHandCursor)
    
    def updateActions(self):
        self.zoomInAct.setEnabled(True)
        self.zoomOutAct.setEnabled(True)
        self.normalSizeAct.setEnabled(True)
        self.fitSizeAct.setEnabled(True)
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
        if self.is_rotated:
            ppixmap = self.imageLabel.pixmap()
        else:
            _frames = self._movie.frameCount()
            if _frames > 1:
                self._movie.stop()
                self._movie.jumpToFrame(0)
            ppixmap = self.original_imageLabel.movie().currentPixmap()
            if _frames > 1:
                self._movie.start()
        self.imageLabel.resize(self.scaleFactor * ppixmap.size())
        #
        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)
        #
        self.zoomInAct.setEnabled(self.scaleFactor/self.pixel_ratio < 3.0)
        self.zoomOutAct.setEnabled(self.scaleFactor/self.pixel_ratio > 0.01)
        #
        self.setWindowTitle("Image Viewer - {} - x{}".format(os.path.basename(self.ipath), round(self.scaleFactor*self.pixel_ratio, 2)))
    
    def adjustScrollBar(self, scrollBar, factor):
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
        if self.is_rotated:
            ppixmap = self.imageLabel.pixmap()
        else:
            ppixmap = self._movie.currentPixmap()
        if ttype == -1:
            image_rotation = 90
        else:
            image_rotation = -90
        # 
        transform = QTransform().rotate(image_rotation)
        ppixmap = ppixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
        #
        self.imageLabel.setPixmap(ppixmap)
        self.is_rotated = True
        self.imageLabel.resize(self.scaleFactor * ppixmap.size())
    
    def eventFilter(self, source, event):
        # mouse scrolling
        if event.type() == QEvent.Type.MouseMove:
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
        #
        return super().eventFilter(source, event)

# type - message - parent
class MyDialog(QMessageBox):
    def __init__(self, *args):
        super(MyDialog, self).__init__(args[-1])
        if args[0] == "Info":
            self.setIcon(QMessageBox.Icon.Information)
            self.setStandardButtons(QMessageBox.StandardButton.Ok)
        elif args[0] == "Error":
            self.setIcon(QMessageBox.Icon.Critical)
            self.setStandardButtons(QMessageBox.StandardButton.Ok)
        elif args[0] == "Question":
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
    #
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
    imageViewer.show()
    sys.exit(app.exec())
