import json
from Logging import MyLogging as mylog
from itertools import combinations
import numpy as np
from StockDB import MarketDB as MD
import pandas as pd


class SharpeIndex:
    def __init__(self, thread_num=1):
        try:
            with open('C:/StockBot/tread_stock_list.json', 'r', encoding='utf-8') as tread_stock_list_json:
                self.__logger = mylog.MyLogging(class_name=SharpeIndex.__name__, thread_num=thread_num)
                self.__tread_stock = json.load(tread_stock_list_json)
                self.__stock_list_100 = \
                    self.__tread_stock['tread_stock']['stock_list_100']
                self.__stock_list_200 = \
                    self.__tread_stock['tread_stock']['stock_list_200']
                self.__market_db = MD.MarketDB()

                self.__logger.write_log(f'{self} init 成功', log_lv=2)

        except FileNotFoundError as e:
            print(f"tread_stock_list.jsonファイルを見つかりません。 {str(e)}")

        except Exception as e:
            self.__logger.write_log(f"Exception occured {self} init : {str(e)}", log_lv=2)

    def __get_stock_combination(self, target_list, split_target_list, combi_r):
        """
        listをsplit_target_list数に分けて、分けたリストでcombi_r数分抽出の全場合の数をリターンする。
        :param target_list:ターゲットリスト
        :param split_target_list:リスト分割数
        :param combi_r:分割リストから何個抽出するか
        :return:全場合の数 List[tuple]
        """

        stock_list = list(np.array_split(target_list, split_target_list))
        combination_list = []
        for tmp_list in stock_list:
            combination_list.append(list(combinations(tmp_list, combi_r)))

        return combination_list

    def get_sharpe_day(self, select_stock_amount):
        """
        sharpe_indexを取得する。市価総額1~100、101~200から一番利益が大きい株を返却
        :param select_stock_amount: 選ぶ株の数
        :return: dataframe
        """
        target_combi_list = self.__get_stock_combination(self.__stock_list_100,
                                                   20, 3)
        for stock_list in target_combi_list:
            for stock_tuple in stock_list:
                df = pd.DataFrame()
                for stock in stock_tuple:
                    df[stock] = self.__market_db.get_stock_price(code=stock, chart_type="D")['close']

                daily_ret = df.pct_change()
                annual_ret = daily_ret.mean() * 252
                daily_cov = daily_ret.cov()
                annual_cov = daily_cov * 252

                port_ret = []
                port_risk = []
                port_weights = []
                sharpe_ratio = []

                for _ in range(20000):
                    weights = np.random.random(len(stock_tuple))
                    weights /= np.sum(weights)

                    returns = np.dot(weights, annual_ret)
                    risk = np.sqrt(np.dot(weights.T, np.dot(annual_cov, weights)))

                    port_ret.append(returns)
                    port_risk.append(risk)
                    port_weights.append(weights)
                    sharpe_ratio.append(returns / risk)  # ①

                portfolio = {'Returns': port_ret, 'Risk': port_risk, 'Sharpe': sharpe_ratio}
                for i, s in enumerate(stock_tuple):
                    portfolio[s] = [weight[i] for weight in port_weights]
                df = pd.DataFrame(portfolio)
                df = df[['Returns', 'Risk', 'Sharpe'] + [s for s in stock_tuple]]  # ②

                max_sharpe = df.loc[df['Sharpe'] == df['Sharpe'].max()]  # ③
                min_risk = df.loc[df['Risk'] == df['Risk'].min()]  # ④

                self.__logger.write_log(max_sharpe, log_lv=2)
                self.__logger.write_log(min_risk, log_lv=2)

    def get_sharpe_day2(self):

        df = pd.DataFrame()
        for stock in self.__stock_list_100:
            df[stock] = self.__market_db.get_stock_price(code=stock, chart_type="D")['close']

        daily_ret = df.pct_change()
        annual_ret = daily_ret.mean() * 252
        daily_cov = daily_ret.cov()
        annual_cov = daily_cov * 252

        port_ret = []
        port_risk = []
        port_weights = []
        sharpe_ratio = []

        for _ in range(20000):
            weights = np.random.random(len(self.__stock_list_100))
            weights /= np.sum(weights)

            returns = np.dot(weights, annual_ret)
            risk = np.sqrt(np.dot(weights.T, np.dot(annual_cov, weights)))

            port_ret.append(returns)
            port_risk.append(risk)
            port_weights.append(weights)
            sharpe_ratio.append(returns / risk)  # ①

        portfolio = {'Returns': port_ret, 'Risk': port_risk, 'Sharpe': sharpe_ratio}
        for i, s in enumerate(self.__stock_list_100):
            portfolio[s] = [weight[i] for weight in port_weights]
        df = pd.DataFrame(portfolio)
        df = df[['Returns', 'Risk', 'Sharpe'] + [s for s in self.__stock_list_100]]  # ②

        max_sharpe = df.loc[df['Sharpe'] == df['Sharpe'].max()]  # ③
        min_risk = df.loc[df['Risk'] == df['Risk'].min()]  # ④

        self.__logger.write_log(max_sharpe, log_lv=2)
        self.__logger.write_log(min_risk, log_lv=2)

        return