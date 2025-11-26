from flask import render_template, request
from . import views, emails, models as md, longbridgeRealTrading
from .all_trading_strategies import backtest_all_trading_strategies
from datetime import datetime, time as dt_time
import time


def init_app(app):
    @app.route('/allTradingStrategy', methods=['GET', 'POST'])
    def handle_trading_backtest():
        if request.method == 'POST':
            form_data = request.form
            response = backtest_all_trading_strategies(form_data)

            return response
            pass

        return render_template('all_trading_strategy.html')

    @app.route("/queryPrices", methods=["GET", "POST"])
    def handle_query():
        if request.method == "POST":

            trade_date = request.form['trade_date']
            ticker = request.form['ticker']

            return render_template('trade_view_price.html', data=views.prepare_web_content(trade_date, ticker))
            pass
        else:
            return render_template('trade_view_price.html', data={})

    @app.route("/queryTradingview", methods=["GET", "POST"])
    def handle_tradingview():
        if request.method == "POST":
            form_data = request.form
            return views.prepare_tradingview(form_data)

        return render_template("trade_view_screener.html")

    @app.route("/startEmailNotification", methods=["GET", "POST"])
    def start_email_notification():
        if request.method == "POST":
            email = request.form["email"]
            interval = request.form["interval"]

            start_time = dt_time(21, 30)
            end_time = dt_time(4, 30)

            while True:
                now = datetime.now().time()
                if now >= start_time or now <= end_time:
                    for ticker, _ in md.ticker_exchanges.items():
                        emails.email_notification(ticker, interval, email)
                else:
                    print(datetime.now().time(), "ONLY RUNNING BETWEEN 21:30-04:30")

                time.sleep(30)

        return render_template("start_email_notification.html")

    @app.route("/thank-you")
    def load_successfully_subscribed():
        return render_template("successfully_subscribed.html")

    @app.route("/longbridge-day-trade", methods=["GET", "POST"])
    def execute_longbridge_day_trade():
        if request.method == "POST":
            email = request.form["email"]
            ticker = request.form["ticker"]
            interval = request.form["interval"]
            quantity = request.form["customQuantity"]

            longbridgeRealTrading.day_trade(email, ticker, interval, quantity)

        return render_template("longbridge_day_trade.html")

    @app.route("/")
    def home():
        handle_query()
        handle_tradingview()
        start_email_notification()
        load_successfully_subscribed()
        return render_template("index.html")
