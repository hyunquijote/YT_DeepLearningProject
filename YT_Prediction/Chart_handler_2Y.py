from CodeDef import *
from datetime import timedelta, datetime
from pandas import DataFrame
import numpy
import matplotlib.pyplot as plt

'''
차트 Y축 왼쪽 오른쪽에 다른 기준으로 표시하기 위에
만들었던 버젼임.
당시에는 오른쪽이 레버리지 현재가
왼쪽이 예측값 이였음.
한쪽으로 몰아서 표기하기로 변경. 
'''

class Chart_handler():

    # 핸들러 설정
    def SetHandler(self,inFig,inCanvas):

        # 변수 설정
        self.Fig           = inFig      # Figure 객체
        self.Canvas        = inCanvas   # Canvas 객체
        self.Qttn          = None      # 차트 시세(차트에 표현될 DataFrame)
        self.X_list        = []         # X축 시간틱리스트
        self.LY_list       = []         # 왼쪽 Y 틱리스트
        self.RY_list       = []         # 오른쪽 Y 틱리스트(KODEX 레버리지 ETF)
        self.existLY_Ticks = False     # 왼쪽 Y 틱리스트 생성여부
        self.existRY_Ticks = False     # 오른쪽 Y 틱리스트 생성여부
        self.Max_X         = ""        # X축 마지막 시각
        self.Cur_X         = ""        # X축 현재가 시각
        self.CurPrcDict    = {}        # 최근 현재가 정보 {종목코드: (시분,가격)}

        # X축 시간 설정 (지금시점으로부터 1분단위로 제한시간까지)
        TimeDelta = timedelta(minutes=1)
        ToDay     = datetime.today()

        TmpQttn   = {}
        Tmplist_1 = []
        Tmplist_2 = []
        for i in range(CodeDef.CHART_X_LIMIT):
            mn = (ToDay + TimeDelta * i).strftime("%H%M")
            self.X_list.append(mn)
            Tmplist_1.append(None)
            Tmplist_2.append(None)

        # 차트에 표현될 DataFrame 기본형 설정
        TmpQttn["mn"         ] = self.X_list
        TmpQttn["Prediction"] = Tmplist_1   # 왼쪽 Y값
        TmpQttn["Index"      ] = Tmplist_2   # 오른쪽 Y값
        self.Qttn = DataFrame(TmpQttn)
        self.Qttn.set_index("mn", inplace=True, drop=True) # index 를 mn으로 변경
        self.X_list = self.Qttn.index.tolist() # X축 리스트형 저장
        self.Max_X  = max(self.X_list)         # X축 마지막 시각
        self.Cur_X  = min(self.X_list)         # X축 현재가 시각

        # 빈 차트 표시
        self.DoDraw()
        return None

    # 실시간 시세업데이트 및 차트 갱신
    # 리스트([[종목코드,현재가,],[]]) 형으로 수신
    # inQttn : 시세 List
    # inSide : Prediction.왼쪽Y  Index.오른쪽Y
    def UpdateRealQttn(self,inQttn, inSide):

        QttnCnt  = len(inQttn)
        LeftVal  = None
        RightVal = None
        ReDraw   = True
        for i in range(QttnCnt):
            QttnList = inQttn[i]
            StkCd  = QttnList[CodeDef.REAL_QTTN_COL_STK_CD]
            InTime = QttnList[CodeDef.REAL_QTTN_COL_TIME ]
            CrPrc  = QttnList[CodeDef.REAL_QTTN_COL_CRPRC]
            #FtPrc  = QttnList[CodeDef.REAL_QTTN_COL_FTPRC]
            #HgPrc  = QttnList[CodeDef.REAL_QTTN_COL_HGPRC]
            #LoPrc  = QttnList[CodeDef.REAL_QTTN_COL_LOPRC]

            MoveQttn = False # 시각변경시 시세이동

            # 이전 현재가와 같을시 무시
            if((StkCd in self.CurPrcDict.keys())
               and self.CurPrcDict[StkCd][0] == InTime
               and self.CurPrcDict[StkCd][1] == CrPrc):
                ReDraw = False
                continue
            else:
                # 갱신
                self.CurPrcDict[StkCd] = (InTime, CrPrc)
                ReDraw = True

            # 초기화: Y 틱 리스트 만들기
            # 오른쪽 Y
            if(inSide == "Index"):
                # 상한/하한 갱신
                if (self.existRY_Ticks):
                    # Y축 상한 갱신
                    if (float(CrPrc) > max(self.RY_list)):
                        for yValue in numpy.arange(max(self.RY_list) + CodeDef.CHART_RY_TICK,
                                                    float(CrPrc) + CodeDef.CHART_RY_TICK,
                                                    CodeDef.CHART_RY_TICK):
                            self.RY_list.append(round(yValue,2))
                    # Y축 하한 갱신
                    if (float(CrPrc) < min(self.RY_list)):
                        for yValue in numpy.arange(min(self.RY_list) - CodeDef.CHART_RY_TICK,
                                                    float(CrPrc) - CodeDef.CHART_RY_TICK,
                                                    -CodeDef.CHART_RY_TICK):
                            self.RY_list.insert(0, round(yValue,2))
                # 최초 틱 범위 만들기
                else:
                    self.existRY_Ticks = True
                    # 현재가에서 위아래 정의된 틱단위까지만 만든다.(ETF 기준임)
                    for yValue in numpy.arange(float(CrPrc) - (CodeDef.CHART_RY_TICK_COUNT * CodeDef.CHART_RY_TICK),
                                                float(CrPrc) + (CodeDef.CHART_RY_TICK_COUNT * CodeDef.CHART_RY_TICK),
                                                CodeDef.CHART_RY_TICK):
                        self.RY_list.append(round(yValue,2))
            # 왼쪽 Y
            else:
                # 상한/하한 갱신
                if (self.existLY_Ticks):
                    # Y축 상한 갱신
                    if (float(CrPrc) > max(self.LY_list)):
                        for yValue in numpy.arange(max(self.LY_list) + CodeDef.CHART_LY_TICK,
                                                    float(CrPrc) + CodeDef.CHART_LY_TICK,
                                                    CodeDef.CHART_LY_TICK):
                            self.LY_list.append(round(yValue,2))
                    # Y축 하한 갱신
                    if (float(CrPrc) < min(self.LY_list)):
                        for yValue in numpy.arange(min(self.LY_list) - CodeDef.CHART_LY_TICK,
                                                    float(CrPrc) - CodeDef.CHART_LY_TICK,
                                                   -CodeDef.CHART_LY_TICK):
                            self.LY_list.insert(0, round(yValue,2))
                # 최초 틱 범위 만들기
                else:
                    self.existLY_Ticks = True
                    # 현재가에서 위아래 정의된 틱단위까지만 만든다.(ETF 기준임)
                    for yValue in numpy.arange(float(CrPrc) - (CodeDef.CHART_LY_TICK_COUNT * CodeDef.CHART_LY_TICK),
                                                float(CrPrc) + (CodeDef.CHART_LY_TICK_COUNT * CodeDef.CHART_LY_TICK),
                                                CodeDef.CHART_LY_TICK):
                        self.LY_list.append(round(yValue,2))

            # 시세 갱신
            if(self.ExistX(InTime)):
                if (inSide == "Prediction"):
                    self.Qttn.ix[InTime, "Prediction"] = float(CrPrc)
                else:
                    self.Qttn.ix[InTime, "Index"] = float(CrPrc)
                #print("시세갱신: ", inSide)
                # 다음 시각으로 이동시 이전시각 값 이월
                if(self.Cur_X != InTime):
                    MoveQttn = True

            # 시세 추가
            else:
                if (inSide == "Prediction"):
                    LeftVal = float(CrPrc)
                    RightVal = None
                else:
                    LeftVal = None
                    RightVal = float(CrPrc)
                # 신규시간 시세일 경우 업데이트를 한다.
                if(int(InTime) > int(self.Max_X)):
                    self.Max_X = InTime            # 최근시각 갱신
                    self.X_list.append(InTime)     # 최근시각 입력
                    DelMn = self.X_list.pop(0)     # 맨 앞 시각 제거
                    self.Qttn = self.Qttn.drop(DelMn) # 맨 앞 시세 삭제
                    # 신규시세 입력
                    NewQttn = DataFrame({"Prediction": [LeftVal],"Index": [RightVal]},index=[InTime])
                    self.Qttn = self.Qttn.append(NewQttn)
                    print("신규시세: ", inSide)
                    # 다음 시각으로 이동시 이전시각 값 이월
                    if (self.Cur_X != InTime):
                        MoveQttn = True
                # 빠진시세 넣기
                else:
                    NewQttn = DataFrame({"Prediction": [LeftVal], "Index": [RightVal]}, index=[InTime])
                    self.Qttn = self.Qttn.append(NewQttn).sort_index()
                    print("빠진시세: ", inSide)

            # 초기화
            LeftVal = None
            RightVal = None

            # 다음 시각으로 이동시 이전시각 값 이월
            if (MoveQttn):
                if (inSide == "Prediction"):
                    tValue = self.Qttn.ix[self.Cur_X, "Index"]
                    self.Qttn.ix[InTime, "Index"] = tValue
                else:
                    tValue = self.Qttn.ix[self.Cur_X, "Prediction"]
                    self.Qttn.ix[InTime, "Prediction"] = tValue
                self.Cur_X = InTime

        #--- for문 종료 ----

        # 차트 갱신
        if( ReDraw ):
            self.DoDraw()
        return None
    
    # 시간축에 입력시각이 있는지 체크
    def ExistX(self, inValue):
        rsltV = False
        if(inValue in self.X_list):
            rsltV = True
        else:
            print("없는 X(시분) 들어옴")
        return rsltV

    # 차트 그리기
    def DoDraw(self):

        try:
            # 기존것 클리어
            self.Fig.clf()
            Ax1 = self.Fig.add_subplot(1, 1, 1)  # fig를 1행 1칸으로 나누어 1칸안에 넣어줍니다

            # 왼쪽Y 기준데이터 설정
            Ax1.plot(self.Qttn.index, self.Qttn["Prediction"], color="r", marker="o", linestyle="--")

            Ax2 = Ax1.twinx()

            # 오른쪽Y 기준데이터 설정
            Ax2.plot(self.Qttn.index, self.Qttn["Index"], color="b", marker="^")

            # X선 먼저 그리기
            Ax1.set_xticks(self.Qttn.index)
            Ax2.set_xticks(self.Qttn.index)

            # X선 보조설정
            for xLabel in Ax1.xaxis.get_ticklabels():
                xLabel.set_rotation(45)  # X값 기울기
            Ax1.xaxis.set_tick_params(labelsize=7)  # X선 틱라벨 크기
            Ax1.xaxis.grid(True, color='gray', linestyle='dashed', linewidth=0.5)  # X값 보조선 표시

            # Y선 보조설정
            Ax1.yaxis.set_tick_params(reset=True, labelsize=7, colors="r", right=False, left=False)
            Ax1.set_yticks(self.LY_list, True)
            Ax2.yaxis.set_tick_params(labelsize=7, colors="b", left=False, right=False)
            Ax2.set_yticks(self.RY_list, True)

            # 라벨설정
            self.Fig.legend(loc='upper center', bbox_to_anchor=(0.5, 1.0), ncol=2, fancybox=True, shadow=True)
            Ax1.set_xlabel("Time")
            Ax1.set_ylabel("Prediction", color="r")
            Ax2.set_ylabel("Index", color="b")

            # 여백조정
            plt.tight_layout()

            self.Canvas.draw()

        except Exception as e:
            print("차트그리기 에러:", e)

        return None