# -*-coding: utf-8 -*-

import pythoncom
import time
import os

import win32com
import win32com.client
import ctypes
from DB_handler import *

class TradarAPI_handler:

    # API 초기화
    def initAPI(self, inMode, inForm):
        UserID   = CodeDef.API_USER_ID
        PassWord = CodeDef.API_USER_PW
        CertPW   = CodeDef.API_CERT_PW

        global gTRADR_SYS_MSG_CD  # 티레이더 시스템메시지 코드
        global gTradrSess_flag    # 티레이더 요청대기 제어
        global gTradrAPI          # 티레이더 API 핸들러
        global gTradrInitDict     # 티레이더 분봉초기화 딕셔너리 {("MN_INIT",TR번호,종목코드) : (시작일,시작시분,종료일,종료시분,요청ID)}
        global gTradrTrReqDict    # 티레이더 요청TR-결과코드 딕셔너리 { 결과코드 : (TRID,종목코드) }
        global gTradrRealReqDict  # 티레이더 실시간 요청정보 딕셔너리 { 결과코드 : (TRID,종목코드) or 종목보드 : (TRID, 결과코드)}
        global gTradrApiDbh       # 티레이더 DB 핸들러
        global gIsTrmsMode        # 전송모드 접속여부
        global gMainForm          # 메인폼 핸들러

        gTRADR_SYS_MSG_CD = 0
        gTradrSess_flag   = False
        gTradrAPI         = None
        gTradrInitDict    = {}
        gTradrTrReqDict   = {}
        gTradrRealReqDict = {}
        gTradrApiDbh      = None
        gIsTrmsMode       = inMode
        gMainForm         = inForm

        # API 초기화
        gTradrApiDbh = DB_handler()
        gTradrAPI = win32com.client.DispatchWithEvents("YuantaAPICOM.YuantaAPI", TradarAPI_handler)
        ret = gTradrAPI.YOA_Initial(CodeDef.SERVER_REAL_TRADAR, r"C:\YuantaAPI")
        ret = gTradrAPI.YOA_Login(UserID, PassWord, CertPW)

        # 혹시 남아있는 실시간 TR이 있다면 중지
        gTradrAPI.YOA_UnRegistAuto("11")

        gTradrSess_flag = True
        while gTradrSess_flag:
            pythoncom.PumpWaitingMessages()

            if (gTRADR_SYS_MSG_CD  == CodeDef.NOTIFY_SYSTEM_NEED_TO_RESTART):  # 모듈변경에 때른 재시작 필요
                ret = gTradrAPI.YOA_UnInitial()
                os.chdir(r"C:\YuantaAPI")
                cwd = os.getcwd()
                os.system("YOASync.exe")
                time.sleep(2)
                os.chdir(cwd)
                ret = gTradrAPI.YOA_Initial(CodeDef.SERVER_REAL_TRADAR, r"C:\YuantaAPI")
                ret = gTradrAPI.YOA_Login(UserID, PassWord, CertPW)

        return None

    def CloseAPI(self):
        try:
            # 실시간 TR 중지
            gTradrAPI.YOA_UnRegistAuto("11")
            # API 핸들러 해제
            if (gTradrAPI is not None):
                gTradrAPI.YOA_UnInitial()
            # DB 핸들러 해제
            if (gTradrApiDbh is not None):
                del gTradrApiDbh

        except Exception as e:
            print(e)

        return None

    # 로그인정보 수신
    def OnLogin(self, nResult, bstrMsg):
        global gTradrSess_flag
        gTradrSess_flag = False
        print(bstrMsg)
        print("---OnLogin-종료-")
        return None

    # 조회데이터 수신
    def OnReceiveData(self, nReqID, bstrDSOID):
        global gTradrSess_flag
        global gTradrTrReqDict

        ReqInfo = gTradrTrReqDict[nReqID]
        trID = ReqInfo[0]

        # 분봉 데이터
        if( trID == "402001"):
            self.ProcMnQttn(nReqID)

        print("---OnReceiveData-종료-")
        return None

    # 시스템메시지 수신
    def OnReceiveSystemMessage(self, nID, bstrAutoID):
        global gTRADR_SYS_MSG_CD
        gTRADR_SYS_MSG_CD = nID
        #print("gSYSTEM_MESSAGE (%s) 메시지(%s)"%(str(nID), bstrAutoID))
        if( nID == CodeDef.NOTIFY_SYSTEM_NEED_TO_RESTART ):
            print("NOTIFY_SYSTEM_NEED_TO_RESTART", nID)
        if (nID == CodeDef.NOTIFY_SYSTEM_LOGIN_FILE_DWN_START):
            print("NOTIFY_SYSTEM_LOGIN_FILE_DWN_START", nID)
        #print("---OnReceiveSystemMessage-종료-")
        return None

    # 에러정보 수신
    def OnReceiveError(self, nReqID, nErrCode, bstrErrMsg):
        print("OnReceiveError: nReqID["+nReqID+"] nErrCode["+nErrCode+"] bstrErrMsg["+bstrErrMsg+"]")
        print("----OnReceiveError-종료-")
        return None

    # 실시간 수신
    def OnReceiveRealData(self, nReqID, bstrAutoID):
        global gTradrAPI
        global gTradrRealReqDict
        global gMainForm, gIsTrmsMode

        # 지수 수신인 경우 전송
        TrInfo   = gTradrRealReqDict[nReqID]
        InTrID   = TrInfo[0]
        InStkCd  = TrInfo[1]
        RcvStkCd = gTradrAPI.YOA_GetTRFieldString(InTrID, "OutBlock1", "jongcode", 0)

        if(InStkCd == RcvStkCd):
            RcvCrPrc = gTradrAPI.YOA_GetTRFieldString(InTrID, "OutBlock1", "curjuka"  , 0) # 현재가
            RcvFtPrc = gTradrAPI.YOA_GetTRFieldString(InTrID, "OutBlock1", "startjuka", 0) # 시가
            RcvHgPrc = gTradrAPI.YOA_GetTRFieldString(InTrID, "OutBlock1", "highjuka" , 0) # 고가
            RcvLoPrc = gTradrAPI.YOA_GetTRFieldString(InTrID, "OutBlock1", "lowjuka"  , 0) # 저가
            RcvTime  = gTradrAPI.YOA_GetTRFieldString(InTrID, "OutBlock1", "time", 0).replace(":", "")  # 시간(HH:SS)

            # 전송모드
            if (gIsTrmsMode):
                # 메인폼을 통한 전송(SndIdxForm_handler에서 사용)
                gMainForm.SendRealQttn(InStkCd, RcvTime, RcvCrPrc, RcvFtPrc, RcvHgPrc, RcvLoPrc )
            # 수신모드
            else:
                # 메인폼으로 보내서 차트에 적용
                QttnInfo = InStkCd + "|" + RcvTime + "|" + RcvCrPrc + "|" + RcvFtPrc + "|" + RcvHgPrc + "|" + RcvLoPrc + "|E"
                # print("Global : ",QttnInfo)
                gMainForm.ProcRcvRealQttn("KOSPI_INDEX", QttnInfo)

        #print("----OnReceiveRealData-종료-")
        return None

    # def OnAddRef(self):
    #     pass
    # def OnRelease(self):
    #     pass
    # def OnGetTypeInfoCount(self, pctinfo):
    #     pass
    # def OnGetTypeInfo(self, itinfo, lcid, pptinfo):
    #     print("OnGetTypeInfo")
    # def OnGetIDsOfNames(self, riid, rgszNames,cNames,lcid,rgdispid):
    #     pass
    # def OnInvoke(self, dispidMember, riid, lcid, wFlags, pdispparams, pvarResult, pexcepinfo, puArgErr):
    #     pass

    #################### 위는 필수 구현 함수  #################################
    #################### 아래는 필요 구현 함수  #################################

    # 조회요청
    # sProcTp : 처리구분 (MN_INIT. 분봉데이터 초기화......)
    # sTrID   : 조회 TR ID
    # lAgs    : 입력파라미터 리스트
    def OnRequest(self, inProcTp, inTrID, inStkCd):
        print("----OnRequest 시작----")
        global gTradrAPI
        global gTradrInitDict
        global gTradrTrReqDict
        global gTradrRealReqDict
        global gTradrSess_flag

        nRslt = 0

        # 실시간 시세
        if (inProcTp == "REAL_QTTN"):
            # 기존실시간 TR 확인
            if (inStkCd in gTradrRealReqDict.keys()):
                ctypes.windll.user32.MessageBoxW(0, "이미 실시간시세 등록된 종목입니다.", "알림", 0)
                return False
            gTradrAPI.YOA_SetTRFieldString(inTrID,"InBlock1", "jongcode", inStkCd, 0)
            nRslt = gTradrAPI.YOA_RegistAuto(inTrID)
            # 딕셔너리 등록
            gTradrRealReqDict[nRslt] = (inTrID,inStkCd)
            gTradrRealReqDict[inStkCd] = (inTrID,nRslt)

        # 분봉데이터 초기화
        elif (inProcTp == "MN_INIT"):
            if (inTrID == "402001"):
                # 초기화 데이터 입수중에 이어서 조회하는 경우는 종료일자를 재조정함.
                EndInfo = gTradrInitDict[("MN_INIT", "402001", inStkCd)]

                # print("설정된 시작일["+EndInfo[0]+"] 시작시분["+EndInfo[1]+"] 종료일["+EndInfo[2]+"] 종료시분["+EndInfo[3]+"] inStkCd["+inStkCd+"]")
                gTradrAPI.YOA_SetTRInfo("402001", "InBlock1")
                try:
                    # 최초조회시는 세팅하고 next 조회시는 필요없음
                    if(EndInfo[4] == -1):
                        gTradrAPI.YOA_SetFieldString("janggubun" , "1", 0)
                        gTradrAPI.YOA_SetFieldString("jongcode"  , inStkCd.zfill(12), 0)
                        gTradrAPI.YOA_SetFieldString("linkgb"    , "0", 0)
                        gTradrAPI.YOA_SetFieldString("timeuint"  , "001M", 0)
                        gTradrAPI.YOA_SetFieldString("startdate" , EndInfo[0], 0)
                        gTradrAPI.YOA_SetFieldString("starttime" , EndInfo[1].ljust(6,"0"), 0)
                        gTradrAPI.YOA_SetFieldString("enddate"   , EndInfo[2], 0)
                        gTradrAPI.YOA_SetFieldString("endtime"   , EndInfo[3].ljust(6,"0"), 0)
                        gTradrAPI.YOA_SetFieldString("readcount" , "500", 0)
                    nRslt = gTradrAPI.YOA_Request("402001" , False, EndInfo[4])
                    gTradrTrReqDict[nRslt] = ("402001" , inStkCd)
                except Exception as e:
                    print(e)
        elif (inProcTp == "TEST"):
            # 기존실시간 TR 해제
            gTradrAPI.YOA_UnRegistAuto(inTrID)
            gTradrAPI.YOA_SetTRFieldString(inTrID,"InBlock1", "jongcode", inStkCd, 0)
            nRslt = gTradrAPI.YOA_RegistAuto(inTrID)
            gTradrTrReqDict[nRslt] = (inTrID,inStkCd)
            print("TEST")
        else:
            print("처리구분 확인!")
            return None

        if( nRslt < 1000 ):
            ret = gTradrAPI.YOA_GetErrorMessage(nRslt)
            print("요청실패 nResult:", nRslt, ret)
            return None

        if(gTradrSess_flag == False):
            self.waitSrvrRspn()
        return None

    # 서버 응답 수신대기
    def waitSrvrRspn(self):
        global gTradrSess_flag

        gTradrSess_flag = True
        while gTradrSess_flag:
            pythoncom.PumpWaitingMessages()

        print("-- waitSrvrRspn -종료- ")
        return None

    # 실시간TR 정지
    # inReqID : 실시간요청 결과ID
    # inStkCd : 종목코드
    def StopRealRcv(self, inReqID, inStkCd):
        global gTradrSess_flag
        global gTradrAPI
        global gTradrRealReqDict

        gTradrSess_flag = False

        # 실시간 딕셔너리 삭제
        ReqID = inReqID
        StkCd = inStkCd
        if (inReqID is not None):
            ReqInfo = gTradrRealReqDict[inReqID]
            StkCd = ReqInfo[1]
        else:
            ReqInfo = gTradrRealReqDict[inStkCd]
            ReqID = ReqInfo[1]

        del gTradrRealReqDict[ReqID]
        del gTradrRealReqDict[StkCd]

        # 실시간수신 해제
        gTradrAPI.YOA_UnRegistAutoWithReqID(ReqID)

        return None

    # 분봉시세 초기화
    def InitMnQttn(self, inMktTpCd, inStkCd, inStrDt, inStrMn, inEndDt, inEndMn):
        print("----InitMnQttn 시작----")
        global gTradrInitDict

        if (inMktTpCd in [CodeDef.MKT_TP_CD_INTERNAL, CodeDef.MKT_TP_CD_INTERNAL_STOCK,
                          CodeDef.MKT_TP_CD_GLOBAL_STOCK]):
            # TR / 종목 딕셔너리 저장
            gTradrInitDict[("MN_INIT", "402001", inStkCd)] = (inStrDt, inStrMn, inEndDt, inEndMn, -1)
            self.OnRequest("MN_INIT", "402001", inStkCd)
        else:
            print("시장구분 입력 오류")
        return None

    # 수신받은 분봉데이터를 입력
    # inReqID : 요청응답ID
    def ProcMnQttn(self, inReqID):
        print("----ProcMnQttn 시작----")
        global gTradrAPI
        global gTradrInitDict
        global gTradrTrReqDict
        global gTradrApiDbh
        global gTradrSess_flag

        TrInfo = gTradrTrReqDict[inReqID]
        TrID   = TrInfo[0]
        NotEnd  = True
        if( TrID == "402001"):
            StkCd = TrInfo[1]
            RowCount = gTradrAPI.YOA_GetRowCount("402001", "OutBlock2")

            InitInfo = gTradrInitDict[("MN_INIT", "402001", StkCd)]
            LastDt = InitInfo[0]
            LastMn = InitInfo[1]

            BaseDt = ""
            BaseMn = ""
            print("RowCount:",RowCount)
            for i in range(RowCount):
                gTradrAPI.YOA_SetTRInfo("402001", "OutBlock2")
                BaseDt  = gTradrAPI.YOA_GetFieldString("basedate" , i) # 기준일
                BaseMn  = gTradrAPI.YOA_GetFieldString("basetime" , i) # 기준시각 (HHMMSS 정수형문자열로 보내줌 ex. 9시 090000 => 90000)
                FtPrc   = gTradrAPI.YOA_GetFieldDouble("startjuka", i) # 시가
                HgPrc   = gTradrAPI.YOA_GetFieldDouble("highjuka" , i) # 고가
                LoPrc   = gTradrAPI.YOA_GetFieldDouble("lowjuka"  , i) # 저가
                ClPrc   = gTradrAPI.YOA_GetFieldDouble("lastjuka" , i) # 종가
                Vlum    = gTradrAPI.YOA_GetFieldDouble("volume"   , i) # 거래량

                BaseMn = BaseMn.zfill(6)  # 앞에 0을 때서 보내주기 때문에 재조정
                BaseMn = BaseMn[:4]  # 시분 분리

                #if(BaseDt is None or len(BaseDt) != 8):
                #    NotEnd = False
                #    break
                #if (BaseMn is None or BaseMn == "000000"):
                #    NotEnd = False
                #    break

                if (i == 499):
                    print("마지막 처리된거 :", BaseDt, BaseMn, i, gTradrAPI.YOA_GetFieldString("jongcode" , i) )
                if(i == 1):
                    print("첫번째 BaseDt BaseDt :",BaseDt,BaseMn, i)

                if ( int(BaseDt+BaseMn) < int(LastDt+LastMn) ):
                    print("조회일자시각 넘김",int(BaseDt) , int(LastDt), int(BaseMn), int(LastMn))
                    NotEnd = False
                    break

                if (i >= 500):
                    print("건수넘김 ",i)
                    break
                gTradrApiDbh.insertMnQttn("KOSPI"
                                    ,StkCd, BaseDt, BaseMn, FtPrc, HgPrc, LoPrc, ClPrc, 0.0, Vlum)
            #--- for문 종료 ---

            # 수신해제
            #rslt = gGlblAPI.YOA_ReleaseData(inReqID)
            #print("TR Release : ", gGlblAPI.YOA_GetErrorMessage(rslt))

            # 제공시세 마지막의 경우 종료시킴
            gTradrAPI.YOA_SetTRInfo("402001", "OutBlock3")
            Nxt = gTradrAPI.YOA_GetFieldString("next", 0)  # 다음시세 존재여부
            print("Next:", Nxt)
            if(Nxt == "0"):
                NotEnd = False

            # 최종일자에 도달못했으면 다시 호출한다.
            if (NotEnd):
                print("다 못받았음.")
                print("마지막 BaseDt BaseMn", BaseDt, BaseMn)
                dDate   = datetime(year=int(BaseDt[:4]), month=int(BaseDt[4:6]), day=int(BaseDt[6:]), hour=int(BaseMn[:2]), minute=int(BaseMn[2:]))
                BaseDt = dDate.strftime("%Y%m%d")
                BaseMn = dDate.strftime("%H%M%S")

                # TR / 종목 딕셔너리 저장
                gTradrInitDict[("MN_INIT", "402001", StkCd)] = (LastDt, LastMn, BaseDt, BaseMn, inReqID)
                gTradrSess_flag = True
                time.sleep(1)
                self.OnRequest("MN_INIT", "402001", StkCd)
            else:
                print("받기끝")
                gTradrSess_flag = False

        # --- if( TrID == "820104") 종료 ---
        return None