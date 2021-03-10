from pywinauto import application
import time
import os,json
import ctypes
import win32com.client
from logging import config, getLogger
import pandas as pd

class Creon:
    def __init__(self):
        try:
            with open('C:\StockBot\creonInfo.json', 'r', encoding='utf-8') as creonInfo_json, \
                    open('C:\StockBot\logging.json', 'r', encoding='utf-8') as logging_json:
                creonInfo = json.load(creonInfo_json)
                config.dictConfig(json.load(logging_json))
                self.__logger = getLogger(__name__)
                self.__id = creonInfo['id']
                self.__pwd = creonInfo['pwd']
                self.__pwdcert = creonInfo['pwdcert']
                self.__path = creonInfo['path']
                self.__cpStatus = win32com.client.Dispatch('CpUtil.CpCybos')
                self.__cpTradeUtil = win32com.client.Dispatch('CpTrade.CpTdUtil')
                self.__objStockChart = win32com.client.Dispatch('CpSysDib.StockChart')

        except FileNotFoundError as e:
            self.__logger.error(f"reonInfo.jsonファイルを見つかりません。 {str(e)}")


        except Exception as e:
            self.__logger.error(f"Exception occured Creon init : {str(e)}")


    def __LoginCreon(self):
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

    # 차트 요청 - 기간 기준으로
    def RequestFromTo(self, code, fromDate, toDate):
        print(code, fromDate, toDate)
        # 연결 여부 체크
        bConnect = self.__cpStatus.IsConnect
        if (bConnect == 0):
            print("PLUS가 정상적으로 연결되지 않음. ")
            return False

        self.__objStockChart.SetInputValue(0, code)  # 종목코드
        self.__objStockChart.SetInputValue(1, ord('1'))  # 기간으로 받기
        self.__objStockChart.SetInputValue(2, toDate)  # To 날짜
        self.__objStockChart.SetInputValue(3, fromDate)  # From 날짜
        # self.objStockChart.SetInputValue(4, 500)  # 최근 500일치
        self.__objStockChart.SetInputValue(5, [0, 2, 3, 4, 5, 8])  # 날짜,시가,고가,저가,종가,거래량
        self.__objStockChart.SetInputValue(6, ord('D'))  # '차트 주기 - 일간 차트 요청
        self.__objStockChart.SetInputValue(9, ord('1'))  # 수정주가 사용
        self.__objStockChart.BlockRequest()

        rqStatus = self.__objStockChart.GetDibStatus()
        rqRet = self.__objStockChart.GetDibMsg1()
        print("통신상태", rqStatus, rqRet)
        if rqStatus != 0:
            exit()

        len = self.__objStockChart.GetHeaderValue(3)

        df = pd.DataFrame()

        for i in range(len):
            print(self.__objStockChart.GetDataValue(0, i))
            print(self.__objStockChart.GetDataValue(1, i))
            print(self.__objStockChart.GetDataValue(2, i))
            print(self.__objStockChart.GetDataValue(3, i))
            print(self.__objStockChart.GetDataValue(4, i))
            print(self.__objStockChart.GetDataValue(5, i))
            # df['date'] = self.__objStockChart.GetDataValue(0, i)
            # df['open'] = self.__objStockChart.GetDataValue(1, i)
            # df['high'] = self.__objStockChart.GetDataValue(2, i)
            # df['low'] = self.__objStockChart.GetDataValue(3, i)
            # df['close'] = self.__objStockChart.GetDataValue(4, i)
            # #df['diff'] = abs(self.__objStockChart.GetDataValue(4, i) - self.__objStockChart.GetDataValue(1, i))
            # df['volume'] = self.__objStockChart.GetDataValue(5, i)

        #print(len)
        return df
