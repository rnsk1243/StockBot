import time
import json
import ctypes
import win32com.client
import logging.handlers
import pandas as pd
from StockDB import DBUpdater as DBU
from datetime import datetime

LT_TRADE_REQUEST = 0
LT_NONTRADE_REQUEST = 1
LT_SUBSCRIBE = 2
MAX_REQUEST_NUM = 2221


class Creon:
    def __init__(self, threadNum):
        try:
            with open('C:/StockBot/Creon/creonConfig.json', 'r', encoding='utf-8') as creonConfig_json:
                self.__threadNum = threadNum
                self.__setLogger() #loggingを初期化する。
                self.__dbu = DBU.DBUpdater()

                self.__creonConfig = json.load(creonConfig_json)
                self.__cpStatus = win32com.client.Dispatch('CpUtil.CpCybos')
                self.__cpTradeUtil = win32com.client.Dispatch('CpTrade.CpTdUtil')
                self.__objStockChart = win32com.client.Dispatch('CpSysDib.StockChart')
                self.__objCpCodeMgr = win32com.client.Dispatch("CpUtil.CpCodeMgr")
                self.__logger.info('Creon init 成功')

        except FileNotFoundError as e:
            print(f"jsonファイルを見つかりません。 {str(e)}")
            self.__logger.error(f"jsonファイルを見つかりません。 {str(e)}")

        except Exception as e:
            print(f"Exception occured Creon init : {str(e)}")
            self.__logger.error(f"Exception occured Creon init : {str(e)}")

    def __setLogger(self):
        """
        Logging初期化
        self.__threadNum(Int) thread番号によって格納するファイル名CreonLog_01~05.logを決める
        :return:
        """

        try:
            with open('C:/StockBot/logging.json', 'r', encoding='utf-8') as logging_json:
                loggingInfo = json.load(logging_json)
                self.__logger = logging.getLogger(__name__)
                self.__logger.setLevel(logging.DEBUG)
                timeFH = logging.handlers.TimedRotatingFileHandler(filename=
                                                                   loggingInfo['CreonLoggingInfo']['logFileNameArrayCreon'][self.__threadNum-1],
                                                                   interval=1, backupCount=30, encoding='utf-8', when='MIDNIGHT')
                timeFH.setLevel(loggingInfo['CreonLoggingInfo']['logLevel']['SET_VALUE'])
                # timeFH.setFormatter(loggingInfo['formatters']['logFileFormatter'])
                timeFH.setFormatter(logging.Formatter(loggingInfo['formatters']['logFileFormatter']['format']))
                #timeFH.setFormatter(logging.Formatter("%(asctime)s|%(levelname)-8s|%(name)s|%(funcName)s|%(message)s"))
                self.__logger.addHandler(timeFH)

        except FileNotFoundError as e:
            print(f"CreonInfo.jsonファイルを見つかりません。 {str(e)}")
            self.__logger.error(f"C:\\StockBot\\logging.jsonファイルを見つかりません。: {str(e)}")

        except Exception as e:
            print(f"Exception occured Creon __setLogger : {str(e)}")
            self.__logger.error(f"Exception occured Creon __setLogger : {str(e)}")

        return

    def CheckCreonSystem(self):
        """CREONPLUSEシステムつながりチェックする"""
        # 管理者権限で実行したのか
        if not ctypes.windll.shell32.IsUserAnAdmin():
            self.__logger.info('check_creon_system() : admin user -> FAILED')
            return False

        # 繋げるのか
        if (self.__cpStatus.IsConnect == 0):
            self.__logger.info('check_creon_system() : connect to server -> FAILED')
            return False

        # 注文関連初期化 - 口座関連コードがある場合のみ
        if (self.__cpTradeUtil.TradeInit(0) != 0):
            self.__logger.info('check_creon_system() : init trade -> FAILED')
            return False

        self.__logger.info('CREONPLUSEシステムつながりチェック True')
        return True

    def __CheckandWait(self, type):
        remainCount = self.__cpStatus.GetLimitRemainCount(type)
        self.__logger.debug(f"残り要請Count : {remainCount}")
        # print(f"残り要請Count : {remainCount}")
        if remainCount <= 0:
            self.__logger.debug(f"データ要請待機 : {self.__cpStatus.LimitRequestRemainTime/1000}秒")
            print(f"データ要請待機 : {self.__cpStatus.LimitRequestRemainTime/1000}秒")
            time.sleep(self.__cpStatus.LimitRequestRemainTime / 1000)

    def __transformDataFrameDB(self, df, chartType):
        """
        株価情報をDBに書き込むためにDBテーブルに変換する。
        :param df: 変換対象DataFrame
        :param chartType: Chart区分("D","W","M","m")
        :return: 返還後のDataFrame
        """
        self.__logger.debug(f"chartType = {chartType}")
        f_weekday = lambda x: x.weekday()

        if chartType == "T":

            df['time'] = df['time'].astype(str)
            df['date'] = df['date'].astype(str)
            df['date'] = df['date'].str.cat(df['time'], sep=' ')
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d %H%M')
            df['week'] = df['date'].apply(f_weekday)
            df['diff'] = df['close'].diff(-1).fillna(0).astype(int)
            df = df[['dailyCount', 'date', 'week', 'open', 'high', 'low', 'close', 'diff', 'volume']]
            return df

        elif chartType == "m":

            df['time'] = df['time'].astype(str)
            df['date'] = df['date'].astype(str)
            df['date'] = df['date'].str.cat(df['time'], sep=' ')
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d %H%M')
            df['week'] = df['date'].apply(f_weekday)
            df['diff'] = df['close'].diff(-1).fillna(0).astype(int)
            df = df[['dailyCount', 'date', 'week', 'open', 'high', 'low', 'close', 'diff', 'volume']]
            return df

        elif chartType == "D":

            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
            df['week'] = df['date'].apply(f_weekday)
            df = df[['date', 'week', 'open', 'high', 'low', 'close', 'diff', 'volume']]
            return df

        elif chartType == "W":

            df['date'] = df['date'].astype(str)
            df['week'] = df['date'].str[-2:-1]
            df['date'] = pd.to_datetime(df['date'].str[:-2], format='%Y%m')
            df['diff'] = df['close'].diff(-1).fillna(0).astype(int)
            df = df[['date', 'week', 'open', 'high', 'low', 'close', 'diff', 'volume']]
            return df

        elif chartType == "M":

            df['date'] = df['date'].astype(str)
            df['date'] = pd.to_datetime(df['date'].str[:-2], format='%Y%m')
            df['diff'] = df['close'].diff(-1).fillna(0).astype(int)
            df = df[['date', 'open', 'high', 'low', 'close', 'diff', 'volume']]
            return df

        else:
            return None

    # Chart情報取得
    def __requestChartAmount(self, code, chartType=None, requestAmount=None, isDaily_m_T=True):
        """
        株価のChart情報取得を行う。行う際に最近順で取得する。
        :param code:(String) 株式コード
        :param chartType:(String) Chart区分("D","W","M","m","T")以外の場合Noneをリターンする。
        :param requestAmount:(Int) 取得数（Noneの場合、最後まで取得）
        :param isDaily_m_T:(Bool) 当日のデータを取得のとき、Chart区分がmまたはTの場合Ture,その以外はFalseに指定
        :return: None
        """
        dailyCountList = []  # 臨時に集めた番号
        stockDateList = []  # 日付
        stockTimeList = []  # 時間
        stockOpenList = []  # Open
        stockHighList = []  # High
        stockLowList = []  # Low
        stockCloseList = []  # Close
        stockDiffList = []  # Diff
        stockVolumeList = []  # Volume
        dailyCount = 0


        if chartType is None: # Chart区分
            chartType = self.__creonConfig['StockChart']['Chart区分']['value']
        if requestAmount is None: # Creonにある全データを取得する。
            requestAmount = self.__creonConfig['StockChart']['要請数']['value']
        if isDaily_m_T is True: #当日のデータだけを取得する。
            requestAmount = self.__creonConfig['StockChart']['要請数']['daily']

        pType1 = self.__creonConfig['StockChart']['要請区分']['type']
        pValue1 = self.__creonConfig['StockChart']['要請区分']['value']
        pType2 = self.__creonConfig['StockChart']['要請数']['type']
        pValue2 = requestAmount
        pType3 = self.__creonConfig['StockChart']['要請内容']['type']
        pValue3 = self.__creonConfig['StockChart']['要請内容']['内容List']
        pType4 = self.__creonConfig['StockChart']['Chart区分']['type']
        pValue4 = chartType
        pType5 = self.__creonConfig['StockChart']['ギャップ補正有無']['type']
        pValue5 = self.__creonConfig['StockChart']['ギャップ補正有無']['value']
        pType6 = self.__creonConfig['StockChart']['修正株株価適用有無']['type']
        pValue6 = self.__creonConfig['StockChart']['修正株株価適用有無']['value']
        pType7 = self.__creonConfig['StockChart']['取引量区分']['type']
        pValue7 = self.__creonConfig['StockChart']['取引量区分']['value']

        self.__logger.debug(f"code : {code}")
        self.__logger.debug(f"要請区分 : {pType1}")
        self.__logger.debug(f"要請区分value : {pValue1}")
        self.__logger.debug(f"要請数 : {pType2}")
        self.__logger.debug(f"要請数value : {pValue2}")
        self.__logger.debug(f"要請内容 : {pType3}")
        self.__logger.debug(f"要請内容value : {pValue3}")
        self.__logger.debug(f"Chart区分 : {pType4}")
        self.__logger.debug(f"Chart区分value : {pValue4}")
        self.__logger.debug(f"ギャップ補正有無 : {pType5}")
        self.__logger.debug(f"ギャップ補正有無value : {pValue5}")
        self.__logger.debug(f"修正株株価適用有無 : {pType6}")
        self.__logger.debug(f"修正株株価適用有無value : {pValue6}")
        self.__logger.debug(f"取引量区分 : {pType7}")
        self.__logger.debug(f"取引量区分value : {pValue7}")
        # code
        self.__objStockChart.SetInputValue(0, code)
        # 要請区分
        self.__objStockChart.SetInputValue(pType1, ord(pValue1))
        # 全要請数
        self.__objStockChart.SetInputValue(pType2, pValue2)
        # 要請内容
        self.__objStockChart.SetInputValue(pType3, pValue3)
        # 'Chart区分
        self.__objStockChart.SetInputValue(pType4, ord(pValue4))
        # ギャップ補正有無
        self.__objStockChart.SetInputValue(pType5, ord(pValue5))
        # 修正株株価適用有無
        self.__objStockChart.SetInputValue(pType6, ord(pValue6))
        # 取引量区分
        self.__objStockChart.SetInputValue(pType7, ord(pValue7))

        requestedAmount = 0  # 受信データ数累計
        result_DWM = pd.DataFrame()
        while pValue2 > requestedAmount:  # 要請数が受信データ累計より大きい場合、受信繰り返す。
            self.__CheckandWait(LT_NONTRADE_REQUEST)  # 要請可能か？チェック
            self.__objStockChart.BlockRequest()  # 受信したデータ以降のデータを要請する。

            curRequestedAmount = self.__objStockChart.GetHeaderValue(3)  # 受信した数
            if curRequestedAmount == 0:
                break

            self.__logger.debug(f"受信数: {curRequestedAmount}")
            requestedAmount += curRequestedAmount
            oldDate = self.__objStockChart.GetDataValue(0, 0)

            for i in range(curRequestedAmount):
                if pValue4 == 'T' or pValue4 == 'm':
                    newDate = self.__objStockChart.GetDataValue(0, i)
                    if oldDate == newDate:
                        dailyCount += 1
                        dailyCountList.append(dailyCount)
                        oldDate = self.__objStockChart.GetDataValue(0, i)

                        stockDateList.append(self.__objStockChart.GetDataValue(0, i))
                        stockTimeList.append(self.__objStockChart.GetDataValue(1, i))
                        stockOpenList.append(self.__objStockChart.GetDataValue(2, i))
                        stockHighList.append(self.__objStockChart.GetDataValue(3, i))
                        stockLowList.append(self.__objStockChart.GetDataValue(4, i))
                        stockCloseList.append(self.__objStockChart.GetDataValue(5, i))
                        stockDiffList.append(self.__objStockChart.GetDataValue(6, i))
                        stockVolumeList.append(self.__objStockChart.GetDataValue(7, i))

                    if oldDate != newDate or curRequestedAmount < MAX_REQUEST_NUM:

                        stockDateList = list(reversed(stockDateList))
                        stockTimeList = list(reversed(stockTimeList))
                        stockOpenList = list(reversed(stockOpenList))
                        stockHighList = list(reversed(stockHighList))
                        stockLowList = list(reversed(stockLowList))
                        stockCloseList = list(reversed(stockCloseList))
                        stockDiffList = list(reversed(stockDiffList))
                        stockVolumeList = list(reversed(stockVolumeList))

                        result = pd.DataFrame({'dailyCount': dailyCountList,
                                               'date': stockDateList,
                                               'time': stockTimeList,
                                               'open': stockOpenList,
                                               'high': stockHighList,
                                               'low': stockLowList,
                                               'close': stockCloseList,
                                               'diff': stockDiffList,
                                               'volume': stockVolumeList,
                                               }, index=[i for i in range(1, dailyCount + 1)])

                        oldDate = newDate
                        result_Tm = self.__transformDataFrameDB(result, chartType)
                        # for row in result_Tm.itertuples(name='count'):
                            #self.__logger.debug(row)

                        # ------------DB INSERT--------------
                        self.__dbu.replace_into_db(code, result_Tm, pValue4)
                        # ------------DB INSERT--------------

                        dailyCountList = []
                        stockDateList = []  # 日付
                        stockTimeList = []  # 時間
                        stockOpenList = []  # Open
                        stockHighList = []  # High
                        stockLowList = []  # Low
                        stockCloseList = []  # Close
                        stockDiffList = []  # Diff
                        stockVolumeList = []  # Volume
                        dailyCount = 0

                        if isDaily_m_T is True:
                            return None

                else: # Chart区分がT,m以外の場合
                    dailyCount += 1
                    dailyCountList.append(dailyCount)
                    stockDateList.append(self.__objStockChart.GetDataValue(0, i))
                    stockTimeList.append(self.__objStockChart.GetDataValue(1, i))
                    stockOpenList.append(self.__objStockChart.GetDataValue(2, i))
                    stockHighList.append(self.__objStockChart.GetDataValue(3, i))
                    stockLowList.append(self.__objStockChart.GetDataValue(4, i))
                    stockCloseList.append(self.__objStockChart.GetDataValue(5, i))
                    stockDiffList.append(self.__objStockChart.GetDataValue(6, i))
                    stockVolumeList.append(self.__objStockChart.GetDataValue(7, i))

            # --------------------------end for----------------------------------------
            if pValue4 != 'T' and pValue4 != 'm':
                stockDateList = list(reversed(stockDateList))
                stockTimeList = list(reversed(stockTimeList))
                stockOpenList = list(reversed(stockOpenList))
                stockHighList = list(reversed(stockHighList))
                stockLowList = list(reversed(stockLowList))
                stockCloseList = list(reversed(stockCloseList))
                stockDiffList = list(reversed(stockDiffList))
                stockVolumeList = list(reversed(stockVolumeList))

                result = pd.DataFrame({'dailyCount': dailyCountList,
                                       'date': stockDateList,
                                       'time': stockTimeList,
                                       'open': stockOpenList,
                                       'high': stockHighList,
                                       'low': stockLowList,
                                       'close': stockCloseList,
                                       'diff': stockDiffList ,
                                       'volume': stockVolumeList,
                                       }, index=[i for i in range(1, dailyCount + 1)])

                result_DWM = self.__transformDataFrameDB(result, chartType).append(result_DWM)

                dailyCountList = []
                stockDateList = []  # 日付
                stockTimeList = []  # 時間
                stockOpenList = []  # Open
                stockHighList = []  # High
                stockLowList = []  # Low
                stockCloseList = []  # Close
                stockDiffList = []  # Diff
                stockVolumeList = []  # Volume
                dailyCount = 0

            if curRequestedAmount < MAX_REQUEST_NUM:
                self.__logger.debug('Creonにある全データを取得した。')
                self.__logger.debug(f"code : {code} / 取得したデータ数 : {requestedAmount}")

                # 取得した結果がMAX_REQUEST_NUMより小さかったら目標まで取得したとみなしてwhile抜ける
                break  # end

        if pValue4 != 'T' and pValue4 != 'm':

            result_DWM['Index'] = [i for i in range(1, requestedAmount + 1)]
            result_DWM = result_DWM.set_index('Index')

            # for row in result_DWM.itertuples(name='count'):
            #     self.__logger.debug(row)

            # ------------DB INSERT--------------
            self.__dbu.replace_into_db(code, result_DWM, pValue4)
            # ------------DB INSERT--------------

        return None

    def __requestStockInfo(self):
        """
        株の情報を取得する
        :return:(pandas.DataFrame) 株情報
        """
        stockCodeList = []
        stockNameList = []

        # 株式コードリスト取得
        stockList1 = self.__objCpCodeMgr.GetStockListByMarket(1)  # 取引マーケット
        stockList2 = self.__objCpCodeMgr.GetStockListByMarket(2)  # KOSDAQ(コスダック)
        lenStockInfo = len(stockList1) + len(stockList2)

        for i, code in enumerate(stockList1):
            # secondCode = self.__objCpCodeMgr.GetStockSectionKind(code) # 副 区分コード
            # stdPrice = self.__objCpCodeMgr.GetStockStdPrice(code)      # 基準価額
            name = self.__objCpCodeMgr.CodeToName(code)  # 株名称
            stockCodeList.append(code)
            stockNameList.append(name)
            # self.__logger.info(f"code : {code} // company : {name}")

        for i, code in enumerate(stockList2):
            # secondCode = self.__objCpCodeMgr.GetStockSectionKind(code) # 副 区分コード
            # stdPrice = self.__objCpCodeMgr.GetStockStdPrice(code)      # 基準価額
            name = self.__objCpCodeMgr.CodeToName(code)  # 株名称
            stockCodeList.append(code)
            stockNameList.append(name)
            # self.__logger.info(f"code : {code} // company : {name}")

        dfStockInfo = pd.DataFrame({'code': stockCodeList,
                                    'company': stockNameList},
                                   index=[i for i in range(1, lenStockInfo + 1)])

        # ------------DB INSERT--------------
        self.__dbu.UpdateStockInfo(dfStockInfo=dfStockInfo)
        # ------------DB INSERT--------------

        return dfStockInfo

    def UpdateStockPrice(self, threadAmount, is_All=False, is_T=False):
        """
        本日の株価を取得します。
        :param threadAmount:(Int) スレッド数
        :param threadNum:(Int) スレッド番号
        :param is_All:(Bool) 全日付の株データを取得するかを選択(defalue-false:取得しなく当日のみ取得)
        :param is_T:(Bool) Tickデータを取得するかを選択(defalue-True:取得)
        :return:
        """

        self.__logger.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 本日の株価を取得します。")
        threadNum = self.__threadNum
        # if threadNum < 1:
        #     self.__logger.error(f"threadNum : {threadNum} ／は1以上にしてください。")
        #     return None

        #取得しようとする株コード
        dfStockInfo = self.__requestStockInfo()

        splitAmount = (int)(dfStockInfo.shape[0]/threadAmount)

        if threadNum == 1:
            df_targetStockInfo = dfStockInfo[:splitAmount]
        elif threadNum == threadAmount:
            df_targetStockInfo = dfStockInfo[(threadNum - 1) * splitAmount:]
        else:
            df_targetStockInfo = dfStockInfo[(threadNum - 1) * splitAmount:(threadNum) * splitAmount]

        targetStockCount = len(df_targetStockInfo)
        complitStockCount = 0

        if is_All is False:

            #当日のみ取得
            for stock in df_targetStockInfo.itertuples(name='stock'):
                self.__logger.debug(f"【当日】 code : {stock.code} // 取得スタート...")
                self.__requestChartAmount(stock.code, 'M', 1, False)
                self.__requestChartAmount(stock.code, 'W', 1, False)
                self.__requestChartAmount(stock.code, 'D', 1, False)
                self.__requestChartAmount(stock.code, 'm', 1, True)
                if is_T is True:
                    self.__requestChartAmount(stock.code, 'T', 1, True)
                complitStockCount += 1

                if complitStockCount % 5 == 0:
                    print(f"thread番号：【{threadNum}】"
                                       f" 【{(int)(100*(complitStockCount / targetStockCount))}%...】"
                                       f" 【完了({complitStockCount}/{targetStockCount})】")
                    self.__logger.info(f"thread番号：【{threadNum}】"
                                       f" 【{(int)(100*(complitStockCount / targetStockCount))}%...】"
                                       f" 【完了({complitStockCount}/{targetStockCount})】")

                self.__logger.info(f"【当日】 code : 【\t{stock.code}\t】 // 取得完了")
        else:
            #全日付取得
            for stock in df_targetStockInfo.itertuples(name='stock'):
                self.__logger.debug(f"【全日】 code : {stock.code} // 取得スタート...")
                self.__requestChartAmount(stock.code, 'M')
                self.__requestChartAmount(stock.code, 'W')
                self.__requestChartAmount(stock.code, 'D')
                self.__requestChartAmount(stock.code, 'm')
                if is_T is True:
                    self.__requestChartAmount(stock.code, 'T')
                complitStockCount += 1

                if complitStockCount % 3 == 0:
                    print(f"thread番号：【{threadNum}】"
                                       f" 【{(int)(100*(complitStockCount / targetStockCount))}%...】"
                                       f" 【完了({complitStockCount}/{targetStockCount})】")
                    self.__logger.info(f"thread番号：【{threadNum}】"
                                       f" 【{(int)(100*(complitStockCount / targetStockCount))}%...】"
                                       f" 【完了({complitStockCount}/{targetStockCount})】")

                self.__logger.info(f"【全日】 code : 【\t{stock.code}\t】 // 取得完了")
        return None

    #할것 완료%만들기 / DB넣고 / 배치파일로만들기 / 분까지만 하고 틱은 따로 필요한 주식만 받도록 하기

