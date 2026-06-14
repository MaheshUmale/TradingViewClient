#!/usr/bin/env python3
"""
This example tests the getDrawings function.
Usage: python get_drawings_script.py <layout_id> [user_id]
"""
import asyncio
import sys
import os
from pprint import pprint

from chanlun.tradingview.misc_requests import get_drawings

async def main():
    """Main function"""
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Error: Please specify a layoutID")
        print("Usage: python get_drawings_script.py <layout_id> [user_id]")
        return

    layout_id = sys.argv[1]
    user_id = sys.argv[2] if len(sys.argv) > 2 else None

    # Get authentication info from environment variables
    session = os.environ.get('TV_SESSION')
    signature = os.environ.get('TV_SIGNATURE')

    # Create credentials dictionary
    credentials = None
    if session or signature:
        credentials = {
            'session': session,
            'signature': signature,
            'id': user_id
        }

    try:
        # Retrieve drawings
        drawings = await get_drawings(layout_id, None, credentials)

        # Print results
        print(f"Found {len(drawings)} drawings:", [
            {
                'id': d.get('id'),
                'symbol': d.get('symbol'),
                'type': d.get('type'),
                'text': d.get('state', {}).get('text')
            }
            for d in drawings
        ])
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
