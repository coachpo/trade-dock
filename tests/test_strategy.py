from app import database
from app import models
from app import longbridgeRealTrading


def strategy(ticker):
    count = 0
    quantity = 100
    total = 0.00
    min_profit_limit = 0.001
    take_profit_limit = 0.02
    stop_loss_limit = 0.005

    cnx = database.connect_to_db()
    cursor = cnx.cursor()

    sql = f"""
    SELECT TO_CHAR((datetime AT TIME ZONE 'HKT' AT TIME ZONE 'America/New_York')::timestamp, 'YYYY/MM/DD HH24:MI:SS') AS "New York Datetime",
           ticker                                                                                                     AS "Ticker",
           ta_recommendation,
           yf_signal,
           ROUND(price_close::numeric, 2)                                                                             AS "Price Close",
           ROUND(price_cost::numeric, 2)                                                                              AS "Price Cost",
           ROUND(price_potential::numeric, 2)                                                                         AS "Price Potential"
    FROM longbridge_trading
    WHERE (datetime BETWEEN TIMESTAMP '2023-10-10 21:30:00' AND TIMESTAMP '2023-10-11 04:00:00')
      AND ticker = %s
    ORDER BY ticker, datetime;
    """

    cursor.execute(sql, (ticker,))
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    data = [dict(zip(columns, row)) for row in rows]

    cursor.close()
    cnx.close()

    def buy(count, total, remarks):
        count += 1
        handling_fee = longbridgeRealTrading.calculate_commission(price, quantity, "Buy")
        sub_total = price * quantity + handling_fee
        total -= sub_total
        data[i]["Price Cost"] = price + handling_fee / quantity

        print(f"{data[i]['New York Datetime']} Buy  {price:8.2f} {quantity:3d} {handling_fee:5.2f}  {-sub_total:10,.2f} ({count}) {remarks}")

        return count, total

    def sell(count, total, remarks):
        count += 1
        handling_fee = longbridgeRealTrading.calculate_commission(price, quantity, "Sell")
        sub_total = price * quantity - handling_fee
        total += sub_total
        data[i]["Price Cost"] = price - handling_fee / quantity

        print(f"{data[i]['New York Datetime']} Sell {price:8.2f} {quantity:3d} {handling_fee:5.2f}  {sub_total:10,.2f} ({count}) {remarks}")

        return count, total

    if len(data) > 0:
        print(f"Datetime (New York) DIR    Price  Qty  Fee  Cash        Remarks")
        for i in range(len(data)):
            if i > 0:
                data[i]["yf_signal"] = data[i - 1]["yf_signal"] if data[i]["yf_signal"] == "Hold" else data[i]["yf_signal"]
                data[i]["Price Cost"] = data[i - 1]["Price Cost"]

            ta_recommendation, yf_signal = data[i]["ta_recommendation"], data[i]["yf_signal"]
            price = float(data[i]['Price Close'])

            price_cost = 0.00
            if data[i]["Price Cost"] is not None:
                price_cost = float(data[i]["Price Cost"])

            if count % 2 == 0:
                if yf_signal == "PotentialBuy" and (ta_recommendation == "BUY" or ta_recommendation == "STRONG_BUY"):
                    if count == 0:
                        count, total = buy(count, total, "Initial")
                    elif price <= price_cost:
                        count, total = buy(count, total, "")
                elif yf_signal == "PotentialBuy" and price <= price_cost * (1 - stop_loss_limit):
                    count, total = buy(count, total, "Second buy")
            else:
                if yf_signal == "PotentialSell" and (ta_recommendation == "SELL" or ta_recommendation == "STRONG_SELL") and price >= price_cost * (1 + min_profit_limit):
                    count, total = sell(count, total, "Normal sell")
                elif price <= price_cost * (1 - stop_loss_limit):
                    count, total = sell(count, total, "Stop loss")
                elif price >= price_cost * (1 + take_profit_limit):
                    count, total = sell(count, total, "Take profit")

        if count % 2 == 1:
            total += float(data[len(data) - 1]['Price Close']) * quantity
        print(f"Ticker: {ticker:5s}                           P/L: {total:10,.2f}\n")


if __name__ == "__main__":

    for ticker in models.ticker_exchanges:
        strategy(ticker)
