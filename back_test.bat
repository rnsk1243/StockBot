::arg1 "2"=최적값
::arg2 몇개월전부터테스트할것인가(개월단위)
::arg3 몇개월동안테스트할것인가(개월단위)
::arg4 "1"=표그리기
::arg5 "표를그릴 주식이름"
::arg6 "0"=시뮬안함 // "1"=최적값을구하고시뮬까지함
::arg7 "1"=stock_sell_buy_score.jsonを初期化する
::arg8 MACD범위
::arg9 몇번반복까지하다가포기할것인가

color a
cd C:\StockBot\StockPortfolio
python C:\StockBot\StockPortfolio\MainBackTest.py "2" "24" "12" "0" "" "1" "1" "100" "2000"
:: 최적값 // 6개월전부터 // 3개월동안 // 표안그림 // 주식이름없음 // 최적&시뮬 // json초기화 // 범위 -100~100 // 2000번까지하다포기
