import sys
sys.path.append('../')
import json
from Logging import MyLogging as mylog
from StockDB import MarketDB as MD
import matplotlib.pyplot as plt
from mplfinance.original_flavor import candlestick_ohlc
import matplotlib.dates as mdates
from StockPortfolio import ElderTradeSystem as ets
import backtrader as bt
import pandas as pd
from datetime import datetime
from datetime import timedelta
import random
from Utility import Tools as tool
import time


path_json_sell_buy_score = 'C:/StockBot/StockPortfolio/stock_sell_buy_score.json'
path_json_tread_stock_list = 'C:/StockBot/tread_stock_list.json'
path2 = "stock_list"
logger = mylog.MyLogging(class_name="BackTest", thread_num=1)
myEts = ets.ElderTradeSystem()
mode1 = 0 # basic
mode2 = 1 # ai
mode3 = 2 # basic + ai
mode = mode2
# w_macd = 1.957097116 # 1.92015856
# score_buy = 74.52860508 # 74.5946444
# score_sell = -6.891501131 # -8.132622257
w_macd = None
score_buy = None
score_sell = None
macd_stoch_data = None
market_db = MD.MarketDB()

def set_format(stock_name, start_date, w_macd, score_buy, score_sell, benefit_money):

    naiyou = {stock_name: {
                            "update_day": datetime.now().strftime('%Y-%m-%d'),
                            "start_date": start_date,
                            "w_macd": w_macd,
                            "score_buy": score_buy,
                            "score_sell": score_sell,
                            "benefit_money": benefit_money
                            }
             }
    return naiyou

class BackTest(bt.Strategy):
    def __init__(self):
        try:
            self.order = None
            self.buyprice = None
            self.buycomm = None
            self.rsi = bt.indicators.RSI_SMA(self.data.close, period=21)
            # logger.write_log(f'{self} init 成功', log_lv=2)

        except Exception as e:
            logger.write_log(f"Exception occured {self} init : {str(e)}", log_lv=5)

    def notify_order(self, order):  # ①
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:  # ②
             if order.isbuy():
                 # logger.write_log(f'BUY  : 주가 {order.executed.price:,.0f}, '
                 #         f'수량 {order.executed.size:,.0f}, '
                 #         f'수수료 {order.executed.comm:,.0f}, '
                 #         f'자산 {cerebro.broker.getvalue():,.0f}', log_lv=2)
                 self.buyprice = order.executed.price
                 self.buycomm = order.executed.comm
             # else:
             #     logger.write_log(f'SELL : 주가 {order.executed.price:,.0f}, '
             #             f'수량 {order.executed.size:,.0f}, '
             #             f'수수료 {order.executed.comm:,.0f}, '
             #             f'자산 {cerebro.broker.getvalue():,.0f}', log_lv=2)
             self.bar_executed = len(self)
        elif order.status in [order.Canceled]:
             logger.write_log('ORDER CANCELD', log_lv=2)
        elif order.status in [order.Margin]:
             logger.write_log('ORDER MARGIN', log_lv=2)
        elif order.status in [order.Rejected]:
             logger.write_log('ORDER REJECTED', log_lv=2)

        self.order = None

    # def next(self):
    #
    #     if not self.position:
    #        if self.rsi < 30:
    #            self.order = self.buy()
    #     else:
    #        if self.rsi > 70:
    #            self.order = self.sell()

    def next(self):

        split_date = str(self.datas[0].datetime.date(0)).split('-')
        if split_date is None or len(split_date) < 3:
            logger.write_log(f"split_date is None or len(split_date) < 3", log_lv=3)
            return
        else:
            now_data = datetime(int(split_date[0]), int(split_date[1]), int(split_date[2]))

        if now_data in macd_stoch_data.index:
            temp_df = macd_stoch_data.loc[now_data]
            hist_inclination_avg = temp_df['hist_inclination_avg']
            slow_d = temp_df['slow_d']

            if mode == mode1:
                is_buy_sell = myEts.is_buy_sell(macd_sec_dpc=hist_inclination_avg,
                                                       slow_d=slow_d)
            elif mode == mode2:
                is_buy_sell = myEts.is_buy_sell(macd_sec_dpc=hist_inclination_avg,
                                                       slow_d=slow_d,
                                                       w_macd=w_macd,
                                                       score_buy=score_buy,
                                                       score_sell=score_sell)
            else:
                return

        else:
            logger.write_log(f"index No = {now_data}", log_lv=3)
            return

        if mode == 3:
            if not self.position:
                if is_buy_sell[0] is True and is_buy_sell[1] is True:
                    self.order = self.buy()
            else:
                if is_buy_sell[0] is False and is_buy_sell[1] is False:
                    self.order = self.sell()
        else:
            if not self.position:
                if is_buy_sell[mode] is True:
                    self.order = self.buy()
            else:
                if is_buy_sell[mode] is False:
                    self.order = self.sell()

    def log(self, txt, dt=None):  # ③
        dt = self.datas[0].datetime.date(0)
        logger.write_log(f'[{dt.isoformat()}] {txt}', log_lv=2)

#########################
# kurikae = 100
# start_date = '2021-01-01' # None
# set_w_macd = [1.9, 2.5]
# set_score_buy = [74, 80]
# set_score_sell = [-8.2, 0]
days = 180
term = 3 # ヶ月
start_days = days+30 # "2021-01-01" # args[2] # 指定より1ヶ月早くなる。指定；2021-01-01、リアル；2021-02-01
end_days = days-(term*30)

args = sys.argv
func_num = args[1] # "1" # args[1]
is_update_insert = ""

if func_num == '--mode=client':
    func_num = "0"
    start_date = (datetime.today() - timedelta(days=start_days)).strftime("%Y-%m-%d")
    end_data = (datetime.today() - timedelta(days=end_days)).strftime("%Y-%m-%d")
    kurikae = 100000
    is_update_insert = "update"
else:
    start_days = int(args[2]) + 30
    end_days = int(args[2]) - (int(args[3]) * 30)

    start_date = (datetime.today() - timedelta(days=start_days)).strftime("%Y-%m-%d")
    end_data = (datetime.today() - timedelta(days=end_days)).strftime("%Y-%m-%d")
    if func_num == "0":
        kurikae = int(args[4])  # 100  # args[3]
        is_update_insert = args[5]

set_w_macd = [1.4, 3.0]
set_score_buy = [65, 85]
set_score_sell = [-15, 15]
delta_w_macd = 0.5
delta_score_buy = 3
delta_score_sell = 3
is_plot = False
# is_plot = True
########################

money = 10000000
fees = 0.0014
buy_persent = 90
bt_obj = BackTest
column1 = "주식이름"  # 株名前
column2 = "이득액"   # 利益金額
dict_info = {"초기금":money, "수수료":fees, "매수율":buy_persent, "기간":start_date}

if func_num == "0":

    try:
        with open(path_json_tread_stock_list, 'r', encoding='utf-8') as tread_stock_list_json, \
                open(path_json_sell_buy_score, 'r', encoding='utf-8') as stock_sell_buy_score_json:
            tread_stock = json.load(tread_stock_list_json)
            stock_list = tread_stock['tread_stock']['target_analysis_list']
            stock_sell_buy_score = json.load(stock_sell_buy_score_json)
            stock_sell_buy_score_list = stock_sell_buy_score['stock_list']

            comp_num = 0

            for stock in stock_list:
                target_stock = stock  # 上で使うため初期化する。
                macd_stoch_data = myEts.get_macd_stochastic(target_stock, start_date=start_date, end_data=end_data)
                if macd_stoch_data is None:
                    continue

                macd_stoch_data.index = pd.to_datetime(macd_stoch_data['date'])
                mydata = market_db.get_stock_price(target_stock, 'D', start_date=start_date, end_date=end_data)
                mydata.index = pd.to_datetime(mydata['date'])
                data = bt.feeds.PandasData(dataname=mydata)

                cur_max_benefit = stock_sell_buy_score_list[target_stock]['benefit_money']  # 現在最高利益金
                cur_w_macd = stock_sell_buy_score_list[target_stock]['w_macd']
                cur_score_buy = stock_sell_buy_score_list[target_stock]['score_buy']
                cur_score_sell = stock_sell_buy_score_list[target_stock]['score_sell']
                logger.write_log(f"【{target_stock}】現在予想利益金：{(cur_max_benefit):,.0f}", log_lv=2)
                result_w_macd = 0
                result_score_buy = 0
                result_score_sell = 0
                is_update = False

                for i in range(kurikae):

                    if cur_w_macd != 0 and cur_score_buy != 0 and cur_score_sell != 0 and cur_max_benefit > 0:
                        # w_macd = cur_w_macd
                        # score_buy = cur_score_buy
                        # score_sell = cur_score_sell
                        w_macd = round(random.uniform(cur_w_macd - delta_w_macd,
                                                      cur_w_macd + delta_w_macd), 2)
                        score_buy = round(random.uniform(cur_score_buy - delta_score_buy,
                                                         cur_score_buy + delta_score_buy), 1)
                        score_sell = round(random.uniform(cur_score_sell - delta_score_sell,
                                                          cur_score_sell + delta_score_sell), 1)
                    else:
                        w_macd = round(random.uniform(set_w_macd[0], set_w_macd[1]), 2)
                        score_buy = round(random.uniform(set_score_buy[0], set_score_buy[1]), 1)
                        score_sell = round(random.uniform(set_score_sell[0], set_score_sell[1]), 1)

                    cerebro = bt.Cerebro()
                    if cerebro is None:
                        logger.write_log('cerebro is None', log_lv=3)
                        continue

                    cerebro.addstrategy(bt_obj)
                    cerebro.adddata(data)
                    cerebro.broker.setcash(money)
                    cerebro.broker.setcommission(commission=fees)  # ④
                    cerebro.addsizer(bt.sizers.PercentSizer, percents=buy_persent)  # ⑤

                    start_money = cerebro.broker.getvalue()
                    # logger.write_log(f'Initial Portfolio Value : {start_money:,.0f} KRW', log_lv=2)
                    cerebro.run()
                    end_money = cerebro.broker.getvalue()
                    # logger.write_log(f'Final Portfolio Value : {new_money:,.0f} KRW', log_lv=2)
                    cur_benefit = end_money - start_money

                    if (i == 0 and is_update_insert == "insert") or (cur_benefit > cur_max_benefit):
                        logger.write_log(
                            f'最高取得率更新 更新前：{(cur_max_benefit):,.0f} → 更新後：{(cur_benefit):,.0f} \n'
                            f'w_macd: \t{result_w_macd}\t score_buy: \t{result_score_buy}\t score_sell: \t{result_score_sell}\t KRW',
                            log_lv=2)
                        cur_max_benefit = cur_benefit
                        result_w_macd = w_macd
                        result_score_buy = score_buy
                        result_score_sell = score_sell
                        is_update = True

                    if is_plot is True:
                        cerebro.plot(style='candlestick')

                    if (i % 1000) == 0:
                        print(f"【{target_stock}】分析中…【{i} / {kurikae}】")

                if is_update is True:
                    naiyou = set_format(stock_name=target_stock,
                                        start_date=start_date,
                                        w_macd=result_w_macd,
                                        score_buy=result_score_buy,
                                        score_sell=result_score_sell,
                                        benefit_money=cur_max_benefit)
                    tool.write_json(path=path_json_sell_buy_score, path2=path2, naiyou=naiyou)
                    logger.write_log(f"【{target_stock}】更新完了", log_lv=2)
                comp_num += 1

                print(f"【{(comp_num / len(stock_list)) * 100}%】完了")

    except FileNotFoundError as e:
        print(f"tread_stock_list.jsonファイルを見つかりません。 {str(e)}")

    except Exception as e:
        print(f"Exception occured : {str(e)}")

elif func_num == "1":

    try:
        with open('C:/StockBot/tread_stock_list.json', 'r', encoding='utf-8') as tread_stock_list_json, \
                open(path_json_sell_buy_score, 'r', encoding='utf-8') as stock_sell_buy_score_json:
            tread_stock = json.load(tread_stock_list_json)
            stock_list = tread_stock['tread_stock']['stock_list']
            stock_sell_buy_score = json.load(stock_sell_buy_score_json)
            stock_sell_buy_score_list = stock_sell_buy_score['stock_list']
            list_result_stock = []
            list_result_money = []

            for stock in stock_list:
                target_stock = stock
                macd_stoch_data = myEts.get_macd_stochastic(target_stock, start_date=start_date, end_data=end_data)
                macd_stoch_data.index = pd.to_datetime(macd_stoch_data['date'])
                w_macd = stock_sell_buy_score_list[target_stock]['w_macd']
                score_buy = stock_sell_buy_score_list[target_stock]['score_buy']
                score_sell = stock_sell_buy_score_list[target_stock]['score_sell']

                if w_macd == 0 or score_buy == 0 or score_sell == 0:
                    logger.write_log(f'Result : \t{target_stock}\t{(0):,.0f}\t KRW', log_lv=2)
                    list_result_stock.append(target_stock)
                    list_result_money.append(0)
                    continue

                mydata = market_db.get_stock_price(target_stock, 'D', start_date=start_date, end_date=end_data)
                mydata.index = pd.to_datetime(mydata['date'])

                cerebro = bt.Cerebro()
                cerebro.addstrategy(bt_obj)
                data = bt.feeds.PandasData(dataname=mydata)

                cerebro.adddata(data)
                cerebro.broker.setcash(money)
                cerebro.broker.setcommission(commission=fees)
                cerebro.addsizer(bt.sizers.PercentSizer, percents=buy_persent)

                start_money = cerebro.broker.getvalue()
                # logger.write_log(f'Initial Portfolio Value : {old_money:,.0f} KRW', log_lv=2)
                cerebro.run()
                end_money = cerebro.broker.getvalue()
                cur_benefit = round(end_money - start_money)
                # logger.write_log(f'Final Portfolio Value : {new_money:,.0f} KRW', log_lv=2)
                logger.write_log(f'Result : \t{target_stock}\t{(cur_benefit):,.0f}\t KRW', log_lv=2)

                list_result_stock.append(target_stock)
                list_result_money.append(cur_benefit)

                if is_plot is True:
                    cerebro.plot(style='candlestick')

            result_dic = {column1: list_result_stock, column2: list_result_money}
            result_dic.update(dict_info)

            df = pd.DataFrame.from_dict(result_dic)
            df.to_excel(f'C:/StockBot/resultExcel/back_test/'
                        f'{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}_simulation.xlsx',
                        sheet_name=f'{start_date}_simulation')

    except FileNotFoundError as e:
        print(f"tread_stock_list.jsonファイルを見つかりません。 {str(e)}")

    except Exception as e:
        print(f"Exception occured : {str(e)}")

# if __name__ == '__main__':
#     start_time = time.time()
#     print(f"time = {time.time() - start_time}")

