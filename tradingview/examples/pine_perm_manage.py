#!/usr/bin/env python3
"""
This example creates a Pine permission manager and tests all available functions.
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta

from ...tradingview import PinePermManager

async def main():
    """Main function"""
    # Check environment variables
    session = os.environ.get('TV_SESSION')
    signature = os.environ.get('TV_SIGNATURE')

    if not session or not signature:
        raise ValueError('Please set TV_SESSION and TV_SIGNATURE environment variables')

    # Get Pine ID from command line arguments
    if len(sys.argv) < 2:
        raise ValueError('Please specify Pine ID as the first argument')

    pine_id = sys.argv[1]
    print('Pine ID:', pine_id)

    # Create Pine permission manager
    manager = PinePermManager(
        session,
        signature,
        pine_id
    )

    # Get authorized users
    users = await manager.get_users()
    print('Authorized users:', users)

    # Add user 'TradingView'
    print("Adding user 'TradingView'...")

    status = await manager.add_user('TradingView')
    if status == 'ok':
        print('User added successfully!')
    elif status == 'exists':
        print('User is already authorized')
    else:
        print('Unknown error occurred...')

    # Get authorized users again
    users = await manager.get_users()
    print('Authorized users:', users)

    # Modify expiration date
    print('Modifying expiration date...')

    # Add one day
    new_date = datetime.now() + timedelta(days=1)
    status = await manager.modify_expiration('TradingView', new_date)

    if status == 'ok':
        print('Expiration modified successfully!')
    else:
        print('Unknown error occurred...')

    # Get authorized users again
    users = await manager.get_users()
    print('Authorized users:', users)

    # Remove expiration date
    print('Removing expiration date...')

    status = await manager.modify_expiration('TradingView')

    if status == 'ok':
        print('Expiration removed successfully!')
    else:
        print('Unknown error occurred...')

    # Get authorized users again
    users = await manager.get_users()
    print('Authorized users:', users)

    # Remove user 'TradingView'
    print("Removing user 'TradingView'...")

    status = await manager.remove_user('TradingView')

    if status == 'ok':
        print('User removed successfully!')
    else:
        print('Unknown error occurred...')

    # Get authorized users again
    users = await manager.get_users()
    print('Authorized users:', users)

if __name__ == '__main__':
    asyncio.run(main())
