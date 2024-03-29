if __name__ == "__main__":
    import core.common.django_settings

from binance.client import Client
from cryptokings.settings import BINANCE_KEY, BINANCE_SECRET
from core.models import Instrument, InstrumentType
import logging
import datetime as dt
import pandas as pd


class MarketDataClient:
    __instance__ = None
    client = None

    @staticmethod
    def get_instance():
        if MarketDataClient.__instance__ is None:
            MarketDataClient.__instance__ = MarketDataClient()
            return MarketDataClient.__instance__
        else:
            return MarketDataClient.__instance__

    def __init__(self):
        self.client = Client(BINANCE_KEY, BINANCE_SECRET)

    # run every night at 12 am
    def update_instruments(self):
        instrument_type =InstrumentType.objects.get(type="SPOT")
        logging.info("Updating Instruments")
        symbols = self.client.get_exchange_info().get("symbols", [])
        symbols = [x.get("symbol") for x in symbols if x.get("quoteAsset") == "USDT"]
        for x in symbols:
            Instrument.objects.get_or_create(symbol=x, type=instrument_type)
        return True

    # run every night at 12 am
    def update_volumes(self):
        logging.info("Updating Volume")
        instrument_type = InstrumentType.objects.get(type="SPOT")
        response = self.client.get_ticker()
        for x in response:
            symbol = x.get("symbol")
            try:
                instrument = Instrument.objects.get(symbol=symbol, type=instrument_type)
                instrument.volume = x.get("quoteVolume")
                instrument.save()
            except:
                pass
        return True

    def get_klines(self, instrument: Instrument, interval, limit=None):
        logging.info("In get_klines")
        if instrument.type.type == "SPOT":
            data = self.client.get_klines(symbol=instrument.symbol, interval=interval, limit=limit)
        elif instrument.type.type == "FUTURES":
            data = self.client.futures_klines(symbol=instrument.symbol, interval=interval, limit=limit)

        objs = []
        for x in data:
            temp = {}
            temp["date_time"] = dt.datetime.fromtimestamp(x[0]/1e3)
            temp["open"] = float(x[1])
            temp["high"] = float(x[2])
            temp["low"] = float(x[3])
            temp["close"] = float(x[4])
            temp["volume"] = float(x[7])
            objs.append(temp)
        return pd.DataFrame(objs)

    def get_historical_klines(self, instrument: Instrument, interval, start_date: dt.datetime, end_date: dt.datetime):
        logging.info("In get_historical_klines")
        if instrument.type.type == "SPOT":
            data = self.client.get_historical_klines(symbol=instrument.symbol, interval=interval, start_str=str(start_date), end_str=str(end_date))
        elif instrument.type.type == "FUTURES":
            data = self.get_klines(instrument, interval)
            return data[(data["date_time"] >= start_date) & (data["date_time"] <= end_date)]

        objs = []
        for x in data:
            temp = {}
            temp["date_time"] = dt.datetime.fromtimestamp(x[0] / 1e3)
            temp["open"] = float(x[1])
            temp["high"] = float(x[2])
            temp["low"] = float(x[3])
            temp["close"] = float(x[4])
            temp["volume"] = float(x[7])
            objs.append(temp)

        return pd.DataFrame(objs)



    def get_previous_week(self):
        now = dt.datetime.utcnow()
        year = now.year
        df = pd.date_range(start=str(year - 1), end=str(year + 1), freq='W-MON')
        df = df[df <= now]
        return df.tolist()[-2]

    def get_previous_monthend(self):
        now = dt.datetime.utcnow()
        year = now.year
        df = pd.date_range(start=str(year - 1), end=str(year + 1), freq='M')
        df = df[df < now]
        return df.tolist()[-1]

    def get_prev_day_hl(self, instrument):
        yestarday = dt.date.today() - dt.timedelta(days=1)
        start_date = dt.datetime(yestarday.year, yestarday.month, yestarday.day)
        end_date = dt.datetime(yestarday.year, yestarday.month, yestarday.day, 23, 59, 59)
        x = self.get_historical_klines(instrument, self.client.KLINE_INTERVAL_1DAY, start_date, end_date)
        return x.iloc[0]["high"], x.iloc[0]["low"]

    # returns tuple (high, low)
    def get_prev_week_hl(self, instrument: Instrument):
        start_date = self.get_previous_week()
        end_date = start_date + dt.timedelta(days=6, hours=23, minutes=59, seconds=59)
        x = self.get_historical_klines(instrument, self.client.KLINE_INTERVAL_1WEEK, start_date, end_date)
        return x.iloc[0]["high"], x.iloc[0]["low"]

    # returns tuple (high, low)
    def get_prev_month_hl(self, instrument: Instrument):
        date = self.get_previous_monthend()
        start_date = dt.datetime(date.year, date.month, 1)
        end_date = dt.datetime(date.year, date.month, date.day, 23, 59, 59)
        x = self.get_historical_klines(instrument, self.client.KLINE_INTERVAL_1MONTH, start_date, end_date)
        return x.iloc[0]["high"], x.iloc[0]["low"]

    # returns r5, r4, r3, r2, r1, pivot, s1, s2, s3, s4, s5
    def get_today_pivots(self, instrument: Instrument):
        date = dt.date.today() - dt.timedelta(days=1)
        start_date = dt.datetime(date.year, date.month, date.day)
        end_date = dt.datetime(date.year, date.month, date.day, 23, 59, 59)
        x = self.get_historical_klines(instrument, self.client.KLINE_INTERVAL_1DAY, start_date, end_date)
        prev_high = x.iloc[0]["high"]
        prev_low = x.iloc[0]["low"]
        prev_close = x.iloc[0]["close"]

        pivot = (prev_high + prev_low + prev_close)/3
        s1 = 2 * pivot - prev_high
        s2 = pivot - (prev_high - prev_low)
        s3 = s1 - (prev_high - prev_low)
        s4 = s2 - (prev_high - prev_low)
        s5 = s3 - (prev_high - prev_low)

        r1 = 2 * pivot - prev_low
        r2 = pivot + (prev_high - prev_low)
        r3 = r1 + (prev_high - prev_low)
        r4 = r2 + (prev_high - prev_low)
        r5 = r3 + (prev_high - prev_low)

        return (r5, r4, r3, r2, r1, pivot, s1, s2, s3, s4, s5)


    def get_all_support_resistances(self, instrument: Instrument):
        prev_month_high, prev_month_low = self.get_prev_month_hl(instrument)
        prev_week_high, prev_week_low = self.get_prev_week_hl(instrument)
        prev_day_high, prev_day_low = self.get_prev_day_hl(instrument)
        r5, r4, r3, r2, r1, pivot, s1, s2, s3, s4, s5 = self.get_today_pivots(instrument)
        return {
            "PREVIOUS MONTH HIGH": prev_month_high,
            "PREVIOUS MONTH LOW": prev_month_low,
            "PREVIOUS WEEK HIGH": prev_week_high,
            "PREVIOUS WEEK LOW": prev_week_low,
            "PREVIOUS DAY HIGH": prev_day_high,
            "PREVIOUS DAY LOW": prev_day_low,
            "PIVOT": pivot,
            "S1": s1,
            "S2": s2,
            "S3": s3,
            "S4": s4,
            "S5": s5,
            "R1": r1,
            "R2": r2,
            "R3": r3,
            "R4": r4,
            "R5": r5,
        }


    # futures section #####################################

    def update_futures_instrument(self):
        logging.info("Updating Futures Instruments")
        instrument_type = InstrumentType.objects.get(type="FUTURES")
        symbols = self.client.futures_exchange_info().get("symbols", [])
        symbols = [x.get("symbol") for x in symbols if x.get("contractType") == "PERPETUAL" and x.get("quoteAsset") == "USDT"]
        for x in symbols:
            Instrument.objects.get_or_create(symbol=x, type=instrument_type)
        return True


if __name__ == "__main__":
    import pprint
    # instrument = Instrument.objects.get(symbol='BTCUSDT', type__type="FUTURES")
    obj = MarketDataClient.get_instance()
    # print(obj.get_prev_month_hl(instrument))
    # print(obj.get_today_pivots(instrument))
    # pprint.pprint(obj.get_all_support_resistances(instrument))
    obj.update_instruments()
    obj.update_volumes()
    obj.update_futures_instrument()

    # instrument = Instrument.objects.get(symbol="BTCUSDT", type__type="FUTURES")
    # print(obj.get_klines(instrument, interval=obj.client.KLINE_INTERVAL_15MINUTE, limit=200))

    # print(obj.get_historical_klines(instrument, obj.client.KLINE_INTERVAL_15MINUTE, dt.datetime(2021, 4, 24, 4), dt.datetime(2021, 4, 24, 5)))


