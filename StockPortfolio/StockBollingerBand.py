import matplotlib.pyplot as plt
from StockDB import Analyzer

mk = Analyzer.MarketDB()
df = mk.get_stock_safe_new_data('카카오') #mk.get_daily_price('삼성전자', '2018-05-05')

df['MA20'] = df['close'].rolling(window=20).mean()  # ①平均
df['stddev'] = df['close'].rolling(window=20).std()  # ②標準偏差
df['upper'] = df['MA20'] + (df['stddev'] * 2)  # ③
df['lower'] = df['MA20'] - (df['stddev'] * 2)  # ④
df['PB'] = (df['close'] - df['lower']) / (df['upper'] - df['lower'])
df['bandwidth'] = (df['upper'] - df['lower']) / df['MA20'] * 100
df = df[19:]  # ⑤

plt.figure(figsize=(9, 8))
plt.subplot(3,1,1)
plt.plot(df.index, df['close'], color='#0000ff', label='Close')  # ⑥
plt.plot(df.index, df['upper'], 'r--', label='Upper band')  # ⑦
plt.plot(df.index, df['MA20'], 'k--', label='Moving average 20')
plt.plot(df.index, df['lower'], 'c--', label='Lower band')
plt.fill_between(df.index, df['upper'], df['lower'], color='0.9')  # ⑧
plt.title('SAMSUNG Bollinger Band (20 day, 2 std)')
plt.grid(True)
plt.legend(loc='best')

plt.subplot(3,1,2)
plt.plot(df.index, df['PB'], color='b', label='%B')
plt.grid(True)
plt.legend(loc='best')

plt.subplot(3,1,3)
plt.plot(df.index, df['bandwidth'], color='m', label='bandwidth')
plt.grid(True)
plt.legend(loc='best')

plt.show()
