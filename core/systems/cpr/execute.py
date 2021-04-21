if __name__ == "__main__":
    import core.common.django_settings

from core.models import Instrument
from core.backend.market_data import MarketDataClient
import datetime as dt

class CPR:
    client = MarketDataClient.get_instance()

    def get_weekly_hl(self):
        x = self.client.client.get_historical_klines('BTCUSDT', self.client.client.KLINE_INTERVAL_1WEEK, "1 week ago UTC")
        print(dt.datetime.fromtimestamp(x[0][0]/1e3))
        print(x[0])


if __name__ == "__main__":
    x = CPR()
    x.get_weekly_hl()
