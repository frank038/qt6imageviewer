#!/usr/bin/python3
# V. 0.5

from PyQt6.QtCore import Qt, QMimeDatabase, QEvent, QSize, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QImage, QImageReader, QPixmap, QPalette, QPainter, QIcon, QTransform, QMovie, QBrush, QColor
from PyQt6.QtPrintSupport import QPrintDialog, QPrinter
from PyQt6.QtWidgets import QAbstractItemView, QListWidget, QListWidgetItem, QHBoxLayout, QVBoxLayout, QWidget, QLabel, QSizePolicy, QScrollArea, QMessageBox, QMainWindow, QMenu, QFileDialog
import subprocess, os, time
from cfg_imageviewer import *

skip_pil = 0
if with_pil:
    from PIL import Image, ImageQt
else:
    skip_pil = 1

# home dir
MY_HOME = os.path.expanduser('~')

# this program working directory
main_dir = os.getcwd()

os.chdir(MY_HOME)

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
    with open ("winsize.cfg", "r") as ifile:
        fcontent = ifile.readline()
        WW1, HH1 = fcontent.split(";")
        WW = int(WW1)
        HH = int(HH1.strip())
except:
    try:
        with open("winsize.cfg", "w") as ifile:
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
                # find better filter
                if image_type in SUPPORTED_MIME:
                    _icon = None
                    try:
                        if (skip_pil == 0) and (image_type in with_pil):
                            image = Image.open(fileName)
                            _pix = ImageQt.toqpixmap(image)
                            _pix.scaled(QSize(ICON_SIZE,ICON_SIZE), Qt.AspectRatioMode.KeepAspectRatio)
                            _icon = QIcon(_pix)
                            if _icon.isNull():
                                del _icon
                                continue
                    except:
                        continue
                    #
                    try:
                        _pix = QPixmap(fileName).scaled(QSize(ICON_SIZE,ICON_SIZE), Qt.AspectRatioMode.KeepAspectRatio)
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
        self.ianimated = None
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
        self.setWindowIcon(QIcon(os.path.join(main_dir, "QImageViewer.svg")))
        #
        self.layout().setContentsMargins(0,0,0,0)
        self.scrollArea.setContentsMargins(0,0,0,0)
        self.imageLabel.setContentsMargins(0,0,0,0)
        #
        self.scrollarea_size = None
        self._is_shown = False
        self._is_resized = False
        
    
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
        # # error in reading a file
        # if ret == -2:
            # if ttype == "i":
                # self.on_open2(new_idx+1, ttype)
            # elif ttype == "d":
                # self.on_open2(new_idx-1, ttype)
    
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
        # update the scrollarea size
        if self._is_resized == True:
            self._is_resized = False
            self.scrollarea_size = self.scrollArea.size()
        _WW = self.scrollarea_size.width()-self.hbar_height
        _HH = self.scrollarea_size.height()-self.vbar_width
        #
        ppixmap = None
        self.is_animated = False
        if self.ianimated:
            self.ianimated.stop()
            self.ianimated = None
        #
        image_type = ""
        try:
            image_type = QMimeDatabase().mimeTypeForFile(fileName, QMimeDatabase.MatchMode.MatchDefault).name()
            if image_type in img_skipped:
                if not self.is_key_nav:
                    QMessageBox.information(self, "Image Viewer", "Cannot load {}.\nSkipped by user.".format(fileName))
                return -2
            elif (skip_pil == 0) and (image_type in with_pil):
                image = Image.open(fileName)
                ppixmap = ImageQt.toqpixmap(image)
                if not ppixmap:
                    QMessageBox.information(self, "Image Viewer", "Cannot load {} with PIL.".format(fileName))
                    return -1
            else:
                image = QImage(fileName)
                if image.isNull():
                    if not self.is_key_nav:
                        QMessageBox.information(self, "Image Viewer", "Cannot load {}.".format(fileName))
                    return -2
                if image_type in animated_format:
                    self.is_animated = True
                else:
                    ppixmap = QPixmap.fromImage(image)
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
        if self.is_animated:
            self.ianimated = QMovie(fileName)
            self.imageLabel.setMovie(self.ianimated)
            self.ianimated.start()
            # 
            ppixmap = self.ianimated.currentPixmap()
            self.ianimated.stop()
            #
            image_width = ppixmap.width()
            image_height = ppixmap.height()
            #
            _a = (_WW-2)/image_width
            _b = (_HH-2)/image_height
            self.scaleFactor = min(_a, _b)
            #
            self.imageLabel.resize(self.scaleFactor * ppixmap.size())
            self.scaleFactorStart = self.scaleFactor
            #
            self.ianimated.start()
        else:
            self.imageLabel.setPixmap(ppixmap)
            #
            image_width = ppixmap.width()
            image_height = ppixmap.height()
            #
            _a = (_WW-2)/image_width
            _b = (_HH-2)/image_height
            self.scaleFactor = min(_a, _b)
            #
            self.imageLabel.resize(self.scaleFactor * ppixmap.size())
            self.scaleFactorStart = self.scaleFactor
        #
        if self.imageLabel.isVisible() == False:
            self.imageLabel.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            self.imageLabel.setVisible(True)
            self.scrollArea.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            self.printAct.setEnabled(True)
            self.updateActions()
            self.infoAct.setEnabled(True)
        # 
        self.setWindowTitle("Image Viewer - {} - x{}".format(os.path.basename(self.ipath), round(self.scaleFactor, 2)))
        #
        if self.is_animated:
            self.rotateLeftAct.setEnabled(False)
            self.rotateRightAct.setEnabled(False)
        else:
            self.rotateLeftAct.setEnabled(True)
            self.rotateRightAct.setEnabled(True)
    
    #
    def print_(self):
        dialog = QPrintDialog(self.printer, self)
        if dialog.exec():
            painter = QPainter(self.printer)
            rect = painter.viewport()
            size = self.imageLabel.pixmap().size()
            size.scale(rect.size(), Qt.KeepAspectRatio)
            painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
            painter.setWindow(self.imageLabel.pixmap().rect())
            painter.drawPixmap(0, 0, self.imageLabel.pixmap())
    
    def info_(self):
        if self.is_animated:
            pw = ""
            ph = ""
            pd = ""
            try:
                ppixmap = self.ianimated.currentPixmap()
                pw = ppixmap.width()
                ph = ppixmap.height()
                pd = ppixmap.depth()
            except:
                pw = self.ianimated.frameRect().width()
                ph = self.ianimated.frameRect().height()
                pd = "Unknown"
            imime = QMimeDatabase().mimeTypeForFile(self.ipath, QMimeDatabase.MatchMode.MatchDefault)
            imime_name = imime.name()
            QMessageBox.information(self, "Image Info", "Name: {}\nWidth: {}\nHeight: {}\nDepth: {}\nType: {}".format(os.path.basename(self.ipath), pw, ph, pd, imime_name))
            return
        # 
        ppixmap = self.imageLabel.pixmap()
        if not ppixmap.isNull():
            pw = ppixmap.width()
            ph = ppixmap.height()
            pd = ppixmap.depth()
            imime = QMimeDatabase().mimeTypeForFile(self.ipath, QMimeDatabase.MatchMode.MatchDefault)
            imime_name = imime.name()
            QMessageBox.information(self, "Image Info", "Name: {}\nWidth: {}\nHeight: {}\nDepth: {}\nType: {}".format(os.path.basename(self.ipath), pw, ph, pd, imime_name))
    
    def zoomIn(self):
        self.scaleImage(1.25)
    
    def zoomOut(self):
        self.scaleImage(0.8)
    
    def normalSize(self):
        self.scaleImage(self.scaleFactorStart/self.scaleFactor)
    
    def createActions(self):
        self.openAct = QAction("&Open...", self, shortcut="Ctrl+o", triggered=self.open)
        self.printAct = QAction("&Print...", self, shortcut="Ctrl+p", enabled=False, triggered=self.print_)
        self.infoAct = QAction("&Info", self, shortcut="Ctrl+i", enabled=False, triggered=self.info_)
        self.exitAct = QAction("E&xit", self, shortcut="Ctrl+q", triggered=self.close)
        #
        self.zoomInAct = QAction("Zoom In (25%)", self, shortcut="Ctrl++", enabled=False, triggered=self.zoomIn)
        self.zoomOutAct = QAction("Zoom Out (25%)", self, shortcut="Ctrl+-", enabled=False, triggered=self.zoomOut)
        self.normalSizeAct = QAction("Normal Size", self, shortcut="Ctrl+n", enabled=False, triggered=self.normalSize)
        self.rotateLeftAct = QAction("Rotate Left", self, shortcut="Ctrl+e", enabled=False, triggered=self.rotateLeft)
        self.rotateRightAct = QAction("Rotate Right", self, shortcut="Ctrl+r", enabled=False, triggered=self.rotateRight)
        self.leftPanelAct = QAction("Left Panel", self, shortcut="Ctrl+p", enabled=False, triggered=self.on_leftpanelaction)
        #
        self.tool1Act = QAction("{}".format(TOOL1NAME or "Tool1"), self, shortcut="Ctrl+1", enabled=True, triggered=self.tool1)
        self.tool2Act = QAction("{}".format(TOOL2NAME or "Tool2"), self, shortcut="Ctrl+2", enabled=True, triggered=self.tool2)
        self.tool3Act = QAction("{}".format(TOOL3NAME or "Tool3"), self, shortcut="Ctrl+3", enabled=True, triggered=self.tool3)
    
    def createMenus(self):
        self.fileMenu = QMenu("&File", self)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.printAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.infoAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = QMenu("&View", self)
        self.viewMenu.addAction(self.zoomInAct)
        self.viewMenu.addAction(self.zoomOutAct)
        self.viewMenu.addAction(self.normalSizeAct)
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

    def updateActions(self):
        self.zoomInAct.setEnabled(True)
        self.zoomOutAct.setEnabled(True)
        self.normalSizeAct.setEnabled(True)
        self.rotateLeftAct.setEnabled(True)
        self.rotateRightAct.setEnabled(True)
        self.leftPanelAct.setEnabled(True)
    
    def scaleImage(self, factor):
        self.scaleFactor *= factor
        if self.is_animated:
            ppixmap = self.ianimated.currentPixmap()
        else:
            ppixmap = self.imageLabel.pixmap()
        self.imageLabel.resize(self.scaleFactor * ppixmap.size())
        #
        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)
        #
        self.zoomInAct.setEnabled(self.scaleFactor < 3.0)
        self.zoomOutAct.setEnabled(self.scaleFactor > 0.333)
        #
        self.setWindowTitle("Image Viewer - {} - x{}".format(os.path.basename(self.ipath), round(self.scaleFactor, 2)))
    
    
    #
    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value()
                               + ((factor - 1) * scrollBar.pageStep() / 2)))
    
    #
    def closeEvent(self, event):
        self.on_close()
    
    #
    def on_close(self):
        new_w = self.size().width()
        new_h = self.size().height()
        if new_w != int(WW) or new_h != int(HH):
            try:
                ifile = open("winsize.cfg", "w")
                ifile.write("{};{}".format(new_w, new_h))
                ifile.close()
            except Exception as E:
                pass
        QApplication.quit()
    
    # load the next or previous image in the folder
    def keyNav(self, incr_idx):
        self.is_key_nav = 1
        if self.ianimated:
            self.ianimated.stop()
            self.ianimated = None
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
        ppixmap = self.imageLabel.pixmap()
        if ttype == -1:
            image_rotation = 90
        else:
            image_rotation = -90
        # 
        transform = QTransform().rotate(image_rotation)
        ppixmap = ppixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
        # update the label
        self.imageLabel.setPixmap(ppixmap)
        self.imageLabel.adjustSize()
        self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size())
    
    
    def eventFilter(self, source, event):
        # mouse scrolling
        if event.type() == QEvent.Type.MouseMove:
            if self.last_time_move_v == 0:
                self.last_time_move_v = event.pos().y()
            vdistance = self.last_time_move_v - event.pos().y()
            self.vscrollbar.setValue(self.vscrollbar.value() + vdistance)
            self.last_time_move_v = event.pos().y()
            #
            if self.last_time_move_h == 0:
                self.last_time_move_h = event.pos().x()
            hdistance = self.last_time_move_h - event.pos().x()
            self.hscrollbar.setValue(self.hscrollbar.value() + hdistance)
            self.last_time_move_h = event.pos().x()
            return True
        elif event.type() == QEvent.Type.MouseButtonRelease:
            self.last_time_move_h = 0
            self.last_time_move_v = 0
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
        self.setWindowIcon(QIcon("icons/program.svg"))
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
