import logging.handlers
import json
from datetime import datetime


class MyLogging:
    def __init__(self, class_name, thread_num=1):
        """
        thread_num(Int) thread番号によって格納するファイル名クラスName_Log_{thread_num}.logを決める
        :param class_name: 呼び出すクラスの名前（class.__name__）
        :param thread_num:
        """
        try:
            with open('C:/StockBot/Logging/logging.json', 'r', encoding='utf-8') as logging_json:
                self.__logging_info = json.load(logging_json)
                self.__thread_num = thread_num
                self.__className = class_name
                self.__set_logger()


        except FileNotFoundError as e:
            print(f"logging.jsonファイルを見つかりません。 {str(e)}")
            self.__logger.error(f"C:\\StockBot\\Logging\\logging.jsonファイルを見つかりません。: {str(e)}")


        except Exception as e:
            print(f"Exception occured MyLogging __init__ : {str(e)}")

    def __set_logger(self):
        """
        Logging初期化
        使うためにはlogging.jsonファイルに"[クラス名]"で定義が必要です。
        :return:
        """
        try:
            # split_tmp = str(self.__className).split('.')
            # __json_class_name = split_tmp[len(split_tmp)-1]
            self.__logger = logging.getLogger(self.__className)
            self.__logger.setLevel(logging.DEBUG)
            timeFH = logging.handlers.TimedRotatingFileHandler(
                filename=self.__logging_info[self.__className]['logFileNameArray'][self.__thread_num - 1],
                interval=1, backupCount=30, encoding='utf-8', when='MIDNIGHT')
            timeFH.setLevel(self.__logging_info[self.__className]['logLevel']['SET_VALUE'])
            timeFH.setFormatter(logging.Formatter(self.__logging_info['formatters']['logFileFormatter']['format']))
            self.__logger.addHandler(timeFH)

        except Exception as e:
            print(f"Exception occured MyLogging __set_logger : 【{str(e)}】")


    def write_log(self, naiyou, log_lv, is_con_print=True):
        """
        logを記録する。
        :param naiyou: 記録内容
        :param log_lv: 2:info, 3:warning, 4:error, 5:critical, その他:debug
        :return:
        """
        tmp = f"Class：【{self.__className}】、log内容：【{naiyou}】"

        if log_lv == 1:
            self.__logger.debug(tmp)
        elif log_lv == 2:
            self.__logger.info(tmp)
        elif log_lv == 3:
            self.__logger.warning(tmp)
        elif log_lv == 4:
            self.__logger.error(tmp)
        elif log_lv == 5:
            self.__logger.critical(tmp)
        else:
            self.__logger.debug(tmp)

        if is_con_print is True:
            tmnow = datetime.now().strftime('%Y-%m-%d %H:%M')
            print(f"【{tmnow}】：{tmp}")
