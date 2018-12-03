import sys, os
import ctypes
from TradarAPI_handler import *
from GlobalAPI_handler import *
from PyQt5 import uic
from PyQt5.QtWidgets import *
from SndSckt_handler import *
from DB_handler import *

ui_path = os.path.dirname(os.path.abspath(__file__))
SndIdxFormClass = uic.loadUiType(os.path.join(ui_path, "RcvIdxForm.ui"))[0]

class SndIdxForm_handler(QDialog, SndIdxFormClass):

    def __init__(self, isUnite="None"):

        # 통합실행일경우 3초 딜레이
        if(isUnite == "TRUE"):
            time.sleep(5)

        super().__init__()

        # 폼 설정
        self.setupUi(self)

        # 전역변수
        global isRcv         # 수신중여부
        isRcv         = False

        # 객체변수 설정
        self.gAPIH = None # API 핸들러
        self.gSckt = None # 송신소켓 핸들러
        self.gDBH  = None # DB 핸들러

        # 버튼이벤트 핸들러 설정
        self.btnRcvIdx.clicked.connect(self.ClickRcvIdx)          # 지수수신시작 버튼
        self.btnStopRcvIdx.clicked.connect(self.ClickStopRcvIdx)  # 지수수신종료 버튼
        self.btnInitQttn.clicked.connect(self.ClickInitQttn)      # 지수수시세 초기화 버튼

        # 상태표시
        self.edtStat.setText("시작전")

        # API 초기화
        try:
            self.gAPIH = TradarAPI_handler()
            #self.gAPIH = GlobalAPI_handler()
            self.gAPIH.initAPI(True, self) # 전송모드 초기화
            print("TRADAR end ")
        except Exception as e:
            print(e)

        # 전송소켓 초기화
        self.gSckt = SndSckt_handler()

        # DB 핸들러 초기화
        self.gDBH = DB_handler()

        # 지수최근 동기화일자 표시
        self.SetLastDtMn()

        return None

    def __del__(self):
        print("dddd")
        try:
            # API 종료
            self.APIH.CloseAPI()
            # 소켓종료
            if (self.gSckt.GetOnSock() == True):
                self.gSckt.ClseSckt()

        except Exception as e:
            print("종료에러:",e)
        return None

    # 지수수신처리 시작
    def ClickRcvIdx(self):
        global isRcv
        if(isRcv):
            # 나중에 종목별로 제어할것
            ctypes.windll.user32.MessageBoxW(0, "이미 실시간시세 등록된 종목입니다.", "알림", 0)
            return None
        isRcv = True

        # 소켓연결
        try:
            if (self.gSckt.GetOnSock() == False):
                self.gSckt.CnntSckt(CodeDef.PORT_INDEX_QTTN)
        except Exception as e:
            print("전송소켓 연결 실패 에러 :",e)
            return None

        # 데이터 요청
        self.edtStat.setText("수신중")
        self.gAPIH.OnRequest("REAL_QTTN","11",CodeDef.INDEX_STK_CD)
        #self.gAPIH.OnRequest("REAL_QTTN", "61", "ESM18")
        return None

    # 지수수신처리 종료
    def ClickStopRcvIdx(self):
        global isRcv
        if(isRcv):
            # 데이터 요청중지
            self.edtStat.setText("수신종료 중")
            self.gAPIH.StopRealRcv(None, CodeDef.INDEX_STK_CD)
            #self.gAPIH.StopRealRcv(None, "ESM18")
            self.edtStat.setText("수신종료")
        return None

    # 실시간 시세전송]
    # inStkCd  : 종목코드
    # inTime   : 시각(HHMM)
    # inCrPrc  : 현재가/종가
    # inFtPrc  : 시가
    # inHgPrc  : 고가
    # inLoPrc  : 저가
    def SendRealQttn(self, inStkCd, inTime, inCrPrc, inFtPrc, inHgPrc, inLoPrc):
        # 소켓전송
        QttnInfo = inStkCd + "|" + inTime + "|" + inCrPrc + "|" + inFtPrc + "|" + inHgPrc + "|" + inLoPrc + "|E"

        self.gSckt.SendData(QttnInfo)
        return None

    # 지수시세초기화 버튼
    def ClickInitQttn(self):
        Chk = ctypes.windll.user32.MessageBoxW(0, "초기화 시작합니다.", "알림", 1)
        if (Chk == 2):
            return None
        try:
            LastDt = ""
            LastMn = ""
            # 최근 동기화일 가져옴
            StkInfo = self.gDBH.queryProcStkInfo(CodeDef.INDEX_STK_CD)
            RowCnt = len(StkInfo.index)
            if(RowCnt == 0):
                LastDt = CodeDef.INIT_STR_DT_DEFAULT
                LastMn = CodeDef.INIT_STR_MN_DEFAULT
            else:
                LastDtMn = StkInfo.iat[0, CodeDef.PROC_STK_COL_LAST_DT_MN]
                LastDt   = LastDtMn[:8]
                LastMn   = LastDtMn[-4:]
                if(LastDt is None or len(LastDt) == 0):
                    LastDt = CodeDef.INIT_STR_DT_DEFAULT
                if (LastMn is None or len(LastMn) == 0):
                    LastMn = CodeDef.INIT_STR_MN_DEFAULT

            print("초기화 시작:", CodeDef.INDEX_STK_CD, LastDt, LastMn, CodeDef.INIT_END_DT_DEFAULT, CodeDef.INIT_END_MN_DEFAULT)
            # 기존데이터 삭제
            self.gDBH.deleteMnQttn("KOSPI",CodeDef.INDEX_STK_CD, LastDt, LastMn, CodeDef.INIT_END_DT_DEFAULT, CodeDef.INIT_END_MN_DEFAULT)

            # 데이터 수신 (빈분봉이 없기 때문에 따로 분봉채우기를 할 필요가 없다.)
            self.gAPIH.InitMnQttn(CodeDef.MKT_TP_CD_INTERNAL, CodeDef.INDEX_STK_CD, LastDt, LastMn, CodeDef.INIT_END_DT_DEFAULT, CodeDef.INIT_END_MN_DEFAULT)

            # 최종 초기화 일자시각 입력
            self.gDBH.updateProcStkLastDtMn("99", CodeDef.INDEX_STK_CD, (CodeDef.INIT_END_DT_DEFAULT + CodeDef.INIT_END_MN_DEFAULT))

            print("초기화 종료")


        except Exception as e:
            print("KOSPI 시세 초기화 에러:", e)
            return None

        # 최근동기화 표시
        self.SetLastDtMn()
        ctypes.windll.user32.MessageBoxW(0, "초기화 완료되었습니다.", "알림", 0)

        return None

    # 최근 지수 동기화일자 표시
    def SetLastDtMn(self):
        StkInfo = self.gDBH.queryProcStkInfo(CodeDef.INDEX_STK_CD)
        RowCnt = len(StkInfo.index)
        if (RowCnt == 0):
            self.edtLastDtMn.setText("데이터 없음")
        else:
            LastDtMn = StkInfo.iat[0, CodeDef.PROC_STK_COL_LAST_DT_MN]
            LastDt = LastDtMn[:8]
            LastMn = LastDtMn[-4:]
            if (LastDt is None or len(LastDt) == 0):
                self.edtLastDtMn.setText("데이터 없음")
            else:
                self.edtLastDtMn.setText(LastDt+"-"+LastMn)

        return None
