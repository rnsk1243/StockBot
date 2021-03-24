from pywinauto import application
import time
import os,json
import ctypes
import win32com.client
from logging import config, getLogger
import pandas as pd

LT_TRADE_REQUEST = 0
LT_NONTRADE_REQUEST = 1
LT_SUBSCRIBE = 2
MAX_REQUEST_NUM = 2221

class Creon:
    def __init__(self):
        try:
            with open('C:\StockBot\creonInfo.json', 'r', encoding='utf-8') as creonInfo_json, \
                    open('C:\StockBot\logging.json', 'r', encoding='utf-8') as logging_json, \
                    open('C:\StockBot\Creon\creonConfig.json', 'r', encoding='utf-8') as creonConfig_json:
                creonInfo = json.load(creonInfo_json)
                config.dictConfig(json.load(logging_json))
                self.__creonConfig = json.load(creonConfig_json)
                self.__logger = getLogger(__name__)
                self.__id = creonInfo['id']
                self.__pwd = creonInfo['pwd']
                self.__pwdcert = creonInfo['pwdcert']
                self.__path = creonInfo['path']
                self.__cpStatus = win32com.client.Dispatch('CpUtil.CpCybos')
                self.__cpTradeUtil = win32com.client.Dispatch('CpTrade.CpTdUtil')
                self.__objStockChart = win32com.client.Dispatch('CpSysDib.StockChart')
                self.__objCpCodeMgr = win32com.client.Dispatch("CpUtil.CpCodeMgr")

        except FileNotFoundError as e:
            self.__logger.error(f"reonInfo.jsonファイルを見つかりません。 {str(e)}")


        except Exception as e:
            self.__logger.error(f"Exception occured Creon init : {str(e)}")


    def LoginCreon(self):
        os.system('taskkill /IM coStarter* /F /T')
        os.system('taskkill /IM CpStart* /F /T')
        os.system('wmic process where "name like \'%coStarter%\'" call terminate')
        os.system('wmic process where "name like \'%CpStart%\'" call terminate')
        time.sleep(5)

        app = application.Application()
        app.start(f"{self.__path} /prj:cp /id:{self.__id} /pwd:{self.__pwd} /pwdcert:{self.__pwdcert} /autostart")
        time.sleep(60)
        self.__logger.info('Creonログイン完了')

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
        self.__logger.info(f"limitType : {type} / 잔여카운트 : {remainCount}")
        if remainCount <= 0:
            self.__logger.info(f"시세/주문 요청대기 : {self.__cpStatus.LimitRequestRemainTime}")
            time.sleep(self.__cpStatus.LimitRequestRemainTime / 1000)

    def __transformDataFrameDB(self, df, chartType):
        """
        株価情報をDBに書き込むためにDBテーブルに変換する。
        :param df: 変換対象DataFrame
        :param chartType: Chart区分("D","W","M","m")
        :return: 返還後のDataFrame
        """
        self.__logger.info(f"chartType = {chartType}")
        f_weekday = lambda x: x.weekday()

        if chartType == "T":

            df['time'] = df['time'].astype(str)
            df['date'] = df['date'].astype(str)
            df['date'] = df['date'].str.cat(df['time'], sep=' ')
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d %H%M')
            df['weekday'] = df['date'].apply(f_weekday)
            df['diff'] = df['close'].diff(-1).fillna(0).astype(int)
            df = df[['dailyCount', 'date', 'weekday', 'open', 'high', 'low', 'close', 'diff', 'volume']]
            return df

        elif chartType == "m":

            df['time'] = df['time'].astype(str)
            df['date'] = df['date'].astype(str)
            df['date'] = df['date'].str.cat(df['time'], sep=' ')
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d %H%M')
            df['weekday'] = df['date'].apply(f_weekday)
            df['diff'] = df['close'].diff(-1).fillna(0).astype(int)
            df = df[['dailyCount', 'date', 'weekday', 'open', 'high', 'low', 'close', 'diff', 'volume']]
            return df

        elif chartType == "D":

            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
            df['weekday'] = df['date'].apply(f_weekday)
            df = df[['date', 'weekday', 'open', 'high', 'low', 'close', 'diff', 'volume']]
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
    def RequestChartAmount(self, code, chartType = None, requestAmount = None):
        """
        株価のChart情報取得を行う。行う際に最近順で取得する。
        :param code: 株式コード
        :param chartType: Chart区分("D","W","M","m","T")以外の場合Noneをリターンする。
        :param requestAmount: 取得数（Noneの場合、最後まで取得）
        :return: pandas.DataFrame
        """

        dailyCountList = []  #一つの種類に対して1日分の株株価の数番号(１番号がスタートの株価)
        dailyCountList2 = [] #要請数の通りに取得した株価の数番号
        stockDateList = []   #日付
        stockTimeList = []   #時間
        stockOpenList = []   #Open
        stockHighList = []   #High
        stockLowList = []    #Low
        stockCloseList = []  #Close
        stockDiffList = []   #Diff
        stockVolumeList = [] #Volume
        dailyCount = 0

        if chartType is None:
            chartType = self.__creonConfig['StockChart']['Chart区分']['value']
        if requestAmount is None:
            requestAmount = self.__creonConfig['StockChart']['要請数']['value']

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

        self.__logger.info(f"code : {code}")
        self.__logger.info(f"要請区分 : {pType1}")
        self.__logger.info(f"要請区分value : {pValue1}")
        self.__logger.info(f"要請数 : {pType2}")
        self.__logger.info(f"要請数value : {pValue2}")
        self.__logger.info(f"要請内容 : {pType3}")
        self.__logger.info(f"要請内容value : {pValue3}")
        self.__logger.info(f"Chart区分 : {pType4}")
        self.__logger.info(f"Chart区分value : {pValue4}")
        self.__logger.info(f"ギャップ補正有無 : {pType5}")
        self.__logger.info(f"ギャップ補正有無value : {pValue5}")
        self.__logger.info(f"修正株株価適用有無 : {pType6}")
        self.__logger.info(f"修正株株価適用有無value : {pValue6}")
        self.__logger.info(f"取引量区分 : {pType7}")
        self.__logger.info(f"取引量区分value : {pValue7}")
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

        requestedAmount = 0 #受信データ数累計
        while pValue2 > requestedAmount: #要請数が受信データ累計より大きい場合、受信繰り返す。
            self.__CheckandWait(LT_NONTRADE_REQUEST) #要請可能か？チェック
            self.__objStockChart.BlockRequest() #受信したデータ以降のデータを要請する。
            # rqStatus = self.__objStockChart.GetDibStatus()
            # rqRet = self.__objStockChart.GetDibMsg1()
            # print("통신상태", rqStatus, rqRet)
            # if rqStatus != 0:
            #     exit()

            curRequestedAmount = self.__objStockChart.GetHeaderValue(3)  # 受信した数
            self.__logger.info(f"受信数: {curRequestedAmount}")
            requestedAmount += curRequestedAmount
            oldDate = self.__objStockChart.GetDataValue(0, 0)
            tempList = []
            isNextDate = False
            for i in range(curRequestedAmount):
                if pValue4 == 'T' or pValue4 == 'm':
                    newDate = self.__objStockChart.GetDataValue(0, i)
                    if oldDate == newDate:
                        dailyCount += 1
                    else:
                        oldDate = newDate
                        dailyCount = 1
                        isNextDate = True
                    tempList.append(dailyCount)

                stockDateList.append(self.__objStockChart.GetDataValue(0, i))
                stockTimeList.append(self.__objStockChart.GetDataValue(1, i))
                stockOpenList.append(self.__objStockChart.GetDataValue(2, i))
                stockHighList.append(self.__objStockChart.GetDataValue(3, i))
                stockLowList.append(self.__objStockChart.GetDataValue(4, i))
                stockCloseList.append(self.__objStockChart.GetDataValue(5, i))
                stockDiffList.append(self.__objStockChart.GetDataValue(6, i))
                stockVolumeList.append(self.__objStockChart.GetDataValue(7, i))
            #end for

            tempList = list(reversed(tempList))  # リスト要素逆順にする。1,2,3,...,99,..
            if isNextDate is False:
                dailyCountList = tempList + dailyCountList  # リスト結合
            else:
                #日替りの場合
                tempList1 = tempList[:tempList.index(1) + 1]
                tempList2 = tempList[tempList.index(1) + 1:]
                dailyCountList = tempList2 + dailyCountList  # リスト結合
                dailyCountList2 = dailyCountList2 + dailyCountList
                dailyCountList = tempList1

            if curRequestedAmount < MAX_REQUEST_NUM:
                #取得した結果がMAX_REQUEST_NUMより小さかったら目標まで取得したとみなしてwhile抜ける
                break #end while

        if pValue4 == 'T' or pValue4 == 'm':
            dailyCountList2 = dailyCountList2 + dailyCountList
            result = pd.DataFrame({'dailyCount': dailyCountList2,
                                   'date': stockDateList,
                                   'time': stockTimeList,
                                   'open': stockOpenList,
                                   'high': stockHighList,
                                   'low': stockLowList,
                                   'close': stockCloseList,
                                   'diff': stockDiffList,
                                   'volume': stockVolumeList,
                                   }, index=[i for i in range(1, requestedAmount + 1)])
        else:
            result = pd.DataFrame({'date': stockDateList,
                                   'time': stockTimeList,
                                   'open': stockOpenList,
                                   'high': stockHighList,
                                   'low': stockLowList,
                                   'close': stockCloseList,
                                   'diff': stockDiffList,
                                   'volume': stockVolumeList,
                                   }, index=[i for i in range(1, requestedAmount + 1)])

        self.__logger.info(f"code : {code} / 取得したデータ数 : {requestedAmount}")
        return self.__transformDataFrameDB(result, chartType)

    def SearchStockInfo(self):
        """
        株の情報を取得する
        :return:
        """
        stockCodeList = []
        stockNameList = []

        # 株式コードリスト取得
        stockList1 = self.__objCpCodeMgr.GetStockListByMarket(1)  # 取引マーケット
        stockList2 = self.__objCpCodeMgr.GetStockListByMarket(2)  # KOSDAQ(コスダック)
        lenStockInfo = len(stockList1) + len(stockList2)

        for i, code in enumerate(stockList1):
            #secondCode = self.__objCpCodeMgr.GetStockSectionKind(code) # 副 区分コード
            #stdPrice = self.__objCpCodeMgr.GetStockStdPrice(code)      # 基準価額
            name = self.__objCpCodeMgr.CodeToName(code) # 株名称
            stockCodeList.append(code)
            stockNameList.append(name)
            self.__logger.info(f"code : {code} // company : {name}")

        for i, code in enumerate(stockList2):
            #secondCode = self.__objCpCodeMgr.GetStockSectionKind(code) # 副 区分コード
            #stdPrice = self.__objCpCodeMgr.GetStockStdPrice(code)      # 基準価額
            name = self.__objCpCodeMgr.CodeToName(code) # 株名称
            stockCodeList.append(code)
            stockNameList.append(name)
            self.__logger.info(f"code : {code} // company : {name}")

        dfStockInfo = pd.DataFrame({'code':stockCodeList,
                                    'company':stockNameList},
                                   index=[i for i in range(1,lenStockInfo+1)])
        return dfStockInfo