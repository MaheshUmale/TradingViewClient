#!/usr/bin/env python3
"""
User Login Example
"""
import asyncio
import os
from getpass import getpass

from ..misc import (
    login_user,
    get_user,
    get_private_indicators
)



async def main():
    """
    Example of retrieving user information.

    To log in and access more data, provide the session token and signature.
    """
    print("TradingView User Login Example")
    print("----------------------------")

    # Get credentials from environment or user input
    username = os.environ.get('TV_USERNAME') or input("Enter username or email: ")
    password = os.environ.get('TV_PASSWORD') or getpass("Enter password: ")

    try:
        # Attempt to log in
        print("\nLogging in...")
        user = await login_user(username, password)

        print(f"\nLogin successful!")
        print(f"Username: {user.username}")
        print(f"User ID: {user.id}")
        print(f"Join Date: {user.join_date}")
        print(f"Followers: {user.followers}")
        print(f"Following: {user.following}")

        # Retrieve private indicators
        print("\nRetrieving private indicators...")
        indicators = await get_private_indicators(user.session, user.signature)

        if indicators:
            print(f"\nFound {len(indicators)} private indicators:")
            for i, ind in enumerate(indicators[:5], 1):
                print(f"{i}. {ind.name} (ID: {ind.id})")

            if len(indicators) > 5:
                print(f"...and {len(indicators) - 5} more")
        else:
            print("\nNo private indicators found")

        # Example of saving session info
        print("\nSession Information:")
        print("To use this session elsewhere, save the following:")
        print(f"Session ID: {user.session}")
        print(f"Signature:  {user.signature}")

        # Demonstrate using saved session to get user info
        print("\nUsing session ID to retrieve user info...")
        user2 = await get_user(user.session, user.signature)
        print(f"Verification successful: {user2.username} (ID: {user2.id})")

    except Exception as e:
        print(f"\nLogin failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
