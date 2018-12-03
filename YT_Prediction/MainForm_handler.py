from PyQt5.QtCore      import *
from InStkForm_handler import *
from GlobalAPI_handler import *
from Chart_handler     import *
from RcvSckt_handler   import *
from SndSckt_handler   import *
from TFQttn_handler    import *
from TestQttn_Sender   import *
from PyQt5             import uic
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

ui_path = os.path.dirname(os.path.abspath(__file__))
MainFormClass = uic.loadUiType(os.path.join(ui_path, "MainForm.ui"))[0]

# 메인 폼 핸들러
class MainForm_handler(QMainWindow, MainFormClass):

    def __init__(self, isUnite="None"):
        super().__init__()

        # 폼 설정
        self.setupUi(self)

        # 객체변수 설정
        self.DBH         = None # DB 핸들러
        self.APIH        = None # API 핸들러
        self.CrtH        = None # 차트 핸들러
        self.QttnSctkT   = None # 시세수신소켓쓰레드
        self.TfRcvSctkT  = None # 딥러닝수신소켓쓰레드
        self.TfSndSctkT  = None # 딥러닝송신소켓
        self.ProcStkList = []    # 처리대상 종목리스트
        self.TestQttnSnd = None # 테스트 시세 전송 쓰레드

        # 수신소켓 동작여부
        self.NowRcvIdxQttn         = False
        self.NowRcvGlobalQttn      = False
        self.NowTensorFlow         = False
        self.NowRcvGlobalSavedQttn = False

        # 버튼이벤트 핸들러 설정
        self.btnInStkCd.clicked.connect           (self.ClickInStkCd           ) # 처리종목 입력
        self.btnDelStkCd.clicked.connect          (self.ClickDelStkCd          ) # 처리종목 삭제
        self.btnInitMnQttn.clicked.connect        (self.ClickInitMnQttn        ) # 처리종목 분봉시세 초기화
        self.btnRcvIdxQttn.clicked.connect        (self.ClickRcvIdxQttn        ) # 지수 실시간 시세 받기/종료
        self.btnRcvGlobalQttn.clicked.connect     (self.ClickRcvGlobalQttn     ) # 글로벌 실시간 시세 받기/종료
        self.btnTensorFlow.clicked.connect        (self.ClickTensorFlow        ) # 딥러닝 송수신 동작/중지
        self.btnRcvGlobalSavedQttn.clicked.connect(self.ClickRcvGlobalSavedQttn) # 저장된 글로벌 시세 받기/종료

        self.btnMnQttnOrd.clicked.connect         (self.ClickMnQttnOrd         ) # 빈분봉처리
        self.btnSetFstQttn.clicked.connect        (self.ClickSetFstQttn        ) # 첫시세 설정
        self.btnMnQttnOrd.setVisible(False)
        self.btnSetFstQttn.setVisible(False)

        # DB 핸들러 초기화
        try:
            self.DBH = DB_handler()  # DB 핸들러
        except Exception as e:
            print("DB 핸들러 오류:",e)

        # API 핸들러 초기화
        try:
            self.APIH = GlobalAPI_handler()
            self.APIH.initAPI(False, self) # 전송모드일 경우 True, 메인폼 수신 False
            print("GLOBAL end ")
        except Exception as e:
            print("API초기화오류:",e)

        # 차트 초기화
        self.fig    = plt.Figure()
        self.canvas = FigureCanvas(self.fig)
        self.vbChart.addWidget(self.canvas)
        self.CrtH   = Chart_handler()
        self.CrtH.SetHandler(self.fig, self.canvas)

        # 처리대상 종목 초기화
        self.ShowProcStkList()

        # 딥러닝 시세 핸들러 초기화
        self.TFH  = TFQttn_handler(self)

        # 통합실행의 경우 수신준비
        if (isUnite == "TRUE"):
            #3초 딜레이후 실행
            time.sleep(3)
            # 지수시세 실시간
            self.ClickRcvIdxQttn()
            # 텐서플로 실시간
            self.ClickTensorFlow()

        return None

    def __del__(self):
        self.APIH.CloseAPI()
        return None

    # 처리대상종목 입력
    def ClickInStkCd(self):
        if (self.NowRcvGlobalQttn):
            ctypes.windll.user32.MessageBoxW(0, "글로번 시세 수신중으로 추가 불가", "알림", 0)
            return None
        inStkForm = InStkForm_handler()
        inStkForm.exec_()
        self.ShowProcStkList()
        return None

    # 처리대상종목 삭제
    def ClickDelStkCd(self):
        if (self.NowRcvGlobalQttn):
            ctypes.windll.user32.MessageBoxW(0, "글로번 시세 수신중으로 추가 불가", "알림", 0)
            return None
        sItem = self.tblProcStkList.selectedItems()
        sMktTpCd = sItem[CodeDef.PROC_STK_COL_MKT_TP_CD].text()  # 시장구분코드
        sStkCd   = sItem[CodeDef.PROC_STK_COL_STK_CD].text()     # 종목코드
        self.DBH.deleteProcStk(sMktTpCd, sStkCd)
        self.ShowProcStkList()
        return None

    # 처리대상 종목 표시
    def ShowProcStkList(self):
        StkList = self.DBH.queryProcStkList()
        RowCnt = len(StkList.index)
        ColCnt = len(StkList.columns)
        self.tblProcStkList.setRowCount(RowCnt)
        self.tblProcStkList.setColumnCount(ColCnt)
        self.tblProcStkList.setHorizontalHeaderLabels(list(StkList))
        # 처리대상 종목리스트
        self.ProcStkList.clear()
        self.ProcStkList = list(StkList["STK_CD"])

        for iRow in range(RowCnt):
            for iCol in range(ColCnt):
                item = QTableWidgetItem(StkList.iat[iRow,iCol])
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.tblProcStkList.setItem(iRow, iCol, item)

        self.tblProcStkList.resizeColumnsToContents()
        self.tblProcStkList.resizeRowsToContents()
        return None

    # 처리대상 종목 리스트 가져오기
    def GetProcStkList(self):
        return self.ProcStkList[:]

    # 처리종목 분봉시세 초기화
    def ClickInitMnQttn(self):
        Chk = ctypes.windll.user32.MessageBoxW(0, "초기화 시작합니다.", "알림", 1)
        if(Chk == 2):
            return None
        # 초기화 대상 종목 리스트 조회
        StkList = self.DBH.queryProcStkList()
        RowCnt = len(StkList.index)
        for iRow in range(RowCnt):

            # 티레이더 글로벌 초기화 확인
            if(StkList.iat[iRow, CodeDef.PROC_STK_COL_RCV_TP] != "GLOBAL"):
                continue

            MktTpCd  = StkList.iat[iRow, CodeDef.PROC_STK_COL_MKT_TP_CD]
            StkCd    = StkList.iat[iRow, CodeDef.PROC_STK_COL_STK_CD]
            LastDtMn = StkList.iat[iRow, CodeDef.PROC_STK_COL_LAST_DT_MN]
            LastDt   = LastDtMn[:8]
            LastMn   = LastDtMn[-4:]
            # 데이터가 없는 경우는 기본값 이용
            if (LastDt is None or len(LastDt.strip()) == 0):
                LastDt = CodeDef.INIT_STR_DT_DEFAULT
            if (LastMn is None or len(LastMn.strip()) == 0):
                LastMn = CodeDef.INIT_STR_MN_DEFAULT

            inEndDt = CodeDef.INIT_END_DT_DEFAULT
            inEndMn = CodeDef.INIT_END_MN_DEFAULT

            # 동기화보다 뒤면 패스
            if(int(LastDt + LastMn) >= int(CodeDef.INIT_END_DT_DEFAULT + CodeDef.INIT_END_MN_DEFAULT)):
                continue

            print("초기화 시작:",StkCd,(LastDt + LastMn) ,(inEndDt + inEndMn))
            try:
                # 기존 시세삭제
                self.DBH.deleteMnQttn(MktTpCd, StkCd, LastDt, LastMn, inEndDt, inEndMn)

                # 시세 분봉 초기입력
                self.APIH.InitMnQttn(MktTpCd, StkCd, LastDt, LastMn, inEndDt, inEndMn)
                print("초기 분송 수신입력 종료:", StkCd)

                # 빈분봉 처리시작
                print("빈분봉처리 시작!!:", StkCd)

                # 빈분봉처리 대상 구간 조회
                print("조회:", MktTpCd, StkCd, LastDt, LastMn, CodeDef.INIT_END_DT_DEFAULT, CodeDef.INIT_END_MN_DEFAULT)
                Qttn = self.DBH.queryMnQttn(MktTpCd,StkCd,LastDt,LastMn,CodeDef.INIT_END_DT_DEFAULT, CodeDef.INIT_END_MN_DEFAULT)

                ProcDt = datetime(year=int(LastDt[:4]), month=int(LastDt[4:6]), day=int(LastDt[6:]),hour=int(LastMn[:2]), minute=int(LastMn[2:]))
                if (CodeDef.isQttnBlnk(self, ProcDt)):
                    ProcDt = CodeDef.getMon07AM(self,ProcDt)

                ProcDt = ProcDt + CodeDef.ONE_MINUTE
                QttnCnt = len(Qttn.index)
                FtPrc   = 0.0
                HgPrc   = 0.0
                LoPrc   = 0.0
                ClPrc   = 0.0
                UpdnPrc = 0.0
                Vlum    = 0.0
                PreQttn = []
                Dt = None
                Mn = None
                for qIdx in range(QttnCnt):
                    Dt      = Qttn.iat[qIdx, CodeDef.QTTN_MN_DATA_COL_DT]
                    Mn      = Qttn.iat[qIdx, CodeDef.QTTN_MN_DATA_COL_MN]
                    FtPrc   = float(Qttn.iat[qIdx, CodeDef.QTTN_MN_DATA_COL_FTPRC])
                    HgPrc   = float(Qttn.iat[qIdx, CodeDef.QTTN_MN_DATA_COL_HGPRC])
                    LoPrc   = float(Qttn.iat[qIdx, CodeDef.QTTN_MN_DATA_COL_LOPRC])
                    ClPrc   = float(Qttn.iat[qIdx, CodeDef.QTTN_MN_DATA_COL_CLPRC])
                    UpdnPrc = float(Qttn.iat[qIdx, CodeDef.QTTN_MN_DATA_COL_UPDN_PRC])
                    Vlum    = float(Qttn.iat[qIdx, CodeDef.QTTN_MN_DATA_COL_VLUM])

                    if((Dt+Mn) == (ProcDt.strftime("%Y%m%d%H%M"))):
                        ProcDt = ProcDt + CodeDef.ONE_MINUTE
                        # 이전시세 백업
                        PreQttn = [FtPrc, HgPrc, LoPrc, ClPrc, UpdnPrc, Vlum]
                        continue
                    else:
                        # 이전시세가 없으면 넘긴다
                        if(len(PreQttn)==0):
                            ProcDt = datetime(year=int(Dt[:4]), month=int(Dt[4:6]), day=int(Dt[6:]),
                                              hour=int(Mn[:2]), minute=int(Mn[2:4]))
                            ProcDt = ProcDt + CodeDef.ONE_MINUTE
                            PreQttn = [FtPrc, HgPrc, LoPrc, ClPrc, UpdnPrc, Vlum]
                            continue

                        EndDt = datetime(year=int(Dt[:4]), month=int(Dt[4:6]), day=int(Dt[6:]),hour=int(Mn[:2]), minute=int(Mn[2:4]))
                        MnCnt = (EndDt - ProcDt).total_seconds()/60.0

                        for eIdx in range(int(MnCnt)):
                            # 비는 시세 확인
                            if(CodeDef.isQttnBlnk(self, ProcDt)):
                                ProcDt = ProcDt + CodeDef.ONE_MINUTE
                                continue
                            if(ProcDt == EndDt):
                                ProcDt = ProcDt + CodeDef.ONE_MINUTE
                                break

                            self.DBH.insertMnQttn(MktTpCd, StkCd, ProcDt.strftime("%Y%m%d"), ProcDt.strftime("%H%M"), PreQttn[0], PreQttn[1], PreQttn[2], PreQttn[3], PreQttn[4], PreQttn[5])
                            ProcDt = ProcDt + CodeDef.ONE_MINUTE

                        # 이전시세 백업
                        PreQttn = [FtPrc, HgPrc, LoPrc, ClPrc, UpdnPrc, Vlum]
                        
                    # 빈분봉 채우기 if 끝
                # 종목 시세 정리 for qIdx in range(QttnCnt): 끝

                # 마지막 시세가 초기화 종료일까지 못갔을 경우 마지막을 채운다.
                if(int(ProcDt.strftime("%Y%m%d%H%M")) < int(CodeDef.INIT_END_DT_DEFAULT+CodeDef.INIT_END_MN_DEFAULT)):

                    EndDt = datetime(year=int(CodeDef.INIT_END_DT_DEFAULT[:4]), month=int(CodeDef.INIT_END_DT_DEFAULT[4:6]), day=int(CodeDef.INIT_END_DT_DEFAULT[6:]), hour=int(CodeDef.INIT_END_MN_DEFAULT[:2]),minute=int(CodeDef.INIT_END_MN_DEFAULT[2:4]))
                    MnCnt = (EndDt - ProcDt).total_seconds() / 60.0

                    for eIdx in range(int(MnCnt)+1):
                        # 비는 시세 확인
                        if (CodeDef.isQttnBlnk(self, ProcDt)):
                            ProcDt = ProcDt + CodeDef.ONE_MINUTE
                            continue
                        if (int(ProcDt.strftime("%H%M")) > int(EndDt.strftime("%H%M"))):
                            #print("ProcDt:",ProcDt,"EndDt:",EndDt)
                            break

                        self.DBH.insertMnQttn(MktTpCd, StkCd, ProcDt.strftime("%Y%m%d"), ProcDt.strftime("%H%M"),
                                              PreQttn[0], PreQttn[1], PreQttn[2], PreQttn[3], PreQttn[4], PreQttn[5])
                        ProcDt = ProcDt + CodeDef.ONE_MINUTE

            except Exception as e:
                print("빈분봉처리에러:",e,StkCd)
                return None

            # 최종 초기화 일자시각 입력
            self.DBH.updateProcStkLastDtMn(MktTpCd, StkCd, (inEndDt+inEndMn))

        # 처리종목별 처리 for iRow in range(RowCnt): 끝

        ctypes.windll.user32.MessageBoxW(0, "초기화 완료되었습니다.", "알림", 0)
        self.ShowProcStkList()
        return None

    # 지수시세 실시간 받기/종료
    def ClickRcvIdxQttn(self):
        # 중지실행
        if(self.NowRcvIdxQttn):
            if (self.QttnSctkT is not None):
                print("지수시세 쓰레드 중지 시작")
                try:
                    self.QttnSctkT.DoStop()
                    self.QttnSctkT.join()
                except Exception as e:
                    print("지수시세 받기 쓰레드 중지 에러:", e)
                    return None
            print("지수시세 Loop 종료됨.")
            self.btnRcvIdxQttn.setText("지수시세수신")
            self.NowRcvIdxQttn = False
            self.btnRcvIdxQttn.setStyleSheet("background-color:None")
        # 받기시작
        else:
            try:
                self.QttnSctkT = RcvSckt_handler(self,CodeDef.PORT_INDEX_QTTN)
                self.QttnSctkT.start()
            except Exception as e:
                print("지수시세 받기 쓰레드 시작 에러:", e)
                return None
            print("지수시세 Loop 시작됨.")
            self.btnRcvIdxQttn.setText("지수시세중지")
            self.NowRcvIdxQttn = True
            self.btnRcvIdxQttn.setStyleSheet("background-color:rgb(255,020,147)")
        return None

    # 글로벌 실시간 시세 받기/종료
    def ClickRcvGlobalQttn(self):
        # 중지실행
        if (self.NowRcvGlobalQttn):
            #for idx in range(len(self.ProcStkList)):
            #    self.APIH.StopRealRcv(None, self.ProcStkList[idx])
            self.APIH.StopAllRealRcv()
            self.btnRcvGlobalQttn.setText("글로벌시세수신")
            self.NowRcvGlobalQttn = False
            self.btnRcvGlobalQttn.setStyleSheet("background-color:None")
            print("Global 시세받기 종료됨.")
        # 받기시작
        else:
            self.btnRcvGlobalQttn.setText("글로벌시세중지")
            self.NowRcvGlobalQttn = True
            self.btnRcvGlobalQttn.setStyleSheet("background-color:rgb(255,020,147)")
            print("Global 시세받기 시작됨.")
            for idx in range(len(self.ProcStkList)):
                self.APIH.OnRequest("REAL_QTTN", "61", self.ProcStkList[idx])
            #self.APIH.waitSrvrRspn()
        return None

    # 글로벌 저장된 시세 받기/종료
    def ClickRcvGlobalSavedQttn(self):
        # 중지실행
        if (self.NowRcvGlobalSavedQttn):
            try:
                self.TestQttnSnd.DoStop()
                #self.TestQttnSnd.join()
            except Exception as e:
                print("저장된 글로벌 시세받기 쓰레드 중지 에러:", e)
                return None
            self.btnRcvGlobalSavedQttn.setText("저장된시세수신")
            self.NowRcvGlobalSavedQttn = False
            self.btnRcvGlobalSavedQttn.setStyleSheet("background-color:None")
            print("저장된 Global 시세받기 종료됨.")
        # 받기시작
        else:
            try:
                if(self.TestQttnSnd is None):
                    # 차트 X축 변경(0900에 시작으로 변경)
                    self.CrtH.SetTestQttnXList()

                    self.TestQttnSnd = TestQttn_Sender(self)
                    self.TestQttnSnd.start()
                else:
                    self.TestQttnSnd.DoRestart()
            except Exception as e:
                print("저장된 글로벌 시세받기 쓰레드 시작 에러:", e)
                return None
            self.btnRcvGlobalSavedQttn.setText("저장된시세수신중지")
            self.NowRcvGlobalSavedQttn = True
            self.btnRcvGlobalSavedQttn.setStyleSheet("background-color:rgb(255,020,147)")
            print("저장된 Global 시세받기 시작됨.")

        return None

    # 실시간 수신시세 처리
    # inProcTp : 처리구분
    # inQttn   : 시세문자열
    def ProcRcvRealQttn(self,inProcTp,inRcvQttn):
        # 다중수신여부 확인
        inQttn = inRcvQttn.split("|")
        InfoCnt  = len(inQttn)
        QttnList = [] # 시세열
        Tmplist  = [] # 임시 시세열
        # 시세 파싱
        for i in range(InfoCnt):
            if(len(inQttn[i]) == 0):
                continue
            # 시세넣기
            if (inQttn[i] == "E"):
                QttnList.append(Tmplist)
                Tmplist = []
            else:
                Tmplist.append(inQttn[i])

        # 시세차트설정
        if(inProcTp == "KOSPI_INDEX"):
            self.CrtH.UpdateRealQttn(QttnList, "CurrentPrice")
            #print("QttnList:",QttnList)
            self.TFH.UpdateQttn(QttnList)
        elif(inProcTp == "GLOBAL_QTTN"):
            #self.CrtH.UpdateRealQttn(QttnList, "Prediction") # 테스트용
            # 딥러닝 시세 업데이트 및 시세 저장
            self.TFH.UpdateQttn(QttnList)
        elif (inProcTp == "TF_RSLT"):
            self.dispText("결과수신!!:" + inRcvQttn)
            self.CrtH.UpdateRealQttn(QttnList, "Prediction")  # 테스트용
        else:
            print("inProcTp 확인")

        return None

    # 딥러닝 동작/중지
    def ClickTensorFlow(self):
        # 실행중지
        if (self.NowTensorFlow):
            # 송신 소켓은 따로 처리하지 않는다.
            # 수신 쓰레드 중지
            if (self.TfRcvSctkT is not None):
                print("딥러닝 쓰레드 중지 시작")
                try:
                    self.TfRcvSctkT.DoStop()
                    self.TfRcvSctkT.join()
                except Exception as e:
                    print("딥러닝 쓰레드 중지에러")
                    print("에러:",e)
                    return None
            print("딥러닝 Loop 종료됨.")
            self.btnTensorFlow.setText("딥러닝연결")
            self.btnTensorFlow.setStyleSheet("background-color:None")
            self.NowTensorFlow = False
        # 동작실행
        else:
            # 수신소켓 쓰레드 시작
            try:
                self.TfRcvSctkT = RcvSckt_handler(self, CodeDef.PORT_TF_RCV_RSLT)
                self.TfRcvSctkT.start()
            except Exception as e:
                print("딥러닝 쓰레드 시작에러:", e)
                return None

            # 송신소켓 접속
            try:
                if(self.TfSndSctkT is None):
                    self.TfSndSctkT = SndSckt_handler()
                if (self.TfSndSctkT.GetOnSock() == False):
                    self.TfSndSctkT.CnntSckt(CodeDef.PORT_TF_DATA)
            except Exception as e:
                print("송신소켓 접속 시작에러:", e)
                return None
            print("딥러닝 Loop 시작됨.")
            self.btnTensorFlow.setStyleSheet("background-color:rgb(255,020,147)")
            self.btnTensorFlow.setText("딥러닝중지")
            self.NowTensorFlow = True

        return None


    # 딥러닝 프로그램에 데이터 전송
    # TFQttn_handler에서 사용
    # inSndData : 전송데이터
    def SendTensorFlow(self,inSndData):
        #self.dispText("시세전송!!:"+inSndData)
        # 데이터 전송
        try:
            if (self.TfSndSctkT is not None and self.TfSndSctkT.GetOnSock()):
                self.TfSndSctkT.SendData(inSndData)
        except Exception as e:
            print("딥러닝 데이터 전송 에러:", e)

        return None


    # 비어있는 분봉시세 초기화만 처리
    def ClickMnQttnOrd(self):
        # 처리대상
        #StkList = ['NQU18','HGU18','ADU18']
        #StkList = ['ADU18']
        StkList = ["USDCNH"]
        RowCnt = len(StkList)
        for iRow in range(RowCnt):
            StkCd = StkList[iRow]
            print("처리시작:",StkCd)
            try:
                # 분봉조회
                #Qttn = self.DBH.queryMnQttn("DERV",StkCd,CodeDef.INIT_STR_DT_DEFAULT, CodeDef.INIT_STR_MN_DEFAULT, CodeDef.INIT_END_DT_DEFAULT, CodeDef.INIT_END_MN_DEFAULT)
                Qttn = self.DBH.queryMnQttn("DERV", StkCd, "20180604", "0900","20181102", "0859")

                ProcDt = datetime(year=int(CodeDef.INIT_STR_DT_DEFAULT[:4]), month=int(CodeDef.INIT_STR_DT_DEFAULT[4:6]), day=int(CodeDef.INIT_STR_DT_DEFAULT[6:]),hour=int(CodeDef.INIT_STR_MN_DEFAULT[:2]), minute=int(CodeDef.INIT_STR_MN_DEFAULT[2:]))
                if (CodeDef.isQttnBlnk(self, ProcDt)):
                    ProcDt = CodeDef.getMon07AM(self,ProcDt)

                QttnCnt = len(Qttn.index)
                FtPrc   = 0.0
                HgPrc   = 0.0
                LoPrc   = 0.0
                ClPrc   = 0.0
                UpdnPrc = 0.0
                Vlum    = 0.0
                PreQttn = []
                for qIdx in range(QttnCnt):
                    Dt      = Qttn.iat[qIdx, CodeDef.QTTN_MN_DATA_COL_DT]
                    Mn      = Qttn.iat[qIdx, CodeDef.QTTN_MN_DATA_COL_MN]
                    FtPrc   = float(Qttn.iat[qIdx, CodeDef.QTTN_MN_DATA_COL_FTPRC])
                    HgPrc   = float(Qttn.iat[qIdx, CodeDef.QTTN_MN_DATA_COL_HGPRC])
                    LoPrc   = float(Qttn.iat[qIdx, CodeDef.QTTN_MN_DATA_COL_LOPRC])
                    ClPrc   = float(Qttn.iat[qIdx, CodeDef.QTTN_MN_DATA_COL_CLPRC])
                    UpdnPrc = float(Qttn.iat[qIdx, CodeDef.QTTN_MN_DATA_COL_UPDN_PRC])
                    Vlum    = float(Qttn.iat[qIdx, CodeDef.QTTN_MN_DATA_COL_VLUM])

                    if( qIdx in [0,1,2,3,4]):
                        print("(Dt+Mn) == (ProcDt.strftime(%Y%m%d%H%M)):", (Dt + Mn), (ProcDt.strftime("%Y%m%d%H%M")))

                    if((Dt+Mn) == (ProcDt.strftime("%Y%m%d%H%M"))):
                        ProcDt = ProcDt + CodeDef.ONE_MINUTE
                        # 이전시세 백업
                        PreQttn = [FtPrc, HgPrc, LoPrc, ClPrc, UpdnPrc, Vlum]
                        continue
                    else:
                        # 이전시세가 없으면 조회 첫번째로 세팅후 넘긴다
                        if(len(PreQttn)==0):
                            ProcDt = datetime(year=int(Dt[:4]), month=int(Dt[4:6]), day=int(Dt[6:]), hour=int(Mn[:2]),minute=int(Mn[2:4]))
                            ProcDt = ProcDt + CodeDef.ONE_MINUTE
                            PreQttn = [FtPrc, HgPrc, LoPrc, ClPrc, UpdnPrc, Vlum]
                            continue

                        #print("(Dt+Mn) == (ProcDt.strftime(%Y%m%d%H%M)):", (Dt + Mn), (ProcDt.strftime("%Y%m%d%H%M")))

                        EndDt = datetime(year=int(Dt[:4]), month=int(Dt[4:6]), day=int(Dt[6:]),hour=int(Mn[:2]), minute=int(Mn[2:4]))
                        MnCnt = (EndDt - ProcDt).total_seconds()/60.0

                        for eIdx in range(int(MnCnt)):
                            # 비는 시세 확인
                            if(CodeDef.isQttnBlnk(self, ProcDt)):
                                ProcDt = ProcDt + CodeDef.ONE_MINUTE
                                continue
                            if(ProcDt == EndDt):
                                ProcDt = ProcDt + CodeDef.ONE_MINUTE
                                break

                            self.DBH.insertMnQttn("DERV"
                                                 , StkCd, ProcDt.strftime("%Y%m%d"), ProcDt.strftime("%H%M"), PreQttn[0], PreQttn[1], PreQttn[2], PreQttn[3], PreQttn[4], PreQttn[5])
                            ProcDt = ProcDt + CodeDef.ONE_MINUTE

                        # 이전시세 백업
                        PreQttn = [FtPrc, HgPrc, LoPrc, ClPrc, UpdnPrc, Vlum]

                        # -- 빈분봉 채워넣기 for문 종료 -----

                # ------- 조회된 시세 main for문 종료 ------
            except Exception as e:
                print(e)
            print("처리끝:",StkCd)
        # --------- 빈분봉처리 종료 ---------
        ctypes.windll.user32.MessageBoxW(0, "초기화 완료되었습니다.", "알림", 0)
        return None

    # 출력 표시
    def dispText(self,inText):
        self.edtChk.append(inText) ## 임시확인
        return None

    # 첫시세 설정
    # 장중 마지막 시세를 가져와 설정함.
    def ClickSetFstQttn(self):

        print("첫시세 설정!!")

        mn = int(datetime.today().strftime("%H%M"))

        if(mn > 1500 or mn < 900):
            ctypes.windll.user32.MessageBoxW(0, "장중에만 사용가능", "알림", 0)
            return None

        FstQttn = self.DBH.queryFstTFQttn()

        RowCnt = len(FstQttn)
        for idx in range(RowCnt):
            FstQttn[idx] = str(FstQttn[idx])

        print("FstQttn:", FstQttn)

        self.TFH.SetFstQttn(FstQttn)

        return None

    # 분봉 시세 저장
    # inProcTp  : 처리구분
    # inStkCd   : 종목코드
    # inDt      : 일자
    # inTime    : 시간(HHMM)
    # inFtPrc   : 시가
    # inHgPrc   : 고가
    # inLoPrc   : 저가
    # inClPrc   : 종가
    # inUpDnPrc : 등락가
    # inVlum    : 거래량
    def insertMnQttn(self, inProcTp, inStkCd, inDt, inMn, inFtPrc, inHgPrc, inLoPrc, inClPrc, inUpDnPrc, inVlum):

        self.DBH.insertMnQttn(inProcTp, inStkCd, inDt,inMn, inFtPrc, inHgPrc, inLoPrc, inClPrc, inUpDnPrc, inVlum)

        return None