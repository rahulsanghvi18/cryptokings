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

        Handler.get_instance().send_all_subscribers(message, Handler.get_instance().spot_group)
        Handler.get_instance().send_all_subscribers(message, Handler.get_instance().futures_group)


    # run periodically
    def check_signals(self):
        logging.info("Checking Signals")

        objs = []
        for instrument in Instrument.objects.filter(type__type="SPOT").order_by("-volume")[:self.no_top_coins]:
            objs.append(instrument)

        self.analyse(objs, Handler.get_instance().spot_group)

        objs = []
        for instrument in Instrument.objects.filter(type__type="SPOT").order_by("-volume")[:self.no_top_coins]:
            try:
                x = Instrument.objects.get(symbol=instrument.symbol, type__type="FUTURES")
                objs.append(x)
            except:
                pass
        self.analyse(objs, Handler.get_instance().futures_group)

    def analyse(self, instruments, contact):
        timeperiod = 13
        message = ""

        for instrument in instruments:
            instrument_message = ""
            df = self.client.get_klines(instrument, self.client.client.KLINE_INTERVAL_15MINUTE, limit=300)
            df = df.iloc[:len(df) - 1]

            df["adx"] = talib.ADX(df["high"], df["low"], df["close"], timeperiod=timeperiod)
            df["slope"] = talib.LINEARREG_SLOPE(df["adx"], timeperiod=timeperiod)
            df["trending"] = (df["slope"] > 0) & (df["slope"] > df["slope"].shift(1)) & (df["adx"] > 25)
            df["trendcrossover"] = (df["trending"] != df.shift(1)["trending"]) & df["trending"]
            df["ema10"] = talib.EMA(df["close"], timeperiod=10)
            df["ema20"] = talib.EMA(df["close"], timeperiod=20)

            trendcrossover = df.iloc[-1]["trendcrossover"]
            close_value = df.iloc[-1]["close"]

            ema10_bullish_crossover = (df["close"] > df["ema10"]) & (df.shift(1)["close"] < df["ema10"])
            ema10_bearish_crossover = (df["close"] < df["ema10"]) & (df.shift(1)["close"] > df["ema10"])
            ema20_bullish_crossover = (df["close"] > df["ema20"]) & (df.shift(1)["close"] < df["ema20"])
            ema20_bearish_crossover = (df["close"] < df["ema20"]) & (df.shift(1)["close"] > df["ema20"])

            if ema10_bullish_crossover[len(ema10_bullish_crossover) - 1]:
                value = df["ema10"].iloc[-1]
                instrument_message += (
                            "**EMA 10 : " + " BULLISH CROSSOVER**\n" + "value : " + str(value) + " close : " + str(
                        close_value) + "\n\n")
            elif ema10_bearish_crossover[len(ema10_bearish_crossover) - 1]:
                value = df["ema10"].iloc[-1]
                instrument_message += (
                            "**EMA 10 : " + " BEARISH CROSSOVER**\n" + "value : " + str(value) + " close : " + str(
                        close_value) + "\n\n")

            if ema20_bullish_crossover[len(ema20_bullish_crossover) - 1]:
                value = df["ema20"].iloc[-1]
                instrument_message += (
                            "**EMA 20 : " + " BULLISH CROSSOVER**\n" + "value : " + str(value) + " close : " + str(
                        close_value) + "\n\n")
            elif ema20_bearish_crossover[len(ema20_bearish_crossover) - 1]:
                value = df["ema20"].iloc[-1]
                instrument_message += (
                            "**EMA 20 : " + " BEARISH CROSSOVER**\n" + "value : " + str(value) + " close : " + str(
                        close_value) + "\n\n")

            if trendcrossover:
                instrument_message += '**TREND : ' + "Trend has Turned +ve keep an eye!**\n\n"
            elif df["trending"].iloc[-1]:
                instrument_message += '**TREND : ' + "Positive!**\n\n"

            for key, value in instrument.cprsystem.items():
                bullish_crossover = (df["close"] > value) & (df.shift(1)["close"] < value)
                bearish_crossover = (df["close"] < value) & (df.shift(1)["close"] > value)

                if bullish_crossover[len(bullish_crossover) - 1]:
                    instrument_message += (
                                "**" + key + " : " + " BULLISH CROSSOVER**\n" + "value : " + str(value) + " close : " + str(
                            close_value) + "\n\n")
                elif bearish_crossover[len(bearish_crossover) - 1]:
                    instrument_message += (
                                "**" + key + " : " + " BEARISH CROSSOVER**\n" + "value : " + str(value) + " close : " + str(
                            close_value) + "\n\n")

            if instrument_message != "":
                instrument_message = '**SYMBOL: ' + instrument.symbol + '\n\n' + "UTC TIME : " + str(
                    df["date_time"].iloc[-1]) + "**\n\n" + instrument_message
                instrument_message += "\n===========================\n"
                message += instrument_message

        if message != "":
            Handler.get_instance().send_all_subscribers(contact, message)


if __name__ == "__main__":
    x = CPR()
    x.update_instruments()
    x.check_signals()
