import pandas as pd
from bs4 import BeautifulSoup
import pymysql, json
import requests
from datetime import datetime
import sys
sys.path.append('C:\StockBot')

class DBUpdater:  
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

            self.__codes = {} # key:株コード:value:社名

        except FileNotFoundError as e:
            print(f"dbInfo.jsonファイルを見つかりません。 {str(e)}")

        except Exception as e:
            print('Exception occured DBUpdater init:', str(e))
               
    def __del__(self):
        """소멸자: MariaDB 연결 해제"""
        self.__conn.close() 

    def UpdateStockInfo(self, dfStockInfo):
        """
            종목코드를 company_info 테이블에 업데이트 한 후 딕셔너리에 저장
            株項目一覧をDBに書き込む　
        　　- dfStockInfo : 株項目DataFrame
        """
        with self.__conn.cursor() as curs:
            curs.execute(self.__sql['SELECT_002'])
            rs = curs.fetchone()
            today = datetime.today().strftime('%Y-%m-%d')
            if rs[0] == None or rs[0].strftime('%Y-%m-%d') < today:
                for idx in range(len(dfStockInfo)):
                    code = dfStockInfo.code.values[idx]
                    company = dfStockInfo.company.values[idx]
                    curs.execute(self.__sql['REPLACE_001'].format(code, company, today))
                    self.__codes[code] = company
                    tmnow = datetime.now().strftime('%Y-%m-%d %H:%M')
                    print(f"[{tmnow}] #{idx+1:04d} REPLACE INTO company_info "\
                        f"VALUES ({code}, {company}, {today})")
                self.__conn.commit()
                print('종목코드 commit 완료')
            else:
                df = pd.read_sql(self.__sql['SELECT_001'], self.__conn)
                for idx in range(len(df)):
                    self.__codes[df['code'].values[idx]] = df['company'].values[idx]

        print('종목코드 딕셔너리에 저장 완료')
        self.__codes_keys = list(self.__codes.keys())
        self.__codes_values = list(self.__codes.values())

    def replace_into_db(self, code, df, chartType):
        """
        Creonから取得したChartデータをREPLACE
        :param code: 株式コード(String)
        :param df: DBに入れるデータ(DataFrame)
        :param chartType:(String) Chart区分("D","W","M","m","T")以外の場合Noneをリターンする。
        :return: None
        """
        try:
            with self.__conn.cursor() as curs:
                for r in df.itertuples():

                    if chartType == 'T': #tick Chart

                        curs.execute(self.__sql['REPLACE_006'].format(
                            0, code, r.dailyCount, r.date, r.week, r.open, r.high, r.low, r.close, r.diff, r.volume))

                    elif chartType == 'm': #分 Chart

                        curs.execute(self.__sql['REPLACE_005'].format(
                            0, code, r.dailyCount, r.date, r.week, r.open, r.high, r.low, r.close, r.diff, r.volume))

                    elif chartType == 'D': #日 Chart

                        curs.execute(self.__sql['REPLACE_004'].format(
                            0, code, r.date, r.week, r.open, r.high, r.low, r.close, r.diff, r.volume))

                    elif chartType == 'W': #週 Chart

                        curs.execute(self.__sql['REPLACE_003'].format(
                            0, code, r.date, r.week, r.open, r.high, r.low, r.close, r.diff, r.volume))

                    elif chartType == 'M': #月 Chart

                        curs.execute(self.__sql['REPLACE_002'].format(
                            0, code, r.date, r.open, r.high, r.low, r.close, r.diff, r.volume))

                    else:
                        return None

                self.__conn.commit()
                # print('[{}] #{:04d} {} ({}) : {} rows > REPLACE INTO daily_' \
                #       'price [OK]'.format(datetime.now().strftime('%Y-%m-%d%H:%M'),
                #                           chartType, self.__codes[code], code, len(df)))
        except Exception as e:
            print(f"Exception occured __replace_into_db:【{chartType}】 {str(e)}")
            return None
