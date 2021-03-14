import pandas as pd
from bs4 import BeautifulSoup
import pymysql, json
import requests
from datetime import datetime
import sys
sys.path.append('C:\StockBot')

class DBUpdater:  
    def __init__(self):
        try:
            """【..\*.json】は最上位フォルダから一階層下のフォルダから実行の基準"""
            with open('C:\StockBot\dbInfo.json', 'r', encoding='utf-8') as dbInfo_json, \
                    open('C:\StockBot\StockDB\sql.json', 'r', encoding='utf-8') as sql_json, \
                    open('C:\StockBot\stockUrl_info.json', 'r', encoding='utf-8') as url_json:
                dbInfo = json.load(dbInfo_json)
                self.__sql = json.load(sql_json)
                self.__url = json.load(url_json)
                host = dbInfo['host']
                user = dbInfo['user']
                password = dbInfo['password']
                dbName = dbInfo['db']
                charset = dbInfo['charset']

            """생성자: MariaDB 연결 및 종목코드 딕셔너리 생성"""
            self.__conn = pymysql.connect(host=host, user=user,
                                          password=password, db=dbName, charset=charset)

            with self.__conn.cursor() as curs:
                curs.execute(self.__sql['CREATE_001'])
                curs.execute(self.__sql['CREATE_002'])
            self.__conn.commit()
            self.__codes = {}

        except FileNotFoundError as e:
            print(f"dbInfo.jsonファイルを見つかりません。 {str(e)}")

        except Exception as e:
            print('Exception occured DBUpdater init:', str(e))
               
    def __del__(self):
        """소멸자: MariaDB 연결 해제"""
        self.__conn.close() 
     
    # def __read_krx_code(self):
    #     """KRX로부터 상장기업 목록 파일을 읽어와서 데이터프레임으로 반환"""
    #     krx = pd.read_html(self.__url['URL001'], header=0)[0]
    #     krx = krx[['종목코드', '회사명']]
    #     krx = krx.rename(columns={'종목코드': 'code', '회사명': 'company'})
    #     krx.code = krx.code.map('{:06d}'.format)
    #     return krx

    def UpdateStockInfo(self, dfStockInfo):
        """
            종목코드를 company_info 테이블에 업데이트 한 후 딕셔너리에 저장
            株項目一覧をDBに書き込む　
        　　- dfStockInfo : 株項目DataFrame
        """
        with self.__conn.cursor() as curs:
            curs.execute(self.__sql['SELECT_002'])
            rs = curs.fetchone()
            today = datetime.today().strftime('%Y-%m-%d')
            if rs[0] == None or rs[0].strftime('%Y-%m-%d') < today:
                for idx in range(len(dfStockInfo)):
                    code = dfStockInfo.code.values[idx]
                    company = dfStockInfo.company.values[idx]
                    curs.execute(self.__sql['REPLACE_001'].format(code, company, today))
                    self.__codes[code] = company
                    tmnow = datetime.now().strftime('%Y-%m-%d %H:%M')
                    print(f"[{tmnow}] #{idx+1:04d} REPLACE INTO company_info "\
                        f"VALUES ({code}, {company}, {today})")
                self.__conn.commit()
                print('종목코드 commit 완료')
            else:
                df = pd.read_sql(self.__sql['SELECT_001'], self.__conn)
                for idx in range(len(df)):
                    self.__codes[df['code'].values[idx]] = df['company'].values[idx]

        print('종목코드 딕셔너리에 저장 완료')
        self.__codes_keys = list(self.__codes.keys())
        self.__codes_values = list(self.__codes.values())

    def __getLastPage(self, code):
        try:
            headers = \
                {'User-Agent': self.__url['UserAgent']}
            with requests.get(self.__url['URL002'].format(code), headers=headers) as res:
                html = BeautifulSoup(res.content, "lxml")
                pgrr = html.find("td", class_="pgRR")
                if pgrr is None:
                    return None
                s = str(pgrr.a["href"]).split('=')
                lastpage = s[-1]
        except Exception as e:
            print('Exception occured __getLastPage:', str(e))
            return None

        return int(lastpage)

    def __getLastDate(self, code, lastPage):
        try:
            headers = \
                {'User-Agent': self.__url['UserAgent']}
            with requests.get(self.__url['URL003'].format(code,lastPage), headers=headers) as res:
                html = BeautifulSoup(res.content, "lxml")
                lastDateList = html.find_all("span", class_="tah p10 gray03")
                if len(lastDateList) == 0:
                    return None
                reLastDateList = []
                for ldate in lastDateList:
                    reLastDateList.append(ldate.text.replace('.','-'))
        except Exception as e:
            print('Exception occured __getLastDate:', str(e))
            return None

        return min(reLastDateList)

    """인수 데이터프레임을 대상으로 데이터를 더 받아야 하는지 확인"""
    def getNotCompleteCompanyList(self, df):
        try:
            resultList = []
            for idx, row in df.iterrows():
                print(f"{idx}번째 진행중...", end="\r")
                lastPage = self.__getLastPage(row[0])
                if lastPage is None:
                    lastPage = 1 #상장 한지 얼마 안된 주는 1page밖에 없다. "맨끝"page가 없음
                lastDate = self.__getLastDate(row[0],lastPage)
                if lastDate is not None:
                    lastDate = self.__getLastDate(row[0], lastPage).split('-')
                    lastDate = datetime(int(lastDate[0]), int(lastDate[1]), int(lastDate[2])).date()
                else:
                    print(f"상장code = {row[0]}의lastDate가None임")
                    continue

                if row[1] > lastDate: #DB에서 가져온 값이 더 빠른 날짜이면 결과리스트에 넣기
                    resultList.append(row[0])
                else:
                    continue

        except Exception as e:
            print('Exception occured __getNotCompleteCompanyList:', str(e))
            return None

        return resultList

    """pages_to_fetch가None일경우 전체를 읽음"""
    def __read_naver(self, code, pages_to_fetch=None):
        """네이버에서 주식 시세를 읽어서 데이터프레임으로 반환"""
        try:
            headers = \
                {'User-Agent': self.__url['UserAgent']}
            if pages_to_fetch is None or pages_to_fetch > 1:
                lastpage = self.__getLastPage(code)
                if pages_to_fetch is None:
                    pages = lastpage #전체
                else:
                    pages = min(lastpage, pages_to_fetch) #전체or지정한 페이지 수
            else:
                pages = 1

            df = pd.DataFrame()
            for page in range(1, pages + 1):
                pg_url = '{}&page={}'.format(self.__url['URL002'].format(code), page)
                with requests.get(pg_url, headers=headers) as resTemp:
                    df = df.append(pd.read_html(resTemp.content, header=0)[0])
                tmnow = datetime.now().strftime('%Y-%m-%d %H:%M')
                print('[{}] {} ({}) : {:04d}/{:04d} pages are downloading...'.
                    format(tmnow, self.__codes[code], code, page, pages), end="\r")
            df = df.rename(columns={'날짜':'date','종가':'close','전일비':'diff'
                ,'시가':'open','고가':'high','저가':'low','거래량':'volume'})
            df['date'] = df['date'].replace('.', '-')
            df = df.dropna()
            df[['close', 'diff', 'open', 'high', 'low', 'volume']] = df[['close',
                'diff', 'open', 'high', 'low', 'volume']].astype(int)
            df = df[['date', 'open', 'high', 'low', 'close', 'diff', 'volume']]
        except Exception as e:
            print('Exception occured __read_naver:', str(e))
            return None
        return df

    def __replace_into_db(self, df, code):
        """네이버에서 읽어온 주식 시세를 DB에 REPLACE"""
        count = 0
        try:
            with self.__conn.cursor() as curs:
                for r in df.itertuples():
                    curs.execute(self.__sql['REPLACE_002'].format(
                        code, r.date, r.open, r.high, r.low, r.close, r.diff, r.volume))
                    count += 1
                self.__conn.commit()
                print('[{}] #{:04d} {} ({}) : {} rows > REPLACE INTO daily_' \
                      'price [OK]'.format(datetime.now().strftime('%Y-%m-%d%H:%M'),
                                          count, self.__codes[code], code, len(df)))
        except Exception as e:
            print('Exception occured __replace_into_db:', str(e))
            return None

    """page가None일겨우 전체를 가져옴"""
    def execute_one(self, company, page=None):

        if company in self.__codes_keys:
            pass
        elif company in self.__codes_values:
            idx = self.__codes_values.index(company)
            company = self.__codes_keys[idx]
        else:
            print(f"ValueError: Code({company}) doesn't exist.")
            return

        df = self.__read_naver(company, page)
        self.__replace_into_db(df, company)

    def getPriceOldData(self):
        df = pd.read_sql(self.__sql['SELECT_003'], self.__conn)
        df = df[['code', 'date']]
        return df

    """모든 상장코드 반환"""
    def getCodeKeyListALL(self):
        return self.__codes_keys