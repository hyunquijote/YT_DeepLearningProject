import sys
from MainForm_handler import *

app = QApplication(sys.argv)
mainWindow = None
if(len(sys.argv) == 2):
    mainWindow = MainForm_handler("TRUE")
else:
    mainWindow = MainForm_handler()
mainWindow.move(20,20)
mainWindow.show()
app.exec_()