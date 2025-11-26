import smtplib
import hashlib
from datetime import datetime
from typing import Optional
from tradingview_ta import TA_Handler
from app import models as md
from app import database as db


def generate_email_notification_id(ticker: str, signal: str, last_updated_datetime: str, last_price: str, interval: str) -> Optional[str]:
    cnx = db.connect_to_db()
    cursor = cnx.cursor()

    cursor.execute(f"""
        SELECT COUNT(*) FROM notification_email WHERE ticker = '{ticker}' AND signal = '{signal}' AND last_updated_datetime = '{last_updated_datetime}' AND last_price = '{last_price}' AND interval = '{interval}';
    """)
    count = cursor.fetchone()[0]

    if count == 0:
        cursor.execute("""
            SELECT TO_CHAR(CURRENT_DATE AT TIME ZONE 'EST', 'YYYYMMDD') || LPAD(CAST(COUNT(*) + 1 AS TEXT), 4, '0') FROM notification_email WHERE creation_time >= CURRENT_DATE AT TIME ZONE 'EST';
        """)

        notification_id = cursor.fetchone()[0]
        notification_id += f"({hashlib.md5((ticker + interval).encode()).hexdigest()[:4]})"

        cursor.execute(
            f"""INSERT INTO notification_email (id, ticker, signal, last_updated_datetime, last_price, interval, creation_time) VALUES ('{notification_id}', '{ticker}', '{signal}', '{last_updated_datetime}', '{last_price}', '{interval}', NOW() AT TIME ZONE 'HKT' AT TIME ZONE 'EST')""")
    else:
        print("Duplicated", ticker, signal, last_updated_datetime, last_price, interval)
        notification_id = None

    cnx.commit()
    cursor.close()
    cnx.close()

    return notification_id


def send_email(receiver_email: str, message: str) -> None:
    sender_email = "******@outlook.com"
    password = "******"

    server = smtplib.SMTP("smtp-mail.outlook.com", 587)
    server.starttls()
    server.login(sender_email, password)
    server.sendmail(sender_email, receiver_email, message)
    server.quit()


def email_notification(ticker: str, interval: str, email: str) -> None:
    try:
        handler = TA_Handler(
            symbol=ticker,
            exchange=md.ticker_exchanges.get(ticker),
            screener="america",
        )

        handler.interval = md.intervals.get(interval)
        analysis = handler.get_analysis()
        db.update_tradingview_data(analysis)

        today_string = datetime.now().strftime("%Y-%m-%d")
        df = md.get_df_interval(ticker, today_string, interval, md.interval_type.get(interval))

        signal_buy, price_buy, datetime_buy = False, 0.00, ""
        signal_sell, price_sell, datetime_sell = False, 0.00, ""
        price_close = analysis.indicators["close"]
        recent_cycle = 26

        for i in range(len(df) - 1, max(len(df) - recent_cycle, -1), -1):
            current, price, datetime_last = df["BuyIndex"].iloc[i], df["Close"].iloc[i], df["Datetime"].iloc[i]
            if current == "PotentialBuy" and not signal_buy:
                signal_buy, price_buy, datetime_buy = True, price, datetime_last
            elif current == "PotentialSell" and not signal_sell:
                signal_sell, price_sell, datetime_sell = True, price, datetime_last
            elif signal_buy and signal_sell:
                break

        if signal_buy:
            print(f"{ticker:5s} ({interval}) Buy  {datetime_buy} {price_buy:,.2f}")
        if signal_sell:
            print(f"{ticker:5s} ({interval}) Sell {datetime_sell} {price_sell:,.2f}")

        recommendation = analysis.summary["RECOMMENDATION"]
        if (recommendation == "STRONG_BUY") and (signal_buy and price_close <= price_buy):
            notification_id = generate_email_notification_id(ticker, "Strong buy", datetime_buy, f"{price_buy:,.2f}", interval)
            if notification_id is not None:
                subject = f"Strong buy {ticker} at ${price_close:,.2f}"
                body = f"Interval: {interval}\nLast updated: {datetime_buy}\nBelow: ${price_buy :,.2f}\n\nReference ID: {notification_id}"
                message = f"Subject: {subject}\n\n{body}"
                send_email(email, message)

        elif (recommendation == "STRONG_SELL") and (signal_sell and price_close >= price_sell):
            notification_id = generate_email_notification_id(ticker, "Strong sell", datetime_sell, f"{price_sell:,.2f}", interval)
            if notification_id is not None:
                subject = f"Strong sell {ticker} at ${price_close:,.2f}"
                body = f"Interval: {interval}\nLast updated: {datetime_sell}\nAbove: ${price_sell :,.2f}\n\nReference ID: {notification_id}"
                message = f"Subject: {subject}\n\n{body}"
                send_email(email, message)

    except Exception as e:
        print(f"{ticker} Error: {e}")
