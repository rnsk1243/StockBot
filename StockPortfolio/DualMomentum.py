import json
from Logging import MyLogging as mylog
from datetime import datetime
from datetime import timedelta
from StockDB import MarketDB as MD
import pandas as pd


class DualMomentum:
    def __init__(self, thread_num=1):
        try:
            with open('C:/StockBot/tread_stock_list.json', 'r', encoding='utf-8') as tread_stock_list_json:
                self.__logger = mylog.MyLogging(class_name=DualMomentum.__name__, thread_num=thread_num)
                self.__tread_stock = json.load(tread_stock_list_json)
                self.__stock_list = \
                    self.__tread_stock['tread_stock']['stock_list']

                self.__market_db = MD.MarketDB()

                self.__logger.write_log(f'{self} init 成功', log_lv=2)

        except FileNotFoundError as e:
            print(f"tread_stock_list.jsonファイルを見つかりません。 {str(e)}")

        except Exception as e:
            self.__logger.write_log(f"Exception occured {self} init : {str(e)}", log_lv=2)


    def get_rltv_momentum(self, start_date=None, end_date=None, stock_count=None):
        """특정 기간 동안 수익률이 제일 높았던 stock_count 개의 종목들 (상대 모멘텀)

        """
        if stock_count is None:
            stock_count = 100
        # KRX 종목별 수익률을 구해서 2차원 리스트 형태로 추가
        rows = []
        columns = ['code', 'company', 'old_price', 'new_price', 'returns']
        for code in self.__stock_list:
            stock_close = self.__market_db.get_stock_close(code, start_date, end_date)
            if stock_close is not None:
                rows.append(stock_close)
            else:
                self.__logger.write_log(f'メソッド：【get_rltv_momentum】株価照会失敗：【{code}】', log_lv=3)

        # 상대 모멘텀 데이터프레임을 생성한 후 수익률순으로 출력
        df = pd.DataFrame(rows, columns=columns)
        df = df[['code', 'company', 'old_price', 'new_price', 'returns']]
        df = df.sort_values(by='returns', ascending=False)
        df = df.head(stock_count)
        df.index = pd.Index(range(stock_count))

        self.__logger.write_log(f'相対モメンタム：\n{df}', log_lv=2)
        self.__logger.write_log(f"Relative momentum【{start_date} ~ {end_date}】：{df['returns'].mean().round(2)}%", log_lv=2)

        return df

    def get_abs_momentum(self, months_ago_num=None, stock_count=None):
        """
        絶対モメンタムを救う。
        :param months_ago_num:何か月前から取得するか指定　デフォルト：１
        :param stock_count: 株種類の数
        :return: None
        """
        if months_ago_num is None:
            days = 30
            start_date_rltv = datetime.today() - timedelta(days=days)
        else:
            days = 30 * months_ago_num
            start_date_rltv = datetime.today() - timedelta(days=days)

        days_half = round(days / 2)
        end_date_rltv = datetime.today() - timedelta(days=days_half)
        start_date_abs = datetime.today() - timedelta(days=(days_half-1))
        end_date_abs = datetime.today()

        rltv_momentum = self.get_rltv_momentum(start_date_rltv, end_date_rltv, stock_count)
        stockList = list(rltv_momentum['code'])

        rows = []
        columns = ['code', 'company', 'old_price', 'new_price', 'returns']
        for code in stockList:
            stock_close = self.__market_db.get_stock_close(code, start_date_abs, end_date_abs)
            if stock_close is not None:
                rows.append(stock_close)
            else:
                self.__logger.write_log(f'メソッド：【get_abs_momentum】株価照会失敗：【{code}】', log_lv=3)

        df = pd.DataFrame(rows, columns=columns)
        df = df[['code', 'company', 'old_price', 'new_price', 'returns']]
        df = df.sort_values(by='returns', ascending=False)

        df.to_excel(f'C:\StockBot\\resultExcel\get_abs_momentum_{days}_days.xlsx', sheet_name=f'abs_momentum_{days}_days')
        self.__logger.write_log(f'絶対モメンタム：\n{df}', log_lv=2)
        self.__logger.write_log(f"Abs momentum【{start_date_abs} ~ {end_date_abs}】：{df['returns'].mean().round(2)}%", log_lv=2)

