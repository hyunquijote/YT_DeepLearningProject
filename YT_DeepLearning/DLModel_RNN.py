import sys, os
import ctypes
form_path = os.path.dirname( os.path.abspath( __file__ ) )
module_path = os.path.normpath( form_path+"\..\YT_Prediction")
sys.path.insert(0, module_path)
import tensorflow as tf
import numpy      as np
from   pandas     import DataFrame
from   CodeDef    import *


# RNN 모델 사용 구현
# 기본형 / LSTM / LSTM with peephole / GRU
class DLModel_RNN:

    # 초기화
    # inTHD : 텐서플로 핸들러
    # inDBH : DB핸들러
    def __init__(self, inTHD, inDBH):

        # 입력 변수 설정
        self.THD = inTHD  # 텐서플로핸들러
        self.DBH = inDBH  # DB 핸들러

        self.PredMnList = CodeDef.TF_LEARNING_MN_LIST  # 예측분 리스트
        self.PredMnCnt  = len(self.PredMnList)

        # 학습 변수 설정
        self.MdlTp         = None                       # STD, LSTM, LSTM_PH, GRU  4가지중에 하나 선택
        self.StkList       = self.DBH.queryProcStkList() # 학습종목 리스트
        self.StkListCnt    = len(self.StkList)           # 학습종목 리스트
        self.Steps         = CodeDef.TF_RNN_SEQ          # 학습단위수(몇분단위 Set으로 학습할것인가)
        self.Inputs        = CodeDef.TF_RNN_INPUT_CNT    # 학습입력 파라미터 갯수 (종목갯수 + 2:현재시분+예상시분)
        self.Outputs       = CodeDef.TF_RNN_OUTPUT_CNT   # 출력 값 갯수
        self.Neurons       = CodeDef.TF_RNN_NEURONS      # 뉴런수
        self.LayersNum     = CodeDef.TF_RNN_LAYERS       # Layer수
        self.LernRt        = CodeDef.TF_RNN_LERN_RATE    # 학습율
        self.BtchSize      = CodeDef.TF_RNN_BTCH_SIZE    # 배치사이즈
        self.DropoutRt     = CodeDef.TF_RNN_DROPOUT_RATE # 드롭아웃률
        self.Epochs        = CodeDef.TF_RNN_EPOCHS       # 반복학습횟수
        self.EpochsIdx     = 0                           # 반복학습인덱스

        self.X_SuffleIdx   = None                       # 학습 입력값 인덱스 셔플(무작위 학습에 이용되는 인덱스 리스트)
        self.Sess          = [None] * self.PredMnCnt    # 예측분 갯수만큼 Session 확보
        self.NormDict      = {}                          # 정규화 정보(입력값별 MinMax 딕셔너리)
        self.RlstMinMaxDF  = None                       # 결과값 역정규화를 위한 MinMax Dataframe


        # 실시간 예측용 시세수신 리스트
        # self.RcvQttn = []
        # for idx in range(self.Steps):
        #     self.RcvQttn.append( [None] * (self.StkListCnt+1) ) # 현재시분추가
        Temp = []
        for idx in range(self.Steps):
            Temp.append( [None] * (self.StkListCnt+1) ) # 현재시분추가
        self.RcvQttn = [Temp] * self.PredMnCnt

        # 실시간 예측용 X 텐서
        self.Pred_X       = None  # 학습 입력 텐서
        # 실시간 예측용 Outputs 텐서
        self.Pred_Outputs = None  # 학습 출력 텐서


        return None

    # 소멸자
    def __del__(self):
        return

    # 모델구분 설정 및 학습저장폴더 확인
    # 입력값
    # inMdlTp : 모델구분
    def SetMdlTp(self, inMdlTp):
        self.MdlTp = inMdlTp
        # 학습 저장 메인폴더 확인 후 생성
        self.SavedCkptMainPath = {}
        self.TestRlstSavePath  = {}
        for mdl in CodeDef.TF_MDL_LIST_RNN:
            # 학습저장 폴더
            self.SavedCkptMainPath[mdl] = form_path + CodeDef.TF_LEARNING_SAVE_MAINDIR + "\\" + self.MdlTp
            # 폴더 없으면 생성
            if not os.path.exists(self.SavedCkptMainPath[mdl]):
                os.mkdir(self.SavedCkptMainPath[mdl])

            # 테스트 결과저장 폴더
            self.TestRlstSavePath[mdl] = form_path + CodeDef.TF_LEARNING_RSLT_DIR + "\\" + self.MdlTp
            # 폴더 없으면 생성
            if not os.path.exists(self.TestRlstSavePath[mdl]):
                os.mkdir(self.TestRlstSavePath[mdl])
        return None

    # 학습수행
    # 입력값
    # inMdlTp       : 모델구분
    # inStrDtMn     : 학습시작일시분(YYYYDDMMHHMM)
    # inEndDtMn     : 학습종료일시분(YYYYDDMMHHMM)
    # inPredMnIdx   : 예측분List(CodeDef.TF_LEARNING_MN_LIST)의 인덱스(int)
    # inSaveInitYn  : 이전학습 초기와 여부(Y/N)
    def DoLearning(self, inMdlTp, inStrDtMn, inEndDtMn, inPredMnIdx, inSaveInitYn):

        try:
            self.MdlTp = inMdlTp

            # 반복학습인덱스 초기화
            self.EpochsIdx = 0

            # 학습 데이터 조회
            #TrainData = self.DBH.queryMdlLernData_Rnn(inStrDtMn, inEndDtMn, self.PredMnList[inPredMnIdx], self.MdlTp)
            # 발표용
            TrainData = self.DBH.queryMdlLernData_STD(inStrDtMn, inEndDtMn, self.PredMnList[inPredMnIdx])

            # 데이터 정규화
            MinMaxData, TrainData = CodeDef.GetNormalizeData(None, self.DBH, TrainData, self.MdlTp)

            # 데이터 시퀀스화(몇분의 흐름단위로 학습시키는가)
            X_train, Y_train = self.GetSeqTrainData(TrainData, self.Steps)
            TrainSetCnt      = X_train.shape[0]  # 학습데이터수

            # 학습 데이터 인덱스 셔플
            self.X_SuffleIdx = np.arange(X_train.shape[0])
            np.random.shuffle(self.X_SuffleIdx)

            # 텐서플로 초기화
            tf.reset_default_graph()

            X = tf.placeholder(tf.float32, [None, self.Steps, self.Inputs], name="X")
            Y = tf.placeholder(tf.float32, [None, self.Outputs])

            # 기본 RNN, LSTM, LSTM peephole, GRU  4가지중에 하나 선택
            Layers = None
            if (self.MdlTp == "RNN_STD"):
                Layers = [tf.contrib.rnn.BasicRNNCell(num_units=self.Neurons, activation=tf.nn.elu)
                               for layer in range(self.LayersNum)]
            elif (self.MdlTp == "LSTM"):
                Layers = [tf.contrib.rnn.BasicLSTMCell(num_units=self.Neurons, activation=tf.nn.elu)
                               for layer in range(self.LayersNum)]
            elif (self.MdlTp == "LSTM_PH"):
                Layers = [
                    tf.contrib.rnn.LSTMCell(num_units=self.Neurons, activation=tf.nn.leaky_relu, use_peepholes=True)
                    for layer in range(self.LayersNum)]
            elif (self.MdlTp == "GRU"):
                Layers = [tf.contrib.rnn.GRUCell(num_units=self.Neurons, activation=tf.nn.leaky_relu)
                               for layer in range(self.LayersNum)]
            else:
                ctypes.windll.user32.MessageBoxW(0, "RNN모델선택오류", "에러", 0)
                return None

            MultiLayerCell = tf.contrib.rnn.MultiRNNCell(Layers)
            RnnOutputs, States = tf.nn.dynamic_rnn(MultiLayerCell, X, dtype=tf.float32)

            # loss 를 계산하기 위한 전처리
            StackedRnnOutputs = tf.reshape(RnnOutputs, [-1, self.Neurons])
            StackedOutputs    = tf.layers.dense(StackedRnnOutputs, self.Outputs)

            Outputs = tf.reshape(StackedOutputs, [-1, self.Steps, self.Outputs])
            Outputs = Outputs[:, self.Steps - 1, :]  # Layer의 결과값에 맞춘 Tensor저장
            Outputs = tf.identity(Outputs, "Outputs")

            Loss       = tf.reduce_mean(tf.square(Outputs - Y))  # loss function = mean squared error
            Optimizer  = tf.train.AdamOptimizer(learning_rate=self.LernRt)
            TrainingOp = Optimizer.minimize(Loss)

            # 세션할당
            self.Sess[inPredMnIdx] = tf.Session()

            # 기존에 학습저장 데이터 복구
            LernDataSaver = tf.train.Saver()
            SavedCkptPath = self.SavedCkptMainPath[self.MdlTp] + "\\Minute_" + str(self.PredMnList[inPredMnIdx])
            # 폴더 없으면 생성
            if not os.path.exists(SavedCkptPath):
                os.mkdir(SavedCkptPath)
            if (inSaveInitYn == "Y"):  # 초기화
                print(self.MdlTp, "학습데이터 초기화")
                self.Sess[inPredMnIdx].run(tf.global_variables_initializer())
            else:  # 복구
                print(self.MdlTp, "기존학습데이터 복구")
                SavedCkptData = tf.train.get_checkpoint_state(SavedCkptPath)
                if (SavedCkptData and tf.train.checkpoint_exists(SavedCkptData.model_checkpoint_path)):
                    LernDataSaver.restore(self.Sess[inPredMnIdx], SavedCkptData.model_checkpoint_path)

            # 학습시작
            print(self.MdlTp, "학습시작")
            for rept in range(int(self.Epochs * TrainSetCnt / self.BtchSize)):
                # 다음 학습배치 데이터 준비
                X_batch, Y_batch = self.GetNextBatch(X_train, Y_train)
                # 학습
                self.Sess[inPredMnIdx].run(TrainingOp, feed_dict={X: X_batch, Y: Y_batch})

                # 학습률 확인
                if (rept % int(5 * TrainSetCnt / self.BtchSize) == 0):
                    # 손실률 출력
                    MseTrain = Loss.eval(session=self.Sess[inPredMnIdx], feed_dict={X: X_train, Y: Y_train})
                    print('%.2f epochs: MSE train = %.6f' % (rept * self.BtchSize / TrainSetCnt, MseTrain))

            # 학습결과 저장
            LernDataSaver.save(self.Sess[inPredMnIdx], SavedCkptPath + CodeDef.TF_LEARNING_SAVE_FILE)

            # 학습종료
            print(self.MdlTp, "학습종료!!")

        except Exception as e:
            print("RNN 모델 학습수행에러(",sys.exc_info()[-1].tb_lineno," line):", e)

        return None

    # 학습 결과 테스트
    # 입력값
    # inMdlTp       : 모델구분
    # inStrDtMn     : 테스트시작일시분(YYYYDDMMHHMM)
    # inEndDtMn     : 테스트종료일시분(YYYYDDMMHHMM)
    # inPredMnIdx   : 예측분List(CodeDef.TF_LEARNING_MN_LIST)의 인덱스(int)
    def DoLearningTest(self, inMdlTp, inStrDtMn, inEndDtMn, inPredMnIdx):

        try:
            # 학습 저장폴더 없으면 중단
            SavedLernDataPath = self.SavedCkptMainPath[inMdlTp] + "\\Minute_" + str(self.PredMnList[inPredMnIdx])
            if not os.path.exists(SavedLernDataPath):
                print("학습저장결과가 없음:", SavedLernDataPath)
                ctypes.windll.user32.MessageBoxW(0, "저장된 학습결과가 없음:\n" + SavedLernDataPath, "오류", 0)
                return None

            # 세션할당
            self.Sess[inPredMnIdx] = tf.Session()

            # 체크포인트 복구
            LernDataSaver = tf.train.import_meta_graph(SavedLernDataPath+CodeDef.TF_LEARNING_SAVE_FILE+".meta")
            SavedLernCkpt = tf.train.get_checkpoint_state(SavedLernDataPath)
            if (SavedLernCkpt and tf.train.checkpoint_exists(SavedLernCkpt.model_checkpoint_path)):
                print("기존모델복구 :" + str(self.PredMnList[inPredMnIdx]) + "분")
                LernDataSaver.restore(self.Sess[inPredMnIdx], SavedLernCkpt.model_checkpoint_path)
            else:
                ctypes.windll.user32.MessageBoxW(0, "기존학습 저장복구 실패:\n" + SavedLernDataPath, "오류", 0)
                return None

            tf.get_default_graph()

            # 테스트 대상 데이터 조회
            #TestData = self.DBH.queryMdlLernData_Rnn(inStrDtMn, inEndDtMn, self.PredMnList[inPredMnIdx], self.MdlTp)
            # 발표용
            TestData = self.DBH.queryMdlLernData_STD(inStrDtMn, inEndDtMn, self.PredMnList[inPredMnIdx])
            YData    = TestData.copy()

            # 이전학습 MinMax데이터 추가 설정
            TestData = CodeDef.addMinMaxData(None, self.DBH, TestData, self.MdlTp)

            # 데이터 정규화 (이전 MinMax 로 정규화 시행)
            MinMaxData, TestData = CodeDef.GetNormalizeData(None, self.DBH, TestData, self.MdlTp, "Y")
            # 데이터 시퀀스화(몇분의 흐름단위로 설정)
            X_test, Y_test = self.GetSeqTrainData(TestData, self.Steps)

            # 학습결과 테스트 실행
            Outputs   = self.Sess[inPredMnIdx].graph.get_tensor_by_name("Outputs:0")
            X         = self.Sess[inPredMnIdx].graph.get_tensor_by_name("X:0")
            PredYData = self.Sess[inPredMnIdx].run(Outputs, feed_dict={X: X_test})

            # 역정규화
            print("MinMaxData:",MinMaxData)
            PredYDF = DataFrame(data=PredYData, columns=['RSLT'])
            Y_pred  = CodeDef.GetDeNormalizeData(None, PredYDF, MinMaxData)
            Y_pred  = Y_pred["RSLT"].values.tolist()

            # 엑셀저장
            YData  = YData.drop([idx for idx in range(self.Steps)], 0) # 흐름분수만큼 삭제.. 나중에 보완할것,
            MnDf   = YData["X_MN"].values.tolist()
            MnList = [CodeDef.GetNextMn(None, str(int(i)).zfill(4), self.PredMnList[inPredMnIdx]) for i in MnDf] # 시간 index
            Y_test = YData["RSLT"].values.tolist()
            Y_pred = CodeDef.SetEtfScaling(None,Y_pred)
            CodeDef.SaveRsltToExcel(None, Y_test, Y_pred, MnList, self.TestRlstSavePath[self.MdlTp] + "\\Minute_" + str(self.PredMnList[inPredMnIdx]) + ".xlsx")

        except Exception as e:
            print("RNN 모델 테스트 에러(", sys.exc_info()[-1].tb_lineno, " line):", e)

        return None

    # 실시간 예측수행을 위한 학습결과 복구
    # 입력값
    # inMdlTp : 모델구분
    def ReadyPrediction(self, inMdlTp):
        try:
            for idx in range(self.PredMnCnt):
                # 학습 저장폴더 없으면 중단
                SavedLernDataPath = self.SavedCkptMainPath[inMdlTp] + "\\Minute_" + str(self.PredMnList[idx])
                if not os.path.exists(SavedLernDataPath):
                    print("학습저장결과가 없음:", SavedLernDataPath)
                    ctypes.windll.user32.MessageBoxW(0, "저장된 학습결과가 없음:\n" + SavedLernDataPath, "오류", 0)
                    return None
                # 세션할당
                self.Sess[idx] = tf.Session()

                # 체크포인트 복구
                LernDataSaver = tf.train.import_meta_graph(SavedLernDataPath + CodeDef.TF_LEARNING_SAVE_FILE + ".meta")
                SavedLernCkpt = tf.train.get_checkpoint_state(SavedLernDataPath)
                if (SavedLernCkpt and tf.train.checkpoint_exists(SavedLernCkpt.model_checkpoint_path)):
                    print("기존모델복구 :" + str(self.PredMnList[idx]) + "분")
                    LernDataSaver.restore(self.Sess[idx], SavedLernCkpt.model_checkpoint_path)
                else:
                    ctypes.windll.user32.MessageBoxW(0, "기존학습 저장복구 실패:\n" + SavedLernDataPath, "오류", 0)
                    return None

            tf.get_default_graph()

            # 정규화를 위한 MinMax 값 설정
            self.SetNormzInfo()

            # 실시간 예측용 시세수신 리스트 초기화
            # self.RcvQttn = []
            # for idx in range(self.Steps):
            #     self.RcvQttn.append( [None] * (self.StkListCnt+1) ) # 예측시분 , 현재시분추가
            Temp = []
            for idx in range(self.Steps):
                Temp.append([None] * (self.StkListCnt + 1))  # 예측시분 , 현재시분추가
            self.RcvQttn = [Temp] * self.PredMnCnt

            # 실시간 예측용 텐서 조기화
            self.Pred_Outputs = self.Sess[0].graph.get_tensor_by_name("Outputs:0")
            self.Pred_X       = self.Sess[0].graph.get_tensor_by_name("X:0")


        except Exception as e:
            print("실시간 예측을 위한 RNN 로딩에러(ReadyPrediction:", sys.exc_info()[-1].tb_lineno, " line):", e)
        return  None

    # 예측실행
    # 입력값
    # inMdlTp     : 모델구분
    # inQttn      : 시세 (리스트)
    # inPredMnIdx : 예측분 인덱스
    def DoPrediction(self, inMdlTp, inQttn, inPredMnIdx):
        try:
            PredVal = 0.0
            #inQttnCnt = len(inQttn)
            Mn     = inQttn[0][0]  # 시분
            Prc    = inQttn[0][1]  # 현재가
            #NextMn = float(CodeDef.GetNextMn(None, str(int(Mn)).zfill(4), self.PredMnList[inPredMnIdx]))

            print("self.RcvQttn[inPredMnIdx]::",self.RcvQttn[inPredMnIdx])
            RcvQttnCnt = len(self.RcvQttn[inPredMnIdx])
            for idx in range(RcvQttnCnt):
                if( None in self.RcvQttn[inPredMnIdx][idx]):
                    print("시세 시퀀스 미충족으로 인한 예측불가( 현재",str(idx),"단계) 총 ",str(RcvQttnCnt),"단계필요")
                    self.RcvQttn[inPredMnIdx][idx] =inQttn[0]
                    return 0.0

            print("시세 시퀀스 충족!! 예측시작")
            # 오래된시세 제거 및 신규시세 입력
            self.RcvQttn[inPredMnIdx].pop(0)
            self.RcvQttn[inPredMnIdx].append([Mn, Prc])
            #self.RcvQttn[inPredMnIdx].append([NextMn, Mn, Prc])

            # 입력 데이터 MinMax추가
            # InData = DataFrame(data=self.RcvQttn[inPredMnIdx], columns=['X_RSLT_MN','X_MN', 'X_122630'])
            InData = DataFrame(data=self.RcvQttn[inPredMnIdx], columns=['X_MN', 'X_122630'])
            NewRow = InData.iloc[:1]
            NewRow = NewRow.rename(index={NewRow.index[0]: InData.shape[0]})
            InData = InData.append(NewRow)
            NewRow = NewRow.rename(index={NewRow.index[0]: InData.shape[0]})
            InData = InData.append(NewRow)

            # InData["X_RSLT_MN"][-2:] = self.NormDict["RSLT_MN"][0]  # Min
            # InData["X_RSLT_MN"][-1:] = self.NormDict["RSLT_MN"][1]  # Max
            InData["X_MN"][-2:]       = self.NormDict["MN"][0]       # Min
            InData["X_MN"][-1:]       = self.NormDict["MN"][1]       # Max
            InData['X_122630'][-2:]  = self.NormDict["122630"][0]   # Min
            InData['X_122630'][-1:]  = self.NormDict["122630"][1]   # Max

            MinMaxData, InData = CodeDef.GetNormalizeData(None, self.DBH, InData, self.MdlTp, "Y")
            InData    = InData.as_matrix().tolist()
            InData    = [InData]

            # 예측수행
            #Outputs   = self.Sess[inPredMnIdx].graph.get_tensor_by_name("Outputs:0")
            #X         = self.Sess[inPredMnIdx].graph.get_tensor_by_name("X:0")
            PredYData = self.Sess[inPredMnIdx].run(self.Pred_Outputs, feed_dict={self.Pred_X: InData})


            # 역정규화
            PredYDF   = DataFrame(data=PredYData, columns=['RSLT'])
            Y_pred    = CodeDef.GetDeNormalizeData(None, PredYDF, self.RlstMinMaxDF)
            Y_pred    = Y_pred["RSLT"].values.tolist()[0]
            Y_pred    = CodeDef.SetEtfScalingVal(None, Y_pred)
            print("실시간 예측결과(", self.PredMnList[inPredMnIdx], "분):", Y_pred)
            PredVal  = Y_pred

        except Exception as e:
            print("실시간 예측수행 에러(RNN DoPrediction:", sys.exc_info()[-1].tb_lineno, " line):", e)

        return PredVal

    # 학습 시퀀스 데이터 설정
    # 입력값
    # inDF     : 정규화된 학습데이터
    # inSeqlen : 학습단위 시퀀스(몇분단위)
    # 리턴값
    # oufDF : 시퀀스화 된 데이터
    def GetSeqTrainData(self, inDF, inSeqlen):
        try:
            DataRow = inDF.as_matrix()  # numpy array 으로 변경
            Data    = []

            # 시퀀스 단위로 데이터 재구성
            for idx in range(len(DataRow) - inSeqlen):
                Data.append((DataRow[idx : idx+inSeqlen]))

            Data = np.array(Data)

            DataRowCnt = Data.shape[0]

            X_Data = Data[:DataRowCnt, : , 1:]
            Y_Data = Data[:DataRowCnt, -1, :1]

        except Exception as e:
            print("학습데이터 시퀀스화(GetSeqTrainData) 에러(", sys.exc_info()[-1].tb_lineno, " line):", e)
            return None, None

        return X_Data, Y_Data

    # 다음 학습배치 데이터 가져오기
    # 입력값
    # inX_train   : 학습 입력 데이터
    # inY_train   : 학습 정답 데이터
    # 리턴값
    #inX_train  inY_train: 셔플된 학습/정답 데이터
    def GetNextBatch(self, inX_train, inY_train):
        try:
            StrIdx = self.EpochsIdx
            self.EpochsIdx += self.BtchSize

            # 반복 학습이 끝날때마다 셔플 인덱스 제구성
            if (self.EpochsIdx > inX_train.shape[0]):
                # 학습 데이터 인덱스 셔플 재수행
                np.random.shuffle(self.X_SuffleIdx)
                StrIdx = 0
                self.EpochsIdx = self.BtchSize

            EndIdx = self.EpochsIdx
        except Exception as e:
            print("다음 학습데이터 가져오기(GetNextBatch) 에러(", sys.exc_info()[-1].tb_lineno, " line):", e)
            return None, None

        return inX_train[self.X_SuffleIdx[StrIdx:EndIdx]], inY_train[self.X_SuffleIdx[StrIdx:EndIdx]]

    # 사용모델 정규화 MinMAx 정보 딕셔너리 보관
    def SetNormzInfo(self):
        # 데이터 정규화 정보 설정
        NormzInfo = self.DBH.queryNormzInfo(self.MdlTp)
        # 종목별 Min Max 딕셔너리 설정
        self.NormDict = {}
        InfoCnt = NormzInfo.values.shape[0]
        if (InfoCnt > 0):
            for idx in range(InfoCnt):
                StkCd  = NormzInfo['X_CD'].values.tolist()[idx]
                MinVal = NormzInfo['MIN_VAL'].values.tolist()[idx]
                MaxVal = NormzInfo['MAX_VAL'].values.tolist()[idx]
                self.NormDict[StkCd] = (MinVal, MaxVal)

        # 결과값 MinMax DF 설정
        MinVal = self.NormDict["RSLT"][0]
        MaxVal = self.NormDict["RSLT"][1]
        MinMaxVal = [[MinVal],[MaxVal]]
        self.RlstMinMaxDF = DataFrame(data=MinMaxVal, columns=['RSLT'])


        print("RNN 실시간예측을 위한 MinMax정보 딕셔너리 초기화:")
        #print("self.NormDict:", self.NormDict)
        #print("self.NormDict:", self.RlstMinMaxDF)

        return None