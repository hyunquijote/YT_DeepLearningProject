from SndIdxForm_handler import *

app = QApplication(sys.argv)
mainWindow = None
if(len(sys.argv) == 2):
    mainWindow = SndIdxForm_handler("TRUE")
else:
    mainWindow = SndIdxForm_handler()
mainWindow.move(800,20)
mainWindow.show()
app.exec_()