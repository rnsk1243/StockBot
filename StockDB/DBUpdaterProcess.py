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
    def __init__(self, func_name, thread_amount, thread_num):
        super(MyProcess, self).__init__()
        self.func_name = func_name
        self.threadAmount = thread_amount
        self.threadNum = thread_num

    def run(self):
        # myco = co.Creon("C:\StockBot\log\log_updateStockPrice.log")
        myco = co.Creon(self.threadNum)

        dfStockInfo = myco.request_stock_info()
        df_splitStockInfo = myco.split_df_stock(dfStockInfo, self.threadAmount)
        workAmount = len(df_splitStockInfo) #取得予定数
        complitAmount = 0 #取得完了項目数

        for stock in df_splitStockInfo.itertuples(name='stock'):

            if self.func_name == 'section_daily_day':

                myco.request_chart_day(code=stock.code, is_all=False)

            elif self.func_name == 'section_daily_day_all':

                myco.request_chart_day(code=stock.code, is_all=True)

            elif self.func_name == 'section_M':

                myco.request_chart_all(code=stock.code, chartType='M')

            elif self.func_name == 'section_W':

                myco.request_chart_all(code=stock.code, chartType='W')

            elif self.func_name == 'section_m':

                myco.request_chart_all(code=stock.code, chartType='m')

            else:
                return

            complitAmount += 1
            print(f"thread番号：【{self.threadNum}】"
                               f" 【{(int)(100*(complitAmount / workAmount))}%...】"
                               f" 【完了({complitAmount}/{workAmount})】")

        return

def execute_daily(arg1):
    try:
        with open('C:/StockBot/config.json', 'r', encoding='utf-8') as daily_config:
            dai_con = json.load(daily_config)
            thread_amount = dai_con[arg1]['threadAmount']

    except FileNotFoundError as e:
        print(f"config.jsonファイルを見つかりません。 {str(e)}")
        # logger.error(f"config.jsonファイルを見つかりません。 {str(e)}")

    except Exception as e:
        print(f'Exception occured execute_daily. {str(e)}')
        # logger.error(f'Exception occured execute_daily. {str(e)}')

    processes = []

    for thread_num in range(1, thread_amount + 1):
        my_pro = MyProcess(arg1, thread_amount, thread_num)
        processes.append(my_pro)
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