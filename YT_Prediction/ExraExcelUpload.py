from openpyxl  import load_workbook, Workbook
from   pandas     import DataFrame
from DB_handler import *

sFile  = None
DBH    = None
inList = []

try:
    print("환율엑셀로딩시작")
    sFile = load_workbook("C:\YT_DeepLearningProject\YT_Prediction\Test_exr.xlsx")
    print("환율엑셀로딩끝")
    DBH = DB_handler()
except Exception as e:
    print("초기화 에러:", e)
    exit()

sSheet = sFile.active
print("입력시작")
idx = 0
for row in sSheet.rows:
    if(row[0].value is None):
        break
    # print(type(row[0].value),type(row[1].value),type(row[2].value),type(row[3].value),type(row[4].value),type(row[5].value))
    dt = str(row[0].value)
    hm = str(row[1].value).zfill(4)
    ft = row[2].value
    hg = row[3].value
    lo = row[4].value
    cl = row[5].value
    ud = row[6].value
    DBH.insertMnQttn("DERV","USDCNH",dt,hm,ft,hg,lo,cl,ud,0.0)
    # tmpList = [dt,hm,"USDKRW",(dt+hm),ft,hg,lo,cl,0.0,0.0]
    # inList.append(tmpList)
    idx = idx + 1

    if((idx % 10000) == 0):
        print(idx,"건처리 완료")

print("입력끝")