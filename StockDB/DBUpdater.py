import pandas as pd
import pymysql, json
from datetime import datetime
import sys
import logging.handlers
sys.path.append('C:\StockBot')

class DBUpdater:  
    def __init__(self, threadNum = 1):
        try:
            """【..\*.json】は最上位フォルダから一階層下のフォルダから実行の基準"""
            with open('C:\StockBot\dbInfo.json', 'r', encoding='utf-8') as dbInfo_json, \
                    open('C:\StockBot\StockDB\sql.json', 'r', encoding='utf-8') as sql_json:
                self.__threadNum = threadNum
                self.__set_logger()  # loggingを初期化する。
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
            self.__logger.error(f"jsonファイルを見つかりません。 {str(e)}")

        except Exception as e:
            print('Exception occured DBUpdater init:', str(e))
            self.__logger.error(f"Exception occured DBUpdater init : {str(e)}")
               
    def __del__(self):
        """소멸자: MariaDB 연결 해제"""
        self.__conn.close()

    def __set_logger(self):
        """
        Logging初期化
        self.__threadNum(Int) thread番号によって格納するファイル名DBUpdaterLog_01~05.logを決める
        :return:
        """

        try:
            with open('C:/StockBot/logging.json', 'r', encoding='utf-8') as logging_json:
                loggingInfo = json.load(logging_json)
                self.__logger = logging.getLogger(__name__)
                self.__logger.setLevel(logging.DEBUG)
                timeFH = logging.handlers.TimedRotatingFileHandler(filename=
                                                                   loggingInfo['DBUpdater']['logFileNameArrayDBUpdater'][self.__threadNum-1],
                                                                   interval=1, backupCount=30, encoding='utf-8', when='MIDNIGHT')
                timeFH.setLevel(loggingInfo['DBUpdater']['logLevel']['SET_VALUE'])
                # timeFH.setFormatter(loggingInfo['formatters']['logFileFormatter'])
                timeFH.setFormatter(logging.Formatter(loggingInfo['formatters']['logFileFormatter']['format']))
                #timeFH.setFormatter(logging.Formatter("%(asctime)s|%(levelname)-8s|%(name)s|%(funcName)s|%(message)s"))
                self.__logger.addHandler(timeFH)

        except FileNotFoundError as e:
            print(f"logging.jsonファイルを見つかりません。 {str(e)}")
            self.__logger.error(f"C:\\StockBot\\logging.jsonファイルを見つかりません。: {str(e)}")

        except Exception as e:
            print(f"Exception occured DBUpdater __setLogger : {str(e)}")
            self.__logger.error(f"Exception occured DBUpdater __setLogger : {str(e)}")

        return

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
                    print(f"[{tmnow}] #{idx+1:04d} REPLACE INTO company_info "\
                        f"VALUES ({code}, {company}, {today})")
                    self.__logger.info(f"[{tmnow}] #{idx + 1:04d} REPLACE INTO company_info " \
                          f"VALUES ({code}, {company}, {today})")
                    self.__conn.commit()
                print('株コード commit 完了。')
                self.__logger.info('株コード commit 完了。')
            else:
                df = pd.read_sql(self.__sql['SELECT_001'], self.__conn)
                for idx in range(len(df)):
                    self.__codes[df['code'].values[idx]] = df['company'].values[idx]

        print(f'Thread Num:【{self.__threadNum}】 / 株情報Update完了。数：【{stockInfoNum}】')
        self.__logger.info(f'株情報Update完了。数：【{stockInfoNum}】')
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
        print(f"DB insert スタート：code:【{code}】、type:【{chartType}】、len:【{goalAmount}】")
        self.__logger.info(f"DB insert スタート：code:【{code}】、type:【{chartType}】、len:【{goalAmount}】")
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
                        self.__logger.error(f"type:【{chartType}】は扱えません。")
                        return None

                    self.__conn.commit()
                    self.__logger.debug(f"excu_result:【{excu_result}】、type:【{chartType}】、execute:【{r}】")


                if goalAmount == excu_result:
                    print(f"insert【挿入】。code:【{code}】、type:【{chartType}】、影響がある行数数:【{excu_result}】")
                    self.__logger.info(f"insert【挿入】。code:【{code}】、type:【{chartType}】、影響がある行数:【{excu_result}】")
                else:
                    print(f"insert【更新＆挿入】。code:【{code}】、入れようとした行数:【{goalAmount}】、影響がある行数:【{excu_result}】")
                    self.__logger.error(f"insert【更新＆挿入】。code:【{code}】、入れようとした行数:【{goalAmount}】、影響がある行数:【{excu_result}】")

                # print('[{}] #{:04d} {} ({}) : {} rows > REPLACE INTO daily_' \
                #       'price [OK]'.format(datetime.now().strftime('%Y-%m-%d%H:%M'),
                #                           chartType, self.__codes[code], code, len(df)))
        except Exception as e:
            print(f"Exception occured __replace_into_db:code:【{code}】、type:【{chartType}】、len:【{goalAmount}】、エラー内容：【{str(e)}】")
            self.__logger.error(f"Exception occured __replace_into_db:code:【{code}】、type:【{chartType}】、len:【{goalAmount}】、エラー内容：【{str(e)}】")
            return None
