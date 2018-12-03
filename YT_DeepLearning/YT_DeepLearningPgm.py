from TFMainForm_handler import *

app = QApplication(sys.argv)
mainWindow = None
if(len(sys.argv) == 2):
    mainWindow = TFMainForm_handler("TRUE")
else:
    mainWindow = TFMainForm_handler()
mainWindow.move(800,300)
mainWindow.show()
app.exec_()