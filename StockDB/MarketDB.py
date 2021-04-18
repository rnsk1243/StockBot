import pandas as pd
import pymysql, json
from datetime import datetime
from datetime import timedelta
import re
import sys
from Logging import MyLogging as mylog
import numpy as np
sys.path.append('C:\StockBot')

class MarketDB:
    def __init__(self):
        try:
            """【..\*.json】は最上位フォルダから一階層下のフォルダから実行の基準"""
            with open('C:\StockBot\dbInfo.json', 'r', encoding='utf-8') as dbInfo_json, \
                    open('C:\StockBot\StockDB\sql.json', 'r', encoding='utf-8') as sql_json:
                self.__logger = mylog.MyLogging(class_name=MarketDB.__name__)
                dbInfo = json.load(dbInfo_json)
                self.__sql = json.load(sql_json)
                host = dbInfo['host']
                user = dbInfo['user']
                password = dbInfo['password']
                dbName = dbInfo['db']
                charset = dbInfo['charset']

            """생성자: MariaDB 연결 및 종목코드 딕셔너리 생성"""
            self.__conn = pymysql.connect(host=host, user=user,
                                          password=password, db=dbName, charset=charset)
            self.__codes = {}
            self.__get_comp_info()


        except FileNotFoundError as e:
            print(f"dbInfo.jsonファイルを見つかりません。 {str(e)}")
            self.__logger.write_log(f"C:\\StockBot\\StockDB\\sql.jsonまたは、"
                                    f"C:\\StockBot\\dbInfo.jsonファイルを見つかりません。 {str(e)}", log_lv=4)

        except Exception as e:
            self.__logger.write_log(f"Exception occured MarketDB init : {str(e)}", log_lv=5)
        
    def __del__(self):
        """소멸자: MariaDB 연결 해제"""
        self.__conn.close()

    def __get_comp_info(self):
        """company_info 테이블에서 읽어와서 codes에 저장"""
        krx = pd.read_sql(self.__sql['SELECT_001'], self.__conn)
        for idx in range(len(krx)):
            self.__codes[krx['code'].values[idx]] = krx['company'].values[idx]
        self.__codes_keys = list(self.__codes.keys())
        self.__codes_values = list(self.__codes.values())

    def __index_to_datetime(self, df):
        """dataframeのインデックスをdatetime64[ns]型にする
            - df : daily_priceテーブルからselect結果のdataframe
        """
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df['date'] = df.index

        if 'week' in df.columns:
            df = df[['code', 'date', 'week', 'open', 'high', 'low', 'close', 'diff', 'volume']]
        else:
            df = df[['code', 'date', 'open', 'high', 'low', 'close', 'diff', 'volume']]

        return df

    def __date_normalization(self, date):
        """
        年月日をDBで使える形に正規化する。(YYYY-MM-DD)
        :param date: "4桁の年に"
        :return: 正常：正規化した日付(string) 、異常：None
        """
        date_split = re.split('\D+', date)
        if date[0] == '':
            date_split = date_split[1:]
        year = int(date_split[0])
        month = int(date_split[1])
        day = int(date_split[2])
        if year < 1900 or year > 2200:
            self.__logger.write_log(f"ValueError: start_year({year:d}) is wrong.", log_lv=3)
            return
        if month < 1 or month > 12:
            self.__logger.write_log(f"ValueError: start_month({month:d}) is wrong.", log_lv=3)
            return
        if day < 1 or day > 31:
            self.__logger.write_log(f"ValueError: start_day({day:d}) is wrong.", log_lv=3)
            return
        normal_date = f"{year:04d}-{month:02d}-{day:02d}"
        return normal_date

    def __set_search_default(self, chart_type):
        """
        検索をかけるdefault日付を決める
        :param chart_type: Chart区分("D","W","M","m")
        :return: タプル（sql,start_date） 異常:None
        """

        if chart_type == "D":
            sql = 'SELECT_004'
            start_date = datetime.today() - timedelta(days=365)
            is_sort = False
            method_name = 'section_daily_day_all'
        elif chart_type == "m":
            sql = 'SELECT_005'
            start_date = datetime.today() - timedelta(days=30)
            is_sort = False
            method_name = 'section_m'
        elif chart_type == "M":
            sql = 'SELECT_006'
            start_date = datetime.today() - timedelta(days=365*30)
            is_sort = False
            method_name = 'section_M'
        elif chart_type == "T":
            sql = 'SELECT_007'
            start_date = datetime.today() - timedelta(days=1)
            is_sort = False
            method_name = 'section_T'
        elif chart_type == "W":
            sql = 'SELECT_008'
            start_date = datetime.today() - timedelta(days=365*10)
            is_sort = True
            method_name = 'section_W'
        else:
            self.__logger.write_log(f"ValueError: chart_type({chart_type}) doesn't exist.", log_lv=3)
            return None

        self.__logger.write_log(f"start_date is initialized to {start_date.strftime('%Y-%m-%d %H:%M:%S')}", log_lv=1)
        return sql, start_date, is_sort, method_name

    def __df_week_sort(self, df):
        """
        date,weekを昇順に整列する。
        :param df: 整列対象のデータプライム
        :return: 正常：dataframe、異常：None
        """
        if df is None:
            return None
        if 'week' in df.columns and 'date' in df.columns:
            df = df.sort_values(['date', 'week'])
            df = df.reset_index(drop=True)
        else:
            self.__logger.write_log(f"up_downカラムが無いので、株価チェックできない。",log_lv=3)
            return None

        return df

    def check_stock_price(self, stock_name, chart_type, df):
        """
        株価をチェックする。
        株価分割、株価併合が発生したか
        :param stock_name: 株名前
        :param chart_type: Chart区分("D","W","M","m")
        :param df: stock dataframe
        :return: True:株価正常 False:株価分割併合発生 None:異常
        """
        if df is None:
            return None
        if 'up_down' in df.columns:
            for row in df.itertuples(name='stock'):
                if np.absolute(row.up_down) > 30:  # 変化率30％超えたか
                    stock_code = self.get_stock_code(stock_name=stock_name)
                    if stock_code is None:
                        self.__logger.write_log(f"株価異常です。株名前：{stock_name} "
                                                f"内容：【{row}】"
                                                f"/ json追記失敗（株名前異常）", log_lv=4)
                        return False

                    try:
                        with open('C:/StockBot/update_price_stock_config.json', 'r', encoding='utf-8') as upsc_json:
                            upsc = json.load(upsc_json)
                            def_val = self.__set_search_default(chart_type=chart_type)
                            method_name = def_val[3]
                            update_stock_list = upsc[method_name]['update_stock_list']
                            update_stock_list.append(stock_code)
                            upsc[method_name]['update_stock_list'] = update_stock_list

                        with open('C:/StockBot/update_price_stock_config.json', 'w', encoding='utf-8') as w_upsc_json:
                            json.dump(upsc, w_upsc_json, indent="\t")
                            self.__logger.write_log(f"株価異常です。株名前：{stock_name} "
                                                    f"内容：【{row}】"
                                                    f" json追記完了", log_lv=3)
                            return False

                    except FileNotFoundError as e:
                        self.__logger.write_log(f"update_price_stock_configファイルを見つかりません。 {str(e)}", log_lv=4)

                    except Exception as e:
                        self.__logger.write_log(f"Exception occured check_stock_price : {str(e)}", log_lv=5)

                    return False

            self.__logger.write_log(f"株価正常 株名前：{stock_name}、chart区分：{chart_type}", log_lv=1)
            return True

        else:
            self.__logger.write_log(f"up_downカラムが無いので、株価チェックできない。",log_lv=3)
            return None

    def get_stock_code(self, stock_name):
        """
        株の名前で株コードを取得する。
        :param stock_name: 株のハングル名前
        :return: 正常：株コード(string) or 異常：None
        """
        if stock_name in self.__codes_keys:
            return stock_name
        elif stock_name in self.__codes_values:
            idx = self.__codes_values.index(stock_name)
            code = self.__codes_keys[idx]
        else:
            self.__logger.write_log(f"ValueError: stock_name({stock_name}) doesn't exist.", log_lv=3)
            return None

        return code

    def add_diff(self, df):
        """
        diffカラムを追加＆更新する。closeカラムが必要です。
        :param df: 株価データプライム
        :return: 株価データプライム（dataframe） 異常：None
        """
        if df is None:
            return None
        if 'close' in df.columns:
            df['diff'] = df['close'].diff(1).fillna(0).astype(int)
        else:
            self.__logger.write_log(f"カラム（close）が無い",log_lv=3)
            return None

        return df

    def add_up_down(self, df):
        """
        up_downカラムを追加＆更新する。close,diffカラムが必要です。
        :param df: 株価データプライム
        :return: 株価データプライム（dataframe） 異常：None
        """
        if df is None:
            return None
        if 'close' in df.columns and 'diff' in df.columns:
            diff_val = df['diff'].values
            close_val = df['close'].values
            if diff_val.shape == close_val.shape:
                diff_val = np.roll(diff_val, -1)  # 1個ずらす。
                up_down_ndarray = ((diff_val / close_val) * 100).round(1)  # 上がり下がり%値
                up_down_ndarray = np.roll(up_down_ndarray,1)  # ずらしたことを元通りにする。
                up_down_ndarray[0] = 0.0
                df['up_down'] = up_down_ndarray
            else:
                self.__logger.write_log(f"shapeが合わないため、分けられません。"
                                        f"diffのshape{diff_val.shape},"
                                        f"closeのshape{close_val.shape}", log_lv=3)
                return None
        else:
            self.__logger.write_log(f"カラム（close, diff）が無い",log_lv=3)
            return None

        return df

    def get_stock_price(self, code, chart_type="D", start_date=None, end_date=None):
        """
        株価を取得する。
        :param code: 株コードまたは株の名前
        :param chart_type: Chart区分("D","W","M","m") デフォルト値："D"
        :param start_date: 検索スタート日　デフォルト：本日から1年前
        :param end_date: 検索End日　デフォルト：本日
        :return: dataframe
        """
        def_val = self.__set_search_default(chart_type=chart_type)
        sql_str = def_val[0]
        is_sort = def_val[2]

        if start_date is None:
            start_date = def_val[1]
        else:
            start_date = self.__date_normalization(start_date)

        if end_date is None:
            end_date = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
            self.__logger.write_log(f"end_date is initialized to {end_date}", log_lv=1)
        else:
            end_date = self.__date_normalization(end_date)

        self.__logger.write_log(f"検索期間：{start_date}～{end_date}", log_lv=1)
         
        #codes_keys = list(self.__codes.keys())
        #codes_values = list(self.__codes.values())

        if code in self.__codes_keys:
            pass
        else:
            code = self.get_stock_code(stock_name=code)

        df = pd.read_sql(self.__sql[sql_str].format(
            code, start_date, end_date), self.__conn)

        if is_sort is True:
            df = self.__df_week_sort(df)

        df = self.add_diff(df)
        df = self.add_up_down(df)
        check_result = self.check_stock_price(stock_name=code, chart_type=chart_type, df=df)

        if check_result is None:
            self.__logger.write_log(f"株価取得異常発生", log_lv=4)
        elif check_result is False:
            self.__logger.write_log(f"株コード：{code}は分割または併合発生のため、アップデート必要", log_lv=3)
        else:
            self.__logger.write_log(f"【正常】株コード：{code} / 取得完了。取得件数：{len(df)}", log_lv=1)
            return df