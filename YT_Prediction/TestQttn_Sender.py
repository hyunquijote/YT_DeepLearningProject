import threading
import time
from  CodeDef    import *
from  DB_handler import *

class TestQttn_Sender(threading.Thread):

    def __init__(self, inForm):
        threading.Thread.__init__(self)
        self.daemon = True

        # 테스트 시세 수신제어
        global isTestQttnRunning
        # 진행시세 index
        global qIndex
        qIndex = 0
        # 데이터 준비 확인
        global existTestQttn
        existTestQttn = False
        # 시세 종목리스트
        global QttnStkList
        # 테스트시세
        global SavedQttnList
        global SavedQttnCnt
        SavedQttnList = None
        SavedQttnCnt  = 0

        # 메인폼
        self.MainForm = inForm
        # DB 핸들러
        self.DBH = DB_handler()

        # 시세종목리스트 초기화
        QttnStkList = self.MainForm.GetProcStkList()
        QttnStkList.insert(0, CodeDef.INDEX_STK_CD)

        # 테스트시세준비
        SavedQttnList = self.DBH.querySavedTestQttn()
        SavedQttnCnt  = len(SavedQttnList.index)
        print("테스트 시세 조회완료")

        return None

    def run(self):
        global isTestQttnRunning
        global qIndex
        global SavedQttnList
        global SavedQttnCnt
        global QttnStkList
        global QttnStkCnt
        global existTestQttn

        # 루프 돌면서 클라이언트로 들어온 데이터 그대로 재 전송
        isTestQttnRunning = True
        while (1):
            # 전문 구성 및 전송
            for idx in range(qIndex, SavedQttnCnt):
                time.sleep(1)
                SavedQttn = SavedQttnList.iloc[idx].tolist()
                SndData   = "QTTN_TEST|"
                Mn        = int(SavedQttn.pop(1))  # 시각
                KospiQttn = None
                for qIdx in range(len(SavedQttn)):
                    SndData = SndData + QttnStkList[qIdx] + "|" + str(Mn).zfill(4) + "|" + str(SavedQttn[qIdx]) + "|0|0|0|E|"
                    if(QttnStkList[qIdx]== CodeDef.INDEX_STK_CD):
                        KospiQttn = CodeDef.INDEX_STK_CD + "|" + str(Mn).zfill(4) + "|" + str(SavedQttn[qIdx]) + "|0|0|0|E|END"
                # 딥러닝에 전송
                SndData = SndData + "END"
                self.MainForm.SendTensorFlow(SndData)
                qIndex = idx
                #print("테스트시세 qIndex, SndData:",qIndex,SndData)
                # 현 ETF 시세는 주가주신으로 처리함.
                self.MainForm.ProcRcvRealQttn("KOSPI_INDEX", KospiQttn)

                while(isTestQttnRunning == False):
                    time.sleep(1)
                    #print("테스트 시세 대기중")

        print("테스트 시세 Loop 종료됨")
        return None

    # 수신 중지
    def DoStop(self):
        global isTestQttnRunning
        isTestQttnRunning = False

        print("테스트 시세수신 종료!!!")
        return None

    # 수신 재시작
    def DoRestart(self):
        global isTestQttnRunning
        isTestQttnRunning = True

        print("테스트 시세수신 재시작!!!")
        return None
