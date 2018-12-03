from CodeDef import *
from datetime import timedelta, datetime
from pandas import DataFrame
import numpy
import matplotlib.pyplot as plt

'''
KODEX 레버리지 종목만 예측하는것으로 변경함.
기존 버젼은 Chart_handler_2Y (Y축 2개 사용버전)
'''

class Chart_handler():

    # 핸들러 설정
    def SetHandler(self,inFig,inCanvas):

        # 변수 설정
        self.Fig        = inFig      # Figure 객체
        self.Canvas     = inCanvas   # Canvas 객체
        self.Qttn       = None      # 차트 시세(차트에 표현될 DataFrame)
        self.X_list     = []         # X축 시간틱 리스트
        self.Y_list     = []         # Y축 틱 리스트(KODEX 레버리지 ETF)
        self.ExistY     = False     # Y축 틱리스트 생성여부
        self.Max_X      = ""         # X축 마지막 시각
        self.CurPrcDict = {}         # 최근 현재가 정보 {종목코드: (시분,가격)}

        # 예측분 리스트 정보
        self.PredMnList = CodeDef.TF_LEARNING_MN_LIST  # 예측분 리스트
        self.PredMnCnt  = len(self.PredMnList)

        # X축 시간 설정 (지금시점으로부터 1분단위로 제한시간까지)
        TimeDelta = timedelta(minutes=1)
        ToDay     = datetime.today()

        TmpQttn = {}
        for i in range(CodeDef.CHART_X_LIMIT):
            mn = (ToDay + TimeDelta * i).strftime("%H%M")
            self.X_list.append(mn)

        # 차트에 표현될 DataFrame 기본형 설정
        TmpQttn["mn"            ] = self.X_list
        TmpQttn["CurrentPrice"] = [None] * CodeDef.CHART_X_LIMIT # Y값
        for idx in range(self.PredMnCnt):
            TmpQttn["Prediction_"+str(self.PredMnList[idx])] = [None] * CodeDef.CHART_X_LIMIT  # Y값

        self.Qttn = DataFrame(TmpQttn)
        self.Qttn.set_index("mn", inplace=True, drop=True) # index 를 mn으로 변경
        self.X_list = self.Qttn.index.tolist() # X축 리스트형 저장
        self.Max_X  = max(self.X_list)         # X축 마지막 시각

        # 빈 차트 표시
        self.DoDraw()
        return None

    # 실시간 시세업데이트 및 차트 갱신
    # 리스트([[종목코드,현재가,],[]]) 형으로 수신
    # inQttn : 시세 List
    # inSide : Prediction.예측값 CurrentPrice.현재가
    def UpdateRealQttn(self,inQttn,inSide):
        try:
            QttnCnt = len(inQttn)  # X축 시간수
            ReDraw  = True        # 차트갱신여부
            for i in range(QttnCnt):
                QttnList = inQttn[i]
                #print("차트 실시간 시세 수신:",QttnList,inSide)
                StkCd  = QttnList[CodeDef.REAL_QTTN_COL_STK_CD] # 예측일경우 예측분
                InTime = QttnList[CodeDef.REAL_QTTN_COL_TIME ]
                CrPrc  = QttnList[CodeDef.REAL_QTTN_COL_CRPRC]

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
                # 상한/하한 갱신
                if (self.ExistY):
                    # Y축 상한 갱신
                    if (float(CrPrc) > max(self.Y_list)):
                        for yValue in numpy.arange(max(self.Y_list) + CodeDef.CHART_RY_TICK,
                                                    float(CrPrc) + CodeDef.CHART_RY_TICK,
                                                    CodeDef.CHART_RY_TICK):
                            self.Y_list.append(round(yValue,2))
                    # Y축 하한 갱신
                    if ( float(CrPrc) > 0.0 and float(CrPrc) < min(self.Y_list)):
                        for yValue in numpy.arange(min(self.Y_list) - CodeDef.CHART_RY_TICK,
                                                    float(CrPrc) - CodeDef.CHART_RY_TICK,
                                                    -CodeDef.CHART_RY_TICK):
                            self.Y_list.insert(0, round(yValue,2))
                # 최초 틱 범위 만들기
                else:
                    self.ExistY = True
                    # 현재가에서 위아래 정의된 틱단위까지만 만든다.(ETF 기준임)
                    for yValue in numpy.arange(float(CrPrc) - (CodeDef.CHART_RY_TICK_COUNT * CodeDef.CHART_RY_TICK),
                                                float(CrPrc) + (CodeDef.CHART_RY_TICK_COUNT * CodeDef.CHART_RY_TICK),
                                                CodeDef.CHART_RY_TICK):
                        self.Y_list.append(round(yValue,2))


                # 시세 갱신
                if(self.ExistX(InTime)):
                    # print("시세갱신: ", inSide)
                    if (inSide == "Prediction"):
                        PredPrc = float(CrPrc)
                        print("에측이 얼마냐!!!!("+StkCd+"):",PredPrc)
                        if(PredPrc <= 0.0):
                            PredPrc = None
                        self.Qttn.ix[InTime, "Prediction_"+StkCd] = PredPrc
                    else:
                        self.Qttn.ix[InTime, "CurrentPrice"] = float(CrPrc)
                # 시세 추가
                else:
                    # 신규시세용 빈 DataFrame 1 Row 생성
                    # 복사본 1row 생성후 값을 설정후 append
                    NewQttn = self.Qttn.iloc[:1]
                    NewQttn = NewQttn.rename(index={NewQttn.index[0]: InTime})
                    ColCnt = len(NewQttn.columns.tolist())
                    for idx in range(ColCnt):
                        NewQttn.ix[InTime, NewQttn.columns.values[idx]] = None

                    if (inSide == "Prediction"):
                        NewQttn.ix[InTime, ("Prediction_"+StkCd)] = float(CrPrc)
                    else:
                        NewQttn.ix[InTime, "CurrentPrice"] = float(CrPrc)

                    self.Qttn = self.Qttn.append(NewQttn)

                    # 신규시간 시세일 경우 업데이트를 한다.
                    if(int(InTime) > int(self.Max_X)):
                        print("신규시세 차트업데이트: ", inSide, self.Qttn)
                        self.Max_X = InTime               # 최근시각 갱신
                        self.X_list.append(InTime)        # 최근시각 입력
                        DelMn     = self.X_list.pop(0)    # 맨 앞 시각 제거
                        self.Qttn = self.Qttn.drop(DelMn) # 맨 앞 시세 삭제

                    # 빠진시세 넣기
                    else:
                        # 인덱스 재정렬
                        self.Qttn = self.Qttn.sort_index()
                        print("빠진시세, CrPrc, InTime: ", inSide, CrPrc, InTime)

            #--- for문 종료 ----

            # 차트 갱신
            if( ReDraw ):
                self.DoDraw()
        except Exception as e:
            print("시세업뎃 차트그리기(UpdateRealQttn) 에러(", sys.exc_info()[-1].tb_lineno, " line):", e)
            return None, None
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
            Ax = self.Fig.add_subplot(1, 1, 1)  # fig를 1행 1칸으로 나누어 1칸안에 넣어줍니다

            # 예측값 기준데이터 설정
            Ax.plot(self.Qttn.index, self.Qttn["CurrentPrice"], color="k", marker="h", linestyle="--")
            for idx in range(self.PredMnCnt):
                Ax.plot(self.Qttn.index, self.Qttn["Prediction_"+str(self.PredMnList[idx])], color=CodeDef.CHART_COLORS[idx], marker=CodeDef.CHART_MARKERS[idx], linestyle="--")

            # X선 먼저 그리기
            Ax.set_xticks(self.Qttn.index)

            # X선 보조설정
            for xLabel in Ax.xaxis.get_ticklabels():
                xLabel.set_rotation(45)  # X값 기울기
            Ax.xaxis.set_tick_params(labelsize=7)  # X선 틱라벨 크기
            Ax.xaxis.grid(True, color='gray', linestyle='dashed', linewidth=0.5)  # X값 보조선 표시

            # Y선 보조설정
            print("self.Y_list:",self.Y_list)
            Ax.yaxis.set_tick_params(reset=True, labelsize=7, right=False, left=False)
            Ax.set_yticks(self.Y_list, True)

            # 라벨설정
            self.Fig.legend(loc='upper center', bbox_to_anchor=(0.5, 1.0), ncol=2, fancybox=True, shadow=True, fontsize = 'x-small')
            Ax.set_xlabel("Time")
            Ax.set_ylabel("Price")

            # 여백조정
            plt.tight_layout()

            self.Canvas.draw()

        except Exception as e:
            print("차트그리기 에러:", sys.exc_info()[-1].tb_lineno, " line):", e)

        return None

    # 저장된 시세를 이용한 테스트 시 차트의 X축을 0900으로 시작하도록 변경한다.
    def SetTestQttnXList(self):
        TimeDelta = timedelta(minutes=1)
        TmpDay    = datetime.today()
        # 테스트
        TmpDay = TmpDay.replace(hour=9, minute=0)
        self.X_list.clear()
        for i in range(CodeDef.CHART_X_LIMIT):
            mn = (TmpDay + TimeDelta * i).strftime("%H%M")
            self.X_list.append(mn)

        TmpQttn = {}
        TmpQttn["mn"] = self.X_list
        TmpQttn["CurrentPrice"] = [None] * CodeDef.CHART_X_LIMIT  # Y값
        for idx in range(self.PredMnCnt):
            TmpQttn["Prediction_" + str(self.PredMnList[idx])] = [None] * CodeDef.CHART_X_LIMIT  # Y값

        del self.Qttn
        self.Qttn = DataFrame(TmpQttn)
        self.Qttn.set_index("mn", inplace=True, drop=True)  # index 를 mn으로 변경
        self.X_list = self.Qttn.index.tolist()  # X축 리스트형 저장
        self.Max_X = max(self.X_list)  # X축 마지막 시각

        # 빈 차트 표시
        self.DoDraw()

        return None