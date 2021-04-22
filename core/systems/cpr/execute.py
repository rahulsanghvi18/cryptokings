if __name__ == "__main__":
    import core.common.django_settings

from core.models import Instrument
from core.backend.market_data import MarketDataClient
import talib
from core.telegram import Handler
import logging


class CPR:
    __instance__ = None

    def __init__(self):
        self.client = MarketDataClient.get_instance()
        self.no_top_coins = 20

    @staticmethod
    def get_instance():
        if CPR.__instance__ is None:
            CPR.__instance__ = CPR()
            return CPR.__instance__
        else:
            return CPR.__instance__

    # update every night
    def update_instruments(self):
        logging.info("Updating CPR values")

        for x in Instrument.objects.all():
            x.cprsystem = {}
            x.save()

        message = "CPR Tracking System Updated\n\n"
        for x in Instrument.objects.order_by("-volume")[:self.no_top_coins]:
            x.cprsystem = self.client.get_all_support_resistances(x)
            message += x.symbol + "\n"
            x.save()
        Handler.get_instance().send_all_subscribers(message)


    # run periodically
    def check_signals(self):
        logging.info("Checking Signals")
        timeperiod = 13
        message = ""

        for instrument in Instrument.objects.order_by("-volume")[:self.no_top_coins]:
            instrument_message = ""
            df = self.client.get_klines(instrument, self.client.client.KLINE_INTERVAL_15MINUTE, limit=300)
            df = df.iloc[:len(df) - 1]
            df["adx"] = talib.ADX(df["high"], df["low"], df["close"], timeperiod=timeperiod)
            df["slope"] = talib.LINEARREG_SLOPE(df["adx"], timeperiod=timeperiod)
            df["trending"] = (df["slope"] > 0) & (df["slope"] > df["slope"].shift(1)) & (df["adx"] > 25)
            df["trendcrossover"] = (df["trending"] != df.shift(1)["trending"]) & df["trending"]

            trendcrossover = df.iloc[-1]["trendcrossover"]
            close_value = df.iloc[-1]["close"]

            if trendcrossover:
                instrument_message += 'TREND : ' + "Trend has Turned +ve keep an eye!\n"
            elif df["trending"].iloc[0]:
                instrument_message += 'TREND : ' + "Positive!\n"

            for key, value in instrument.cprsystem.items():
                bullish_crossover = (df["close"] > value) & (df.shift(1)["close"] < value)
                bearish_crossover = (df["close"] < value) & (df.shift(1)["close"] > value)

                if bullish_crossover[len(bullish_crossover) - 1]:
                    instrument_message += (key + " : " + " BULLISH CROSSOVER\n" + "value : " + str(value) + " close : " + str(close_value) + "\n\n")
                elif bearish_crossover[len(bearish_crossover) - 1]:
                    instrument_message += (key + " : " + " BEARISH CROSSOVER\n" + "value : " + str(value) + " close : " + str(close_value) + "\n\n")

            if instrument_message != "":
                instrument_message = 'SYMBOL: ' + instrument.symbol + '\n\n' + instrument_message
                instrument_message += "\n===========================\n"
                message += instrument_message

        if message != "":
            Handler.get_instance().send_all_subscribers(message)


if __name__ == "__main__":
    x = CPR()
    x.check_signals()
