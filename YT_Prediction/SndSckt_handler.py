import socket

class SndSckt_handler:

    def __init__(self):
        self.SrvrAddr = None
        self.SendSock = None
        self.OnSock   = False
        return None

    # 소켓접속
    # inPort : 포트번호 CodeDef 참조
    def CnntSckt(self,inPort):
        self.SrvrAddr = ('127.0.0.1', inPort)  # 본인 무선 LAN IPv4도 가능
        self.SendSock = socket.socket(socket.AF_INET,
                                  socket.SOCK_STREAM)  # AF_INET: 인터넷소캣, SOCK_DGRAM: UDP, SOCK_STREAM: TCP
        self.SendSock.connect(self.SrvrAddr)
        self.OnSock = True
        print("Socket works")
        return None

    # 접속종료
    def ClseSckt(self):
        if(self.SendSock is not None):
            self.SendSock.close()
            self.OnSock = False
        return None

    # 접속상태 리턴
    def GetOnSock(self):
        #print("self.OnSock: " ,self.OnSock)
        return self.OnSock

    # 데이터 송신
    # inData  : 송신 데이터
    def SendData(self, inData):
        try:
            self.SendSock.send(inData.encode())
            # self.SendSock.sendto(QttnInfo.encode(), gSrvrAddr) #UDP 전송
        except Exception as e:
            print("전송에러:", e)
            self.ClseSckt(self)
        return None

