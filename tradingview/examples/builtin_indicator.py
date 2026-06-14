#!/usr/bin/env python3
"""
This example tests built-in indicators, specifically volume-based indicators like Volume Profile.
"""
import asyncio
import os
import time

from ...tradingview import Client, BuiltInIndicator

async def main():
    """Main function"""
    # Create Volume Profile indicator
    volume_profile = BuiltInIndicator('VbPFixed@tv-basicstudies-241!')

    # Check if authentication is required
    need_auth = volume_profile.type not in [
        'VbPFixed@tv-basicstudies-241',
        'VbPFixed@tv-basicstudies-241!',
        'Volume@tv-basicstudies-241',
    ]

    if need_auth and (not os.environ.get('TV_SESSION') or not os.environ.get('TV_SIGNATURE')):
        raise ValueError('Please set your TV_SESSION and TV_SIGNATURE environment variables')

    # Create client
    client = Client(
        token=os.environ.get('TV_SESSION') if need_auth else None,
        signature=os.environ.get('TV_SIGNATURE') if need_auth else None
    )

    # Connect to TradingView
    await client.connect()

    # Create chart session
    chart = client.Session.Chart()

    # Set market
    chart.set_market('BINANCE:BTCEUR', {
        'timeframe': '60',
        'range': 1,
    })

    # Set necessary options based on indicator type
    volume_profile.set_option('first_bar_time', int(time.time()) - 10**8)
    # Additional options may be required for other indicators
    # volume_profile.set_option('first_visible_bar_time', int(time.time()) - 10**8)

    # Create indicator study
    vol = chart.Study(volume_profile)

    # Handle updates
    def on_update():
        # Filter and process Volume Profile data
        horiz_hists = [h for h in vol.graphic.horizHists if h.lastBarTime == 0]
        horiz_hists.sort(key=lambda h: h.priceHigh, reverse=True)

        for h in horiz_hists:
            # Calculate price midpoint and display volume bars
            mid_price = round((h.priceHigh + h.priceLow) / 2)
            up_vol = '_' * int(h.rate[0] / 3)
            down_vol = '_' * int(h.rate[1] / 3)
            print(f"~ {mid_price} € : {up_vol}{down_vol}")

        # Task complete, shutdown connection
        asyncio.create_task(client.end())

    vol.on_update(on_update)

    # Prevent infinite wait with a timeout
    try:
        await asyncio.wait_for(asyncio.sleep(30), timeout=30)
    except asyncio.TimeoutError:
        print("Operation timed out, forcing connection close")
        await client.end()

if __name__ == '__main__':
    asyncio.run(main())
