#!/usr/bin/env python3
"""
Advanced Historical K-line Data Acquisition Tool
Supports command line arguments, custom time ranges, and multiple data export formats.

Usage Examples:
python advanced_historical_klines.py --symbol=BINANCE:BTCUSDT --timeframe=60 --days=30
python advanced_historical_klines.py --symbol=NASDAQ:AAPL --timeframe=D --from=2023-01-01 --to=2023-12-31

python -m tradingview.examples.advanced_historical_klines --symbol=BINANCE:BTCUSDT --timeframe=60 --days=7 --debug
"""
import asyncio
import argparse
import json
import csv
import os
import sys
import time
from datetime import datetime
from pprint import pprint

# Add project root directory to system path - must be done before importing tradingview
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import dotenv and load environment variables
from dotenv import load_dotenv
load_dotenv()
print('Loading configuration from .env...')

# Import tradingview modules
from tradingview import Client, get_indicator

# Debug mode
DEBUG = True

def debug_print(*args):
    """Debug print helper function"""
    if DEBUG:
        print("[DEBUG]", *args)

# Parse command line arguments
def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Advanced Historical K-line Data Acquisition Tool')
    parser.add_argument('--symbol', type=str, default='BINANCE:BTCUSDT', help='Trading symbol (e.g., BINANCE:BTCUSDT)')
    parser.add_argument('--timeframe', type=str, default='60', help='Timeframe (e.g., 60 for 1h, D for daily)')
    parser.add_argument('--range', type=int, default=500, help='Number of K-lines to fetch')
    parser.add_argument('--output', type=str, default='data', help='Output directory')
    parser.add_argument('--format', type=str, default='json', choices=['json', 'csv'], help='Output format')
    parser.add_argument('--file', type=str, help='Output filename (without extension)')
    parser.add_argument('--indicators', type=str, default='false', choices=['true', 'false'], help='Whether to include indicator data')
    parser.add_argument('--days', type=int, help='Fetch data for the last N days')
    parser.add_argument('--from', dest='from_date', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--to', dest='to_date', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--token', type=str, help='TradingView session ID')
    parser.add_argument('--signature', type=str, help='TradingView signature')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')

    return parser.parse_args()

# Process date parameters
def process_date_params(args):
    """Process date-related parameters"""
    config = {}

    # If days specified
    if args.days:
        config['to'] = int(time.time())
        config['from'] = config['to'] - (args.days * 86400)
    else:
        # If specific start/end dates specified
        if args.from_date:
            config['from'] = int(datetime.strptime(args.from_date, '%Y-%m-%d').timestamp())

        if args.to_date:
            config['to'] = int(datetime.strptime(args.to_date, '%Y-%m-%d').timestamp())
        else:
            config['to'] = int(time.time())

    return config

async def main():
    """Main function"""
    # Parse command line arguments
    args = parse_args()

    # Set debug mode
    global DEBUG
    DEBUG = args.debug

    # Process date parameters
    date_config = process_date_params(args)

    # Merge all configurations
    config = {
        'symbol': args.symbol,
        'timeframe': args.timeframe,
        'range': args.range,
        'output_dir': args.output,
        'format': args.format,
        'include_indicators': args.indicators.lower() == 'true',
        'file_name': args.file,
        'token': args.token,
        'signature': args.signature,
        **date_config
    }

    # Generate default filename if not specified
    if not config['file_name']:
        symbol = config['symbol'].replace(':', '_')
        timeframe = config['timeframe']
        date_str = datetime.now().strftime('%Y-%m-%d')
        config['file_name'] = f"{symbol}_{timeframe}_{date_str}"

    # Ensure output directory exists
    os.makedirs(config['output_dir'], exist_ok=True)

    # Display configuration info
    print('=== Historical K-line Data Acquisition Tool ===')
    print('Configuration:')
    print(f"Symbol: {config['symbol']}")
    print(f"Timeframe: {config['timeframe']}")
    if 'from' in config:
        print(f"Start Time: {datetime.fromtimestamp(config['from']).strftime('%Y-%m-%d %H:%M:%S')}")
    if 'to' in config:
        print(f"End Time: {datetime.fromtimestamp(config['to']).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Output Format: {config['format']}")
    print(f"Output File: {os.path.join(config['output_dir'], config['file_name'] + '.' + config['format'])}")
    print('============================')

    # Get authentication info from environment or parameters
    session = os.environ.get('TV_SESSION')
    signature = os.environ.get('TV_SIGNATURE')

    # Use command line arguments if environment variables are missing
    if not session and config['token']:
        session = config['token']
    if not signature and config['signature']:
        signature = config['signature']

    # Check for sufficient authentication info
    if not session or not signature:
        print("Error: TradingView authentication info required.")
        print("Please set TV_SESSION and TV_SIGNATURE environment variables, or use --token and --signature parameters.")
        return

    print(f"Using Token: {session}")
    print(f"Using Signature: {signature}")

    try:
        # Create client
        debug_print("Creating TradingView client...")
        client = Client(
            token=session,
            signature=signature,
            DEBUG=DEBUG
        )

        # Connect to TradingView
        debug_print("Connecting to TradingView server...")
        await client.connect()
        debug_print("Connection successful!")

        # Create Chart session
        debug_print("Creating Chart session...")
        chart = client.Session.Chart()

        # Indicator data storage
        indicators_data = {}

        # Error handling
        def on_error(*err):
            print('Error:', *err)
            asyncio.create_task(client.end())

        chart.on_error(on_error)

        # Setup timeout task
        timeout_task = asyncio.create_task(
            asyncio.sleep(90)  # 90 second timeout
        )

        # Ensure WebSocket connection is stable
        debug_print("Waiting for WebSocket connection to stabilize...")
        await asyncio.sleep(2)

        # Setup market parameters
        market_params = {
            'timeframe': config['timeframe'],
            'range': config['range']
        }

        # Add time range parameters
        if 'to' in config:
            market_params['to'] = config['to']
        if 'from' in config:
            market_params['from'] = config['from']

        debug_print(f"Setting market parameters: {market_params}")

        # Set market
        debug_print(f"Setting symbol: {config['symbol']}")
        chart.set_market(config['symbol'], market_params)

        # Allow time for async task creation
        await asyncio.sleep(1)

        # Data loaded flag
        data_loaded = False

        # Callback for successful symbol load
        def on_symbol_loaded():
            debug_print("Symbol loaded successfully!")
            print(f"Loading data for \"{chart.infos.description}\"...")

            # Add indicators if requested
            if config['include_indicators']:
                asyncio.create_task(add_indicators())

        chart.on_symbol_loaded(on_symbol_loaded)

        # Callback for data updates
        def on_update():
            nonlocal data_loaded
            if data_loaded:
                return

            # Check data validity
            if not hasattr(chart, 'periods') or not chart.periods:
                debug_print("Waiting for data...")
                return

            print(f"Received {len(chart.periods)} K-line records")

            try:
                # Process data records
                kline_data = []
                for period in chart.periods:
                    try:
                        # Ensure required attributes exist
                        candle = {
                            'time': getattr(period, 'time', 0),
                            'datetime': datetime.fromtimestamp(getattr(period, 'time', 0)).strftime('%Y-%m-%d %H:%M:%S'),
                            'open': getattr(period, 'open', 0),
                            'high': getattr(period, 'max', 0),
                            'low': getattr(period, 'min', 0),
                            'close': getattr(period, 'close', 0),
                            'volume': getattr(period, 'volume', 0)
                        }
                        kline_data.append(candle)
                    except Exception as e:
                        print(f"Error processing K-line record: {e}")
                        continue

                # If no valid data yet
                if not kline_data:
                    print("No valid data received yet, continuing to wait...")
                    return

                # Sort by time ascending
                kline_data.sort(key=lambda x: x['time'])

                # Display time range
                if kline_data:
                    print(f"Data time range: {kline_data[0]['datetime']} to {kline_data[-1]['datetime']}")

                # Merge indicator data if available
                if indicators_data:
                    for candle in kline_data:
                        for indicator_name, indicator_values in indicators_data.items():
                            # Find indicator data for matching timestamp
                            for ind_data in indicator_values:
                                if ind_data['time'] == candle['time']:
                                    candle[indicator_name] = ind_data['value']
                                    break

                # Export processed data
                export_data(kline_data)

                # Mark as loaded
                data_loaded = True

                # Cancel timeout task
                try:
                    timeout_task.cancel()
                except Exception:
                    pass

                # Shutdown connection
                print('Data acquisition complete, closing connection...')
                asyncio.create_task(close_connection())
            except Exception as e:
                print(f"Error handling update: {e}")
                import traceback
                traceback.print_exc()

        chart.on_update(on_update)

        async def close_connection():
            """Shutdown connection"""
            print("Closing connection...")
            await asyncio.sleep(1)
            # Remove chart session
            if hasattr(chart, 'remove'):
                await chart.remove()
            elif hasattr(chart, 'delete'):
                chart.delete()
            else:
                print("Warning: Could not find removal method for chart session")

            await client.end()
            print("Connection closed")

        # Export data to file
        def export_data(data):
            """Export data to file"""
            file_path = os.path.join(config['output_dir'], config['file_name'] + '.' + config['format'])

            try:
                if config['format'] == 'json':
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2)
                elif config['format'] == 'csv':
                    if not data:
                        return

                    with open(file_path, 'w', newline='', encoding='utf-8') as f:
                        # Extract all field names
                        headers = list(data[0].keys())
                        writer = csv.DictWriter(f, fieldnames=headers)
                        writer.writeheader()
                        writer.writerows(data)
                else:
                    raise ValueError(f"Unsupported output format: {config['format']}")

                print(f"Data saved to: {file_path}")
            except Exception as e:
                print('Error saving data:', e)

        # Add technical indicators
        async def add_indicators():
            """Add technical indicators to the chart"""
            print('Adding technical indicators...')

            try:
                # Example indicators
                indicators = [
                    {'name': 'EMA20', 'type': 'STD;EMA', 'options': {'Length': 20}},
                    {'name': 'SMA50', 'type': 'STD;SMA', 'options': {'Length': 50}},
                    {'name': 'RSI14', 'type': 'STD;RSI', 'options': {'Length': 14}}
                ]

                for indicator in indicators:
                    indic = await get_indicator(indicator['type'])

                    # Set indicator parameters
                    for option_name, option_value in indicator['options'].items():
                        indic.set_option(option_name, option_value)

                    # Create indicator study
                    study = chart.Study(indic)

                    # Initialize storage for this indicator
                    indicators_data[indicator['name']] = []

                    # Callback for indicator updates
                    def create_update_handler(indicator_name):
                        def on_indicator_update():
                            nonlocal study
                            if not study.periods:
                                return

                            # Store indicator data points
                            indicators_data[indicator_name] = [
                                {'time': period.time, 'value': period.plot_0}
                                for period in study.periods
                            ]

                            print(f"{indicator_name} indicator updated, total {len(indicators_data[indicator_name])} records")

                        return on_indicator_update

                    study.on_update(create_update_handler(indicator['name']))

                    # Allow time for study creation
                    await asyncio.sleep(0.5)

            except Exception as e:
                print('Failed to add indicators:', e)
                import traceback
                traceback.print_exc()

        # Regular status check task
        async def status_check():
            """Periodically check connection and data loading progress"""
            while not data_loaded:
                debug_print(f"Connection: {'Open' if client.is_open else 'Closed'}, Logged in: {'Yes' if client.is_logged else 'No'}")
                if hasattr(chart, 'periods') and chart.periods:
                    debug_print(f"Loaded K-lines: {len(chart.periods)}")
                else:
                    debug_print("No K-line data received yet")
                await asyncio.sleep(5)

        # Start status monitoring
        status_check_task = asyncio.create_task(status_check())

        try:
            # Wait for data or timeout
            await timeout_task
            print("Operation timed out (symbol may not exist or network issues)")
            status_check_task.cancel()
            await client.end()
        except asyncio.CancelledError:
            # Task cancelled because data was loaded
            status_check_task.cancel()

    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\nOperation interrupted by user')
        sys.exit(0)
