#!/usr/bin/env python3
"""
This example demonstrates synchronous retrieval of data for multiple indicators.
"""
import asyncio
import os

from ...tradingview import Client, get_indicator

async def main():
    """Main function"""
    # Check environment variables
    session = os.environ.get('TV_SESSION')
    signature = os.environ.get('TV_SIGNATURE')

    if not session or not signature:
        raise ValueError('Please set TV_SESSION and TV_SIGNATURE environment variables')

    # Create client
    client = Client(
        token=session,
        signature=signature
    )

    # Connect to TradingView
    await client.connect()

    # Helper function to fetch data for a single indicator
    async def get_indicator_data(indicator):
        """Retrieves data for a specific indicator"""
        # Create chart session
        chart = client.Session.Chart()
        chart.set_market('BINANCE:DOTUSDT')

        # Create indicator study
        study = chart.Study(indicator)

        print(f'Fetching data for "{indicator.description}"...')

        # Use Future to await the first update
        future = asyncio.Future()

        def on_update():
            if not future.done():
                future.set_result(study.periods)
                print(f'"{indicator.description}" fetch complete!')

        study.on_update(on_update)

        # Wait for data update
        return await future

    # Main execution
    print('Retrieving all indicators...')

    # Define indicator IDs to fetch
    indicator_ids = [
        'PUB;3lEKXjKWycY5fFZRYYujEy8fxzRRUyF3',
        'PUB;5nawr3gCESvSHQfOhrLPqQqT4zM23w3X',
        'PUB;vrOJcNRPULteowIsuP6iHn3GIxBJdXwT'
    ]

    # Get indicator definitions
    indicators = []
    for indic_id in indicator_ids:
        try:
            indicator = await get_indicator(indic_id)
            indicators.append(indicator)
        except Exception as e:
            print(f'Failed to retrieve indicator {indic_id}: {e}')

    # Retrieve data for all indicators concurrently
    indic_data = await asyncio.gather(*[get_indicator_data(indicator) for indicator in indicators])

    # Display results
    print('Indicator Data Results:')
    for i, data in enumerate(indic_data):
        print(f'Indicator {i+1}: {len(data)} records retrieved')
        if data:
            print(f'Data sample: {data[0]}')

    print('All tasks completed!')

    # Shutdown client
    await client.end()

if __name__ == '__main__':
    asyncio.run(main())
