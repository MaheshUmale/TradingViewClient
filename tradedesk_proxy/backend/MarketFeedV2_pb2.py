# Improved Mock for Protobuf Generated File
class FeedResponse:
    def __init__(self):
        self.feeds = {}

    def ParseFromString(self, data):
        # In a real scenario, this would deserialize binary data.
        # For testing, we assume the object is already populated or mock it.
        pass

    def SerializeToString(self):
        return b"mock_binary"

# Mock classes to simulate Protobuf structure for MessageToDict
class LTPC:
    def __init__(self, ltp=0.0):
        self.ltp = ltp

class MarketOHLC:
    def __init__(self, open=0.0, high=0.0, low=0.0, close=0.0, volume=0):
        self.ohlc = [{"open": open, "high": high, "low": low, "close": close, "volume": volume}]

class MarketFullFeed:
    def __init__(self, ltp=0.0):
        self.ltpc = LTPC(ltp)
        self.marketOHLC = MarketOHLC(ltp, ltp, ltp, ltp, 100)

class Feed:
    def __init__(self, ltp=0.0):
        self.ff = {"marketFF": MarketFullFeed(ltp)}
