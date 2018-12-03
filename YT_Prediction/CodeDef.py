from  decimal  import Decimal
from  datetime import timedelta, datetime
from  pandas   import DataFrame
import pandas as pd
import sys
import sklearn.preprocessing

class CodeDef():
    # ----------------------- API 시스템 정보 ---------------------------
    # API 사용자 ID / PW
    API_USER_ID  = "API 유저 ID 넣을것"
    API_USER_PW  = "API 유저 패스워드 넣을것"
    API_CERT_PW  = "증권 공인인증서 패스워드 넣을것"

    # 접속서버 주소
    SERVER_REAL_GLOBAL  = "real.tradarglobal.api.com"  # 티레이더글로벌 운영 서버
    SERVER_SIMUL_TRADAR = "simul.tradar.api.com"        # 티레이더 모의투자 서버
    SERVER_DEV_TRADAR   = "dev.tradar.api.com"          # 티레이더글로벌 개발 서버
    SERVER_REAL_TRADAR  = "real.tradar.api.com"         # 티레이더글로벌 운영 서버

    # 시스템 통보코드
    NOTIFY_SYSTEM_NEED_TO_RESTART      = 26  # 모듈변경에 때른 재시작 필요
    NOTIFY_SYSTEM_LOGIN_START          = 27  # 로그인을 시작합니다.
    NOTIFY_SYSTEM_LOGIN_REQ_USERINFO   = 28  # 사용자 정보를 요청합니다.
    NOTIFY_SYSTEM_LOGIN_RCV_USERINFO   = 29  # 사용자 정보를 수신했습니다.
    NOTIFY_SYSTEM_LOGIN_FILE_DWN_START = 30  # 파일다운로드를 시작합니다.
    NOTIFY_SYSTEM_LOGIN_FILE_DWN_END   = 31  # 파일다운로드가완료되었습니다.

    # 결과코드
    RESULT_FAIL            = -1    # API실패반환코드
    RESULT_SUCCESS         = 1000  # API성공반환코드
    RESPONSE_LOGIN_FAIL    = 1     # 로그인실패코드
    RESPONSE_LOGIN_SUCCESS = 2     # 로그인성공코드

    # 에러코드
    ERROR_MODULE_NOT_FOUND           = 11  # YuantaOpenAPI모듈을찾을수없습니다.
    ERROR_FUNCTION_NOT_FOUND         = 12  # YuantaOpenAPI함수를찾을수없습니다.
    ERROR_NOT_INITIAL                = 13  # YuantaOpenAPI초기화상태가아닙니다.

    ERROR_SYSTEM_CERT_ERROR          = 20  # 인증오류입니다.
    ERROR_SYSTEM_MAX_CON             = 21  # 다중접속한도초과입니다.
    ERROR_SYSTEM_FORCE_KILL          = 22  # 강제종료되었습니다.
    ERROR_SYSTEM_EMERGENCY           = 23  # 시스템비상상황입니다.
    ERROR_SYSTEM_INFINIT_CALL        = 24  # 이상호출로접속이종료됩니다.
    ERROR_SYSTEM_SOCKET_CLOSE        = 25  # 네트웍연결이끊어졌습니다.

    ERROR_NOT_LOGINED                = 101  # 로그인상태가아닙니다.
    ERROR_ALREADY_LOGINED            = 102  # 이미로그인된상태입니다.
    ERROR_INDEX_OUT_OF_BOUNDS        = 103  # 인덱스가가용범위를넘었습니다.
    ERROR_TIMEOUT_DATA               = 104  # 타임아웃이발생하였습니다.
    ERROR_USERINFO_NOT_FOUND         = 105  # 사용자정보를찾을수없습니다.
    ERROR_ACCOUNT_NOT_FOUND          = 106  # 계좌번호를찾을수없습니다.
    ERROR_ACCOUNT_PASSWORD_INCORRECT = 107  # 계좌비밀번호를잘못입력하셨습니다.
    ERROR_TYPE_NOT_FOUND             = 108  # 요청한타입을찾을수없습니다.

    ERROR_CERT_PASSWORD_INCORRECT    = 110  # 공인인증비밀번호가일치하지않습니다.
    ERROR_CERT_NOT_FOUND             = 111  # 공인인증서를찾을수없습니다.
    ERROR_CETT_CANCEL_SELECT         = 112  # 공인인증서선택을취소했습니다.
    ERROR_NEED_TO_UPDATE             = 113  # 공인인증업데이트가필요합니다.
    ERROR_CERT_7_ERROR               = 114  # 공인인증7회오류입니다.
    ERROR_CERT_ERROR                 = 115  # 공인인증오류입니다.
    ERROR_CERT_PASSWORD_SHORTER      = 116  # 공인인증서비밀번호가최소길이보다짧습니다.
    ERROR_ID_SHORTER                 = 117  # 로그인아이디가최소길이보다짧습니다.
    ERROR_ID_PASSWORD_SHORTER        = 118  # 로그인비밀번호가최소길이보다짧습니다.

    ERROR_CERT_OLD                   = 121  # 폐기된인증서입니다.
    ERROR_CERT_TIME_OVER             = 122  # 만료된인증서입니다.
    ERROR_CERT_STOP                  = 123  # 정지된인증서입니다.
    ERROR_CERT_NOTMATCH_SN           = 124  # SN이일치하지않는인증서입니다.
    ERROR_CERT_ETC                   = 125  # 기타오류인증서입니다.
    ERROR_CERT_TIME_OUT              = 126  # 타인증기관발급인증서검증에서타임아웃이발생하였습니다.다시시도해주십시오

    ERROR_REQUEST_FAIL               = 201  # DSO요청이실패하였습니다.
    ERROR_DSO_NOT_FOUND              = 202  # DSO를찾을수없습니다.
    ERROR_BLOCK_NOT_FOUND            = 203  # 블록을찾을수없습니다..
    ERROR_FIELD_NOT_FOUND            = 204  # 필드를찾을수없습니다.
    ERROR_REQUEST_NOT_FOUND          = 205  # 요청정보를찾을수없습니다.
    ERROR_ATTR_NOT_FOUND             = 206  # 필드의속성을찾을수없습니다.
    ERROR_REGIST_FAIL                = 207  # AUTO등록이실패하였습니다.
    ERROR_AUTO_NOT_FOUND             = 208  # AUTO를찾을수없습니다.
    ERROR_KEY_NOT_FOUND              = 209  # 요청한키를찾을수없습니다.
    ERROR_VALUE_NOT_FOUND            = 210  # 요청한값을찾을수없습니다.

    # ----------------------- 종목 정보 ---------------------------
    # 시장구분코드
    MKT_TP_CD_INTERNAL             = "0"  # 국내주식
    MKT_TP_CD_GLOBAL_STOCK         = "1"  # 해외주식
    MKT_TP_CD_GLOBAL_DERIVATIVE    = "2"  # 해외선물옵션
    MKT_TP_CD_INTERNAL_STOCK       = "3"  # 국내주식
    MKT_TP_CD_INTERNAL_KOSPIFUTURE = "4"  # 국내 코스피선물
    MKT_TP_CD_INTERNAL_KOSPIOPTION = "5"  # 국내 코스피옵션
    MKT_TP_CD_GLOBAL_FUTURE        = "6"  # 해외 선물
    MKT_TP_CD_GLOBAL_OPTION        = "7"  # 해외 옵션

    # 최종 동기화 일자 기본
    INIT_STR_DT_DEFAULT = "20181030"
    INIT_STR_MN_DEFAULT = "1518"
    # 초기화종료일은 전날자정까지로 설정 ※ 추후 변경
    #INIT_END_DT_DEFAULT = (date.today() + timedelta(days=-1)).strftime("%Y%m%d")
    INIT_END_DT_DEFAULT = "20181120"
    INIT_END_MN_DEFAULT = "1520"

    # 처리대상 종목테이블위젯 컬럼
    PROC_STK_COL_MKT_TP_CD    = 0  # 시장구분
    PROC_STK_COL_STK_CD       = 1  # 종목코드
    PROC_STK_COL_STR_DT       = 2  # 처리시작일
    PROC_STK_COL_END_DT       = 3  # 처리종료일
    PROC_STK_COL_STR_DT_MN    = 4  # 데이터시작일시분
    PROC_STK_COL_LAST_DT_MN   = 5  # 데이터최종처리일시분
    PROC_STK_COL_RCV_TP       = 6  # 수신구분

    # DERV_MN_QTTN_INFO 테이블 컬럼
    QTTN_MN_DATA_COL_DT       = 0
    QTTN_MN_DATA_COL_MN       = 1
    QTTN_MN_DATA_COL_STK_CD   = 2
    QTTN_MN_DATA_COL_FTPRC    = 3
    QTTN_MN_DATA_COL_HGPRC    = 4
    QTTN_MN_DATA_COL_LOPRC    = 5
    QTTN_MN_DATA_COL_CLPRC    = 6
    QTTN_MN_DATA_COL_UPDN_PRC = 7
    QTTN_MN_DATA_COL_VLUM     = 8

    # ----------------------- 시세 정보 ---------------------------
    # 코스피지수 시세 컬럼
    REAL_QTTN_COL_STK_CD = 0  # 종목코드
    REAL_QTTN_COL_TIME   = 1  # 시간(HHMM)
    REAL_QTTN_COL_CRPRC  = 2  # 현재가
    REAL_QTTN_COL_FTPRC  = 3  # 시가
    REAL_QTTN_COL_HGPRC  = 4  # 고가
    REAL_QTTN_COL_LOPRC  = 5  # 저가
    REAL_QTTN_COL_END    = 6  # 종료 표시(E)
    REAL_QTTN_COL_COUNT  = 7  # 실시간시세 컬럼수
    
    # 시세 포트
    PORT_INDEX_QTTN   = 8080  # 지수수신정보(ETF KODEX 레버리지시세 수신포트)
    PORT_TF_RCV_RSLT  = 9080  # 텐서플로 결과 수신 포트
    PORT_TF_DATA      = 7080  # 텐서플로 데이터 송수신 포트

    # 지수 기준시세(현재는 KODEX 레버리지)
    INDEX_STK_CD = "122630"

    # ----------------------- 차트 정보 ---------------------------
    # 차트 시세컬럼
    CHART_Y1_COL = "last"      # last : 티레이더글로벌 실시간시세[61] 현재가
    CHART_Y2_COL = "curjuka"  # curjuka : 티레이더 실시간시세[11] 현재가

    CHART_X_LIMIT = 60  # 차트 X축 시간범위 제한(현시각으로 부터 CHART_X_LIMIT 분 후까지)

    CHART_RY_TICK_COUNT = 10.0  # 오른쪽 Y축 상하틱(초기 KODEX 레버리지 ETF 기준 10틱 위아래)
    CHART_RY_TICK       = 5     # 오른쪽 Y축 틱단위(초기 KODEX 레버리지 ETF 기준 )
    #CHART_RY_TICK       = 0.25  # 오른쪽 Y축 틱단위(테스트 해외선물 ESM18)

    CHART_LY_TICK_COUNT = 10.0  # 왼쪽 Y축 상하틱(10틱 위아래)
    #CHART_LY_TICK       = 0.01  # 왼쪽 Y축 틱단위(테스트 해외선물 CLN18)
    CHART_LY_TICK       = 5     # 왼쪽 Y축 틱단위(초기 KODEX 레버리지 ETF 기준)

    CHART_MARKERS = ["o","x","+",".","*","s","d","^","v",">","<","p","h"] # 차트 마커
    CHART_COLORS  = ["r", "b", "g", "y", "m", "c", "w", "k"]                 # 차트 색상

    # ----------------------- 딥러닝 관련 ---------------------------
    TF_LEARNING_ONEDAY_DATA_CNT  = 380   # 하루 학습 데이터량 0901~1520 까지
    TF_LEARNING_DATA_TIME_COL_NM = "RSLT_MN" # 학습데이터의 시각(HHMM) 컬럼명

    TF_PREDICTION_INPUT_CNT  = 11   # 예측 입력값 리스트 맴버수
    TF_PREDICTION_OUTPUT_CNT = 1    # 예측 출력값 리스트 맴버수

    TF_LAYER_1_NEURON_CNT    = 11   # 1번째 은닉층 뉴런수
    TF_LAYER_2_NEURON_CNT    = 121    # 2번째 은닉층 뉴런수
    TF_LAYER_3_NEURON_CNT    = 242    # 3번째 은닉층 뉴런수
    TF_LAYER_4_NEURON_CNT    = 121    # 4번째 은닉층 뉴런수

    TF_LAYER_NEURON_CNT_LIST = [1024, 512, 256, 128] # 뉴런수 배열 (index순)
    TF_LAYER_CNT             = 4                     # 은닉층수

    TF_LEARNING_STR_DT = "20181001" # 학습대상 시작일
    TF_LEARNING_STR_MN = "0900"      # 학습대상 시작시각(HHMM)
    TF_LEARNING_END_DT = "20181119" # 학습대상 종료일
    TF_LEARNING_END_MN = "1520"      # 학습대상 종료시각(HHMM)

    TF_TEST_STR_DT     = "20181120"  # 테스트 대상 시작일
    TF_TEST_STR_MN     = "0900"       # 테스트 대상 시작시각(HHMM)
    TF_TEST_END_DT     = "20181120"  # 테스트 대상 종료일
    TF_TEST_END_MN     = "1520"       # 테스트 대상 종료시각(HHMM)

    #TF_LEARNING_MN_LIST     = [10,20,30]  # 학습 분 리스트(예측분)
    TF_LEARNING_MN_LIST      = [10]        # 학습 분 리스트(예측분)

    # 기본 딥러닝 모델 하이퍼파라미터
    TF_MDL_LIST_STD          = ["STD"]  # 기본 모델 리스트
    TF_LEARNING_INPUT_CNT    = 3     # 학습 입력값 리스트 맴버수
    TF_LEARNING_OUTPUT_CNT   = 1     # 학습 출력값 리스트 맴버수
    TF_LEARNING_DROPOUT_RATE = 1.0   # 드롭아웃률
    TF_LEARNING_RATE         = 0.01  # 학습율
    TF_LEARNING_EPOCH        = 100   # 반복학습횟수
    TF_LEARNING_CNT          = 1000  # 학습횟수

    # RNN 모델관련 하이퍼파라미터
    TF_MDL_LIST_RNN          = ["RNN_STD", "LSTM_PH",  "LSTM",  "GRU"]  # RNN 모델 리스트
    TF_RNN_INPUT_CNT         = 2     # 학습 입력값 리스트 맴버수
    TF_RNN_OUTPUT_CNT        = 1     # 학습 출력값 리스트 맴버수
    TF_RNN_DROPOUT_RATE      = 0.7   # 드롭아웃률
    TF_RNN_LERN_RATE         = 0.001 # 학습율
    TF_RNN_EPOCHS            = 100   # 반복학습횟수
    TF_RNN_BTCH_SIZE         = 50    # 학습단위 사이즈
    TF_RNN_SEQ               = 20    # 흐름단위 (분단위)
    TF_RNN_NEURONS           = 200   # 뉴런수
    TF_RNN_LAYERS            = 2     # 계층수

    TF_LEARNING_SAVE_MAINDIR = "\TrainingSave"              # 학습데이터 저장폴더
    TF_LEARNING_SAVE_DIR     = "\TrainingSave\Minute"      # 학습데이터 저장 분별폴더
    TF_LEARNING_SAVE_FILE    = "\TrainingCheckPoint.ckpt" # 학습데이터 저장파일
    TF_LEARNING_LOG_DIR      = "\TrainingLog"               # 학습로그 폴더
    TF_LEARNING_RSLT_FILE    = "\TestResult\TestRslt"      # 학습테스트 결과저장 엑셀파일
    TF_LEARNING_RSLT_DIR     = "\TestResult"                # 학습테스트 결과저장 폴더

    TF_PREDICTION_SAVE_FILE  = "\RealPrediction\RealPrediction.xlsx"  # 실시간예측 결과저장 엑셀파일
    TF_PREDICTION_SAVE_DIR   = "\RealPrediction"                         # 실시간예측 결과저장폴더

    # 데이터 정규화 (MinMaxScalar)
    # 입력값
    # inDBH         : DB 헨들러객체
    # inDF          : 정규화 대상 데이터(DataFrame)
    # inMdlNm       : 모델명
    # inInMinMaxYn  : 대상데이터안에 MinMax 포함여부(실시간예측의 경우 Y)
    # 리턴값 (MinMaxDf, OutDF)
    # MinmaxDF : 컬럼별 최대최소 정보. inDF 의 Min/Max 에 +-30%를 적용한 값과 정보
    # outDF    : 정규화된 데이터(DataFrame)
    def GetNormalizeData(self, inDBH, inDF, inMdlNm, inInMinMaxYn = "N"):

        MinMaxDf   = None  # MinMax 값
        outDF      = None  # 정규화 결과 값
        NeedUpdate = False # MinMax 값 업데이트 필요여부
        try:
            MinMaxScaler = sklearn.preprocessing.MinMaxScaler()
            outDF = inDF.copy()
            # 컬럼 리스트
            ColList = inDF.columns.values.tolist();
            ColCnt  = len(ColList)

            # MinMax 설정 처리
            if(inInMinMaxYn == "N"):

                # 기존 MinMax값 조회
                MinMaxV = inDBH.queryNormzInfo(inMdlNm)
                NormDict = {}
                InfoCnt = MinMaxV.values.shape[0]
                if (InfoCnt > 0):
                    for idx in range(InfoCnt):
                        X_Cd = MinMaxV['X_CD'].values.tolist()[idx]
                        MinVal = MinMaxV['MIN_VAL'].values.tolist()[idx]
                        MaxVal = MinMaxV['MAX_VAL'].values.tolist()[idx]
                        # print(X_Cd, MinVal,MaxVal)
                        NormDict[X_Cd] = (MinVal, MaxVal)

                # Min/Max 값을 넣을 신규 row 2개를 맨마지막에 넣음.
                NewRow = outDF.iloc[:1]
                NewRow = NewRow.rename(index={NewRow.index[0]: outDF.shape[0]})
                outDF = outDF.append(NewRow)
                NewRow = NewRow.rename(index={NewRow.index[0]: outDF.shape[0]})
                outDF = outDF.append(NewRow)

                # 컬럼별 Min/Max 값 설정
                for idx in range(ColCnt):
                    ColMn = ColList[idx]
                    MinVal = float(Decimal(str(outDF[ColMn].values.min())) * Decimal(str(0.7)))
                    MaxVal = float(Decimal(str(outDF[ColMn].values.max())) * Decimal(str(1.3)))

                    NeedUpdate = False
                    ColKey = ColMn.replace("X_", "")
                    if( ColKey in NormDict):
                        PreMinVal = NormDict[ColKey][0]
                        PreMaxVal = NormDict[ColKey][1]
                        if(MinVal != 0.0 and MinVal > PreMinVal):
                            MinVal = PreMinVal
                        else:
                            NeedUpdate = True
                        if (PreMaxVal > MaxVal):
                            MaxVal = PreMaxVal
                        else:
                            NeedUpdate = True
                    else:
                        NeedUpdate = True

                    outDF[ColMn][-2:] = MinVal
                    outDF[ColMn][-1:] = MaxVal

                    # MinMax 값 갱신
                    if(NeedUpdate):
                        inDBH.insertMinMaxValues(inMdlNm, ColKey, MinVal, MaxVal)

            # Min/Max row 분리 및 인덱스 변경
            MinMaxDf = outDF.tail(2)
            MinMaxDf = MinMaxDf.rename(index={MinMaxDf.index[1]: 0})  # MIN
            MinMaxDf = MinMaxDf.rename(index={MinMaxDf.index[0]: 1})  # MAX

            # 정규화
            for idx in range(ColCnt):
                ColMn  = ColList[idx]
                outDF[ColMn] = MinMaxScaler.fit_transform(outDF[ColMn].values.reshape(-1, 1))

            # 마지막 Min/Max Row 삭제
            outDF    = outDF.drop([outDF.shape[0] - 1, outDF.shape[0] - 2], 0)

        except Exception as e:
            print("데이터 정규화(GetNormalizeData)에러(", sys.exc_info()[-1].tb_lineno, " line):", e)
            return None

        return MinMaxDf, outDF

    # 데이터 역정규화 (MinMaxScalar inverse)
    # 입력값
    # inDF       : 역정규화 대상 데이터(DataFrame)
    # inMinmaxDF : 정규화시 사용된 MinMax 데이터.(DataFrame)
    # 리턴값
    # inDF       : 역정규화된 데이터(DataFrame)
    def GetDeNormalizeData(self, inDF, inMinmaxDF):

        try:
            MinMaxScaler = sklearn.preprocessing.MinMaxScaler()
            ColList = inDF.columns.values.tolist();
            ColCnt  = len(ColList)
            # 역정규화
            for idx in range(ColCnt):
                ColMn  = ColList[idx]
                # 기존 MinMax로 정규범위 설정
                MinMaxScaler.fit_transform(inMinmaxDF[ColMn].values.reshape(-1, 1))
                # 역정규화
                inDF[ColMn] = MinMaxScaler.inverse_transform(inDF[ColMn].values.reshape(-1, 1))

        except Exception as e:
            print("데이터 역정규화(GetDeNormalizeData)에러:", e)
            return None

        return inDF


    # 넘어온 테스트 데이터에 저장해둔 MinMax 값추가 설정
    # 입력값
    # inDBH         : DB 헨들러객체
    # inDF          : 테스트 데이터(DataFrame)
    # inMdlNm       : 모델구분명
    def addMinMaxData(self, inDBH, inDF, inMdlNm):
        try:
            # 이전 Min Max 값을 조회
            MinMaxV = inDBH.queryNormzInfo(inMdlNm)
            NormDict = {}
            InfoCnt = MinMaxV.values.shape[0]
            if (InfoCnt > 0):
                for idx in range(InfoCnt):
                    X_Cd   = MinMaxV['X_CD'].values.tolist()[idx]
                    MinVal = MinMaxV['MIN_VAL'].values.tolist()[idx]
                    MaxVal = MinMaxV['MAX_VAL'].values.tolist()[idx]
                    #print(X_Cd, MinVal,MaxVal)
                    NormDict[X_Cd] = (MinVal, MaxVal)
            else:
                print("저장된 MinMax가 없음:", inMdlNm)
                return None

            #print("조회된 MinMax 정보\n", NormDict)

            # Min/Max 값을 넣을 신규 row 2개를 맨마지막에 넣음.
            NewRow = inDF.tail(1)
            NewRow = NewRow.rename(index={NewRow.index[0]: inDF.shape[0]})
            inDF = inDF.append(NewRow)
            NewRow = NewRow.rename(index={NewRow.index[0]: inDF.shape[0]})
            inDF = inDF.append(NewRow)
            inDF[:][-2:] = float(0.0)

            ColList = inDF.columns.values.tolist();
            ColCnt = len(ColList)
            for idx in range(ColCnt):
                ColNm  = ColList[idx]
                ColKey = ColNm.replace("X_","")
                inDF[ColNm][-2:] = 0.0
                inDF[ColNm][-2:] = NormDict[ColKey][0] # Min
                inDF[ColNm][-1:] = NormDict[ColKey][1] # Max

        except KeyError as e:
            print("저장된 MinMax값이 없음:", e)
        except Exception as e:
            print("MinMax 값 추가처리(addMinMaxData)에러:", e)

        return inDF

    # 결과값 엑셀 저장
    # 입력값
    # inRealY  : 정답값   리스트
    # inPredY  : 예측값값 리스트
    # inTimeY  : 시간 리스트
    # inFileNm : 절대경로를 포함한 파일명
    def SaveRsltToExcel(self, inRealY, inPredY, inTime, inFileNm):
        try:
            Y  = DataFrame(inRealY, columns=["Real_Y"])
            PY = DataFrame(inPredY, columns=["Prediction_Y"])
            MN = DataFrame(inTime,  columns=["MN"])

            AY    = pd.merge(Y, PY, how="outer", left_index=True, right_index=True)
            RsltY = pd.merge(AY, MN, how="outer", left_index=True, right_index=True)
            RsltY.set_index("MN", inplace=True, drop=True)  # index 를 mn으로 변경

            writer = pd.ExcelWriter(inFileNm, engine='xlsxwriter')
            RsltY.to_excel(writer, sheet_name='Sheet1')
            writer.close()

        except Exception as e:
            print("학습결과 엑셀저장 에러:", e)
        return None


    #------------------ 공통 함수 / 변수 --------------------#

    # Tick 조회
    # inMktTp : 시장구분 (KOSPI.코스피 KOSDAQ.코스닥 ETF.ETF)
    # inPrice : 가격
    def GetTicks(self,inMktTp, inPrice):
        # 코스피
        if(inMktTp == "KOSPI"):
            if(inPrice < 1000 ):
                return 1
            elif(inPrice >= 1000    and inPrice < 5000):
                return 5
            elif (inPrice >= 5000   and inPrice < 10000):
                return 10
            elif (inPrice >= 10000  and inPrice < 50000):
                return 50
            elif (inPrice >= 50000  and inPrice < 100000):
                return 100
            elif (inPrice >= 100000 and inPrice < 500000):
                return 500
            else:
                return 1000
        # 코스닥
        elif (inMktTp == "KOSDAQ"):
            if (inPrice < 1000):
                return 1
            elif (inPrice >= 1000  and inPrice < 5000):
                return 5
            elif (inPrice >= 5000  and inPrice < 10000):
                return 10
            elif (inPrice >= 10000 and inPrice < 50000):
                return 50
            else:
                return 100
        # ETF
        elif(inMktTp == "ETF"):
            return 5
        else:
            print("inMktTp 에러 : ", inMktTp)
            return False


    # 해외파생 주말기간여부 (토요일 아침 6시1분부터 월요일 아침 7시0분까지 시세없음)
    # 시장마다 유동적이긴 하나 현재 글로벌에서 수신되지 않음. (CME 기준)
    # inDt 일자 : datetime 타입
    def isQttnBlnk(self, inDt):

        WDay = inDt.weekday()
        Mn   = int(inDt.strftime("%H%M"))
        
        # 토
        if (WDay == 5 and Mn > 600 and Mn <= 2359 ):
            return True
        # 일
        if (WDay == 6):
            return True
        # 월
        if (WDay == 0 and Mn > 0 and Mn <= 700):
            return True

        return False

    # 입력일자 기준 최근 월요일 07시 리턴
    # inDt 일자 : datetime 타입
    def getMon07AM(self, inDt):
        WDay = inDt.weekday()
        Mn = int(inDt.strftime("%H%M"))
        OneDay = timedelta(days=1)
        TwoDays = timedelta(days=2)

        # 토
        if (WDay == 5 and Mn > 600 and Mn <= 2359):
            print("토")
            inDt = inDt + TwoDays
            inDt = inDt.replace(hour=7, minute=0)
        # 일
        if (WDay == 6):
            print("일")
            inDt = inDt + OneDay
            inDt = inDt.replace(hour=7, minute=0)
        # 월
        if (WDay == 0 and Mn > 0 and Mn <= 700):
            print("월")
            inDt = inDt.replace(hour=7, minute=0)

        return inDt

    # 상품별 테이블 가져오기
    def GetMktTable(self, inMktTpCd):

        Table = ""
        if(inMktTpCd == "KOSPI"):
            Table = "KOSPI_MN_QTTN_INFO"
        elif(inMktTpCd in ("DERV",CodeDef.MKT_TP_CD_GLOBAL_DERIVATIVE, CodeDef.MKT_TP_CD_GLOBAL_FUTURE, CodeDef.MKT_TP_CD_GLOBAL_OPTION)):
            Table = "DERV_MN_QTTN_INFO"
        elif(inMktTpCd in ("STK",CodeDef.MKT_TP_CD_INTERNAL, CodeDef.MKT_TP_CD_GLOBAL_STOCK, CodeDef.MKT_TP_CD_INTERNAL_STOCK)):
            Table = "STK_MN_QTTN_INFO"
        else:
            print("정의 없음: ", inMktTpCd)

        return Table


    # 결과값 ETF 스케일링
    # inYlist : 결과값 리스트
    def SetEtfScaling(self, inYlist):
        RowCnt = len(inYlist)
        for idx in range(RowCnt):
            Val = inYlist[idx]
            strV = str(int(round(Val)))
            Prc = int(strV[-1:])

            if (Prc >= 7):
                inYlist[idx] = float(round(int(round(Val)), -1))
            elif (Prc <= 3):
                inYlist[idx] = float(int(round(Val)) - Prc)
            else:
                inYlist[idx] = float(strV[:-1] + "5")

        return inYlist

    # 결과값 ETF 스케일링
    # inVal : 결과값
    def SetEtfScalingVal(self, inVal):
        RsltVal = 0.0
        strVal = str(int(round(inVal)))
        PrcVal = int(strVal[-1:])

        if (PrcVal >= 7):
            RsltVal = float(round(int(round(inVal)), -1))
        elif (PrcVal <= 3):
            RsltVal = float(int(round(inVal)) - PrcVal)
        else:
            RsltVal = float(strVal[:-1] + "5")

        return RsltVal

    # 다음 시분 가져오기
    # inStdMn : 기준시분(HHMM)
    # inMn    : + 분(int)
    def GetNextMn(self,inStdMn, inMn):

        ONE_MINUTE = timedelta(minutes=1)
        TEMP_DATE  = datetime(year=2000, month=1, day=1, hour=1, minute=1)

        NextMn = ""

        iM = int(inStdMn[:2])
        iN = int(inStdMn[2:])

        TEMP_DATE = TEMP_DATE.replace(hour=iM, minute=iN)

        NextMn = (TEMP_DATE + (ONE_MINUTE * inMn)).strftime("%H%M")

        return NextMn