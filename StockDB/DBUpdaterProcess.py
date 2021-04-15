import multiprocessing
from datetime import datetime
from threading import Timer
import sys
#print(sys.path)
sys.path.append('C:/StockBot')
import json, calendar, time
from Creon import Creon as co
from Creon import CreonLogin as cl
from Logging import MyLogging as mylog
from StockPortfolio import StockIgnore as si
import numpy as np
import pandas as pd


class MyProcess(multiprocessing.Process):
    def __init__(self, func_name, thread_amount, thread_num, is_select_update, update_stock_list):
        super(MyProcess, self).__init__()
        self.func_name = func_name
        self.threadAmount = thread_amount
        self.thread_num = thread_num
        self.is_select_update = is_select_update
        self.update_stock_list = update_stock_list

    def run(self):
        # p_creon = co.Creon("C:\StockBot\log\log_updateStockPrice.log")
        p_logger = mylog.MyLogging(class_name=MyProcess.__name__, thread_num=self.thread_num)
        p_ignore = si.StockIgnore(thread_num=self.thread_num)
        p_creon = co.Creon(self.thread_num)
        df_stock_info = p_creon.request_stock_info()

        p_logger.write_log(f"株コード指定Updateなのか？：【{self.is_select_update}】", log_lv=2)
        if self.is_select_update is True:
            target_list = []
            for stock in self.update_stock_list:
                if stock in df_stock_info.values: # 実際存在する株コードか
                    target_list.append(stock)
                    p_logger.write_log(f"指定アップデート追加コード：{stock}", log_lv=2)
                else:
                    p_logger.write_log(f"関数名前：【{self.func_name}】 Updateで指定した【{stock}】は存在しないです。確認ください。", log_lv=3)
            df_split_stock_info = pd.DataFrame({'code':target_list})
        else:
            df_split_stock_info = p_creon.split_df_stock(df_stock_info, self.threadAmount)

        work_amount = len(df_split_stock_info)  # 取得予定数
        p_logger.write_log(f"取得予定数：{work_amount}", log_lv=2)
        complit_amount = 0  # 取得完了項目数

        for stock in df_split_stock_info.itertuples(name='stock'):

            if self.func_name == 'section_daily_day':
                is_not_update = p_ignore.is_ignore_update_price(chart_type="day", target_stock_code=stock.code)
                if is_not_update is False:
                    p_creon.request_chart_day(code=stock.code, is_all=False)
                else:
                    p_logger.write_log(f"株価取得除外code：【day】【{stock.code}】", log_lv=2)

            elif self.func_name == 'section_daily_day_all':
                is_not_update = p_ignore.is_ignore_update_price(chart_type="day", target_stock_code=stock.code)
                if is_not_update is False:
                    p_creon.request_chart_day(code=stock.code, is_all=True)
                else:
                    p_logger.write_log(f"株価取得除外code：【day】【{stock.code}】", log_lv=2)

            elif self.func_name == 'section_M':
                is_not_update = p_ignore.is_ignore_update_price(chart_type="month", target_stock_code=stock.code)
                if is_not_update is False:
                    p_creon.request_chart_all(code=stock.code, chartType='M')
                else:
                    p_logger.write_log(f"株価取得除外code：【month】【{stock.code}】", log_lv=2)

            elif self.func_name == 'section_W':
                is_not_update = p_ignore.is_ignore_update_price(chart_type="week", target_stock_code=stock.code)
                if is_not_update is False:
                    p_creon.request_chart_all(code=stock.code, chartType='W')
                else:
                    p_logger.write_log(f"株価取得除外code：【week】【{stock.code}】", log_lv=2)

            elif self.func_name == 'section_m':
                is_not_update = p_ignore.is_ignore_update_price(chart_type="min", target_stock_code=stock.code)
                if is_not_update is False:
                    p_creon.request_chart_all(code=stock.code, chartType='m')
                else:
                    p_logger.write_log(f"株価取得除外code：【min】【{stock.code}】", log_lv=2)
            else:
                p_logger.write_log(f"【{self.func_name}】は扱わないメソッドです。",log_lv=3)
                return

            complit_amount += 1
            p_logger.write_log(f"完了：\t{self.func_name}\t{stock.code}\t", log_lv=2)
            p_logger.write_log(f"thread番号：【{self.thread_num}】"
                               f" 【{(int)(100*(complit_amount / work_amount))}%...】"
                               f" 【完了({complit_amount}/{work_amount})】", log_lv=2)
        return

def execute_daily(arg1):
    try:
        with open('C:/StockBot/update_price_stock_config.json', 'r', encoding='utf-8') as upsc:
            dai_con = json.load(upsc)
            thread_amount = dai_con[arg1]['threadAmount']
            is_select_update = dai_con[arg1]['is_select_update']
            update_stock_list = dai_con[arg1]['update_stock_list']

    except FileNotFoundError as e:
        print(f"config.jsonファイルを見つかりません。 {str(e)}")
        # logger.error(f"config.jsonファイルを見つかりません。 {str(e)}")

    except Exception as e:
        print(f'Exception occured execute_daily. {str(e)}')
        # logger.error(f'Exception occured execute_daily. {str(e)}')

    processes = []
    split_updat_stock_list = np.array_split(update_stock_list, thread_amount)

    for thread_num in range(1, thread_amount + 1):
        my_pro = MyProcess(arg1, thread_amount, thread_num, is_select_update, split_updat_stock_list[thread_num-1])
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