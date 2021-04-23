if __name__ == "__main__":
    import core.common.django_settings
from core.backend.market_data import MarketDataClient
from core.systems.cpr import CPR


def everydayat0():
    MarketDataClient.get_instance().update_instruments()
    MarketDataClient.get_instance().update_futures_instrument()

def every6hours():
    MarketDataClient.get_instance().update_volumes()
    CPR.get_instance().update_instruments()

def every15mins():
    CPR.get_instance().check_signals()
