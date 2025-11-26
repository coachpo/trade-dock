import app.longbridgeRealTrading
import base64
from io import BytesIO
import json
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf
import ta
import mplfinance as mpf



def plot_trading_strategy_yield_curve(df):
    mc = mpf.make_marketcolors(up='#ffffff', down='#ffffff', inherit=True)
    s = mpf.make_mpf_style(marketcolors=mc)
    ap = mpf.make_addplot(df['Relative'], type='line', secondary_y=False, color='#2fff9c', width=0.5)

    buy_markers = df['Close'].where(df['Direction'] == 'Buy')
    sell_markers = df['Close'].where(df['Direction'] == 'Sell')

    ap_buy = mpf.make_addplot(buy_markers, type='scatter', markersize=35, marker='^', color='#2fff9c')
    ap_sell = mpf.make_addplot(sell_markers, type='scatter', markersize=35, marker='v', color='#ff2f92')

    addplot = [ap, ap_buy, ap_sell]
    fig, axes = mpf.plot(df, type='candle', style=s, addplot=addplot, returnfig=True, volume=False, figsize=(10, 6), **(dict(warn_too_much_data=len(df) + 1)))

    axes[0].grid(False)
    axes[0].spines['top'].set_visible(False)
    axes[0].spines['right'].set_visible(False)
    axes[0].spines['bottom'].set_visible(False)
    axes[0].spines['left'].set_visible(False)

    axes[0].set_xticklabels([])
    axes[0].set_xticks([])
    axes[0].yaxis.set_label_text("")
    axes[0].tick_params(axis='y', which='both', length=0, colors='#ffffff')  # Set the color of y-axis numbers

    figure_file = BytesIO()
    fig.savefig(figure_file, format='svg', transparent=True, bbox_inches='tight')
    figure_file.seek(0)
    plt.close(fig)

    return base64.b64encode(figure_file.getvalue()).decode('utf-8')


def backtest_all_trading_strategies(form_data):
    ticker = form_data.get('ticker')
    date_start = form_data.get('date_start')
    date_end = form_data.get('date_end')
    interval = form_data.get('interval')
    strategy = form_data.get('strategy')
    holding = int(form_data.get('holding'))
    holding_min = int(form_data.get('holding_min'))
    holding_max = int(form_data.get('holding_max'))
    cash = float(form_data.get('cash'))
    quantity = int(form_data.get('quantity'))

    df = yf.download(ticker, start=date_start, end=date_end, interval=interval, progress=False)



    if strategy == 'grid':
        df = grid_trading_strategy(
            price_ceiling=float(form_data.get('price_ceiling')),
            price_floor=float(form_data.get('price_floor')),
            rise=float(form_data.get('rise')),
            fall=float(form_data.get('fall')),
            holding=holding,
            holding_min=holding_min,
            holding_max=holding_max,
            cash=cash,
            quantity=quantity,
            df=df
        )
    elif strategy == 'macd':
        df = macd_trading_strategy(
            holding=holding,
            holding_min=holding_min,
            holding_max=holding_max,
            cash=cash,
            quantity=quantity,
            crsi_lower=float(form_data.get('crsi_lower')),
            crsi_upper=float(form_data.get('crsi_upper')),
            df=df
        )
    elif strategy == 'twap':
        print('twap')
        df = twap_trading_strategy(
            holding=holding,
            holding_min=holding_min,
            holding_max=holding_max,
            cash=cash,
            quantity=quantity,
            df=df
        )
    elif strategy == 'vwap':
        print('vwap')

    trading_history = []
    for i in range(len(df)):
        if df['Direction'][i] == 'Buy' or df['Direction'][i] == 'Sell' or i == 0:
            current = {
                'datetime': f"{df.index[i].strftime('%d/%m/%Y<br>%H:%M:%S')}",
                'total_asset': df['Total Asset'][i],
                'cash': df['Cash'][i],
                'price': df['Benchmark'][i],
                'direction': df['Direction'][i],
                'position': f"{df['Quantity'][i]}",
                'commission': df['Commission'][i],
                'holding': f"{df['Holding'][i]}"
            }
            trading_history.append(current)

    figure_data_svg = plot_trading_strategy_yield_curve(df)

    return f"{figure_data_svg}`{json.dumps(trading_history)}"


def calculate_df(df):
    df["Datetime"] = pd.to_datetime(df.index)

    df["DIF"] = ta.trend.MACD(df["Close"], window_slow=26, window_fast=12).macd()
    df["DEM"] = df["DIF"].ewm(span=9).mean()
    df["Histogram"] = df["DIF"] - df["DEM"].ewm(span=9).mean()

    df["KDJ"] = ta.momentum.StochasticOscillator(df["High"], df["Low"], df["Close"]).stoch()
    df["K"] = ta.momentum.StochasticOscillator(df["High"], df["Low"], df["Close"], window=9).stoch()
    df["D"] = df["K"].ewm(com=2).mean()
    df["J"] = 3 * df["K"] - 2 * df["D"]

    df["RSI"] = ta.momentum.RSIIndicator(df["Close"], window=14).rsi()
    df["CRSI"] = (df["RSI"] + 2 * df["RSI"].shift(1) + 3 * df["RSI"].shift(2) + 4 * df["RSI"].shift(3)) / 10

    df['TWAP'] = df['Close'].expanding().mean()
    df['VWAP'] = (df['Volume'] * df['Close']).cumsum() / df['Volume'].cumsum()

    return df


def macd_trading_strategy(**kwargs):
    df = kwargs.get('df')
    df = calculate_df(df)
    holding = int(kwargs.get('holding'))
    cash = float(kwargs.get('cash'))
    holding_max = int(kwargs.get('holding_max'))
    holding_min = int(kwargs.get('holding_min'))
    quantity = int(kwargs.get('quantity'))
    crsi_lower = kwargs.get('crsi_lower')
    crsi_upper = kwargs.get('crsi_upper')

    df['Holding'] = holding
    df['Cash'] = cash
    df['Quantity'] = quantity
    df['Direction'] = ''
    df['Benchmark'] = 0.0
    df['Commission'] = 0.0
    df['Total Asset'] = 0.0
    df['Relative'] = 0.0
    df['Original Asset'] = 0.0

    for i in range(len(df)):
        direction = ''
        commission = 0.0
        price_benchmark = 0.0
        price_close = df['Close'][i]
        price_low = df['Low'][i]
        price_high = df['High'][i]

        holding = df['Holding'][i - 1] if i > 0 else df['Holding'][0]
        cash = df['Cash'][i - 1] if i > 0 else df['Cash'][0]
        quantity = df['Quantity'][i]

        if (df['DIF'][i] <= df['DEM'][i] and df['J'][i] < df['K'][i] and df['CRSI'][i] >= crsi_upper) and holding - quantity >= holding_min:
            direction = 'Sell'
            commission = app.longbridgeRealTrading.calculate_commission(price_high, quantity, direction)
            holding -= quantity
            cash += (price_high * quantity - commission)
            price_benchmark = price_high

        elif (df['DIF'][i] > df['DEM'][i] and df['J'][i] >= df['K'][i] and df['CRSI'][i] <= crsi_lower) and holding + quantity <= holding_max and price_low * quantity <= cash:
            direction = 'Buy'
            commission = app.longbridgeRealTrading.calculate_commission(price_low, quantity, direction)
            holding += quantity
            cash -= (price_low * quantity + commission)
            price_benchmark = price_low

        df.iloc[i, df.columns.get_loc('Direction')] = direction
        df.iloc[i, df.columns.get_loc('Commission')] = commission
        df.iloc[i, df.columns.get_loc('Holding')] = holding
        df.iloc[i, df.columns.get_loc('Cash')] = cash
        df.iloc[i, df.columns.get_loc('Quantity')] = quantity
        df.iloc[i, df.columns.get_loc('Benchmark')] = price_benchmark
        df.iloc[i, df.columns.get_loc('Total Asset')] = cash + price_close * holding
        df.iloc[i, df.columns.get_loc('Relative')] = df['Close'][i] * (cash + price_close * holding) / (df['Cash'][0] + df['Close'][0] * df['Holding'][0])

    return df


def grid_trading_strategy(**kwargs):
    df = kwargs.get('df')
    price_benchmark = float(df['Open'][0])
    price_ceiling = float(kwargs.get('price_ceiling'))
    price_floor = float(kwargs.get('price_floor'))
    rise = float(kwargs.get('rise') / 100)
    fall = float(kwargs.get('fall') / 100)
    holding = int(kwargs.get('holding'))
    holding_max = int(kwargs.get('holding_max'))
    holding_min = int(kwargs.get('holding_min'))
    cash = float(kwargs.get('cash'))
    quantity = int(kwargs.get('quantity'))

    df['Holding'] = holding
    df['Cash'] = cash
    df['Quantity'] = quantity
    df['Direction'] = ""
    df['Benchmark'] = 0.0
    df['Commission'] = 0.0
    df['Total Asset'] = 0.0
    df['Relative'] = 0.0
    df['Original Asset'] = 0.0

    for i in range(len(df)):

        price_close = df['Close'][i]
        price_low = df['Low'][i]
        price_high = df['High'][i]
        price_sell = price_benchmark * (1 + rise)
        price_buy = price_benchmark * (1 - fall)
        direction = ''
        commission = 0.0
        holding = df['Holding'][i - 1] if i > 0 else df['Holding'][0]
        cash = df['Cash'][i - 1] if i > 0 else df['Cash'][0]
        quantity = df['Quantity'][i]

        if price_floor <= price_close <= price_ceiling:
            if price_high >= price_sell:
                if holding - quantity >= holding_min:
                    direction = "Sell"
                    commission = app.longbridgeRealTrading.calculate_commission(price_high, quantity, direction)
                    holding -= quantity
                    cash += (price_high * quantity - commission)
            elif price_low <= price_buy:
                if holding + quantity <= holding_max and cash / price_close >= quantity + 1:
                    direction = "Buy"
                    commission = app.longbridgeRealTrading.calculate_commission(price_low, quantity, direction)
                    holding += quantity
                    cash -= (price_low * quantity + commission)
            if direction != "":
                price_benchmark = price_close

        df.iloc[i, df.columns.get_loc('Direction')] = direction
        df.iloc[i, df.columns.get_loc('Commission')] = commission
        df.iloc[i, df.columns.get_loc('Holding')] = holding
        df.iloc[i, df.columns.get_loc('Cash')] = cash
        df.iloc[i, df.columns.get_loc('Quantity')] = quantity
        df.iloc[i, df.columns.get_loc('Benchmark')] = price_benchmark
        df.iloc[i, df.columns.get_loc('Total Asset')] = cash + price_close * holding
        df.iloc[i, df.columns.get_loc('Relative')] = df['Close'][i] * (cash + price_close * holding) / (df['Cash'][0] + df['Close'][0] * df['Holding'][0])

    return df


def twap_trading_strategy(**kwargs):
    df = kwargs.get('df')
    df = calculate_df(df)
    holding = int(kwargs.get('holding'))
    holding_max = int(kwargs.get('holding_max'))
    holding_min = int(kwargs.get('holding_min'))
    cash = float(kwargs.get('cash'))
    quantity = int(kwargs.get('quantity'))

    df['Holding'] = holding
    df['Cash'] = cash
    df['Quantity'] = quantity
    df['Direction'] = ""
    df['Benchmark'] = 0.0
    df['Commission'] = 0.0
    df['Total Asset'] = 0.0
    df['Relative'] = 0.0
    df['Original Asset'] = 0.0

    for i in range(len(df)):
        print(f"Price: {df['Close'][i]:.2f} TWAP: {df['TWAP'][i]:.2f}")

    return df
