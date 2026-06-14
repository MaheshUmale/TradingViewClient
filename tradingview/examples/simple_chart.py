#!/usr/bin/env python3
"""
This example creates a simple BTCEUR daily chart.
"""
import asyncio
import os
import time

from .. import Client

# Example export for testing:
# export TV_SESSION=...
# export TV_SIGNATURE=...

async def main():
    """Main function"""
    print(" HARDCODED SESSSION AND SIGNATURE ")
    session = os.environ.get('TV_SESSION')
    signature = os.environ.get('TV_SIGNATURE')
    session ='zhmz7oc3t9bjv4kkeuhlt49nz36kl19q'
    signature='v3:DuhNyx1YpzkFphNntBBH3M7D4wEYVUeSUWoPrsaipOA='

    if not session or not signature:
        raise ValueError('Please set TV_SESSION and TV_SIGNATURE environment variables')

    client = Client(
        token=session,
        signature=signature
    )

    # Connect to TradingView
    await client.connect()

    chart = client.Session.Chart()  # Initialize Chart session
    print(" SETTING CHART --------")
    # Set market
    chart.set_market('COINBASE:BTCUSD', {
        'timeframe': 'D',
    })
    print(" SET CHART ")

    # Error handling
    def on_error(*err):
        print('Chart error:', *err)

    chart.on_error(on_error)

    # Callback when symbol is loaded
    def on_symbol_loaded():
        print(f'Market "{chart.infos.description}" loaded!')

    chart.on_symbol_loaded(on_symbol_loaded)

    # Callback when price updates
    def on_update():
        if not chart.periods or not chart.periods[0]:
            return
        print(f'[{chart.infos.description}]: {chart.periods[0].close} {chart.infos.currency_id}')

    chart.on_update(on_update)

    # Switch market after 5 seconds
    print('\nSwitching market to COINBASE:BTCUSD in 5 seconds...')
    await asyncio.sleep(5)

    print('Setting market to COINBASE:BTCUSD...')
    chart.set_market('COINBASE:BTCUSD', {
        'timeframe': 'D',
    })

    # Change timeframe after 5 seconds
    print('\nChanging timeframe to 15m in 5 seconds...')
    await asyncio.sleep(5)

    print('Setting timeframe to 15m...')
    chart.set_series('15')

    # Switch symbol again after 5 seconds
    print('\nSwitching to OANDA:XAUUSD in 5 seconds...')
    await asyncio.sleep(5)

    print('Setting symbol to OANDA:XAUUSD...')
    chart.set_market('OANDA:XAUUSD', {
        'timeframe': 'D',
    })

    # Close chart after 5 seconds
    print('\nClosing chart in 5 seconds...')
    await asyncio.sleep(5)

    print('Closing chart...')
    chart.delete()

    # Shutdown client after 5 seconds
    print('\nShutting down client in 5 seconds...')
    await asyncio.sleep(5)

    print('Shutting down client...')
    await client.end()

if __name__ == '__main__':
    asyncio.run(main())
