import sys, os
import ctypes
form_path = os.path.dirname(os.path.abspath(__file__))
module_path = os.path.normpath(form_path + "\..\YT_Prediction")
sys.path.insert(0, module_path)
import tensorflow as tf
import numpy      as np
from pandas       import DataFrame
from CodeDef      import *


# 기본딥러닝 모델 사용 구현
class DLModel_STD:

    # 초기화
    # inTHD : 텐서플로 핸들러
    # inDBH : DB핸들러
    def __init__(self, inTHD, inDBH):

        # 입력 변수 설정
        self.THD = inTHD  # 텐서플로핸들러
        self.DBH = inDBH  # DB 핸들러

        self.PredMnList = CodeDef.TF_LEARNING_MN_LIST  # 예측분 리스트
        self.PredMnCnt = len(self.PredMnList)

        # 학습 변수 설정
        self.StkList   = self.DBH.queryProcStkList()  # 학습종목 리스트
        self.Inputs    = len(self.StkList) + 2  # 학습입력 파라미터 갯수 (종목갯수 + 2:현재시분+예상시분)
        self.LernRt    = 0.01 # 학습율
        self.Epochs    = 100  # 반복학습횟수
        self.EpochsIdx = 0    # 반복학습인덱스

        self.X         = None  # 학습 입력값
        self.Y         = None  # 학습 정답입력값
        self.Layers    = 1  # 계층수
        self.Sess      = [None] * self.PredMnCnt  # 예측분 갯수만큼 Session 확보

        self.NormDict  = {}  # 정규화 정보(입력값별 MinMax 딕셔너리)

        return None

    # 소멸자
    def __del__(self):
        return

    # 모델구분 설정 및 학습저장폴더 확인
    # 입력값
    # inMdlTp : 모델구분
    def SetMdlTp(self, inMdlTp):
        self.MdlTp = inMdlTp
        # 학습 저장 메인폴더 / 테스트결과 저장 폴더 확인 후 생성
        self.SavedCkptMainPath = {}
        self.TestRlstSavePath  = {}
        for mdl in CodeDef.TF_MDL_LIST_STD:
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

            #-- 모델 초기화 시작 --#

            # 변수설정 (행, 열)
            X = tf.placeholder(tf.float32, [None, CodeDef.TF_LEARNING_INPUT_CNT  ], name="X")  # 학습입력값
            Y = tf.placeholder(tf.float32, [None, CodeDef.TF_LEARNING_OUTPUT_CNT ], name="Y")  # 결과값

            TStep    = tf.Variable(0, trainable=False, name="TStep")  # 학습횟수
            KeepDrop = tf.placeholder(tf.float32, name="KeepDrop")    # 과적합을 피하기위한 드롭아웃
            # tf.layers.batch_normalization 사용을 고려해볼것 코딩순서는 batch_norm > relu > drop 순

            # 가중치변수 초기화
            W1 = tf.get_variable("W1", shape=[CodeDef.TF_LEARNING_INPUT_CNT, CodeDef.TF_LAYER_1_NEURON_CNT ],initializer=tf.keras.initializers.he_normal())
            W2 = tf.get_variable("W2", shape=[CodeDef.TF_LAYER_1_NEURON_CNT, CodeDef.TF_LAYER_2_NEURON_CNT ],initializer=tf.keras.initializers.he_normal())
            W3 = tf.get_variable("W3", shape=[CodeDef.TF_LAYER_2_NEURON_CNT, CodeDef.TF_LAYER_3_NEURON_CNT ],initializer=tf.keras.initializers.he_normal())
            W4 = tf.get_variable("W4", shape=[CodeDef.TF_LAYER_3_NEURON_CNT, CodeDef.TF_LEARNING_OUTPUT_CNT],initializer=tf.keras.initializers.he_normal())

            # 편향 초기화
            B1 = tf.Variable(tf.zeros([CodeDef.TF_LAYER_1_NEURON_CNT ], name="B1"))
            B2 = tf.Variable(tf.zeros([CodeDef.TF_LAYER_2_NEURON_CNT ], name="B2"))
            B3 = tf.Variable(tf.zeros([CodeDef.TF_LAYER_3_NEURON_CNT ], name="B3"))
            B4 = tf.Variable(tf.zeros([CodeDef.TF_LEARNING_OUTPUT_CNT], name="B4"))

            # 가중치 및 편향으로 Layer 구성, 활상화함수(relu 사용)
            # Layer 1
            Layer1 = None
            Layer2 = None
            Layer3 = None
            Layer4 = None
            TModel = None
            Layer1 = tf.add(tf.matmul(X, W1), B1)
            Layer1 = tf.nn.relu(Layer1)
            Layer1 = tf.nn.dropout(Layer1, KeepDrop)
            # Layer 2
            Layer2 = tf.add(tf.matmul(Layer1, W2), B2)
            Layer2 = tf.nn.relu(Layer2)
            Layer2 = tf.nn.dropout(Layer2, KeepDrop)
            # Layer 3
            Layer3 = tf.add(tf.matmul(Layer2, W3), B3)
            Layer3 = tf.nn.relu(Layer3)
            Layer3 = tf.nn.dropout(Layer3, KeepDrop)
            # 출력층
            TModel = tf.add(tf.matmul(Layer3, W4), B4)
            TModel = tf.nn.relu(TModel)
            TModel = tf.identity(TModel, "TModel")

            # 최적화 모델
            TOptimizer = None
            TOption    = None
            TCost      = None
            # 손실값
            TCost = tf.reduce_mean(tf.square(TModel - Y))
            # 최적화 설정 : 다른 최적화 함수들도 테스트 해볼것 RMSPropOptimizer 등등
            TOptimizer = tf.train.AdamOptimizer(learning_rate=CodeDef.TF_LEARNING_RATE)
            TOption = TOptimizer.minimize(TCost, global_step=TStep)

            # 예측 분별로 세션 다중화
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

            # 학습데이터 조회
            LernDataSets  = self.DBH.queryMdlLernData_STD(inStrDtMn, inEndDtMn, self.PredMnList[inPredMnIdx])
            InputDataSets = LernDataSets.values  # numpy.ndarray
            X_data = InputDataSets[:, 1:].tolist()  # 학습입력
            Y_data = InputDataSets[:, :1].tolist()  # 정답결과

            # 학습시작
            for epoch in range(CodeDef.TF_LEARNING_EPOCH):
                for step in range(CodeDef.TF_LEARNING_CNT):

                    LernCost, _, _ = self.Sess[inPredMnIdx].run([TCost, TModel, TOption],
                                                          feed_dict={X: X_data, Y: Y_data, KeepDrop: CodeDef.TF_LEARNING_DROPOUT_RATE})

                    if (step >= CodeDef.TF_LEARNING_CNT - 5):
                        print("Step,Cost: ", self.Sess[inPredMnIdx].run(TStep), LernCost)

            # 학습결과 저장
            LernDataSaver.save(self.Sess[inPredMnIdx], SavedCkptPath + CodeDef.TF_LEARNING_SAVE_FILE)

            print(self.MdlTp, "학습종료!!")

        except Exception as e:
            print("딥러닝 기본 모델 학습수행에러(", sys.exc_info()[-1].tb_lineno, " line):", e)

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
            LernDataSaver = tf.train.import_meta_graph(SavedLernDataPath + CodeDef.TF_LEARNING_SAVE_FILE + ".meta")
            SavedLernCkpt = tf.train.get_checkpoint_state(SavedLernDataPath)
            if (SavedLernCkpt and tf.train.checkpoint_exists(SavedLernCkpt.model_checkpoint_path)):
                print("기존모델복구 :" + str(self.PredMnList[inPredMnIdx]) + "분")
                LernDataSaver.restore(self.Sess[inPredMnIdx], SavedLernCkpt.model_checkpoint_path)
            else:
                ctypes.windll.user32.MessageBoxW(0, "기존학습 저장복구 실패:\n" + SavedLernDataPath, "오류", 0)
                return None

            tf.get_default_graph()

            # 테스트 대상 데이터 조회
            TestData = self.DBH.queryMdlLernData_STD(inStrDtMn, inEndDtMn, self.PredMnList[inPredMnIdx])
            TArray   = TestData.values  # numpy.ndarray
            X_test   = TArray[:, 1:].tolist()  # 학습입력
            Y_test   = TArray[:, :1].tolist()  # 정답결과

            # 학습결과 테스트 실행
            TModel   = self.Sess[inPredMnIdx].graph.get_tensor_by_name("TModel:0")
            X        = self.Sess[inPredMnIdx].graph.get_tensor_by_name("X:0")
            KeepDrop = self.Sess[inPredMnIdx].graph.get_tensor_by_name("KeepDrop:0")
            # 예측수행
            Y_pred   = self.Sess[inPredMnIdx].run([TModel], feed_dict={ X: X_test ,KeepDrop:1.0})
            # 결과값 ETF 값으로 스케일링
            Y_pred = Y_pred[0]
            Ycnt   = len(Y_pred)
            Temp   = []
            for idx in range(Ycnt):
                Temp.append(float(Y_pred[idx][0]))
            print(Temp)
            Y_pred = CodeDef.SetEtfScaling(None, Temp)

            # 결과엑셀저장
            MnDf   = TestData["X_RSLT_MN"].values.tolist()
            MnList = [str(int(i)).zfill(4) for i in MnDf]  # 시간 index            
            CodeDef.SaveRsltToExcel(None, Y_test, Y_pred, MnList, self.TestRlstSavePath[self.MdlTp] + "\\Minute_" + str(self.PredMnList[inPredMnIdx]) + ".xlsx")

        except Exception as e:
            print("딥러닝 기본 모델 테스트 에러(", sys.exc_info()[-1].tb_lineno, " line):", e)

        return None

    # 가중치 초기화변수 생성 (균등분포)
    # inInCnt   : 입력행수
    # inOutCnt  : 출력력행수
    # inUniform : 균등분포사용여부
    def GetXavierInit(self, inInCnt, inOutCnt, inUniform=True):
        if inUniform:
            print("균등분포사용")
            InitRange = tf.sqrt(6.0 / (inInCnt + inOutCnt))
            return tf.random_uniform_initializer(-InitRange, InitRange)
        else:
            print("절단정규분포사용")
            Stddev = tf.sqrt(3.0 / (inInCnt + inOutCnt))
            return tf.truncated_normal_initializer(stddev=Stddev)