import sys
sys.path.append('../')
import json
from Logging import MyLogging as mylog
from StockDB import MarketDB as MD
from StockPortfolio import ElderTradeSystem as ets
import backtrader as bt
import pandas as pd
from datetime import datetime
from datetime import timedelta
import random
from Utility import Tools as tool
from StockPortfolio import BackTest as mybt

class BackTestFindOptimalMACD:
    def __init__(self, months_ago, for_months, thread_num=1):
        try:
            self.__path_json_sell_buy_score = 'C:/StockBot/StockPortfolio/stock_sell_buy_score.json'
            self.__path_json_tread_stock_list = 'C:/StockBot/tread_stock_list.json'
            self.__path2 = "stock_list"

            with open(self.__path_json_tread_stock_list, 'r', encoding='utf-8') as tread_stock_list_json, \
                    open(self.__path_json_sell_buy_score, 'r', encoding='utf-8') as stock_sell_buy_score_json:
                tread_stock = json.load(tread_stock_list_json)
                stock_sell_buy_score = json.load(stock_sell_buy_score_json)

                self.__logger = mylog.MyLogging(class_name=BackTestFindOptimalMACD.__name__, thread_num=thread_num)
                self.__stock_list = tread_stock['tread_stock']['target_analysis_list']
                # stock_list = tread_stock['tread_stock']['test']
                self.__stock_sell_buy_score_list = stock_sell_buy_score['stock_list']
                self.__today = datetime.now().strftime('%Y-%m-%d')
                self.__myEts = ets.ElderTradeSystem()

                days1 = (months_ago * 30) + 30
                days2 = (for_months * 30)
                self.__start_date = (datetime.today() - timedelta(days=days1)).strftime("%Y-%m-%d")
                self.__end_date = (datetime.today() - timedelta(days=days2)).strftime("%Y-%m-%d")
                self.__market_db = MD.MarketDB()
                self.__bt_obj = mybt.BackTest
                self.__logger.write_log(f"backTest 期間；【{self.__start_date}】～【{self.__end_date}】", log_lv=2)

        except FileNotFoundError as e:
            self.__logger.write_log(f"jsonファイルを見つかりません。 {str(e)}", log_lv=3)

        except Exception as e:
            self.__logger.write_log(f"Exception occured : {str(e)}", log_lv=5)

    def update_MACD(self, is_init=True, is_plot=True, plot_stock_name=None, random_range=100, akirame=2000, move_term=None):
        """
        MACDヒストグラムの変化率最適値調査
        :param is_init: stock_sell_buy_score.jsonを初期化するか　True:初期化
        :param is_plot: plotを描く　True:描く
        :param plot_stock_name: 描く株名前
        :param random_range: 最適値調査の範囲
        :param akirame: 諦める繰り返し回数
        :param move_term: 一番長いの何日移動平均か
        :return:
        """
        try:
            set_w_macd_buy = [0.0, random_range]
            set_w_macd_sell = [-random_range, 0.0]

            money = 10000000
            fees = 0.0014
            buy_persent = 90
            plot_obj = None
            comp_num = 0
            stock_amount = len(self.__stock_list)
            back_test_arg_list = [0]*10 # 初期化
            back_test_arg_list[0] = self.__logger
            back_test_arg_list[1] = 2
            back_test_arg_list[2] = self.__myEts

            #[0] = __logger // [1]=__mode // [2]=__ets // [3]=__macd_stoch_data // [4]=__macd_buy // [5]=__macd_sell

            if is_init is True:
                tool.json_clean(path=self.__path_json_sell_buy_score, path2="stock_list")

            for stock in self.__stock_list:
                target_stock = stock  # 上で使うため初期化する。
                macd_stoch_data = self.__myEts.get_macd_stochastic(target_stock, start_date=self.__start_date,
                                                                   end_date=self.__end_date,
                                                                   days_long=move_term)
                if macd_stoch_data is None or len(macd_stoch_data) < 30:
                    self.__except_write(arg_target_stock=target_stock, arg_start_date=self.__start_date, arg_end_date=self.__end_date)
                    continue

                macd_stoch_data.index = pd.to_datetime(macd_stoch_data['date'])
                mydata = self.__market_db.get_stock_price(target_stock, 'D', start_date=self.__start_date, end_date=self.__end_date)
                mydata.index = pd.to_datetime(mydata['date'])
                data = bt.feeds.PandasData(dataname=mydata)
                back_test_arg_list[3] = macd_stoch_data

                cur_macd_buy = 0   # 現在買うmacd基準
                cur_macd_sell = 0  # 現在販売macd基準
                cur_max_benefit = 0  #現在最高取得お金
                is_update = False  #jsonファイルに記載するか
                is_detail = False  #最適値調査するか
                is_success = False  #Find成功
                tust_num = 0  #最適値調査するか、現在最高取得お金が何回目出したか
                i = 0  # 探せなかった場合、whileを抜け出すための回数

                # ---------------------------- 単一株に対して調査スタート ------------------------------------
                while True:
                    if tust_num > 2 and is_detail is True:
                        macd_buy = cur_macd_buy - 0.1
                        if macd_buy < 0:
                            macd_buy = 0
                        macd_sell = cur_macd_sell + 0.1
                        if macd_sell > 0:
                            macd_sell = 0
                    else:
                        macd_buy = round(random.uniform(set_w_macd_buy[0], set_w_macd_buy[1]))
                        macd_sell = round(random.uniform(set_w_macd_sell[0], set_w_macd_sell[1]))

                    back_test_arg_list[4] = macd_buy
                    back_test_arg_list[5] = macd_sell

                    cerebro = bt.Cerebro()
                    if cerebro is None:
                        self.__logger.write_log('cerebro is None', log_lv=3)
                        continue
                    cerebro.addstrategy(self.__bt_obj, back_test_arg_list)
                    cerebro.adddata(data)
                    cerebro.broker.setcash(money)
                    cerebro.broker.setcommission(commission=fees)  # ④
                    cerebro.addsizer(bt.sizers.PercentSizer, percents=buy_persent)  # ⑤

                    start_money = cerebro.broker.getvalue()
                    # self.__logger.write_log(f'Initial Portfolio Value : {start_money:,.0f} KRW', log_lv=2)
                    try:
                        cerebro.run()
                    except Exception as e:
                        self.__except_write(arg_target_stock=target_stock,
                                            arg_start_date=self.__start_date,
                                            arg_end_date=self.__end_date)
                        self.__logger.write_log(f"Exception occured : {str(e)}", log_lv=3)
                        continue

                    end_money = cerebro.broker.getvalue()
                    # self.__logger.write_log(f'Final Portfolio Value : {new_money:,.0f} KRW', log_lv=2)
                    cur_benefit = end_money - start_money
                    #print(f"cur_benefit==============================={cur_benefit}")

                    if cur_benefit == cur_max_benefit:
                        tust_num += 1
                    else:
                        if tust_num > 2:
                            is_success = True
                            self.__logger.write_log(f"========================={target_stock}:成功======================", log_lv=2)
                            self.__logger.write_log(
                                f'取得お金； {(cur_max_benefit):,.0f}\n'
                                f'macd_buy: \t{macd_buy}\t macd_sell: \t{macd_sell}\t', log_lv=2)
                            break

                    if i == 0 or cur_benefit >= cur_max_benefit:
                        if cur_benefit > cur_max_benefit:
                            is_detail = True
                        cur_max_benefit = cur_benefit
                        cur_macd_buy = macd_buy
                        cur_macd_sell = macd_sell
                        # print(f"cur_macd_buy={cur_macd_buy}")
                        is_update = True

                    if is_plot is True and plot_stock_name == target_stock:
                        plot_obj = cerebro #cerebro.plot(style='candlestick')

                    if i > akirame:
                        is_success = False
                        self.__logger.write_log(f"========================={target_stock}:失敗======================", log_lv=2)
                        self.__logger.write_log(
                            f'取得お金； {(cur_max_benefit):,.0f}\n'
                            f'macd_buy: \t{macd_buy}\t macd_sell: \t{macd_sell}\t', log_lv=2)
                        break
                    i += 1
                # ---------------------- 単一株最適値調査終わり ----------------------------
                if is_update is True:
                    naiyou = self.__set_format(stock_name=target_stock,
                                               is_success=is_success,
                                               start_date=self.__start_date,
                                               end_date=self.__end_date,
                                               macd_buy=cur_macd_buy,
                                               macd_sell=cur_macd_sell,
                                               benefit_money=cur_max_benefit)
                    tool.write_json(path=self.__path_json_sell_buy_score, path2=self.__path2, naiyou=naiyou)
                    self.__logger.write_log(f"【{target_stock}】更新完了", log_lv=2)

                comp_num += 1
                print(f"--------------------------------------------------【{(comp_num / stock_amount) * 100}%】完了")

            # ------------------------ 全株最適値調査終わり ----------------------------
            if plot_obj is not None:
                plot_obj.plot(style='candlestick')

            return True

        except FileNotFoundError as e:
            self.__logger.write_log(f"tread_stock_list.jsonファイルを見つかりません。 {str(e)}", log_lv=3)
            return False

        except Exception as e:
            self.__logger.write_log(f"Exception occured : {str(e)}", log_lv=5)
            return False

    def __except_write(self, arg_target_stock, arg_start_date, arg_end_date):
        naiyou = self.__set_format(stock_name=arg_target_stock,
                            is_success=False,
                            start_date=arg_start_date,
                            end_date=arg_end_date,
                            macd_buy=0,
                            macd_sell=0,
                            benefit_money=0)
        tool.write_json(path=self.__path_json_sell_buy_score, path2=self.__path2, naiyou=naiyou)
        self.__logger.write_log(f"\t{arg_target_stock}\t分析失敗 dataがNoneまたは量が少ない", log_lv=3)

    def __set_format(self, stock_name, is_success, start_date, end_date, macd_buy, macd_sell, benefit_money):
        naiyou = {stock_name: {
                                "is_success": is_success,
                                "update_day": datetime.now().strftime('%Y-%m-%d'),
                                "start_date": start_date,
                                "end_date": end_date,
                                "macd_buy": macd_buy,
                                "macd_sell": macd_sell,
                                "benefit_money": benefit_money
                                }
                 }
        return naiyou
