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
        time.sleep(90)
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

    # Chart情報取得
    def RequestChartAmount(self, code, chartType = None, requestAmount = None):
        """
        株価のChart情報取得を行う。行う際に最近順で取得する。
        :param code: 株式コード
        :param chartType: Chart区分
        :param requestAmount: 取得数（Noneの場合、最後まで取得）
        :return: pandas.DataFrame
        """
        result = pd.DataFrame()
        stockDateList = []
        stockTimeList = []
        stockOpenList = []
        stockHighList = []
        stockLowList = []
        stockCloseList = []
        stockDiffList = []
        stockVolumeList = []

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

        requestedAmount = 0
        while pValue2 > requestedAmount:
            self.__CheckandWait(LT_NONTRADE_REQUEST)
            self.__objStockChart.BlockRequest()
            # rqStatus = self.__objStockChart.GetDibStatus()
            # rqRet = self.__objStockChart.GetDibMsg1()
            # print("통신상태", rqStatus, rqRet)
            # if rqStatus != 0:
            #     exit()

            curRequestedAmount = self.__objStockChart.GetHeaderValue(3)  # 수신개수
            if curRequestedAmount <= 1:
                self.__logger.info(f"code : {code} / 가져온 데이터 총 갯수 : {requestedAmount}")
                break
            else:
                self.__logger.info(f"수신갯수: {curRequestedAmount}")
                requestedAmount += curRequestedAmount

            for i in range(curRequestedAmount):
                stockDateList.append(self.__objStockChart.GetDataValue(0, i))
                stockTimeList.append(self.__objStockChart.GetDataValue(1, i))
                stockOpenList.append(self.__objStockChart.GetDataValue(2, i))
                stockHighList.append(self.__objStockChart.GetDataValue(3, i))
                stockLowList.append(self.__objStockChart.GetDataValue(4, i))
                stockCloseList.append(self.__objStockChart.GetDataValue(5, i))
                stockDiffList.append(self.__objStockChart.GetDataValue(6, i))
                stockVolumeList.append(self.__objStockChart.GetDataValue(7, i))

        result = pd.DataFrame({'date':stockDateList,
                               'time':stockTimeList,
                               'open':stockOpenList,
                               'high':stockHighList,
                               'low': stockLowList,
                               'close': stockCloseList,
                               'diff': stockDiffList,
                               'volume': stockVolumeList,
                               }, index=[i for i in range(1, requestedAmount+1)])

        return result

    """株の情報を取得する"""
    def SearchStockInfo(self):

        stockCodeList = []
        stockNameList = []

        # 종목코드 리스트 구하기
        stockList1 = self.__objCpCodeMgr.GetStockListByMarket(1)  # 거래소
        stockList2 = self.__objCpCodeMgr.GetStockListByMarket(2)  # 코스닥
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