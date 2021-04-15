import pandas as pd
import pymysql, json
from datetime import datetime
from datetime import timedelta
import re
import sys
sys.path.append('C:\StockBot')

class MarketDB:
    def __init__(self):
        try:
            """【..\*.json】は最上位フォルダから一階層下のフォルダから実行の基準"""
            with open('C:\StockBot\dbInfo.json', 'r', encoding='utf-8') as dbInfo_json, \
                    open('C:\StockBot\StockDB\sql.json', 'r', encoding='utf-8') as sql_json:
                dbInfo = json.load(dbInfo_json)
                self.__sql = json.load(sql_json)
                host = dbInfo['host']
                user = dbInfo['user']
                password = dbInfo['password']
                dbName = dbInfo['db']
                charset = dbInfo['charset']

            """생성자: MariaDB 연결 및 종목코드 딕셔너리 생성"""
            self.__conn = pymysql.connect(host=host, user=user,
                                          password=password, db=dbName, charset=charset)
            self.__codes = {}
            self.__get_comp_info()


        except FileNotFoundError as e:
            print(f"dbInfo.jsonファイルを見つかりません。 {str(e)}")

        except Exception as e:
            print('Exception occured MarketDB init:', str(e))
        
    def __del__(self):
        """소멸자: MariaDB 연결 해제"""
        self.__conn.close()

    def __get_comp_info(self):
        """company_info 테이블에서 읽어와서 codes에 저장"""
        krx = pd.read_sql(self.__sql['SELECT_001'], self.__conn)
        for idx in range(len(krx)):
            self.__codes[krx['code'].values[idx]] = krx['company'].values[idx]
        self.__codes_keys = list(self.__codes.keys())
        self.__codes_values = list(self.__codes.values())

    def __index_to_datetime(self, df):
        """dataframeのインデックスをdatetime64[ns]型にする
            - df : daily_priceテーブルからselect結果のdataframe
        """
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df['date'] = df.index
        df = df[['code', 'date', 'open', 'high', 'low', 'close', 'diff', 'volume']]
        return df

    def get_daily_price(self, code, start_date=None, end_date=None, isStockSplit=True):
        """KRX 종목의 일별 시세를 데이터프레임 형태로 반환
            - code       : KRX 종목코드('005930') 또는 상장기업명('삼성전자')
            - start_date : 조회 시작일('2020-01-01'), 미입력 시 1년 전 오늘
            - end_date   : 조회 종료일('2020-12-31'), 미입력 시 오늘 날짜
        """
        if start_date is None:
            one_year_ago = datetime.today() - timedelta(days=365)
            start_date = one_year_ago.strftime('%Y-%m-%d')
            print("start_date is initialized to '{}'".format(start_date))
        else:
            start_lst = re.split('\D+', start_date)
            if start_lst[0] == '':
                start_lst = start_lst[1:]
            start_year = int(start_lst[0])
            start_month = int(start_lst[1])
            start_day = int(start_lst[2])
            if start_year < 1900 or start_year > 2200:
                print(f"ValueError: start_year({start_year:d}) is wrong.")
                return
            if start_month < 1 or start_month > 12:
                print(f"ValueError: start_month({start_month:d}) is wrong.")
                return
            if start_day < 1 or start_day > 31:
                print(f"ValueError: start_day({start_day:d}) is wrong.")
                return
            start_date=f"{start_year:04d}-{start_month:02d}-{start_day:02d}"

        if end_date is None:
            end_date = datetime.today().strftime('%Y-%m-%d')
            print("end_date is initialized to '{}'".format(end_date))
        else:
            end_lst = re.split('\D+', end_date)
            if end_lst[0] == '':
                end_lst = end_lst[1:] 
            end_year = int(end_lst[0])
            end_month = int(end_lst[1])
            end_day = int(end_lst[2])
            if end_year < 1800 or end_year > 2200:
                print(f"ValueError: end_year({end_year:d}) is wrong.")
                return
            if end_month < 1 or end_month > 12:
                print(f"ValueError: end_month({end_month:d}) is wrong.")
                return
            if end_day < 1 or end_day > 31:
                print(f"ValueError: end_day({end_day:d}) is wrong.")
                return
            end_date = f"{end_year:04d}-{end_month:02d}-{end_day:02d}"
         
        #codes_keys = list(self.__codes.keys())
        #codes_values = list(self.__codes.values())

        if code in self.__codes_keys:
            pass
        elif code in self.__codes_values:
            idx = self.__codes_values.index(code)
            code = self.__codes_keys[idx]
        else:
            print(f"ValueError: Code({code}) doesn't exist.")

        df = pd.read_sql(self.__sql['SELECT_004'].format(
            code, start_date, end_date), self.__conn)
        df = self.__index_to_datetime(df)

        # if isStockSplit is True:
        #     stockPriceChangeDate = pd.read_sql(self.__sql['SELECT_005'].format(
        #         code), self.__conn)
        #     maxDate = stockPriceChangeDate['MAX(daily_price.date)'][0] #株が分割または併合された日
        #
        #     if maxDate is not None:
        #         startDate = maxDate + timedelta(days=1) #株が分割または併合された日の翌日から検索
        #         df = df[startDate:]
        #     else:
        #         pass

        return df

    # def get_stock_safe_new_data(self, code):
    #     """株式分割または株式併合が行った以降の情報のみ検索"""
    #
    #     if code in self.__codes_keys:
    #         pass
    #     elif code in self.__codes_values:
    #         idx = self.__codes_values.index(code)
    #         code = self.__codes_keys[idx]
    #     else:
    #         print(f"ValueError: Code({code}) doesn't exist.")
    #
    #     df = pd.read_sql(self.__sql['SELECT_006'].format(
    #         code, code), self.__conn)
    #     df = self.__index_to_datetime(df)
    #
    #     return df
    #
    # def get_stock_safe_old_data(self, code):
    #     """株式分割または株式併合が行った以降の情報のみ検索"""
    #
    #     if code in self.__codes_keys:
    #         pass
    #     elif code in self.__codes_values:
    #         idx = self.__codes_values.index(code)
    #         code = self.__codes_keys[idx]
    #     else:
    #         print(f"ValueError: Code({code}) doesn't exist.")
    #
    #     df = pd.read_sql(self.__sql['SELECT_007'].format(
    #         code, code), self.__conn)
    #     df = self.__index_to_datetime(df)
    #
    #     return df