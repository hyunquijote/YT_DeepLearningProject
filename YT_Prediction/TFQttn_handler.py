from datetime import datetime, timedelta
from CodeDef import *

# 딥러닝 관련 시세 처리 핸들러
# 메모리 상에 실시간 종목 시세를 가지고 조건이되면 딥러닝APP 로 전송처리함.
class TFQttn_handler:

    def __init__(self,inForm):

        self.StkList     = []     # 처리종목 리스트
        self.StkIdxDict  = {}     # 처리종목 딕셔너리    {종목코드 : 인덱스}
        self.CrPrcDict   = {}     # 현재가/종가 딕셔너리 {시각: [StkList[0]의 현재가, StkList[1]의 현재가, ...] }
        self.FtPrcDict   = {}     # 시가 딕셔너리        {시각: [StkList[0]의 시가, StkList[1]의 시가, ...] }
        self.HgPrcDict   = {}     # 고가 딕셔너리        {시각: [StkList[0]의 고가, StkList[1]의 고가, ...] }
        self.LoPrcDict   = {}     # 저가 딕셔너리        {시각: [StkList[0]의 저가, StkList[1]의 저가, ...] }
        self.CurMn       = ""     # 처리현재시각(HHMM)
        self.MainForm    = inForm # 메인폼

        # 현재시각
        self.CurMn = datetime.today().strftime("%H%M")

        # 처리 종목 초기화
        # 입력 순서는 KODEX레버리지, 처리종목순
        self.StkList = self.MainForm.GetProcStkList()
        self.StkList.insert(0,CodeDef.INDEX_STK_CD)
        StkCnt = len(self.StkList)
        for idx in range(StkCnt):
            self.StkIdxDict[self.StkList[idx]] = idx  # 종목별 인덱스 정보

        # 시세 초기화
        self.CrPrcDict[self.CurMn] = [None] * StkCnt
        self.FtPrcDict[self.CurMn] = [None] * StkCnt
        self.HgPrcDict[self.CurMn] = [None] * StkCnt
        self.LoPrcDict[self.CurMn] = [None] * StkCnt

        return None


    # 시세정보 업데이트
    def UpdateQttn(self, inQttn):
        QttnCnt = len(inQttn)
        for i in range(QttnCnt):
            QttnList = inQttn[i]
            StkCd  = QttnList[CodeDef.REAL_QTTN_COL_STK_CD]
            CrPrc  = QttnList[CodeDef.REAL_QTTN_COL_CRPRC ]
            FtPrc  = QttnList[CodeDef.REAL_QTTN_COL_FTPRC ]
            HgPrc  = QttnList[CodeDef.REAL_QTTN_COL_HGPRC ]
            LoPrc  = QttnList[CodeDef.REAL_QTTN_COL_LOPRC ]
            InTime = QttnList[CodeDef.REAL_QTTN_COL_TIME  ]

            # 시간이동으로 시세전송 및 이월
            if(InTime != self.CurMn and int(InTime) > int(self.CurMn)):
                print("TF시세갱신! InTime, self.CurMn:", InTime, self.CurMn)
                # 1분전 시세를 이월
                self.CrPrcDict[InTime] = self.CrPrcDict[self.CurMn]
                self.FtPrcDict[InTime] = self.FtPrcDict[self.CurMn]
                self.HgPrcDict[InTime] = self.HgPrcDict[self.CurMn]
                self.LoPrcDict[InTime] = self.LoPrcDict[self.CurMn]
                # 딥러닝 전송 및 시세 저장
                self.SndTFQttn(self.CurMn)

                # 처리시각 갱신
                self.CurMn = InTime
            # -- 끝 --

            # 현시세 갱신
            idx = self.StkIdxDict[StkCd]
            self.CrPrcDict[self.CurMn][idx] = CrPrc
            self.FtPrcDict[self.CurMn][idx] = FtPrc
            self.HgPrcDict[self.CurMn][idx] = HgPrc
            self.LoPrcDict[self.CurMn][idx] = LoPrc

        return None


    # 딥러닝 프로그램에 시세전송
    # inProcMn : 처리대상 시각
    def SndTFQttn(self, inProcMn):
        chk = inProcMn +"|"
        SendOk = True
        SndData = "QTTN|"
        # 종목/시세리스트 구성
        # QTTN|종목코드|시각(HHMM)|현재or종가|시가|고가|저가|E|종목코드....|END
        StkCnt = len(self.StkList)
        try:
            for idx in range(StkCnt):
                SndData = SndData + self.StkList[idx] + "|"
                SndData = SndData + inProcMn + "|"
                # 현재가
                if(self.CrPrcDict[inProcMn][idx] is None):
                    SndData = SndData + "None|"
                else:
                    SndData = SndData + self.CrPrcDict[inProcMn][idx] + "|"
                # 시가
                if (self.FtPrcDict[inProcMn][idx] is None):
                    SndData = SndData + "None|"
                else:
                    SndData = SndData + self.FtPrcDict[inProcMn][idx] + "|"
                # 고가
                if (self.HgPrcDict[inProcMn][idx] is None):
                    SndData = SndData + "None|"
                else:
                    SndData = SndData + self.HgPrcDict[inProcMn][idx] + "|"
                # 저가
                if (self.LoPrcDict[inProcMn][idx] is None):
                    SndData = SndData + "None|"
                else:
                    SndData = SndData + self.LoPrcDict[inProcMn][idx] + "|"
                # 종목종료표시
                SndData = SndData + "E|"


                if (self.CrPrcDict[inProcMn][idx] is None):
                    print("빈시세 발견으로 전송불가:", inProcMn, self.StkList[idx], self.CrPrcDict[inProcMn][idx])
                    SendOk = False
                    chk = chk + self.StkList[idx] + "|None|"
                else:
                    chk = chk + self.StkList[idx] + "|" + self.CrPrcDict[inProcMn][idx] + "|"

            SndData = SndData + "END"
        except Exception as e:
            print(e)
            return None

        print("시세갱신상황:",chk)

        # 전송 및 시세 저장
        if(SendOk):
            self.MainForm.SendTensorFlow(SndData)

        return None

    # 최초 시세 설정
    # 최근시세로 설정하며
    # 전체 종목의 시세가 다 찰때까지 기다리는것을 방지한다.
    # inQttn : 최근시세 (처리종목순서와 같다)
    def SetFstQttn(self,inQttn):
        StkCnt = len(self.StkList)
        for idx in range(StkCnt):
            # 시세 갱신
            stkIdx = self.StkIdxDict[self.StkList[idx]]
            self.CrPrcDict[self.CurMn][stkIdx] = inQttn[idx]
            self.FtPrcDict[self.CurMn][stkIdx] = inQttn[idx]
            self.HgPrcDict[self.CurMn][stkIdx] = inQttn[idx]
            self.LoPrcDict[self.CurMn][stkIdx] = inQttn[idx]

        print("최초시세설정:",self.CurMn)
        self.SndTFQttn(self.CurMn)
        return None
