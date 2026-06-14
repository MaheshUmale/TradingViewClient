#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TradingView Module External Integration Examples
Demonstrates how to use the TradingView data source in different scenarios.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

# Import TradingView module components
from .api_server import TradingViewAPIServer
from .data_cache_manager import DataCacheManager, CacheLevel
from .enhanced_data_quality_monitor import DataQualityMonitor, AlertLevel
from .enhanced_client import EnhancedTradingViewClient

# Import other system modules (assumed to exist)
try:
    from trading_core.data_manager import IDataSource, MarketData
    from chanpy.Chan import CChan
    # from config.config_manager import get_config
except ImportError:
    # Mock interfaces for examples
    class IDataSource:
        pass

    class MarketData:
        def __init__(self, symbol: str, timeframe: str, klines: List[Dict]):
            self.symbol = symbol
            self.timeframe = timeframe
            self.klines = klines

from tradingview.utils import get_logger

logger = get_logger(__name__)


# ==================== Scenario 1: As a trading_core Data Source ====================

class TradingViewDataSource(IDataSource):
    """TradingView Data Source Adapter - Integrated into trading_core"""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize data source"""
        self.config = config or {}
        self.client = None
        self.cache_manager = None
        self.quality_monitor = None
        self.initialized = False

    async def initialize(self) -> bool:
        """Initialize the data source"""
        try:
            # Initialize enhanced client
            self.client = EnhancedTradingViewClient({
                'auto_reconnect': True,
                'health_monitoring': True,
                'performance_optimization': True,
                'max_reconnect_attempts': 10,
                'heartbeat_interval': 30
            })

            # Initialize cache manager
            self.cache_manager = DataCacheManager(
                db_path=self.config.get('cache_db_path', 'trading_data_cache.db'),
                max_memory_size=self.config.get('max_cache_size', 2000)
            )

            # Initialize quality monitor
            self.quality_monitor = DataQualityMonitor({
                'critical_quality_score': 0.7,
                'warning_quality_score': 0.85
            })

            # Register quality alert handler
            self.quality_monitor.register_alert_handler(self._handle_quality_alert)

            # Connect to TradingView
            await self.client.connect()

            self.initialized = True
            logger.info("TradingView data source initialized successfully")
            return True

        except Exception as e:
            logger.error(f"TradingView data source initialization failed: {e}")
            self.initialized = False
            return False

    async def get_historical_data(self, symbol: str, timeframe: str,
                                count: int = 500, **kwargs) -> Optional[MarketData]:
        """Fetch historical data"""
        if not self.initialized:
            logger.error("Data source not initialized")
            return None

        try:
            # First check cache
            cached_data = await self.cache_manager.get_historical_data(
                symbol, timeframe, count, **kwargs
            )

            if cached_data and cached_data.get('quality_score', 0) >= 0.8:
                logger.info(f"Using cached data: {symbol}:{timeframe}")
                return MarketData(
                    symbol=symbol,
                    timeframe=timeframe,
                    klines=cached_data['klines']
                )

            # Fetch data from TradingView
            chart_session = self.client.Session.Chart()
            raw_data = await chart_session.get_historical_data(
                symbol=symbol,
                timeframe=timeframe,
                count=count,
                **kwargs
            )

            # Data quality check
            formatted_data = {
                'symbol': symbol,
                'timeframe': timeframe,
                'klines': raw_data.get('data', []),
                'quality_score': 1.0
            }

            quality_result = await self.quality_monitor.evaluate_data_quality(
                symbol, timeframe, formatted_data
            )

            formatted_data['quality_score'] = quality_result.quality_score

            # Store in cache if quality is sufficient
            if quality_result.quality_score >= 0.8:
                await self.cache_manager.store_historical_data(
                    symbol, timeframe, formatted_data
                )

            return MarketData(
                symbol=symbol,
                timeframe=timeframe,
                klines=formatted_data['klines']
            )

        except Exception as e:
            logger.error(f"Failed to fetch historical data: {e}")
            return None

    async def subscribe_realtime_data(self, symbols: List[str],
                                    callback: callable) -> bool:
        """Subscribe to real-time data"""
        if not self.initialized:
            return False

        try:
            # Create subscription for each symbol
            for symbol in symbols:
                chart_session = self.client.Session.Chart()
                await chart_session.subscribe_realtime(
                    symbol=symbol,
                    callback=lambda data: self._handle_realtime_data(data, callback)
                )

            logger.info(f"Real-time data subscription successful: {symbols}")
            return True

        except Exception as e:
            logger.error(f"Real-time data subscription failed: {e}")
            return False

    async def _handle_realtime_data(self, data: Dict[str, Any], callback: callable):
        """Handle real-time data"""
        try:
            # Fast data quality check
            if self._is_data_valid(data):
                await callback(data)
            else:
                logger.warning(f"Real-time data quality check failed: {data.get('symbol', 'unknown')}")

        except Exception as e:
            logger.error(f"Failed to handle real-time data: {e}")

    def _is_data_valid(self, data: Dict[str, Any]) -> bool:
        """Fast data validity check"""
        required_fields = ['symbol', 'timestamp', 'price']

        for field in required_fields:
            if field not in data or data[field] is None:
                return False

        try:
            price = float(data['price'])
            timestamp = int(data['timestamp'])

            if price <= 0 or timestamp <= 0:
                return False

            return True

        except (ValueError, TypeError):
            return False

    async def _handle_quality_alert(self, alert):
        """Handle data quality alerts"""
        if alert.level in [AlertLevel.CRITICAL, AlertLevel.ERROR]:
            logger.error(f"Critical data quality alert: {alert.message}")
            # Can trigger data source switching or other emergency measures here
        else:
            logger.warning(f"Data quality alert: {alert.message}")

    async def get_health_status(self) -> Dict[str, Any]:
        """Get data source health status"""
        if not self.initialized:
            return {'status': 'uninitialized'}

        client_health = self.client.get_health_status() if self.client else {}
        cache_stats = await self.cache_manager.get_statistics() if self.cache_manager else {}
        quality_stats = self.quality_monitor.get_quality_statistics() if self.quality_monitor else {}

        return {
            'status': 'healthy' if client_health.get('connected', False) else 'unhealthy',
            'client_health': client_health,
            'cache_statistics': cache_stats,
            'quality_statistics': quality_stats
        }

    async def shutdown(self):
        """Shutdown data source"""
        if self.client:
            await self.client.disconnect()

        logger.info("TradingView data source shut down")


# ==================== Scenario 2: Providing data for chanpy ====================

class ChanpyDataFeeder:
    """Provides data for chanpy theory analysis"""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize data feeder"""
        self.config = config or {}
        self.data_source = TradingViewDataSource(config)
        self.chan_instances = {}  # Store CChan instances

    async def initialize(self) -> bool:
        """Initialize"""
        return await self.data_source.initialize()

    async def create_chan_analysis(self, symbol: str, timeframe: str,
                                 chan_config: Dict[str, Any] = None) -> Optional[str]:
        """Create Chan theory analysis instance"""
        try:
            # Fetch historical data
            market_data = await self.data_source.get_historical_data(
                symbol, timeframe, count=1000
            )

            if not market_data or not market_data.klines:
                logger.error(f"Unable to fetch data for Chan analysis: {symbol}:{timeframe}")
                return None

            # Convert to chanpy format
            chanpy_data = self._convert_to_chanpy_format(market_data.klines)

            # Create CChan instance (assuming CChan interface)
            chan_instance = CChan(
                code=symbol,
                begin_time=None,
                end_time=None,
                data_src="custom",
                lv_list=[timeframe],
                config=chan_config or {}
            )

            # Load data into CChan
            for kline in chanpy_data:
                chan_instance.add_lv_iter(kline)

            # Store instance
            instance_id = f"{symbol}_{timeframe}_{int(time.time())}"
            self.chan_instances[instance_id] = {
                'chan': chan_instance,
                'symbol': symbol,
                'timeframe': timeframe,
                'created_at': time.time(),
                'last_update': time.time()
            }

            logger.info(f"Created Chan analysis instance: {instance_id}")
            return instance_id

        except Exception as e:
            logger.error(f"Failed to create Chan analysis: {e}")
            return None

    def _convert_to_chanpy_format(self, klines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert data format to what chanpy requires"""
        chanpy_klines = []

        for kline in klines:
            try:
                chanpy_kline = {
                    'time': datetime.fromtimestamp(int(kline['timestamp'])),
                    'open': float(kline['open']),
                    'high': float(kline['high']),
                    'low': float(kline['low']),
                    'close': float(kline['close']),
                    'volume': float(kline.get('volume', 0))
                }
                chanpy_klines.append(chanpy_kline)

            except (ValueError, TypeError, KeyError) as e:
                logger.warning(f"Failed to convert K-line data: {e}")
                continue

        return chanpy_klines

    async def update_chan_analysis(self, instance_id: str) -> bool:
        """Update Chan theory analysis"""
        if instance_id not in self.chan_instances:
            logger.error(f"Chan analysis instance does not exist: {instance_id}")
            return False

        try:
            instance = self.chan_instances[instance_id]
            symbol = instance['symbol']
            timeframe = instance['timeframe']

            # Get latest data
            market_data = await self.data_source.get_historical_data(
                symbol, timeframe, count=100  # Fetch recent 100 K-lines
            )

            if not market_data or not market_data.klines:
                return False

            # Convert and update
            chanpy_data = self._convert_to_chanpy_format(market_data.klines)

            # Update CChan instance
            chan = instance['chan']
            for kline in chanpy_data:
                chan.add_lv_iter(kline)

            instance['last_update'] = time.time()

            logger.debug(f"Updated Chan analysis instance: {instance_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update Chan analysis: {e}")
            return False

    def get_chan_analysis_result(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get Chan theory analysis result"""
        if instance_id not in self.chan_instances:
            return None

        try:
            instance = self.chan_instances[instance_id]
            chan = instance['chan']

            # Get buy/sell points
            buy_sell_points = []
            if hasattr(chan, 'get_bsp'):
                bsp_list = chan.get_bsp()
                for bsp in bsp_list:
                    buy_sell_points.append({
                        'type': bsp.type.value if hasattr(bsp.type, 'value') else str(bsp.type),
                        'timestamp': int(bsp.klu.time.timestamp()) if hasattr(bsp.klu, 'time') else 0,
                        'price': float(bsp.klu.close) if hasattr(bsp.klu, 'close') else 0.0,
                        'is_buy': bsp.is_buy if hasattr(bsp, 'is_buy') else None
                    })

            # Get center (ZhongShu) information
            zs_list = []
            if hasattr(chan, 'get_zs'):
                zs_data = chan.get_zs()
                for zs in zs_data:
                    zs_list.append({
                        'level': zs.level if hasattr(zs, 'level') else 0,
                        'high': float(zs.high) if hasattr(zs, 'high') else 0.0,
                        'low': float(zs.low) if hasattr(zs, 'low') else 0.0,
                        'begin_time': int(zs.begin.time.timestamp()) if hasattr(zs.begin) and hasattr(zs.begin, 'time') else 0,
                        'end_time': int(zs.end.time.timestamp()) if hasattr(zs.end) and hasattr(zs.end, 'time') else 0
                    })

            return {
                'instance_id': instance_id,
                'symbol': instance['symbol'],
                'timeframe': instance['timeframe'],
                'created_at': instance['created_at'],
                'last_update': instance['last_update'],
                'buy_sell_points': buy_sell_points,
                'zs_list': zs_list,
                'analysis_time': time.time()
            }

        except Exception as e:
            logger.error(f"Failed to get Chan analysis result: {e}")
            return None


# ==================== Scenario 3: RESTful API Integration Example ====================

class TradingViewRESTClient:
    """TradingView REST API Client"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize REST client"""
        self.base_url = base_url.rstrip('/')
        self.session = None

    async def __aenter__(self):
        """Async context manager entry"""
        import aiohttp
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def get_historical_data(self, symbol: str, timeframe: str,
                                count: int = 500, **kwargs) -> Optional[Dict[str, Any]]:
        """Fetch historical data"""
        if not self.session:
            raise RuntimeError("Client not initialized, please use 'with' statement")

        url = f"{self.base_url}/api/v1/data/historical"

        payload = {
            'symbol': symbol,
            'timeframe': timeframe,
            'count': count,
            **kwargs
        }

        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to fetch historical data: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Request historical data failed: {e}")
            return None

    async def get_health_status(self) -> Optional[Dict[str, Any]]:
        """Get health status"""
        if not self.session:
            raise RuntimeError("Client not initialized")

        url = f"{self.base_url}/api/v1/health"

        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None

        except Exception as e:
            logger.error(f"Failed to get health status: {e}")
            return None

    async def get_supported_symbols(self) -> Optional[List[str]]:
        """Get supported symbols"""
        if not self.session:
            raise RuntimeError("Client not initialized")

        url = f"{self.base_url}/api/v1/symbols"

        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('data', {}).get('symbols', [])
                else:
                    return None

        except Exception as e:
            logger.error(f"Failed to get symbol list: {e}")
            return None


# ==================== Scenario 4: WebSocket Real-time Data Integration ====================

class TradingViewWebSocketClient:
    """TradingView WebSocket Client"""

    def __init__(self, ws_url: str = "ws://localhost:8000/ws/realtime"):
        """Initialize WebSocket client"""
        self.ws_url = ws_url
        self.websocket = None
        self.subscriptions = set()
        self.message_handlers = {}
        self.running = False

    async def connect(self) -> bool:
        """Connect to WebSocket"""
        try:
            import websockets

            self.websocket = await websockets.connect(self.ws_url)
            self.running = True

            # Start message processing loop
            asyncio.create_task(self._message_loop())

            logger.info(f"WebSocket connected successfully: {self.ws_url}")
            return True

        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            return False

    async def disconnect(self):
        """Disconnect WebSocket"""
        self.running = False

        if self.websocket:
            await self.websocket.close()

        logger.info("WebSocket disconnected")

    async def subscribe(self, symbols: List[str], timeframes: List[str] = None):
        """Subscribe to real-time data"""
        if not self.websocket:
            logger.error("WebSocket not connected")
            return

        message = {
            'type': 'subscribe',
            'symbols': symbols,
            'timeframes': timeframes or ['1'],
            'timestamp': int(time.time())
        }

        await self.websocket.send(json.dumps(message))

        for symbol in symbols:
            self.subscriptions.add(symbol)

        logger.info(f"Subscribed to real-time data: {symbols}")

    async def unsubscribe(self, symbols: List[str], timeframes: List[str] = None):
        """Unsubscribe from data"""
        if not self.websocket:
            return

        message = {
            'type': 'unsubscribe',
            'symbols': symbols,
            'timeframes': timeframes or ['1'],
            'timestamp': int(time.time())
        }

        await self.websocket.send(json.dumps(message))

        for symbol in symbols:
            self.subscriptions.discard(symbol)

        logger.info(f"Unsubscribed: {symbols}")

    def register_message_handler(self, message_type: str, handler: callable):
        """Register message handler"""
        self.message_handlers[message_type] = handler

    async def _message_loop(self):
        """Message processing loop"""
        while self.running and self.websocket:
            try:
                message = await self.websocket.recv()
                data = json.loads(message)

                message_type = data.get('type')
                if message_type in self.message_handlers:
                    handler = self.message_handlers[message_type]
                    await handler(data)

            except Exception as e:
                logger.error(f"Failed to handle WebSocket message: {e}")
                break


# ==================== Usage Examples ====================

async def example_trading_core_integration():
    """Example 1: Integration into trading_core"""
    logger.info("=== Example 1: trading_core Integration ===")

    # Initialize data source
    data_source = TradingViewDataSource({
        'cache_db_path': 'example_trading_core.db',
        'max_cache_size': 1000
    })

    if await data_source.initialize():
        # Fetch historical data
        market_data = await data_source.get_historical_data(
            'BINANCE:BTCUSDT', '15', count=500
        )

        if market_data:
            logger.info(f"Fetched {len(market_data.klines)} K-line data points")

            # Subscribe to real-time data
            async def realtime_callback(data):
                logger.info(f"Received real-time data: {data.get('symbol')} = {data.get('price')}")

            await data_source.subscribe_realtime_data(
                ['BINANCE:BTCUSDT', 'BINANCE:ETHUSDT'],
                realtime_callback
            )

        # Get health status
        health = await data_source.get_health_status()
        logger.info(f"Data source health status: {health.get('status')}")

        await data_source.shutdown()


async def example_chanpy_integration():
    """Example 2: Integration into chanpy"""
    logger.info("=== Example 2: chanpy Integration ===")

    # Initialize data feeder
    feeder = ChanpyDataFeeder({
        'cache_db_path': 'example_chanpy.db'
    })

    if await feeder.initialize():
        # Create Chan analysis
        instance_id = await feeder.create_chan_analysis(
            'BINANCE:BTCUSDT', '15',
            {'bi_strict': True, 'trigger_step': True}
        )

        if instance_id:
            logger.info(f"Created Chan analysis instance: {instance_id}")

            # Wait for some time and then update
            await asyncio.sleep(2)

            # Update analysis
            if await feeder.update_chan_analysis(instance_id):
                # Get analysis result
                result = feeder.get_chan_analysis_result(instance_id)
                if result:
                    logger.info(f"Buy/Sell points: {len(result.get('buy_sell_points', []))}")
                    logger.info(f"Centers (ZhongShu): {len(result.get('zs_list', []))}")


async def example_rest_api():
    """Example 3: REST API Usage"""
    logger.info("=== Example 3: REST API Integration ===")

    async with TradingViewRESTClient() as client:
        # Get health status
        health = await client.get_health_status()
        if health:
            logger.info(f"API service status: {health.get('status')}")

        # Get supported symbols
        symbols = await client.get_supported_symbols()
        if symbols:
            logger.info(f"Supported symbols count: {len(symbols)}")

        # Fetch historical data
        data = await client.get_historical_data('BINANCE:BTCUSDT', '15', count=100)
        if data and data.get('status') == 'success':
            klines = data.get('data', {}).get('klines', [])
            logger.info(f"Fetched {len(klines)} historical K-lines")


async def example_websocket():
    """Example 4: WebSocket Real-time Data"""
    logger.info("=== Example 4: WebSocket Real-time Data ===")

    client = TradingViewWebSocketClient()

    # Register message handlers
    async def handle_realtime_data(data):
        symbol = data.get('symbol')
        price = data.get('data', {}).get('price')
        logger.info(f"Real-time data: {symbol} = ${price}")

    async def handle_subscribed(data):
        logger.info(f"Subscription confirmed: {data.get('symbols')}")

    client.register_message_handler('realtime_data', handle_realtime_data)
    client.register_message_handler('subscribed', handle_subscribed)

    if await client.connect():
        # Subscribe to data
        await client.subscribe(['BINANCE:BTCUSDT', 'BINANCE:ETHUSDT'])

        # Wait for data reception
        await asyncio.sleep(10)

        # Unsubscribe and disconnect
        await client.unsubscribe(['BINANCE:BTCUSDT'])
        await client.disconnect()


async def run_all_examples():
    """Run all examples"""
    logger.info("Starting TradingView integration examples")

    try:
        # Note: These examples require corresponding services to be running
        # await example_trading_core_integration()
        # await example_chanpy_integration()
        # await example_rest_api()
        # await example_websocket()

        # Mock example run completion
        logger.info("All integration examples mock run completed")

    except Exception as e:
        logger.error(f"Failed to run examples: {e}")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Run examples
    asyncio.run(run_all_examples())