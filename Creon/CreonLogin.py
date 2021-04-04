from pywinauto import application
import time
import os, json
from logging import config, getLogger

class CreonLogin:
    def __init__(self):
        try:
            with open('C:/StockBot/logging.json', 'r', encoding='utf-8') as logging_json:
                loggingInfo = json.load(logging_json)
                config.dictConfig(loggingInfo)
                self.__logger = getLogger(__name__)

        except FileNotFoundError as e:
            self.__logger.error(f"C:\\StockBot\\logging.jsonファイルを見つかりません。 {str(e)}")

        except Exception as e:
            self.__logger.error(f"Exception occured CreonLogin init : {str(e)}")

    def LoginCreon(self):
        """
        Creonログインする。
        :return:
        """
        try:
            with open('C:/StockBot/creonInfo.json', 'r', encoding='utf-8') as creonInfo_json:
                creonInfo = json.load(creonInfo_json)

                os.system('taskkill /IM coStarter* /F /T')
                os.system('taskkill /IM CpStart* /F /T')
                os.system('wmic process where "name like \'%coStarter%\'" call terminate')
                os.system('wmic process where "name like \'%CpStart%\'" call terminate')
                time.sleep(5)

                app = application.Application()
                app.start(f"{creonInfo['path']} /prj:cp /id:{creonInfo['id']} /pwd:{creonInfo['pwd']} /pwdcert:{creonInfo['pwdcert']} /autostart")
                time.sleep(60)
                self.__logger.info('Creonログイン完了')

        except FileNotFoundError as e:
            print(f"C:\\StockBot\\creonInfo.jsonファイルを見つかりません。 {str(e)}")
            self.__logger.error(f"C:\\StockBot\\creonInfo.jsonファイルを見つかりません。 {str(e)}")

        except Exception as e:
            print(f"Exception occured LoginCreon : {str(e)}")
            self.__logger.error(f"Exception occured LoginCreon : {str(e)}")