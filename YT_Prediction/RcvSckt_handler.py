import socket
import threading
from  CodeDef import *

class RcvSckt_handler(threading.Thread):

    def __init__(self, inForm, inPort):
        threading.Thread.__init__(self)
        self.daemon = True

        # 수신루핑 제어
        global isQttnRunning
        global isTFRunning

        # 메인폼
        self.MainForm = inForm

        # 소켓바인딩
        self.Sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.Sckt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #self.Sctk.setblocking(0)
        self.Sckt.bind(('127.0.0.1', inPort))
        self.Sckt.listen(1)  # 소켓당 1개만 연결

        # 쓰레드 Looping 제어 초기화
        self.ScktTp   = inPort
        isQttnRunning = True
        isTFRunning   = True

        print("--수신소켓 초기화 종료--")
        return None

    def run(self):
        global isQttnRunning
        global isTFRunning
        isRunning = True
        print("accept DoWait")
        c_sock, addr = self.Sckt.accept()
        print("accepted!!:",c_sock)
        # 루프 돌면서 클라이언트로 들어온 데이터 그대로 재 전송
        while (1):

            if (self.ScktTp == CodeDef.PORT_INDEX_QTTN
            and isQttnRunning == False):
                break
            if (self.ScktTp == CodeDef.PORT_TF_RCV_RSLT
            and isTFRunning == False):
                break

            readBuf = c_sock.recv(1024)
            if (len(readBuf) != 0):
                ProcTp =""
                # 시세수신 (MainForm_handler 사용)
                if (self.ScktTp == CodeDef.PORT_INDEX_QTTN):
                    ProcTp = "KOSPI_INDEX"
                # 텐서플로 결과수신용 (MainForm_handler 사용)
                elif (self.ScktTp == CodeDef.PORT_TF_RCV_RSLT):
                    ProcTp = "TF_RSLT"
                # 텐서플로 글로벌 시세수신
                elif (self.ScktTp == CodeDef.PORT_TF_DATA):
                    ProcTp = "TF_DATA"

                self.MainForm.ProcRcvRealQttn(ProcTp, readBuf.decode())
            else:
                print("0으로 들어옴")

        print("수신 Loop 종료됨")
        return None

    # 수신 중지
    def DoStop(self):
        global isQttnRunning
        global isTFRunning

        if (self.ScktTp == CodeDef.PORT_INDEX_QTTN):
            print("시세수신 Loop 중지!!")
            isQttnRunning = False
        # 텐서플로 결과수신용
        elif (self.ScktTp == CodeDef.PORT_TF_RCV_RSLT):
            print("딥러닝결과수신 Loop 중지!!")
            isTFRunning = False

        print("종료해라!!")
        return None