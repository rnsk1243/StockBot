import multiprocessing
from datetime import datetime
from threading import Timer
import sys
#print(sys.path)
sys.path.append('C:\StockBot')
from StockDB import DBUpdater as DBU
import json, calendar, time
import numpy as np

class MyProcess(multiprocessing.Process):
    def __init__(self, comList, page):
        super(MyProcess, self).__init__()
        self.comList = comList
        self.page = page

    def run(self):
        dbu = DBU.DBUpdater()

        if self.page is None:
            targetComList = dbu.getNotCompleteCompanyList(self.comList)
            self.comList = targetComList
            print(f"미완 상장주 갯수 = {len(self.comList)}")
            for code in self.comList:
                print(f"미완 상장주 = {code}")

        for company in self.comList:
            dbu.execute_one(company=company, page=self.page)


def execute_daily(arg1):
    try:
        with open('C:\StockBot\config.json', 'r', encoding='utf-8') as in_file:
            config = json.load(in_file)
            pages_to_fetch = config[arg1]['pages_to_fetch']
            if pages_to_fetch == "None":
                pages_to_fetch = None
            core_num = config[arg1]['core_num']
    except FileNotFoundError:
        with open('C:\StockBot\config.json', 'w', encoding='utf-8') as out_file:
            pages_to_fetch = 1
            core_num = 5
            config = \
            {
                "section1": {
                    "pages_to_fetch": pages_to_fetch,
                    "core_num": core_num
                },
                "section2": {
                    "pages_to_fetch": "None",
                    "core_num": 10
                }
            }
            json.dump(config, out_file)

    processes = []
    dbu = DBU.DBUpdater()

    if pages_to_fetch is None:
        codeKeyList = np.array_split(dbu.getPriceOldData(), core_num) # 미완성만 골라 업데이트
    else:
        codeKeyList = np.array_split(dbu.getCodeKeyListALL(), core_num)  # 전체 상장주에 대해 업데이트

    if codeKeyList is not None and len(codeKeyList) > 0:
        for idx in range(0, core_num):
            myPro = MyProcess(codeKeyList[idx], pages_to_fetch)
            processes.append(myPro)
        [p.start() for p in processes]
        [p.join() for p in processes]

    tmnow = datetime.now()
    lastday = calendar.monthrange(tmnow.year, tmnow.month)[1]
    if tmnow.month == 12 and tmnow.day == lastday:
        tmnext = tmnow.replace(year=tmnow.year + 1, month=1, day=1,
                               hour=17, minute=0, second=0)
    elif tmnow.day == lastday:
        tmnext = tmnow.replace(month=tmnow.month + 1, day=1, hour=17,
                               minute=0, second=0)
    else:
        tmnext = tmnow.replace(day=tmnow.day + 1, hour=17, minute=0,
                               second=0)
    tmdiff = tmnext - tmnow
    secs = tmdiff.seconds
    t = Timer(secs, execute_daily)
    print("Waiting for next update ({}) ... ".format(tmnext.strftime
                                                     ('%Y-%m-%d %H:%M')))
    t.start()

if __name__ == '__main__':
    start_time = time.time()
    args = sys.argv
    execute_daily(args[1])
    print(f"time = {time.time() - start_time}")
    # mycreon = co.Creon()
    # mycreon.LoginCreon()
    # mycreon.CheckCreonSystem()
    # print("----")

