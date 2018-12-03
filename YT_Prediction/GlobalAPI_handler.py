# -*-coding: utf-8 -*-

import pythoncom
import time
from datetime import timedelta, date, datetime
import os

import win32com
import win32com.client
import ctypes
from DB_handler import *

class GlobalAPI_handler:

    # API 초기화
    def initAPI(self,inMode, inForm):
        UserID    = CodeDef.API_USER_ID
        PassWord  = CodeDef.API_USER_PW
        CertPW    = CodeDef.API_CERT_PW

        # 데이터 수신
        global gGLBL_SYS_MSG_CD     # 티레이더글로벌 시스템메시지 코드
        global gGlblSess_flag       # 티레이더글로벌 요청대기 제어
        global gGlblAPI             # 티레이더글로벌 API 핸들러
        global gGlblInitDict        # 티레이더글로벌 분봉초기화 딕셔너리 {("MN_INIT",TR번호,종목코드) : (시작일,시작시분,종료일,종료시분)}
        global gGlblTrReqDict       # 티레이더글로벌 조회요청정보 딕셔너리 { 결과코드 : (TRID,종목코드) }
        global gGlblRealReqDict     # 티레이더글로벌 실시간 요청정보 딕셔너리 { 결과코드 : (TRID,종목코드) or 종목보드 : (TRID, 결과코드)}
        global gGlblApiDbh          # 티레이더글로벌 DB 핸들러
        global gIsTrmsMode          # 전송모드 접속여부
        global gMainForm            # 메인폼 핸들러

        gGLBL_SYS_MSG_CD    = 0
        gGlblSess_flag      = False
        gGlblAPI            = None
        gGlblInitDict       = {}
        gGlblTrReqDict      = {}
        gGlblRealReqDict    = {}
        gGlblApiDbh         = None
        gIsTrmsMode         = inMode
        gMainForm           = inForm

        # 접속에따른 초기화
        gGlblAPI = win32com.client.DispatchWithEvents("YuantaAPICOM.YuantaAPI", GlobalAPI_handler)
        gGlblApiDbh = DB_handler()
        ret = gGlblAPI.YOA_Initial(CodeDef.SERVER_REAL_GLOBAL, r"C:\YuantaAPI")
        ret = gGlblAPI.YOA_Login(UserID, PassWord, CertPW)

        # 혹시 남아있는 실시간 TR이 있다면 중지
        gGlblAPI.YOA_UnRegistAuto("61")

        gGlblSess_flag = True
        while gGlblSess_flag:
            pythoncom.PumpWaitingMessages()

            if (gGLBL_SYS_MSG_CD  == CodeDef.NOTIFY_SYSTEM_NEED_TO_RESTART):  # 모듈변경에 때른 재시작 필요
                ret = gGlblAPI.YOA_UnInitial()
                os.chdir(r"C:\YuantaAPI")
                cwd = os.getcwd()
                os.system("YOASync.exe")
                time.sleep(2)
                os.chdir(cwd)
                ret = gGlblAPI.YOA_Initial(CodeDef.SERVER_REAL_GLOBAL, r"C:\YuantaAPI")
                ret = gGlblAPI.YOA_Login(UserID, PassWord, CertPW)

        return None

    def CloseAPI(self):
        global gGlblApiDbh
        global gGlblAPI
        try:
            # 실시간 TR 중지
            gGlblAPI.YOA_RegistAuto("61")
            # API 핸들러 해제
            if (gGlblAPI is not None):
                gGlblAPI.YOA_UnInitial()
            # DB 핸들러 해제
            if (gGlblApiDbh is not None):
                del gGlblApiDbh

        except Exception as e:
            print("CloseAPI 에러:", e)

        return None

    def OnLogin(self, nResult, bstrMsg):
        global gGlblSess_flag
        gGlblSess_flag = False
        print(bstrMsg)
        print("---OnLogin-종료-")
        return None

    def OnReceiveData(self, nReqID, bstrDSOID):
        global gGlblSess_flag
        global gGlblTrReqDict

        ReqInfo = gGlblTrReqDict[nReqID]
        trID = ReqInfo[0]

        # 분봉 데이터
        if( trID == "820104"):
            self.ProcGlobalMnQttn(nReqID)

        print("---OnReceiveData-종료-")
        return None


    def OnReceiveSystemMessage(self, nID, bstrAutoID):
        global gGLBL_SYS_MSG_CD
        gGLBL_SYS_MSG_CD = nID
        #print("gSYSTEM_MESSAGE (%s) 메시지(%s)"%(str(nID), bstrAutoID))
        if( nID == CodeDef.NOTIFY_SYSTEM_NEED_TO_RESTART ):
            print("NOTIFY_SYSTEM_NEED_TO_RESTART", nID)
        if (nID == CodeDef.NOTIFY_SYSTEM_LOGIN_FILE_DWN_START):
            print("NOTIFY_SYSTEM_LOGIN_FILE_DWN_START", nID)
        #print("---OnReceiveSystemMessage-종료-")
        return None

    def OnReceiveError(self, nReqID, nErrCode, bstrErrMsg):
        print("OnReceiveError: nReqID[" + nReqID + "] nErrCode[" + nErrCode + "] bstrErrMsg[" + bstrErrMsg + "]")
        print("----OnReceiveError-종료-")
        return None

    def OnReceiveRealData(self, nReqID, bstrAutoID):
        global gGlblAPI
        global gGlblRealReqDict
        global gIsTrmsMode
        global gMainForm

        TrInfo = gGlblRealReqDict[nReqID]
        InTrID = TrInfo[0]
        InStkCd = TrInfo[1]
        #print("bstrAutoID nReqID InTrID InStkCd",bstrAutoID, nReqID, InTrID, InStkCd)
        RcvStkCd = gGlblAPI.YOA_GetTRFieldString(InTrID, "OutBlock1", "jongcode", 0)  # 종목코드
        RcvCrPrc = gGlblAPI.YOA_GetTRFieldString(InTrID, "OutBlock1", "last"     , 0) # 현재가
        RcvFtPrc = gGlblAPI.YOA_GetTRFieldString(InTrID, "OutBlock1", "start"    , 0) # 시가
        RcvHgPrc = gGlblAPI.YOA_GetTRFieldString(InTrID, "OutBlock1", "high"     , 0) # 고가
        RcvLoPrc = gGlblAPI.YOA_GetTRFieldString(InTrID, "OutBlock1", "low"      , 0) # 저가
        RcvTime  = gGlblAPI.YOA_GetTRFieldString(InTrID, "OutBlock1", "time"     , 0).replace(":","") # 시간(HH:SS)

        # 전송모드
        if (gIsTrmsMode):
            # 메인폼을 통한 전송(SndIdxForm_handler 에서 사용할때)
            gMainForm.SendRealQttn(InStkCd, RcvTime, RcvCrPrc, RcvFtPrc, RcvHgPrc, RcvLoPrc)
        # 수신모드
        else:
            # 메인폼으로 보내서 차트에 적용 및 딥러닝 전송(MainForm_handler에서 사용)
            QttnInfo = InStkCd + "|" + RcvTime + "|" + RcvCrPrc + "|" + RcvFtPrc + "|" + RcvHgPrc + "|" + RcvLoPrc + "|E"
            gMainForm.ProcRcvRealQttn("GLOBAL_QTTN",QttnInfo)

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
    # inProcTp : 처리구분 (MN_INIT. 분봉데이터 초기화......)
    # inTrID   : TR ID
    # inStkCd  : 종목코드
    def OnRequest(self, inProcTp, inTrID, inStkCd):
        print("----OnRequest 시작----")
        global gGlblAPI
        global gGlblInitDict
        global gGlblTrReqDict
        global gGlblRealReqDict
        global gGlblSess_flag

        nRslt = 0
        DoRealRcv = True

        # 분봉데이터 초기화
        if ( inProcTp == "MN_INIT"):
            if( inTrID == "820104"):
                # 초기화 데이터 입수중에 이어서 조회하는 경우는 종료일자를 재조정함.
                EndInfo = gGlblInitDict[("MN_INIT", "820104", inStkCd)]

                #print("설정된 시작일["+EndInfo[0]+"] 시작시분["+EndInfo[1]+"] 종료일["+EndInfo[2]+"] 종료시분["+EndInfo[3]+"] inStkCd["+inStkCd+"]")
                gGlblAPI.YOA_SetTRInfo("820104","InBlock1")
                try:
                    gGlblAPI.YOA_SetFieldString("jongcode"  , inStkCd   , 0)
                    gGlblAPI.YOA_SetFieldString("timeuint"  , "001M"   , 0)
                    gGlblAPI.YOA_SetFieldString("startdate" , EndInfo[0], 0)
                    gGlblAPI.YOA_SetFieldString("starttime" , EndInfo[1].ljust(6,"0"), 0)
                    gGlblAPI.YOA_SetFieldString("enddate"   , EndInfo[2], 0)
                    gGlblAPI.YOA_SetFieldString("endtime"   , EndInfo[3].ljust(6,"0"), 0)
                    gGlblAPI.YOA_SetFieldString("readcount" , "500"  , 0)
                    gGlblAPI.YOA_SetFieldString("link_yn"   , "N"     , 0)
                    nRslt = gGlblAPI.YOA_Request("820104", True, -1)
                    gGlblTrReqDict[nRslt] = ("820104",inStkCd)
                except Exception as e:
                    print(e)
        elif (inProcTp == "REAL_QTTN"):
            # 기존실시간 TR 확인
            if(inStkCd in gGlblRealReqDict.keys()):
                ctypes.windll.user32.MessageBoxW(0, "이미 실시간시세 등록된 종목입니다.", "알림", 0)
                return False
            gGlblAPI.YOA_SetTRFieldString(inTrID,"InBlock1", "jongcode", inStkCd, 0)
            nRslt = gGlblAPI.YOA_RegistAuto(inTrID)
            # 딕셔너리 등록
            gGlblRealReqDict[nRslt]   = (inTrID,inStkCd)
            gGlblRealReqDict[inStkCd] = (inTrID, nRslt)
            DoRealRcv = False
        elif (inProcTp == "TEST"):
            # 기존실시간 TR 해제
            gGlblAPI.YOA_UnRegistAuto(inTrID)
            gGlblAPI.YOA_SetTRFieldString(inTrID,"InBlock1", "jongcode", inStkCd, 0)
            nRslt = gGlblAPI.YOA_RegistAuto(inTrID)
            gGlblRealReqDict[nRslt] = (inTrID, inStkCd)
            gGlblRealReqDict[inStkCd] = (inTrID, nRslt)
            print("REAL_TEST")
        else:
            print("처리구분 확인!")
            return None

        if( nRslt < 1000 ):
            ret = gGlblAPI.YOA_GetErrorMessage(nRslt)
            print("요청실패 nResult:", nRslt, ret)
            return None

        if (DoRealRcv and gGlblSess_flag == False):
            self.waitSrvrRspn()
        return None


    # 분봉시세 초기화
    def InitMnQttn(self, inMktTpCd, inStkCd, inStrDt, inStrMn, inEndDt, inEndMn):
        print("----InitMnQttn 시작----")
        global gGlblInitDict

        if ( inMktTpCd in [CodeDef.MKT_TP_CD_GLOBAL_DERIVATIVE, CodeDef.MKT_TP_CD_GLOBAL_FUTURE, CodeDef.MKT_TP_CD_GLOBAL_OPTION ]):
            # TR / 종목 딕셔너리 저장
            gGlblInitDict[("MN_INIT","820104",inStkCd)] = (inStrDt, inStrMn, inEndDt, inEndMn)
            self.OnRequest("MN_INIT","820104", inStkCd)
        else:
            print("시장구분 입력 오류")
        return None

    # 수신받은 해외파생 분봉데이터를 입력
    # inReqID : 요청응답ID
    def ProcGlobalMnQttn(self, inReqID):
        print("----ProcGlobalMnQttn 시작----")
        global gGlblAPI
        global gGlblTrReqDict
        global gGlblInitDict
        global gGlblApiDbh
        global gGlblSess_flag
        global gMainForm

        TrInfo = gGlblTrReqDict[inReqID]
        TrID   = TrInfo[0]
        NotEnd  = True
        if( TrID == "820104"):
            StkCd = TrInfo[1]
            RowCount = gGlblAPI.YOA_GetRowCount("820104", "MSG")

            InitInfo = gGlblInitDict[("MN_INIT", "820104", StkCd)]
            #print(InitInfo)
            LastDt = InitInfo[0]
            LastMn = InitInfo[1]

            BaseDt = ""
            BaseMn = ""
            print("RowCount:",RowCount)
            for i in range(1, RowCount): # 해외선물분봉은 요청시각+1분부터 들어온다. 이상함
                gGlblAPI.YOA_SetTRInfo("820104", "MSG")
                BaseDt  = gGlblAPI.YOA_GetFieldString("basedate" , i) # 기준일
                BaseMn  = gGlblAPI.YOA_GetFieldString("basetime" , i) # 기준시각(HHMMSS 정수형문자열로 보내줌 ex. 9시 090000 => 90000)
                FtPrc   = gGlblAPI.YOA_GetFieldDouble("startjuka", i) # 시가
                HgPrc   = gGlblAPI.YOA_GetFieldDouble("highjuka" , i) # 고가
                LoPrc   = gGlblAPI.YOA_GetFieldDouble("lowjuka"  , i) # 저가
                ClPrc   = gGlblAPI.YOA_GetFieldDouble("lastjuka" , i) # 종가
                UpDnPrc = gGlblAPI.YOA_GetFieldDouble("diff_prc" , i) # 등락가
                Vlum    = gGlblAPI.YOA_GetFieldDouble("volume"   , i) # 거래량

                BaseMn = BaseMn.zfill(6) # 앞에 0을 때서 보내주기 때문에 재조정
                BaseMn = BaseMn[:4]      # 시분 분리

                #if(BaseDt is None or len(BaseDt) != 8):
                #    NotEnd = False
                #    break
                #if (BaseMn is None or BaseMn == "0000"):
                #    NotEnd = False
                #    break

                #if (i == 499):
                #    print("마지막 처리된거 :", BaseDt, BaseMn, i, gGlblAPI.YOA_GetFieldString("jongcode" , i) )
                #if(i == 1):
                #    print("첫번째 BaseDt BaseDt :",BaseDt,BaseMn, i)

                if (int(BaseDt+BaseMn) < int(LastDt+LastMn)):
                    print("조회일자시각 넘김",int(BaseDt) , int(LastDt), int(BaseMn), int(LastMn))
                    NotEnd = False
                    break

                if (i >= 500):
                    print("건수넘김 ",i)
                    break
                gMainForm.insertMnQttn("DERV",StkCd, BaseDt, BaseMn, FtPrc, HgPrc, LoPrc, ClPrc, UpDnPrc, Vlum)
                #gGlblApiDbh.insertMnQttn("DERV",StkCd, BaseDt, BaseMn[:4], FtPrc, HgPrc, LoPrc, ClPrc, UpDnPrc, Vlum)

            #--- for문 종료 ---

            # 수신해제
            #rslt = gGlblAPI.YOA_ReleaseData(inReqID)
            #print("TR Release : ", gGlblAPI.YOA_GetErrorMessage(rslt))

            # 제공시세 마지막의 경우 종료시킴
            gGlblAPI.YOA_SetTRInfo("820104", "OutBlock2")
            Nxt = gGlblAPI.YOA_GetFieldString("next", 0)  # 다음시세 존재여부
            print("Next:", Nxt)
            if(Nxt == "0"):
                NotEnd = False


            # 최종일자에 도달못했으면 다시 호출한다.
            if (NotEnd):
                print("다 못받았음.")
                print("마지막 BaseDt BaseMn", BaseDt, BaseMn)
                dDate   = datetime(year=int(BaseDt[:4]), month=int(BaseDt[4:6]), day=int(BaseDt[6:]), hour=int(BaseMn[:2]), minute=int(BaseMn[2:]))
                newLastDt  = dDate - CodeDef.ONE_MINUTE
                BaseDt = newLastDt.strftime("%Y%m%d")
                BaseMn = newLastDt.strftime("%H%M%S")

                # TR / 종목 딕셔너리 저장
                gGlblInitDict[("MN_INIT", "820104", StkCd)] = (LastDt, LastMn, BaseDt, BaseMn)
                # 기존TR 해제
                gGlblAPI.YOA_Reset("820104")
                gGlblSess_flag = True
                time.sleep(1)
                self.OnRequest("MN_INIT", "820104", StkCd)
            else:
                print("받기끝")
                gGlblSess_flag = False

        # --- if( TrID == "820104") 종료 ---
        return None

    # 서버 응답 수신대기
    def waitSrvrRspn(self):
        global gGlblSess_flag
        gGlblSess_flag = True

        while gGlblSess_flag:
            pythoncom.PumpWaitingMessages()

        print("-- waitSrvrRspn -종료- ")
        return None

    # 실시간TR 정지
    def StopRealRcv(self, inReqID, inStkCd):
        global gGlblSess_flag
        global gGlblAPI
        global gGlblRealReqDict

        gGlblSess_flag = False
        # 실시간 딕셔너리 삭제
        ReqID = inReqID
        StkCd = inStkCd
        if(inReqID is not None):
            print("111")
            ReqInfo = gGlblRealReqDict[inReqID]
            StkCd = ReqInfo[1]
        else:
            ReqInfo = gGlblRealReqDict[inStkCd]
            ReqID = ReqInfo[1]

        # 실시간수신 해제
        RsltV = gGlblAPI.YOA_UnRegistAutoWithReqID(ReqID)
        print("실시간수신해제 결과 RsltV StkCd inReqID: ",RsltV, StkCd, inReqID)

        del gGlblRealReqDict[ReqID]
        del gGlblRealReqDict[StkCd]

        return None

    # 실시간TR 전체 정지
    def StopAllRealRcv(self):

        global gGlblAPI
        RsltV = gGlblAPI.YOA_UnRegistAuto("61")

        print("전체 실시간수신해제 결과 RsltV: ", RsltV)

        return None