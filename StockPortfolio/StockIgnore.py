import json
from Logging import MyLogging as mylog

class StockIgnore:
    def __init__(self, thread_num=1):
        try:
            with open('C:/StockBot/ignore_stock.json', 'r', encoding='utf-8') as ignore_stock_json:
                self.__logger = mylog.MyLogging(class_name=StockIgnore.__name__, thread_num=thread_num)
                self.__ignore_stock = json.load(ignore_stock_json)
                self.__ignore_update_price_month_list = \
                    self.__ignore_stock['ignore_stock_list']['update_price']['month']
                self.__ignore_update_price_week_list = \
                    self.__ignore_stock['ignore_stock_list']['update_price']['week']
                self.__ignore_update_price_day_list = \
                    self.__ignore_stock['ignore_stock_list']['update_price']['day']
                self.__ignore_update_price_min_list = \
                    self.__ignore_stock['ignore_stock_list']['update_price']['min']
                self.__ignore_update_price_tick_list = \
                    self.__ignore_stock['ignore_stock_list']['update_price']['tick']

                self.__logger.write_log(f'{self} init 成功', log_lv=2)

        except FileNotFoundError as e:
            print(f"jsonファイルを見つかりません。 {str(e)}")

        except Exception as e:
            self.__logger.write_log(f"Exception occured {self} init : {str(e)}", log_lv=2)

    def is_ignore_update_price(self, chart_type, target_stock_code):
        """
        株価取得を除外する株のか確認
        :param chart_type:["month","week","day","min","tick"]
        :param target_stock_code: 株コード("A005930")
        :return: bool(True:除外対象、False:取得対象、None:例外)
        """

        if chart_type == "tick":
            result = target_stock_code in self.__ignore_update_price_tick_list

        elif chart_type == "min":
            result = target_stock_code in self.__ignore_update_price_min_list

        elif chart_type == "day":
            result = target_stock_code in self.__ignore_update_price_day_list

        elif chart_type == "week":
            result = target_stock_code in self.__ignore_update_price_week_list

        elif chart_type == "month":
            result = target_stock_code in self.__ignore_update_price_month_list

        else:
            self.__logger.write_log(f"chartType:【{chart_type}】は扱っていません。", log_lv=3)
            result = None

        return result
