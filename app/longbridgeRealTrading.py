import time
from datetime import datetime

from longbridge.openapi import TradeContext, Config
from tradingview_ta import TA_Handler

from app import database as db
from app import emails
from app import models as md


def init():
    # Long Bridge initialization
    config = Config.from_env()
    return TradeContext(config)


def calculate_commission(price, position, direction):
    # Long Bridge commission fee
    res = max(1, 0.005 * position) + 0.003 * position

    if direction == "Sell":
        res += max(0.01, 0.000008 * price * position) + min(7.27, max(0.01, 0.000145 * position))

    return res


def get_current_position(ctx, ticker):
    # get the Long Bridge account's position according to the ticker
    resp = ctx.stock_positions()
    for channel in resp.channels:
        for item in channel.positions:
            if item.symbol == ticker + ".US":
                return item.quantity


def update_longbridge_trading(datetime, ticker, interval, position, ta_recommendation, yf_signal, potential_reference,
                              email, direction, order_id, handling_fee, price_cost, price_potential):
    # Update to the database, longbridge trading
    cnx = db.connect_to_db()
    cursor = cnx.cursor()

    sql = "INSERT INTO longbridge_trading (datetime, ticker, interval, position, ta_recommendation, yf_signal, price_close, email, direction, order_id, handling_fee, price_cost, price_potential) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"

    cursor.execute(sql, (
    datetime, ticker, interval, position, ta_recommendation, yf_signal, potential_reference, email, direction, order_id,
    handling_fee, price_cost, price_potential))

    cnx.commit()
    cursor.close()
    cnx.close()


def day_trade(email, ticker, interval, quantity):
    # ctx = init()
    today = datetime.today()
    # flag_sent_report = False

    longbridge_trading = [{
        "datetime": datetime.now(),
        "ticker": ticker,
        "interval": interval,
        "position": 0,
        "ta_recommendation": "",
        "yf_signal": "Hold",
        "price_close": 0.00,
        "email": email,
        "direction": "",
        "order_id": "",
        "handling_fee": 0.00,
        "price_cost": 0.00,
        "price_potential": 0.00
    }]

    while True:
        try:
            print(f"%s %5s %3s %s" % (today.strftime('%Y/%m/%d %H:%M:%S'), ticker, interval, email))

            # 1. Get the recommendations from TradingView
            handler = TA_Handler(
                symbol=ticker,
                exchange=md.ticker_exchanges.get(ticker),
                screener="america",
            )

            handler.interval = md.intervals.get(interval)
            analysis = handler.get_analysis()
            ta_recommendation = analysis.summary["RECOMMENDATION"]

            # 2. Get and signal according to Yahoo Finance's data
            df = md.get_df_interval(ticker, today.strftime("%Y-%m-%d"), interval, md.interval_type[interval])

            # If the latest BuyIndex is not Hold, then use the last one
            # yf_signal = longbridge_trading[-1]["yf_signal"] if df["BuyIndex"][len(df) - 1] == "Hold" else df["BuyIndex"][len(df) - 1]
            yf_signal = longbridge_trading.iloc[-1]["yf_signal"] if df["BuyIndex"].iloc[-1] == "Hold" else \
            df["BuyIndex"].iloc[-1]
            price_close = df["Close"][len(df) - 1]

            # 3. Get the current position
            position = longbridge_trading[-1]["position"]
            # position = get_current_position(ctx, ticker)

            # 4. Start Trading zone
            direction, order_id = "", ""
            handling_fee, price_cost = 0.00, longbridge_trading[-1]["price_cost"]
            take_profit_limit = 0.01
            stop_loss_limit = 0.005
            # buy_lower_limit = 0.01

            # For phase 1, just use dummy position
            price_potential = 0.00

            if position == 0:
                if yf_signal == "PotentialBuy" and (ta_recommendation == "BUY" or ta_recommendation == "STRONG_BUY"):
                    direction = "Buy"
                    handling_fee = calculate_commission(price_close, quantity, direction)
                    price_cost = price_close + handling_fee / quantity
                    position = quantity

                    subject = f"Order filled: buy {ticker} at ${price_close: ,.2f}"
                    body = f"Interval: {interval}\nTicker: {ticker}\nPrice: ${price_close: ,.2f}\nQuantity: {quantity}\nHandling Fee: ${handling_fee:,.2f}\nCash: -${price_close * quantity + handling_fee: ,.2f}\nDatetime: {today.strftime('%Y/%m/%d %H:%M:%S (HKT)')}"
                    emails.send_email(email, f"Subject: {subject}\n\n{body}")
            elif position > 0:
                if ((price_close >= price_cost * (1 + take_profit_limit) or price_close <= price_cost * (
                        1 - stop_loss_limit)) or
                        (yf_signal == "PotentialSell" and (
                                ta_recommendation == "SELL" or ta_recommendation == "STRONG_SELL") and price_close > price_cost)):
                    direction = "Sell"
                    handling_fee = calculate_commission(price_close, quantity, direction)
                    price_cost = price_close - handling_fee / quantity
                    position = 0

                    subject = f"Order filled: sell {ticker} at ${price_close: ,.2f}"
                    body = f"Interval: {interval}\nTicker: {ticker}\nPrice: ${price_close: ,.2f}\nQuantity: {quantity}\nHandling Fee: ${handling_fee: ,.2f}\nCash: +${price_close * quantity - handling_fee: ,.2f}\nDatetime: {today.strftime('%Y/%m/%d %H:%M:%S (HKT)')}"
                    emails.send_email(email, f"Subject: {subject}\n\n{body}")
            # End   Trading zone

            longbridge_trading.append({
                "datetime": datetime.now(),
                "ticker": ticker,
                "interval": interval,
                "position": position,
                "ta_recommendation": ta_recommendation,
                "yf_signal": yf_signal,
                "price_close": price_close,
                "email": email,
                "direction": direction,
                "order_id": order_id,
                "handling_fee": handling_fee,
                "price_cost": price_cost,
                "price_potential": price_potential
            })

            update_longbridge_trading(datetime.now(), ticker, interval, position, ta_recommendation, yf_signal,
                                      price_close, email, direction, order_id, handling_fee, price_cost,
                                      price_potential)

        except Exception as e:
            print(f"{ticker} Error: {e}")

        time.sleep(20)
