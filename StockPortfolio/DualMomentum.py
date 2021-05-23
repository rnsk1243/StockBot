import sys
sys.path.append('../')
import json
from Logging import MyLogging as mylog
from datetime import datetime
from datetime import timedelta
from StockDB import MarketDB as MD
import pandas as pd
from Utility import Tools as tool

path_json_dm_result = 'C:/StockBot/StockPortfolio/dual_momentum_result.json'
today = datetime.now().strftime('%Y-%m-%d')
def set_format(stock_name, rank, start_date, end_date, returns):

    naiyou = {stock_name: {
                            "rank": rank,
                            "update_day": today,
                            "start_date": start_date,
                            "end_date": end_date,
                            "returns": returns
                          }
             }
    return naiyou

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


    def get_rltv_momentum(self, months_ago_num, months_ago_end, stock_count=None):
        """특정 기간 동안 수익률이 제일 높았던 stock_count 개의 종목들 (상대 모멘텀)

        """
        if stock_count is None:
            stock_count = 100

        months_ago_num_day = months_ago_num * 30
        months_ago_end_day = months_ago_end * 30
        # KRX 종목별 수익률을 구해서 2차원 리스트 형태로 추가
        start_date_rltv = (datetime.today() - timedelta(days=months_ago_num_day)).strftime("%Y-%m-%d")
        end_date_rltv = (datetime.today() - timedelta(days=months_ago_end_day)).strftime("%Y-%m-%d")

        self.__logger.write_log(f"상대 모멘텀 期間；【{start_date_rltv}】～【{end_date_rltv}】", log_lv=2)

        rows = []
        columns = ['code', 'company', 'old_price', 'new_price', 'returns']
        for code in self.__stock_list:
            stock_close = self.__market_db.get_stock_close(code, start_date_rltv, end_date_rltv)
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
        self.__logger.write_log(f"Relative momentum【{start_date_rltv} ~ {end_date_rltv}】：{df['returns'].mean().round(2)}%", log_lv=2)

        return df, start_date_rltv, end_date_rltv

    def get_abs_momentum(self, months_ago_num, months_ago_end, stock_count=100):
        """
        絶対モメンタムを救う。
        :param months_ago_num:何か月前から取得するか指定　デフォルト：１
        :param stock_count: 株種類の数
        :return: None
        """
        months_ago_num_day = months_ago_num*30
        months_ago_end_day = months_ago_end*30

        during = months_ago_num_day - months_ago_end_day
        during_half = round(during / 2)
        temp = (months_ago_num_day - during_half)
        # start_date_rltv = (datetime.today() - timedelta(days=months_ago_num_day)).strftime("%Y-%m-%d")
        # end_date_rltv = (datetime.today() - timedelta(days=temp)).strftime("%Y-%m-%d")

        start_date_abs = (datetime.today() - timedelta(days=(temp-1))).strftime("%Y-%m-%d")
        end_date_abs = (datetime.today() - timedelta(days=months_ago_end_day)).strftime("%Y-%m-%d")

        self.__logger.write_log(f"絶対モメンタム:【{start_date_abs}】～【{end_date_abs}】", log_lv=2)

        rltv_momentum = self.get_rltv_momentum(months_ago_num_day, temp, stock_count)
        stockList = list(rltv_momentum[0]['code'])

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

        return df, start_date_abs, end_date_abs

    def print_json(self, df, start_date, end_date):
        tool.json_clean(path=path_json_dm_result, path2="target_stock")
        i = 1
        for row in df.itertuples():
            naiyou = set_format(stock_name=row[2],
                                rank=i,
                                start_date=start_date,
                                end_date=end_date,
                                returns=row[5])
            tool.write_json(path=path_json_dm_result, path2="target_stock", naiyou=naiyou)
            i += 1

        df.to_excel(f'C:/StockBot/resultExcel/momentum/abs_momentum_'
                    f'{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}.xlsx',
                    sheet_name=f'momentum')
        self.__logger.write_log(f'絶対モメンタム：\n{df}', log_lv=2)
        self.__logger.write_log(f"Abs momentum【{start_date} ~ {end_date}】：{df['returns'].mean().round(2)}%",
                                log_lv=2)

# dm = DualMomentum()
# re = dm.get_abs_momentum(months_ago_num=6, months_ago_end=3, stock_count=100)
# dm.print_json(re[0], re[1], re[2])

if __name__ == '__main__':
    args = sys.argv

    arg1 = int(args[1])
    arg2 = int(args[2])
    arg3 = int(args[3])
    arg4 = args[4]
    during = (arg1 - arg2) * 30
    dm = DualMomentum()

    if arg4 == "0":
        result = dm.get_rltv_momentum(months_ago_num=arg1, months_ago_end=arg2, stock_count=arg3)
    else:
        result = dm.get_abs_momentum(months_ago_num=arg1, months_ago_end=arg2, stock_count=arg3)

    dm.print_json(result[0], result[1], result[2])
