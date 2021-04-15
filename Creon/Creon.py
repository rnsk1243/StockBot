import time
import json
import ctypes
import win32com.client
import pandas as pd
from StockDB import DBUpdater as dbu
from Logging import MyLogging as mylog

LT_TRADE_REQUEST = 0
LT_NONTRADE_REQUEST = 1
LT_SUBSCRIBE = 2
MAX_REQUEST_NUM = 2221


class Creon:
    def __init__(self, thread_num=1):
        try:
            with open('C:/StockBot/Creon/creonConfig.json', 'r', encoding='utf-8') as creonConfig_json:
                self.__thread_num = thread_num
                self.__logger = mylog.MyLogging(class_name=Creon.__name__, thread_num=thread_num)
                self.__dbu = dbu.DBUpdater(self.__thread_num)

                self.__creonConfig = json.load(creonConfig_json)
                self.__cpStatus = win32com.client.Dispatch('CpUtil.CpCybos')
                self.__cpTradeUtil = win32com.client.Dispatch('CpTrade.CpTdUtil')

                self.__objCpCodeMgr = win32com.client.Dispatch("CpUtil.CpCodeMgr")
                self.__logger.write_log('Creon init 成功', log_lv=2)

        except FileNotFoundError as e:
            print(f"jsonファイルを見つかりません。 {str(e)}")

        except Exception as e:
            self.__logger.write_log(f"Exception occured Creon init : {str(e)}", log_lv=2)

    def check_creon_system(self):
        """CREONPLUSEシステムつながりチェックする"""
        # 管理者権限で実行したのか
        if not ctypes.windll.shell32.IsUserAnAdmin():
            self.__logger.write_log('check_creon_system() : admin user -> FAILED', log_lv=2)
            return False

        # 繋げるのか
        if (self.__cpStatus.IsConnect == 0):
            self.__logger.write_log('check_creon_system() : connect to server -> FAILED', log_lv=2)
            return False

        # 注文関連初期化 - 口座関連コードがある場合のみ
        if (self.__cpTradeUtil.TradeInit(0) != 0):
            self.__logger.write_log('check_creon_system() : init trade -> FAILED', log_lv=2)
            return False

        self.__logger.write_log('CREONPLUSEシステムつながりチェック True', log_lv=2)
        return True

    def __check_and_wait(self, type):
        remainCount = self.__cpStatus.GetLimitRemainCount(type)
        self.__logger.write_log(f"残り要請Count : {remainCount}", log_lv=1, is_con_print=False)
        # print(f"残り要請Count : {remainCount}")
        if remainCount <= 0:
            self.__logger.write_log(f"データ要請待機 : {self.__cpStatus.LimitRequestRemainTime/1000}秒", log_lv=2)
            time.sleep(self.__cpStatus.LimitRequestRemainTime / 1000)

    def __transform_data_frame_db(self, df, chartType):
        """
        株価情報をDBに書き込むためにDBテーブルに変換する。
        :param df: 変換対象DataFrame
        :param chartType: Chart区分("D","W","M","m")
        :return: 返還後のDataFrame
        """
        self.__logger.write_log(f"chartType = {chartType}", log_lv=1, is_con_print=False)
        f_weekday = lambda x: x.weekday()

        if chartType == "T":

            df['time'] = df['time'].astype(str)
            df['date'] = df['date'].astype(str)
            df['date'] = df['date'].str.cat(df['time'], sep=' ')
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d %H%M')
            df['week'] = df['date'].apply(f_weekday)
            df['diff'] = df['close'].diff(-1).fillna(0).astype(int)
            df = df[['date', 'week', 'open', 'high', 'low', 'close', 'diff', 'volume']]
            # df = df[['dailyCount', 'date', 'week', 'open', 'high', 'low', 'close', 'diff', 'volume']]
            return df

        elif chartType == "m":

            df['time'] = df['time'].astype(str)
            df['date'] = df['date'].astype(str)
            df['date'] = df['date'].str.cat(df['time'], sep=' ')
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d %H%M')
            df['week'] = df['date'].apply(f_weekday)
            df['diff'] = df['close'].diff(-1).fillna(0).astype(int)
            df = df[['date', 'week', 'open', 'high', 'low', 'close', 'diff', 'volume']]
            return df

        elif chartType == "D":

            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
            df['week'] = df['date'].apply(f_weekday)
            df['diff'] = df['close'].diff(-1).fillna(0).astype(int)
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

    def __set_request_obj(self, code, chartType, requestAmount):
        """
        通信オブジェクトを初期化する。
        :param code 株コード
        :param chartType: グラフタイプ（'M','W','D','m','T'）
        :param requestAmount: 要請数
        :return: 通信オブジェクト
        """

        objStockChart = win32com.client.Dispatch('CpSysDib.StockChart')

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

        self.__logger.write_log(f"code : {code}", log_lv=1, is_con_print=False)
        self.__logger.write_log(f"要請区分 : {pType1}", log_lv=1, is_con_print=False)
        self.__logger.write_log(f"要請区分value : {pValue1}", log_lv=1, is_con_print=False)
        self.__logger.write_log(f"要請数 : {pType2}", log_lv=1, is_con_print=False)
        self.__logger.write_log(f"要請数value : {pValue2}", log_lv=1, is_con_print=False)
        self.__logger.write_log(f"要請内容 : {pType3}", log_lv=1, is_con_print=False)
        self.__logger.write_log(f"要請内容value : {pValue3}", log_lv=1, is_con_print=False)
        self.__logger.write_log(f"Chart区分 : {pType4}", log_lv=1, is_con_print=False)
        self.__logger.write_log(f"Chart区分value : {pValue4}", log_lv=1, is_con_print=False)
        self.__logger.write_log(f"ギャップ補正有無 : {pType5}", log_lv=1, is_con_print=False)
        self.__logger.write_log(f"ギャップ補正有無value : {pValue5}", log_lv=1, is_con_print=False)
        self.__logger.write_log(f"修正株株価適用有無 : {pType6}", log_lv=1, is_con_print=False)
        self.__logger.write_log(f"修正株株価適用有無value : {pValue6}", log_lv=1, is_con_print=False)
        self.__logger.write_log(f"取引量区分 : {pType7}", log_lv=1, is_con_print=False)
        self.__logger.write_log(f"取引量区分value : {pValue7}", log_lv=1, is_con_print=False)
        # code
        objStockChart.SetInputValue(0, code)
        # 要請区分
        objStockChart.SetInputValue(pType1, ord(pValue1))
        # 全要請数
        objStockChart.SetInputValue(pType2, pValue2)
        # 要請内容
        objStockChart.SetInputValue(pType3, pValue3)
        # 'Chart区分
        objStockChart.SetInputValue(pType4, ord(pValue4))
        # ギャップ補正有無
        objStockChart.SetInputValue(pType5, ord(pValue5))
        # 修正株株価適用有無
        objStockChart.SetInputValue(pType6, ord(pValue6))
        # 取引量区分
        objStockChart.SetInputValue(pType7, ord(pValue7))

        return objStockChart

    def request_chart_day(self, code, is_all=True):
        """
        月、週データを取得
        :param code: 株コード
        :param is_all:全日 or 一日
        :return: None
        """

        chartType = 'D'
        if is_all is True:
            goal_amount = 9999999
        else:
            goal_amount = 2220

        objStockChart = self.__set_request_obj(code, 'D', goal_amount)

        requestedAmount = 0  # 受信データ数累計
        while goal_amount > requestedAmount:  # 要請数が受信データ累計より大きい場合、受信繰り返す。
            self.__check_and_wait(LT_NONTRADE_REQUEST)  # 要請可能か？チェック
            objStockChart.BlockRequest()  # 受信したデータ以降のデータを要請する。

            curRequestedAmount = objStockChart.GetHeaderValue(3)  # 受信した数
            if curRequestedAmount == 0:
                break

            self.__logger.write_log(f"受信数: {curRequestedAmount}", log_lv=1, is_con_print=False)

            stockDateList = []  # 日付
            stockTimeList = []  # 時間
            stockOpenList = []  # Open
            stockHighList = []  # High
            stockLowList = []  # Low
            stockCloseList = []  # Close
            stockDiffList = []  # Diff
            stockVolumeList = []  # Volume

            for i in range(curRequestedAmount):

                stockDateList.append(objStockChart.GetDataValue(0, i))
                stockTimeList.append(objStockChart.GetDataValue(1, i))
                stockOpenList.append(objStockChart.GetDataValue(2, i))
                stockHighList.append(objStockChart.GetDataValue(3, i))
                stockLowList.append(objStockChart.GetDataValue(4, i))
                stockCloseList.append(objStockChart.GetDataValue(5, i))
                stockDiffList.append(objStockChart.GetDataValue(6, i))
                stockVolumeList.append(objStockChart.GetDataValue(7, i))

            # --------------------------end for----------------------------------------

            result = pd.DataFrame({'date': stockDateList,
                                   'time': stockTimeList,
                                   'open': stockOpenList,
                                   'high': stockHighList,
                                   'low': stockLowList,
                                   'close': stockCloseList,
                                   'diff': stockDiffList,
                                   'volume': stockVolumeList,
                                   })

            result = self.__transform_data_frame_db(result, chartType)

            # ------------DB INSERT--------------
            self.__dbu.replace_into_db(code, result, chartType)
            # ------------DB INSERT--------------
            requestedAmount += curRequestedAmount


            if curRequestedAmount < MAX_REQUEST_NUM:
                self.__logger.write_log('Creonにある全データを取得した。', log_lv=2, is_con_print=False)
                self.__logger.write_log(f"code : {code} / 取得したデータ数 : {requestedAmount}", log_lv=2, is_con_print=False)

                # 取得した結果がMAX_REQUEST_NUMより小さかったら目標まで取得したとみなしてwhile抜ける
                break  # end

        return None

    def request_chart_all(self, code, chartType):
        """
        月、週、分の全日データを取得
        :param code: 株コード
        :param chartType:'M','W','m'
        :return: None
        """

        goal_amount = 9999999

        objStockChart = self.__set_request_obj(code, chartType, goal_amount)

        requestedAmount = 0  # 受信データ数累計
        while goal_amount > requestedAmount:  # 要請数が受信データ累計より大きい場合、受信繰り返す。
            self.__check_and_wait(LT_NONTRADE_REQUEST)  # 要請可能か？チェック
            objStockChart.BlockRequest()  # 受信したデータ以降のデータを要請する。

            curRequestedAmount = objStockChart.GetHeaderValue(3)  # 受信した数
            if curRequestedAmount == 0:
                break

            self.__logger.write_log(f"受信数: {curRequestedAmount}", log_lv=1, is_con_print=False)

            stockDateList = []  # 日付
            stockTimeList = []  # 時間
            stockOpenList = []  # Open
            stockHighList = []  # High
            stockLowList = []  # Low
            stockCloseList = []  # Close
            stockDiffList = []  # Diff
            stockVolumeList = []  # Volume

            for i in range(curRequestedAmount):

                stockDateList.append(objStockChart.GetDataValue(0, i))
                stockTimeList.append(objStockChart.GetDataValue(1, i))
                stockOpenList.append(objStockChart.GetDataValue(2, i))
                stockHighList.append(objStockChart.GetDataValue(3, i))
                stockLowList.append(objStockChart.GetDataValue(4, i))
                stockCloseList.append(objStockChart.GetDataValue(5, i))
                stockDiffList.append(objStockChart.GetDataValue(6, i))
                stockVolumeList.append(objStockChart.GetDataValue(7, i))

            # --------------------------end for----------------------------------------

            result = pd.DataFrame({'date': stockDateList,
                                   'time': stockTimeList,
                                   'open': stockOpenList,
                                   'high': stockHighList,
                                   'low': stockLowList,
                                   'close': stockCloseList,
                                   'diff': stockDiffList,
                                   'volume': stockVolumeList,
                                   })

            result = self.__transform_data_frame_db(result, chartType)

            # ------------DB INSERT--------------
            self.__dbu.replace_into_db(code, result, chartType)
            # ------------DB INSERT--------------
            requestedAmount += curRequestedAmount

            if curRequestedAmount < MAX_REQUEST_NUM:
                self.__logger.write_log('Creonにある全データを取得した。', log_lv=2, is_con_print=False)
                self.__logger.write_log(f"code : {code} / 取得したデータ数 : {requestedAmount}", log_lv=2, is_con_print=False)

                # 取得した結果がMAX_REQUEST_NUMより小さかったら目標まで取得したとみなしてwhile抜ける
                break  # end

        return None

    def request_stock_info(self):
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
            self.__logger.write_log(f"code : {code} // company : {name}", log_lv=1, is_con_print=False)

        for i, code in enumerate(stockList2):
            # secondCode = self.__objCpCodeMgr.GetStockSectionKind(code) # 副 区分コード
            # stdPrice = self.__objCpCodeMgr.GetStockStdPrice(code)      # 基準価額
            name = self.__objCpCodeMgr.CodeToName(code)  # 株名称
            stockCodeList.append(code)
            stockNameList.append(name)
            self.__logger.write_log(f"code : {code} // company : {name}", log_lv=1, is_con_print=False)

        dfStockInfo = pd.DataFrame({'code': stockCodeList,
                                    'company': stockNameList},
                                   index=[i for i in range(1, lenStockInfo + 1)])

        # ------------DB INSERT--------------
        self.__dbu.UpdateStockInfo(dfStockInfo=dfStockInfo)
        # ------------DB INSERT--------------

        return dfStockInfo

    def split_df_stock(self, dfStockInfo, threadAmount):
        """
        thread数で株データframeを分ける
        :param dfStockInfo: データframe
        :param threadAmount: thread数
        :return: 分けたデータframe
        """


        thread_num = self.__thread_num
        splitAmount = (int)(dfStockInfo.shape[0] / threadAmount)

        if thread_num == 1:
            result = dfStockInfo[:splitAmount]
        elif thread_num == threadAmount:
            result = dfStockInfo[(thread_num - 1) * splitAmount:]
        else:
            result = dfStockInfo[(thread_num - 1) * splitAmount:(thread_num) * splitAmount]

        return result