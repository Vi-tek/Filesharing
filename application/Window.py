import logging
import os

import qrcode.image.pil
from core import sharing_server as shs
from PIL.ImageQt import ImageQt

from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot, QRegExp, QSize, QThread
from PyQt5.QtGui import QRegExpValidator, QIcon, QPixmap
from PyQt5.QtWidgets import \
    QLineEdit, QPushButton, QFileDialog, QLabel, QTextEdit, QMessageBox, \
    QFrame, QWidget, QVBoxLayout, QHBoxLayout, QApplication, QMainWindow

logger = logging.getLogger(__name__)


class Worker(QObject):
    logs = pyqtSignal(str)
    qr_code = pyqtSignal(qrcode.image.pil.PilImage)

    def __init__(self, *, path, port):
        super(Worker, self).__init__()
        self.path = path
        self.port = port

    @pyqtSlot()
    def start_server(self):
        self.server = shs.HTTPServer(self.path, self.port)
        self.logs.emit(f"{self.server.logs()}")
        self.qr_code.emit(self.server.QR_code())
        self.server.run_server()


class PathInput(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Path Like: C:/Users/user/Desktop...")


class PortInput(QLineEdit):
    def __init__(self, parent=None):
        super(PortInput, self).__init__(parent)
        validator = QRegExpValidator(QRegExp("[0-9]*"))
        self.setValidator(validator)
        self.setPlaceholderText("Port")
        self.textChanged.connect(self.check_port_value)

    def check_port_value(self):
        text = self.text()
        text_length = len(text)
        if text_length > 0:
            if int(text) > 65535 or text_length > 5:
                self.setText("65535")
                self.msgbox = MessageBox(
                    MessageBox.Icon.Warning,
                    "Invalid Port Number",
                    "Port number must be less than 65535")
                self.msgbox.show()


class RunButton(QPushButton):
    def __init__(self, parent=None):
        super(RunButton, self).__init__(parent)
        self.setText("Run")
        self.setObjectName("btn_run")


class BrowseButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("Browse")



class BrowseDirectory(QFileDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        app_icon = QIcon()
        app_icon.addFile(os.getcwd() + "..//assets//invisible.ico", QSize(256, 256))
        self.setWindowIcon(app_icon)

    def open(self):
        directory_name = self.getExistingDirectory(self, "Select Folder")
        return directory_name.replace("/", "\\")


class QR_Label(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)


class Logger(logging.Handler, QObject):
    appendPlainText = pyqtSignal(str)

    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)

    def emit(self, record):
        msg = str(record.getMessage())
        self.appendPlainText.emit(msg)



class Logs(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setPlaceholderText("Logs...")
        self.setReadOnly(True)


class MessageBox(QMessageBox):
    def __init__(self, icon: QMessageBox.Icon, title: str, text: str, parent=None):
        super(MessageBox, self).__init__(parent)
        self.setIcon(icon)
        self.setWindowIcon(MainWindow().windowIcon())
        self.setWindowTitle(title)
        self.setText(text)


class Line(QFrame):
    def __init__(self, parent=None):
        super(Line, self).__init__(parent=parent)
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)
        self.setObjectName("line")


class MainWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.path_input = PathInput()
        self.port_input = PortInput()
        self.btn_browse = BrowseButton()
        self.btn_run = RunButton()
        self.QR_Label = QR_Label()
        self.QR_Label.resize(200, 200)



        self.logs = Logs()
        self.line1 = Line()
        self.line2 = Line()

        self.browse = BrowseDirectory()

        consoleHandler = Logger()
        consoleHandler.appendPlainText.connect(self.logs.append)
        logger.addHandler(consoleHandler)
        shs.logger.addHandler(consoleHandler)

        self.first_layout = QVBoxLayout()
        self.second_layout = QHBoxLayout()

        self.setLayout(self.gui())

        self.btn_browse.clicked.connect(self.browse_files)
        self.btn_run.clicked.connect(self.run_server)

    def browse_files(self):
        self.path_input.setText(self.browse.open())

    def run_server(self):
        if self.path_input.text() != "" and self.port_input.text() != "":
            if self.btn_run.text() != "Stop":
                self.change_btn_on_run("Stop", False)

                self.obj = Worker(path=self.path_input.text(), port=self.port_input.text())
                self.thread = QThread(self)

                self.obj.logs.connect(self.logs.append)
                self.obj.qr_code.connect(self.set_qr_code)
                self.obj.moveToThread(self.thread)

                self.thread.started.connect(self.obj.start_server)
                self.thread.start()

            else:
                self.obj.server.stop_()
                self.thread.quit()

                del self.obj
                del self.thread
                self.logs.clear()
                self.change_btn_on_run("Run", True)


    def set_qr_code(self, im):
        self.QR_Label.setPixmap(QPixmap.fromImage(ImageQt(im)))

    def change_btn_on_run(self, text: str, enabled: bool):
        self.btn_run.setText(text)
        self.btn_browse.setEnabled(enabled)
        self.path_input.setEnabled(enabled)
        self.port_input.setEnabled(enabled)

    def gui(self):


        left = QFrame()
        left.setFrameShape(QFrame.StyledPanel)

        self.second_layout.addWidget(self.path_input)
        self.second_layout.setStretchFactor(self.path_input, 2)
        self.second_layout.addWidget(self.btn_browse)
        self.second_layout.addWidget(self.port_input)
        self.second_layout.addWidget(self.btn_run)

        self.first_layout.addLayout(self.second_layout)
        self.first_layout.addWidget(self.line1)
        self.first_layout.addWidget(self.logs)
        self.first_layout.addWidget(self.line2)
        self.first_layout.addWidget(self.QR_Label)

        return self.first_layout


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        WIDTH, HEIGHT = 950, 600

        styleSheet = """
        QMainWindow {
            background-color: #1f1f1f;            
        }
    
        QLineEdit {
            font-size: 10pt;
            background-color: #3d3d3d;
            color: 	#c8c8c8;
            border: 0px;
            border-style: flat;
            padding: 3px;
        }
        
        QLineEdit:hover {
            background-color: #1f1f1f;
            color: #ffffff;

        }
        QLineEdit:focus{
            color: #ffffff;
            background-color: #1f1f1f;
        }
        
        QPushButton {
            font-size: 10pt;
            padding: 4px;
            padding-left: 15px;
            padding-right: 15px;    
            border-style: flat;
            background-color: #424242;
            color: 	#c8c8c8;
            font-family: Cascadia;
        }
        
        QPushButton:hover {
            background-color: #1f1f1f;
            color: #ffffff;
        }
        
        QPushButton:pressed {
            background-color: #0f0f0f;
        }
        
        #btn_run {
            padding-right: 15px;
            padding-left: 15px;
        }
        
        QTextEdit {
            font-size: 10pt;
            background-color: #1f1f1f;
            border: 0px;
            color: rgb(255, 255, 255);
        }
        
        QTextEdit:focus {
            border: none;
            outline: none;
        }
        
        #line {
            border-top: 1px solid #9e9e9e;
        }
        """
        self.setStyleSheet(styleSheet)
        self.setWindowTitle("HTTP File Sharing")
        app_icon = QIcon()
        app_icon.addFile(os.getcwd() + "\Assets\invisible.ico", QSize(256, 256))
        self.setWindowIcon(app_icon)

        self.resize(WIDTH, HEIGHT)
        self.central_widget = MainWidget()
        self.setCentralWidget(self.central_widget)

def mains():
    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
