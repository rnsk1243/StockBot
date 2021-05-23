import sys
sys.path.append('../')
import json
from Logging import MyLogging as mylog
from StockDB import MarketDB as MD
from StockPortfolio import ElderTradeSystem as ets
import backtrader as bt
from StockPortfolio import BackTest as mybt
import pandas as pd
from datetime import datetime
from datetime import timedelta


class BackSimulation:
    def __init__(self, months_ago, for_months, thread_num=1):
        try:
            self.__path_json_sell_buy_score = 'C:/StockBot/StockPortfolio/stock_sell_buy_score.json'
            self.__path_json_tread_stock_list = 'C:/StockBot/tread_stock_list.json'

            with open(self.__path_json_tread_stock_list, 'r', encoding='utf-8') as tread_stock_list_json, \
                    open(self.__path_json_sell_buy_score, 'r', encoding='utf-8') as stock_sell_buy_score_json:
                tread_stock = json.load(tread_stock_list_json)
                stock_sell_buy_score = json.load(stock_sell_buy_score_json)

                self.__logger = mylog.MyLogging(class_name=BackSimulation.__name__, thread_num=thread_num)
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

    def simulation(self, mode=1, is_plot=False, plot_stock_name=None, move_term=None, slow_d_buy=None, slow_d_sell=None):

        try:
            list_result_stock = []
            list_result_money = []
            money = 10000000
            fees = 0.0014
            buy_persent = 90
            plot_obj = None
            column1 = "주식이름"  # 株名前
            column2 = "이득액"   # 利益金額
            dict_info = {"초기금":money, "수수료":fees, "매수율":buy_persent, "기간":self.__start_date}

            if slow_d_buy is None:
                slow_d_buy = 20
            if slow_d_sell is None:
                slow_d_sell = 80

            back_test_arg_list = [0] * 10  # [0] = __logger // [1]=__mode // [2]=__ets // [3]=__macd_stoch_data // [4]=__macd_buy // [5]=__macd_sell
            back_test_arg_list[0] = self.__logger
            back_test_arg_list[1] = mode
            back_test_arg_list[2] = self.__myEts

            for stock in self.__stock_list:

                target_stock = stock

                if mode == 3:
                    is_success = self.__stock_sell_buy_score_list[target_stock]['is_success']
                    if is_success is False:
                        self.__logger.write_log(f'Result : \t{target_stock}\t{(0):,.0f}\t KRW', log_lv=2)
                        list_result_stock.append(target_stock)
                        list_result_money.append(0)
                        continue
                    # ------------------------
                    befit_money = self.__stock_sell_buy_score_list[target_stock]['benefit_money']
                    if befit_money <= 0:
                        continue
                    # -----------------------

                macd_stoch_data = self.__myEts.get_macd_stochastic(target_stock,
                                                            start_date=self.__start_date,
                                                            end_date=self.__end_date,
                                                            days_long=move_term)
                if macd_stoch_data is None or len(macd_stoch_data) < 30:
                    self.__logger.write_log(f"{target_stock}\t予測失敗 dataがNoneまたは量が少ない", log_lv=3)
                    continue

                macd_stoch_data.index = pd.to_datetime(macd_stoch_data['date'])
                back_test_arg_list[3] = macd_stoch_data

                macd_buy = self.__stock_sell_buy_score_list[target_stock]['macd_buy']
                macd_sell = self.__stock_sell_buy_score_list[target_stock]['macd_sell']
                back_test_arg_list[4] = macd_buy
                back_test_arg_list[5] = macd_sell
                back_test_arg_list[6] = slow_d_buy
                back_test_arg_list[7] = slow_d_sell

                mydata = self.__market_db.get_stock_price(target_stock, 'D', start_date=self.__start_date, end_date=self.__end_date)
                mydata.index = pd.to_datetime(mydata['date'])
                data = bt.feeds.PandasData(dataname=mydata)

                cerebro = bt.Cerebro()
                cerebro.addstrategy(self.__bt_obj, back_test_arg_list)

                cerebro.adddata(data)
                cerebro.broker.setcash(money)
                cerebro.broker.setcommission(commission=fees)
                cerebro.addsizer(bt.sizers.PercentSizer, percents=buy_persent)

                start_money = cerebro.broker.getvalue()
                # self.__logger.write_log(f'Initial Portfolio Value : {old_money:,.0f} KRW', log_lv=2)
                try:
                    cerebro.run()
                except Exception as e:
                    self.__logger.write_log(f"{target_stock}\t予測失敗 {str(e)}", log_lv=3)
                    continue
                end_money = cerebro.broker.getvalue()
                cur_benefit = round(end_money - start_money)
                # self.__logger.write_log(f'Final Portfolio Value : {new_money:,.0f} KRW', log_lv=2)
                self.__logger.write_log(f'Result : \t{target_stock}\t{(cur_benefit):,.0f}\t KRW', log_lv=2)

                list_result_stock.append(target_stock)
                list_result_money.append(cur_benefit)

                if is_plot is True and plot_stock_name == target_stock:
                    plot_obj = cerebro
                    #cerebro.plot(style='candlestick')

            result_dic = {column1: list_result_stock, column2: list_result_money}
            result_dic.update(dict_info)

            df = pd.DataFrame.from_dict(result_dic)
            df.to_excel(f'C:/StockBot/resultExcel/back_test/'
                        f'{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}_simulation.xlsx',
                        sheet_name=f'{self.__start_date}_simulation')

            if plot_obj is not None:
                plot_obj.plot(style='candlestick')

        except FileNotFoundError as e:
            print(f"tread_stock_list.jsonファイルを見つかりません。 {str(e)}")

        except Exception as e:
            print(f"Exception occured : {str(e)}")