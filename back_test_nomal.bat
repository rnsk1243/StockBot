::arg1 "1"=노말모드 // "4"=RSI
::arg2 몇개월전부터테스트할것인가(개월단위) 예12개월전부터
::arg3 몇개월전까지테스트할것인가(개월단위) 예3개월동안  
::arg4 "1"=표그리기
::arg5 "표를그릴 주식이름"
::arg6 시세가 몇%까지 떨어져야 살 것인가 20 
::arg7 시세가 몇%까지 오르면 팔 것인가 80

color a
cd C:\StockBot\StockPortfolio
python C:\StockBot\StockPortfolio\MainBackTest.py "1" "3" "0" "1" "A005930" "20" "80"
:: 노말모드 // 3개월전부터 // 0개월동안 // 표안그림 // 주식이름없음
