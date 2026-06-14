#!/usr/bin/env python3
"""
This example demonstrates how to retrieve historical K-line data.
You can specify the trading symbol, timeframe, and time range.
"""
import asyncio
import json
import time
from datetime import datetime
import os
import sys

# Add project root directory to system path - must be done before importing tradingview
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import dotenv and load environment variables
from dotenv import load_dotenv
load_dotenv()
print('Loading configuration from .env...')

# Import tradingview modules
from tradingview import Client
from tradingview.chart.session import ChartSession

# python -m tradingview.examples.historical_klines
async def main():
    """Main function"""
    # Create a new TradingView client
    # Provide session and signature if you want to login for more data access

    session = os.environ.get('TV_SESSION')
    signature = os.environ.get('TV_SIGNATURE')

    if not session or not signature:
        raise ValueError('Please set TV_SESSION and TV_SIGNATURE environment variables')

    client = Client(
        token=session,
        signature=signature
    )

    # Connect to TradingView
    await client.connect()

    # Initialize Chart session
    chart: ChartSession = client.Session.Chart()

    # Set configuration parameters
    config = {
        'symbol': 'BINANCE:BTCUSDT',  # Trading symbol
        'timeframe': '60',           # Timeframe (in minutes, or 'D' for daily)
        'range': 500,                # Number of K-lines to retrieve
        'to': int(time.time()),      # End timestamp (defaults to current time)
        # 'from': 1672531200,        # Start timestamp (optional if to and range are set)
        'save_to_file': True,        # Whether to save data to a file
        'file_name': 'btcusdt_1h_data.json' # Filename for saving
    }

    # Set market and parameters
    chart.set_market(config['symbol'], {
        'timeframe': config['timeframe'],
        'range': config['range'],
        'to': config['to']
    })

    # Error handling
    def on_error(*err):
        print('Error fetching data:', *err)
        asyncio.create_task(client.end())

    chart.on_error(on_error)

    # Callback when symbol is loaded
    def on_symbol_loaded():
        print(f"Symbol \"{chart.infos.description}\" loaded successfully!")
        print(f"Exchange: {chart.infos.exchange}")
        print(f"Timeframe: {config['timeframe']}")
        print(f"Requested count: {config['range']}")

    chart.on_symbol_loaded(on_symbol_loaded)

    # Flag for data completion
    data_loaded = False

    # Callback when price data updates
    def on_update():
        nonlocal data_loaded
        if data_loaded or not chart.periods or not chart.periods[0]:
            return

        print(f"Successfully retrieved {len(chart.periods)} K-line records")

        # Process and format data
        kline_data = [{
            'time': period.time,
            'datetime': datetime.fromtimestamp(period.time).isoformat(),
            'open': period.open,
            'high': period.max,
            'low': period.min,
            'close': period.close,
            'volume': period.volume
        } for period in chart.periods]

        # Sort by time ascending
        kline_data.sort(key=lambda x: x['time'])

        # Display first and last data points
        print('First record:', kline_data[0])
        print('Last record:', kline_data[-1])

        # Optional: Save to file
        if config['save_to_file']:
            with open(config['file_name'], 'w', encoding='utf-8') as f:
                json.dump(kline_data, f, indent=2)
            print(f"Data saved to file: {config['file_name']}")

        # Mark as loaded to avoid duplicate processing
        data_loaded = True

        # Close connection
        print('Data retrieval complete, closing connection...')
        asyncio.create_task(close_connection())

    chart.on_update(on_update)

    async def close_connection():
        """Shutdown connection"""
        await asyncio.sleep(1)
        chart.delete()
        await client.end()

    # Advanced: Fetch more historical data (optional)
    async def fetch_more_historical_data():
        """Fetch additional history"""
        print('Fetching more historical data...')
        chart.fetch_more(5)  # Fetch 5 more bars

    # Advanced: Add indicators (optional)
    async def add_indicator():
        """Add indicator data"""
        from tradingview import get_indicator

        print('Adding indicator data...')

        # Example with EMA
        ema = await get_indicator('STD;EMA')
        ema.set_option('Length', 14)  # Set EMA period

        ema_study = chart.Study(ema)

        def on_ema_update():
            if not ema_study.periods or not ema_study.periods[0]:
                return
            print('EMA indicator data updated')
            print('EMA data sample:', ema_study.periods[0])

        ema_study.on_update(on_ema_update)

    # Uncomment to test additional features:
    # await asyncio.sleep(3)
    # await fetch_more_historical_data()
    # await asyncio.sleep(2)
    # await add_indicator()

    # Wait for connection to close
    try:
        # Prevent infinite wait with a timeout
        await asyncio.wait_for(asyncio.sleep(60), timeout=60)
    except asyncio.TimeoutError:
        print("Operation timed out, forcing connection close")
        chart.delete()
        await client.end()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\nProgram interrupted by user')
