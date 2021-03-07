from pywinauto import application
import time
import os,json
import ctypes
import win32com.client
from logging import config, getLogger

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






