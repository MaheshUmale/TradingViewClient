#!/usr/bin/env python3
"""
This example tests the search functionality for markets and indicators.
"""
import asyncio
import json
import sys
from pprint import pprint

from .. import search_market_v3, search_indicator

async def main():
    """Main function"""
    print("===== Testing Search Functionality =====")

    # Search for markets
    print("\nSearching for market: BINANCE:")
    try:
        markets = await search_market_v3('BINANCE:')
        print(f"Found {len(markets)} markets:")

        # Show first 5 results
        for i, market in enumerate(markets[:5], 1):
            print(f"{i}. {market.id} - {market.description} ({market.type})")

        if len(markets) > 5:
            print(f"...and {len(markets) - 5} more")

        # Search for a specific symbol
        if markets:
            market_name = 'BTCUSDT'
            print(f"\nSearching for specific symbol: {market_name}")

            try:
                btc_markets = await search_market_v3(f'BINANCE:{market_name}')

                if btc_markets:
                    market = btc_markets[0]
                    print(f"Found symbol: {market.id}")
                    print(f"Description:  {market.description}")
                    print(f"Exchange:     {market.exchange}")
                    print(f"Type:         {market.type}")

                    # Retrieve technical analysis data
                    print("\nRetrieving technical analysis...")
                    try:
                        ta_data = await market.get_ta()
                        if ta_data:
                            print("Technical Analysis Results:")
                            pprint(ta_data)
                        else:
                            print("Unable to retrieve technical analysis data")
                    except Exception as e:
                        print(f"Error retrieving technical analysis: {str(e)}")
                else:
                    print(f"No matching symbol found for: {market_name}")
            except Exception as e:
                print(f"Error searching for specific symbol: {str(e)}")
    except Exception as e:
        print(f"Error searching for markets: {str(e)}")

    # Search for indicators
    print("\nSearching for indicator: RSI")
    try:
        indicators = await search_indicator('RSI')
        print(f"Found {len(indicators)} indicators:")

        # Show first 5 results
        for i, indicator in enumerate(indicators[:5], 1):
            print(f"{i}. {indicator.name} - Author: {indicator.author['username']} - Type: {indicator.type}")

        if len(indicators) > 5:
            print(f"...and {len(indicators) - 5} more")

        # Search for another type of indicator
        print("\nSearching for indicator: MACD")
        try:
            macd_indicators = await search_indicator('MACD')
            print(f"Found {len(macd_indicators)} MACD-related indicators")

            # Show difference between built-in and custom indicators
            print("\nIndicator Classification:")
            builtin_count = sum(1 for ind in indicators if ind.author['username'] == '@TRADINGVIEW@')
            custom_count = len(indicators) - builtin_count
            print(f"Built-in indicators: {builtin_count}")
            print(f"Custom indicators:   {custom_count}")
        except Exception as e:
            print(f"Error searching for MACD indicator: {str(e)}")
    except Exception as e:
        print(f"Error searching for RSI indicator: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\nProgram interrupted by user')
        sys.exit(0)
    except Exception as e:
        print(f"Program execution error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
