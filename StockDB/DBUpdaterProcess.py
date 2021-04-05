import multiprocessing
from datetime import datetime
from threading import Timer
import sys
#print(sys.path)
sys.path.append('C:/StockBot')
import json, calendar, time
from Creon import Creon as co
from Creon import CreonLogin as cl


class MyProcess(multiprocessing.Process):
    def __init__(self, threadAmount, threadNum, is_All, is_T):
        super(MyProcess, self).__init__()
        self.threadAmount = threadAmount
        self.threadNum = threadNum
        self.is_All = is_All
        self.is_T = is_T

    def run(self):
        # myco = co.Creon("C:\StockBot\log\log_updateStockPrice.log")
        myco = co.Creon(self.threadNum)
        myco.update_stock_price(threadAmount=self.threadAmount, is_All=self.is_All, is_T=self.is_T)

def execute_daily(arg1):
    try:
        with open('C:/StockBot/config.json', 'r', encoding='utf-8') as daily_config:
            # open('C:/StockBot/logging.json', 'r', encoding='utf-8') as logging_json:
            # loggingInfo = json.load(logging_json)
            # config.dictConfig(loggingInfo)
            # logger = getLogger(__name__)
            daiCon = json.load(daily_config)
            threadAmount = daiCon[arg1]['threadAmount']
            is_All = daiCon[arg1]['is_All']
            is_T = daiCon[arg1]['is_T']

    except FileNotFoundError as e:
        print(f"config.jsonファイルを見つかりません。 {str(e)}")
        # logger.error(f"config.jsonファイルを見つかりません。 {str(e)}")

    except Exception as e:
        print(f'Exception occured execute_daily. {str(e)}')
        # logger.error(f'Exception occured execute_daily. {str(e)}')

    processes = []

    for threadNum in range(1, threadAmount + 1):
        myPro = MyProcess(threadAmount, threadNum, is_All, is_T)
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
    print("Waiting for next update ({}) ... ".
                format(tmnext.strftime('%Y-%m-%d %H:%M')))
    t.start()

if __name__ == '__main__':
    start_time = time.time()
    args = sys.argv

    loginCreon = cl.CreonLogin()
    loginCreon.LoginCreon()

    execute_daily(args[1])
    print(f"time = {time.time() - start_time}")