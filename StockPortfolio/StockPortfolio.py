import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from StockDB import Analyzer, DBUpdater
import sys
sys.path.append('C:\StockBot')

mk = Analyzer.MarketDB()
stocks = ['삼성전자', 'SK하이닉스', '현대자동차', 'NAVER']
df = pd.DataFrame()
for s in stocks:
    df[s] = mk.get_daily_price(s, '2020-05-01', '2021-02-19')['close']

daily_ret = df.pct_change() #일간변동률
annual_ret = daily_ret.mean() * 252 #연간 수익률 = 일간변동률의평균*개장일수
daily_cov = daily_ret.cov() #일간리스크
annual_cov = daily_cov * 252 #연간리스크

port_ret = []
port_risk = []
port_weights = []
sharpe_ratio = []

for _ in range(20000):
    weights = np.random.random(len(stocks))
    weights /= np.sum(weights)

    returns = np.dot(weights, annual_ret)
    risk = np.sqrt(np.dot(weights.reshape(1,4).T.reshape(-1), np.dot(annual_cov, weights)))

    port_ret.append(returns)
    port_risk.append(risk)
    port_weights.append(weights)
    sharpe_ratio.append(returns/risk)

portfolio = {'Returns': port_ret, 'Risk': port_risk, 'Sharpe': sharpe_ratio}
for i, s in enumerate(stocks):
    portfolio[s] = [weight[i] for weight in port_weights]
df = pd.DataFrame(portfolio)
df = df[['Returns', 'Risk', 'Sharpe'] + [s for s in stocks]]

max_sharpe = df.loc[df['Sharpe']==df['Sharpe'].max()]
min_risk = df.loc[df['Risk']==df['Risk'].min()]

print(f"maxSharpe={max_sharpe}")
print(f"min_risk={min_risk}")

df.plot.scatter(x='Risk', y='Returns', c='Sharpe', cmap='viridis',
    edgecolors='k', figsize=(11,7), grid=True)  # ⑤
plt.scatter(x=max_sharpe['Risk'], y=max_sharpe['Returns'], c='r',
    marker='*', s=300)  # ⑥
plt.scatter(x=min_risk['Risk'], y=min_risk['Returns'], c='r',
    marker='X', s=200)  # ⑦
plt.title('Portfolio Optimization')
plt.xlabel('Risk')
plt.ylabel('Expected Returns')
plt.show()