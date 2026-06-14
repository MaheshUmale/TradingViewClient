#!/usr/bin/env python3
"""
This example creates a chart and attaches all private indicators belonging to the user.
"""
import asyncio
import os
import sys

from .. import Client, get_private_indicators

async def main():
    """Main function"""
    # Check for required environment variables
    session = os.environ.get('TV_SESSION')
    signature = os.environ.get('TV_SIGNATURE')
    
    session ='zhmz7oc3t9bjv4kkeuhlt49nz36kl19q'
    signature='v3:DuhNyx1YpzkFphNntBBH3M7D4wEYVUeSUWoPrsaipOA='
    if not session or not signature:
        raise ValueError('Please set TV_SESSION and TV_SIGNATURE environment variables')

    # Create and connect client
    client = Client(token=session, signature=signature)
    await client.connect()

    # Create chart session
    chart = client.Session.Chart()

    # Set market
    chart.set_market('BINANCE:BTCEUR', {
        'timeframe': 'D',
    })

    # Retrieve all private indicators
    print('Retrieving private indicators...')
    indic_list = await get_private_indicators(session, signature)

    if not indic_list:
        print('No private indicators found in your account')
        await client.end()
        return

    print(f'Found {len(indic_list)} private indicators')

    # Track loading progress
    loaded_indicators = 0
    total_indicators = len(indic_list)

    # Process each indicator
    for indic in indic_list:
        try:
            # Fetch full indicator definition
            print(f'Loading indicator: {indic.name}...')
            # private_indic = await indic.get()

            # Create study for the indicator
            # indicator = chart.Study(private_indic)

            # # Callback when indicator study is ready
            # def on_ready():
            #     nonlocal loaded_indicators
            #     print(f'Indicator {indic.name} loaded!')
            #     loaded_indicators += 1

            #     # Close connection once all indicators are loaded
            #     if loaded_indicators == total_indicators:
            #         print('All indicators loaded, shutting down...')
            #         asyncio.create_task(client.end())

            # indicator.on_ready(on_ready)

            # # Callback when indicator data updates
            # def on_update():
            #     if not indicator.periods:
            #         return

            #     print(f'Plot values for {indic.name}:', indicator.periods[0] if indicator.periods else None)

            #     # Show strategy report if available
            #     if indicator.strategy_report:
            #         print(f'Strategy report for {indic.name}:', indicator.strategy_report)

            # indicator.on_update(on_update)

        except Exception as e:
            print(f'Error loading indicator {indic.name}: {e}')
            loaded_indicators += 1

    # Immediate shutdown if no indicators or all failed
    if loaded_indicators == total_indicators:
        await client.end()
    else:
        # Wait up to 60 seconds for updates
        try:
            await asyncio.wait_for(asyncio.sleep(60), timeout=60)
            print('Wait timeout reached, exiting...')
            await client.end()
        except asyncio.CancelledError:
            pass

if __name__ == '__main__':
    asyncio.run(main())
