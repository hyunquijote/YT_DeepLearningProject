from PyQt5.QtWidgets import *
from PyQt5 import uic, QtCore
from DB_handler import *
import datetime
import os

ui_path = os.path.dirname(os.path.abspath(__file__))
InStkFormClass = uic.loadUiType(os.path.join(ui_path, "InStkForm.ui"))[0]

# 처리대상 종목 입력 폼 핸들러
class InStkForm_handler(QDialog, InStkFormClass):

    def __init__(self):
        super().__init__()
        # 객체변수 설정
        self.gStkDbh = DB_handler()  # DB 핸들러
        # 폼 설정
        self.setupUi(self)
        self.btnSave.clicked.connect(self.ClickSave)
        self.btnClse.clicked.connect(self.ClickClse)
        self.cmbMktTpCd.addItem("0.국내(주식,선물옵션)")
        self.cmbMktTpCd.addItem("1.해외 주식")
        self.cmbMktTpCd.addItem("2.해외 선물옵션")
        self.cmbMktTpCd.addItem("3.국내 주식")
        self.cmbMktTpCd.addItem("4.국내 선물")
        self.cmbMktTpCd.addItem("5.국내 옵션")
        self.cmbMktTpCd.addItem("6.해외 선물")
        self.cmbMktTpCd.addItem("7.해외 옵션")
        self.dedtStrDt.setCalendarPopup(True)
        self.dedtEndDt.setCalendarPopup(True)
        self.dedtStrDt.setDate(datetime.datetime.today())
        self.dedtEndDt.setDate(QtCore.QDate(3000,1,1))
        return None

    def __del__(self):
        del self.gStkDbh
        return None

    def ClickSave(self):
        try:
            self.gStkDbh.insertProcStk(self.cmbMktTpCd.currentText()[:1],self.edtStkCd.text(),self.dedtStrDt.text().replace("-",""),self.dedtEndDt.text().replace("-",""))
        except Exception as e:
            print(e)
        self.close()
        return None

    def ClickClse(self):
        self.close()
        return None