import sys
sys.path.append('../')
import backtrader as bt
from datetime import datetime

class BackTest(bt.Strategy):
    def __init__(self, arg_list):
        try:
            self.order = None
            self.buyprice = None
            self.buycomm = None
            self.__logger = arg_list[0]
            self.__mode = arg_list[1]
            self.__ets = arg_list[2]
            self.__macd_stoch_data = arg_list[3] # macd_stoch_data.index = pd.to_datetime(macd_stoch_data['date'])
            self.__macd_buy = arg_list[4]
            self.__macd_sell = arg_list[5]
            self.__slow_d_buy = arg_list[6]
            self.__slow_d_sell = arg_list[7]
            self.rsi = bt.indicators.RSI_SMA(self.data.close, period=21)
            self.target_macd = 0
            # logger.write_log(f'{self} init 成功', log_lv=2)

        except Exception as e:
            self.__logger.write_log(f"Exception occured {self} init : {str(e)}", log_lv=5)

    def notify_order(self, order):  # ①
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:  # ②
             if order.isbuy():
                 # logger.write_log(f'BUY  : 주가 {order.executed.price:,.0f}, '
                 #         f'수량 {order.executed.size:,.0f}, '
                 #         f'수수료 {order.executed.comm:,.0f}, '
                 #         f'자산 {cerebro.broker.getvalue():,.0f}', log_lv=2)
                 self.buyprice = order.executed.price
                 self.buycomm = order.executed.comm
             # else:
             #     logger.write_log(f'SELL : 주가 {order.executed.price:,.0f}, '
             #             f'수량 {order.executed.size:,.0f}, '
             #             f'수수료 {order.executed.comm:,.0f}, '
             #             f'자산 {cerebro.broker.getvalue():,.0f}', log_lv=2)
             self.bar_executed = len(self)
        elif order.status in [order.Canceled]:
             self.__logger.write_log('ORDER CANCELD', log_lv=2)
        elif order.status in [order.Margin]:
             self.__logger.write_log('ORDER MARGIN', log_lv=2)
        elif order.status in [order.Rejected]:
             self.__logger.write_log('ORDER REJECTED', log_lv=2)

        self.order = None

    def next(self):
        split_date = str(self.datas[0].datetime.date(0)).split('-')
        #print(split_date)
        if split_date is None or len(split_date) < 3:
            self.__logger.write_log(f"split_date is None or len(split_date) < 3", log_lv=3)
            return
        else:
            now_data = datetime(int(split_date[0]), int(split_date[1]), int(split_date[2]))

        if now_data in self.__macd_stoch_data.index:
            temp_df = self.__macd_stoch_data.loc[now_data]

            hist_inclination_avg = temp_df['hist_inclination_avg']
            slow_d = temp_df['slow_d']
            is_buy_sell = None  # 買う；True　売る；False 何もしない；None
            print_info_list = [temp_df['code'],
                               temp_df['date'],
                               temp_df['close'],
                               temp_df['delta_hist_sec_dpc'],
                               hist_inclination_avg]

            if self.__mode == 1:
                is_buy_sell = self.__ets.is_buy_sell_nomal(print_info_list=print_info_list,
                                                           macd_sec_dpc=hist_inclination_avg,
                                                           slow_d=slow_d,
                                                           slow_d_buy=self.__slow_d_buy,
                                                           slow_d_sell=self.__slow_d_sell)
            elif self.__mode == 2:
                is_buy_sell = self.__ets.is_buy_sell_learning(
                                                        macd_sec_dpc=hist_inclination_avg,
                                                        macd_buy=self.__macd_buy,
                                                        macd_sell=self.__macd_sell)
            elif self.__mode == 3:
                is_buy_sell = self.__ets.is_buy_sell_challenge(
                                                        print_info_list=print_info_list,
                                                        macd_sec_dpc=hist_inclination_avg,
                                                        slow_d=slow_d,
                                                        macd_buy=self.__macd_buy,
                                                        macd_sell=self.__macd_sell)
            elif self.__mode == 4:
                if self.rsi < 30:
                    is_buy_sell = True
                if self.rsi > 70:
                    is_buy_sell = False
            else:
                return

            if not self.position:
                if is_buy_sell is True:
                    self.order = self.buy()
            else:
                if is_buy_sell is False:
                    self.order = self.sell()

            self.target_macd += 1

        else:
            self.__logger.write_log(f"index No = {now_data}", log_lv=3)
            return

    def log(self, txt, dt=None):  # ③
        dt = self.datas[0].datetime.date(0)
        self.__logger.write_log(f'[{dt.isoformat()}] {txt}', log_lv=2)


# if __name__ == '__main__':
#     start_time = time.time()
#     print(f"time = {time.time() - start_time}")

