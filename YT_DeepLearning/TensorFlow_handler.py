import sys, os
form_path = os.path.dirname( os.path.abspath( __file__ ) )
module_path = os.path.normpath( form_path+"\..\YT_Prediction")
sys.path.insert(0, module_path)
import tensorflow  as tf
import pandas      as pd
from   pandas      import DataFrame
from   CodeDef     import *
from   DLModel_RNN import *
from   DLModel_STD import *


# 딥러닝 수행 핸들러
class TensorFlow_handler:

    LearingOption = "STD"
    # LearingOption = "RNN_LSTM"

    # 초기화
    # inMain  : 메인폼
    # inDBH   : DB핸들러
    def __init__(self, inMain, inDBH):

        # 객체변수 설정
        self.DBH      = inDBH   # DB 핸들러
        self.MainForm = inMain  # 메인폼

        self.PredMnList = CodeDef.TF_LEARNING_MN_LIST  # 예측분 리스트
        self.PredMnCnt  = len(self.PredMnList)

        # 사용모델 세션
        self.MdlSess    = None

        return None

    # 모델 세션 선택
    # 입력값
    # inMdlTp      : 모델구분
    # inRealPredYn : 실시간 예측준비여부
    def SetMdlSess(self, inMdlTp, inRealPredYn="N"):

        # 기본 딥러닝 모델
        if (inMdlTp in CodeDef.TF_MDL_LIST_STD):
            self.MdlSess = DLModel_STD(self, self.DBH)
        # RNN 모델
        elif (inMdlTp in CodeDef.TF_MDL_LIST_RNN):
            self.MdlSess = DLModel_RNN(self, self.DBH)

        # 모델구분 설정
        self.MdlSess.SetMdlTp(inMdlTp)

        # 실시간 예측수행인 경우 학습결과 로드
        if(inRealPredYn == "Y"):
            self.MdlSess.ReadyPrediction(inMdlTp)
        return None

    # 예측 수해
    # 입력값
    # inMdlTp   : 모델구분
    # inQttn    : 입력데이터(리스트)
    # inPredIdx : 예측분 리스트 인덱스
    def DoPrediction(self, inMdlTp, inQttn, inPredIdx):

        PredV = 0.0

        print(inMdlTp+"모델 예측수행(" + str(self.PredMnList[inPredIdx]) + ")")
        PredV = self.MdlSess.DoPrediction(inMdlTp, inQttn, inPredIdx)

        return PredV

    # 신경망 학습
    # 입력값
    # inMdlTp       : 모델 구분
    # inStrDtMn     : 학습시작일자시각
    # inEndDtMn     : 학습종료일자시각
    # inIdx         : 예측리스트 인덱스
    def DoLearning(self, inMdlTp, inStrDtMn, inEndDtMn, inIdx):

        try:
            # 모델 세션 선택
            self.SetMdlSess(inMdlTp)

            print(inMdlTp + " 학습실행")
            self.MdlSess.DoLearning(inMdlTp, inStrDtMn, inEndDtMn, inIdx, "Y")

        except Exception as e:
            print("학습수행 에러:", e)

        return None

    # 학습결과 테스트
    # 입력값
    # inMdlTp       : 모델구분
    # inTestStrDtMn : 학습결과테스트시작일자시각
    # inTestEndDtMn : 학습결과테스트종료일자시각
    # inIdx         : 예측리스트 인덱스
    def DoLearningTest(self, inMdlTp, inTestStrDtMn, inTestEndDtMn, inIdx):

        try:
            # 모델 세션 선택
            self.SetMdlSess(inMdlTp)

            # 테스트 수행
            self.MdlSess.DoLearningTest(inMdlTp, inTestStrDtMn, inTestEndDtMn, inIdx)

        except Exception as e:
            print("학습결과 테스트수행 에러:", e)

        return None