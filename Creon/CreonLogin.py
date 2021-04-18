from pywinauto import application
import time
import os, json
from Logging import MyLogging as mylog
import win32com.client

class CreonLogin:
    def __init__(self):
        try:
            self.__logger = mylog.MyLogging(class_name=CreonLogin.__name__)
            self.__cpStatus = win32com.client.Dispatch('CpUtil.CpCybos')
        except Exception as e:
            self.__logger.write_log(f"Exception occured CreonLogin init : {str(e)}", log_lv=5)

    def check_login_creon(self):
        """
        creonにログインされているか確認
        :return: True:ログイン状態 False:非ログイン状態
        """
        if (self.__cpStatus.IsConnect == 0):
            self.__logger.write_log('check_creon_system() : IsConnect == 0', log_lv=1)
            return False
        else:
            return True

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
                self.__logger.write_log('Creonログイン完了', log_lv=2)

        except FileNotFoundError as e:
            self.__logger.write_log(f"C:\\StockBot\\creonInfo.jsonファイルを見つかりません。 {str(e)}", log_lv=4)
        except Exception as e:
            self.__logger.write_log(f"Exception occured LoginCreon : {str(e)}", log_lv=5)