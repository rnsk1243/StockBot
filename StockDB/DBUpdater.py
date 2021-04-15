import pandas as pd
import pymysql, json
from datetime import datetime
import sys
from Logging import MyLogging as mylog
sys.path.append('C:/StockBot')

class DBUpdater:  
    def __init__(self, thread_num=1):
        try:
            """【../*.json】は最上位フォルダから一階層下のフォルダから実行の基準"""
            with open('C:/StockBot/dbInfo.json', 'r', encoding='utf-8') as dbInfo_json, \
                    open('C:/StockBot/StockDB/sql.json', 'r', encoding='utf-8') as sql_json:
                self.__thread_num = thread_num
                self.__logger = mylog.MyLogging(class_name=DBUpdater.__name__, thread_num=thread_num)
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
            print(f"jsonファイルを見つかりません。 {str(e)}")

        except Exception as e:
            self.__logger.write_log(f"Exception occured DBUpdater init : {str(e)}", log_lv=2)

    def UpdateStockInfo(self, dfStockInfo):
        """
            종목코드를 company_info 테이블에 업데이트 한 후 딕셔너리에 저장
            株項目一覧をDBに書き込む　
        　　- dfStockInfo : 株項目DataFrame
        """
        stockInfoNum = len(dfStockInfo)
        with self.__conn.cursor() as curs:
            curs.execute(self.__sql['SELECT_002'])
            rs = curs.fetchone()
            today = datetime.today().strftime('%Y-%m-%d')
            if rs[0] == None or rs[0].strftime('%Y-%m-%d') < today:
                for idx in range(stockInfoNum):
                    code = dfStockInfo.code.values[idx]
                    company = dfStockInfo.company.values[idx]
                    curs.execute(self.__sql['REPLACE_001'].format(code, company, today))
                    self.__codes[code] = company
                    tmnow = datetime.now().strftime('%Y-%m-%d %H:%M')
                    self.__logger.write_log(f"[{tmnow}] #{idx + 1:04d} REPLACE INTO company_info " \
                          f"VALUES ({code}, {company}, {today})", log_lv=2, is_con_print=False)
                    self.__conn.commit()
                self.__logger.write_log('株コード commit 完了。', log_lv=2)
            else:
                df = pd.read_sql(self.__sql['SELECT_001'], self.__conn)
                for idx in range(len(df)):
                    self.__codes[df['code'].values[idx]] = df['company'].values[idx]

        self.__logger.write_log(f'Thread Num:【{self.__thread_num}】 / 株情報Update完了。数：【{stockInfoNum}】', log_lv=2)
        # self.__codes_keys = list(self.__codes.keys())
        # self.__codes_values = list(self.__codes.values())

    def replace_into_db(self, code, df, chartType):
        """
        Creonから取得したChartデータをREPLACE
        :param code: 株式コード(String)
        :param df: DBに入れるデータ(DataFrame)
        :param chartType:(String) Chart区分("D","W","M","m","T")以外の場合Noneをリターンする。
        :return: None
        """
        goalAmount = len(df)
        self.__logger.write_log(f"DB insert スタート：code:【{code}】、type:【{chartType}】、len:【{goalAmount}】", log_lv=2)
        try:
            with self.__conn.cursor() as curs:
                excu_result = 0
                for r in df.itertuples():

                    if chartType == 'T': #tick Chart

                        excu_result += curs.execute(self.__sql['REPLACE_006'].format(
                            code, r.dailyCount, r.date, r.week, r.open, r.high, r.low, r.close, r.diff, r.volume))

                    elif chartType == 'm': #分 Chart

                        excu_result += curs.execute(self.__sql['REPLACE_005'].format(
                            code, r.date, r.week, r.open, r.high, r.low, r.close, r.diff, r.volume))

                    elif chartType == 'D': #日 Chart

                        excu_result += curs.execute(self.__sql['REPLACE_004'].format(
                            code, r.date, r.week, r.open, r.high, r.low, r.close, r.diff, r.volume))

                    elif chartType == 'W': #週 Chart

                        excu_result += curs.execute(self.__sql['REPLACE_003'].format(
                            code, r.date, r.week, r.open, r.high, r.low, r.close, r.diff, r.volume))

                    elif chartType == 'M': #月 Chart

                        excu_result += curs.execute(self.__sql['REPLACE_002'].format(
                            code, r.date, r.open, r.high, r.low, r.close, r.diff, r.volume))

                    else:
                        self.__logger.write_log(f"type:【{chartType}】は扱えません。", log_lv=4)
                        return None

                    self.__conn.commit()
                    self.__logger.write_log(f"excu_result:【{excu_result}】、type:【{chartType}】、execute:【{r}】", log_lv=1, is_con_print=False)
                if goalAmount == excu_result:
                    self.__logger.write_log(f"insert【挿入】。code:【{code}】、type:【{chartType}】、影響がある行数:【{excu_result}】", log_lv=2)
                else:
                    self.__logger.write_log(f"insert【更新＆挿入】。code:【{code}】、入れようとした行数:【{goalAmount}】、影響がある行数:【{excu_result}】", log_lv=2)

                # print('[{}] #{:04d} {} ({}) : {} rows > REPLACE INTO daily_' \
                #       'price [OK]'.format(datetime.now().strftime('%Y-%m-%d%H:%M'),
                #                           chartType, self.__codes[code], code, len(df)))
        except Exception as e:
            self.__logger.write_log(f"Exception occured __replace_into_db:code:【{code}】、type:【{chartType}】、len:【{goalAmount}】、エラー内容：【{str(e)}】", log_lv=5)
            return None
