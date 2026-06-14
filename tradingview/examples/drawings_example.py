#!/usr/bin/env python3
"""
Example of retrieving chart drawings.
"""
import asyncio
import json
import os
from pprint import pprint

from ..misc import (
    get_chart_token,
    get_drawings,
    login_user
)

async def main():
    """Main function"""
    print("TradingView Chart Drawings Retrieval Example")
    print("------------------------------------------")

    # Requires a layout ID, which can be found in any saved TradingView chart URL.
    # e.g., 'abcdefgh' from https://www.tradingview.com/chart/abcdefgh/
    layout_id = input("Enter chart layout ID: ")
    if not layout_id:
        print("Error: Layout ID is required")
        return

    symbol = input("Enter market symbol (optional, e.g., BINANCE:BTCUSDT): ")

    # Determine whether to use authentication
    use_auth = input("Use authentication? (y/n): ").lower() == 'y'
    credentials = None

    if use_auth:
        # Get credentials from environment or user input
        username = os.environ.get('TV_USERNAME') or input("Enter username or email: ")
        password = os.environ.get('TV_PASSWORD') or input("Enter password: ")

        try:
            # Login
            print("\nLogging in...")
            user = await login_user(username, password)
            print(f"Login successful: {user.username}")

            credentials = {
                'id': user.id,
                'session': user.session,
                'signature': user.signature
            }
        except Exception as e:
            print(f"Login failed: {e}")
            return

    try:
        # Get chart token
        print("\nRetrieving chart token...")
        chart_token = await get_chart_token(layout_id, credentials)
        print(f"Token retrieved: {chart_token[:10]}...")

        # Retrieve drawings
        print("\nRetrieving chart drawings...")
        drawings = await get_drawings(layout_id, symbol, credentials)

        print(f"\nFound {len(drawings)} drawings:")

        # Group drawings by type
        drawing_types = {}
        for drawing in drawings:
            drawing_type = drawing.get('type', 'unknown')
            if drawing_type not in drawing_types:
                drawing_types[drawing_type] = 0
            drawing_types[drawing_type] += 1

        # Display drawing type statistics
        print("\nDrawing Type Statistics:")
        for drawing_type, count in drawing_types.items():
            print(f"{drawing_type}: {count}")

        # Show details of the first drawing
        if drawings:
            print("\nExample Drawing Details (First):")
            first_drawing = drawings[0]
            print(f"Type: {first_drawing.get('type', 'unknown')}")
            print(f"ID:   {first_drawing.get('id', 'unknown')}")

            # Show position information if available
            if 'points' in first_drawing:
                print("\nLocation Points:")
                for i, point in enumerate(first_drawing['points']):
                    print(f"Point {i+1}: {point}")

            # Show style information if available
            if 'style' in first_drawing:
                print("\nStyle:")
                for key, value in first_drawing['style'].items():
                    print(f"  {key}: {value}")

    except Exception as e:
        print(f"Failed to retrieve chart drawings: {e}")

if __name__ == "__main__":
    asyncio.run(main())
