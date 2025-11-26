import numpy as np
from datetime import datetime
from tradingview_ta import TA_Handler
from app import models as md
import matplotlib.pyplot as plt
import matplotlib.dates as mpl_dates
import mplfinance as mpf
import io


def prepare_tradingview(form_data):
    res = []
    interval = form_data.get('interval')
    tickers = form_data.getlist('ticker')

    for ticker in tickers:
        exchange = md.ticker_exchanges[ticker]
        handler = TA_Handler(
            symbol=ticker,
            exchange=exchange,
            screener="america",
        )

        handler.interval = md.intervals.get(interval)
        current = {
            'ticker': ticker,
            'latest_price': '',
            'latest_change': '',
            'recommend': '',
            'buy': '',
            'neutral': '',
            'sell': '',
            'indicators': {}
        }

        try:
            now = datetime.now()
            print("Ticker: %-5s\t%4s\ton: %s" % (
                ticker, interval, now.strftime("%d/%m/%y %H:%M:%S")))

            analysis = handler.get_analysis()
            latest_price = analysis.indicators["close"]
            latest_change = analysis.indicators["change"]
            ratting = analysis.summary
            current['latest_price'] = f"{latest_price:,.2f}"
            current['latest_change'] = f"{latest_change:,.2f}"
            current['recommend'] = ratting.get('RECOMMENDATION')
            current['buy'] = ratting.get('BUY')
            current['neutral'] = ratting.get('NEUTRAL')
            current['sell'] = ratting.get('SELL')
            current['indicators'] = analysis.indicators
        except Exception as e:
            print(f"Error retrieving data for {ticker} at {interval}: {e}")

        res.append(current)

    return res


def prepare_web_content(trade_date, ticker):
    def find_timing(df):
        buy_time, sell_time = "", ""
        buy_price, sell_price = 0.00, 0.00
        for i in range(len(df) - 1, -1, -1):
            if df["BuyIndex"][i] == "PotentialBuy" and buy_time == "":
                buy_time = datetime.strftime(df["Datetime"][i], "%Y/%m/%d %H:%M")
                buy_price = df["Low"][i]
            elif df["BuyIndex"][i] == "PotentialSell" and sell_time == "":
                sell_time = datetime.strftime(df["Datetime"][i], "%Y/%m/%d %H:%M")
                sell_price = df["High"][i]

        return buy_time, f"{buy_price:,.2f}", sell_time, f"{sell_price:,.2f}"

    now = datetime.now()
    print("Trade date: %s\tTicker: %-5s\tCalculation date: %s" % (trade_date, ticker, now.strftime("%d/%m/%y %H:%M:%S")))

    df = md.get_df_interval(ticker, trade_date, "1m", md.interval_type.get("1m"))
    buy_time, buy_price, sell_time, sell_price = find_timing(df)

    res = {
        'trade_date': trade_date,
        'ticker': ticker,
        'CRSI': f"{df['CRSI'][len(df) - 1]:,.2f}",
        'Close': f"{df['Close'][len(df) - 1]:,.2f}",
        '1m_buy_time': buy_time,
        '1m_buy_price': buy_price,
        '1m_sell_time': sell_time,
        '1m_sell_price': sell_price,
        'figure_1m': plot_stock_price_svg(df)
    }

    df = md.get_df_interval(ticker, trade_date, "5m", md.interval_type.get("5m"))
    buy_time, buy_price, sell_time, sell_price = find_timing(df)
    res.update({
        '5m_buy_time': buy_time,
        '5m_buy_price': buy_price,
        '5m_sell_time': sell_time,
        '5m_sell_price': sell_price,
        'figure_5m': plot_stock_price_svg(df)
    })

    df = md.get_df_interval(ticker, trade_date, "15m", md.interval_type.get("15m"))
    buy_time, buy_price, sell_time, sell_price = find_timing(df)
    res.update({
        '15m_buy_time': buy_time,
        '15m_buy_price': buy_price,
        '15m_sell_time': sell_time,
        '15m_sell_price': sell_price,
        'figure_15m': plot_stock_price_svg(df)
    })

    df = md.get_df_interval(ticker, trade_date, "30m", md.interval_type.get("30m"))
    buy_time, buy_price, sell_time, sell_price = find_timing(df)
    res.update({
        '30m_buy_time': buy_time,
        '30m_buy_price': buy_price,
        '30m_sell_time': sell_time,
        '30m_sell_price': sell_price,
        'figure_30m': plot_stock_price_svg(df)
    })

    df = md.get_df_interval(ticker, trade_date, "60m", md.interval_type.get("60m"))
    buy_time, buy_price, sell_time, sell_price = find_timing(df)
    res.update({
        '1h_buy_time': buy_time,
        '1h_buy_price': buy_price,
        '1h_sell_time': sell_time,
        '1h_sell_price': sell_price,
        'figure_1h': plot_stock_price_svg(df)
    })

    df = md.get_df_interval(ticker, trade_date, "1d", md.interval_type.get("1d"))
    buy_time, buy_price, sell_time, sell_price = find_timing(df)
    res.update({
        '1d_buy_time': buy_time,
        '1d_buy_price': buy_price,
        '1d_sell_time': sell_time,
        '1d_sell_price': sell_price,
        'figure_1d': plot_stock_price_svg(df)
    })

    return res


def plot_stock_price_svg(df):
    plt.rcParams.update({
        "font.family": "monospace",
        "text.color": "#0055cc",
        "axes.labelcolor": "#0055cc",
        "xtick.color": "#212529",
        "ytick.color": "#212529",
        "axes.edgecolor": "#212529",
        "lines.color": "#0055cc"
    })

    mc = mpf.make_marketcolors(up='#0055cc', down='#ff2f92', edge='inherit', wick='inherit')
    s = mpf.make_mpf_style(marketcolors=mc)
    fig, axlist = mpf.plot(df, type='candle', style=s, returnfig=True, figsize=(5, 3), **(dict(warn_too_much_data=len(df) + 1)))

    for ax in axlist:
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)

        ax.grid(False)

        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.set_xticks([])
        ax.set_yticks([])

        ax.yaxis.set_label_text('')

    fig.patch.set_alpha(0)

    plt.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)

    file_figure = io.BytesIO()
    plt.savefig(file_figure, format='svg', bbox_inches='tight', pad_inches=0, transparent=True)
    file_figure.seek(0)
    data_figure = file_figure.getvalue()
    svg_figure = data_figure.decode('utf8')

    plt.close()

    return svg_figure
