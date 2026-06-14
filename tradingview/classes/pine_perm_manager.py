"""
Pine Permission Manager Class
"""
import aiohttp
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from ..utils import gen_auth_cookies

class PinePermManager:
    """
    Manager for handling TradingView Pine Script indicator permissions.
    """
    def __init__(self, session_id: str, signature: str, pine_id: str):
        """
        Initialize the Pine permission manager.

        Args:
            session_id: TradingView session ID.
            signature: Authentication signature.
            pine_id: The ID of the Pine indicator to manage.
        """
        if not session_id:
            raise ValueError("Session ID must be provided")
        if not signature:
            raise ValueError("Signature must be provided")
        if not pine_id:
            raise ValueError("Pine ID must be provided")

        self.session_id = session_id
        self.signature = signature
        self.pine_id = pine_id

    async def get_users(self, limit: int = 10, order: str = '-created') -> List[Dict[str, Any]]:
        """
        Retrieve the list of authorized users.

        Args:
            limit: Maximum number of users to retrieve.
            order: Sorting order for the results.

        Returns:
            List[Dict]: List of user objects.
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://www.tradingview.com/pine_perm/list_users/?limit={limit}&order_by={order}",
                data=f"pine_id={self.pine_id.replace(';', '%3B')}",
                headers={
                    "origin": "https://www.tradingview.com",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "cookie": gen_auth_cookies(self.session_id, self.signature)
                }
            ) as resp:
                if resp.status >= 400:
                    error_data = await resp.json()
                    raise ValueError(error_data.get('detail', 'Invalid credentials or Pine ID'))

                data = await resp.json()
                return data.get('results', [])

    async def add_user(self, username: str, expiration: Optional[datetime] = None) -> str:
        """
        Add an authorized user.

        Args:
            username: The username to authorize.
            expiration: Optional expiration time for the authorization.

        Returns:
            str: The status of the operation.
        """
        data = f"pine_id={self.pine_id.replace(';', '%3B')}&username_recip={username}"
        if expiration:
            data += f"&expiration={expiration.isoformat()}"

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://www.tradingview.com/pine_perm/add/",
                data=data,
                headers={
                    "origin": "https://www.tradingview.com",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "cookie": gen_auth_cookies(self.session_id, self.signature)
                }
            ) as resp:
                if resp.status >= 400:
                    error_data = await resp.json()
                    raise ValueError(error_data.get('detail', 'Invalid credentials or Pine ID'))

                data = await resp.json()
                return data.get('status', None)

    async def modify_expiration(self, username: str, expiration: Optional[datetime] = None) -> str:
        """
        Modify the authorization expiration time for a user.

        Args:
            username: The username to modify.
            expiration: The new expiration time.

        Returns:
            str: The status of the operation.
        """
        data = f"pine_id={self.pine_id.replace(';', '%3B')}&username_recip={username}"
        if expiration:
            data += f"&expiration={expiration.isoformat()}"

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://www.tradingview.com/pine_perm/modify_user_expiration/",
                data=data,
                headers={
                    "origin": "https://www.tradingview.com",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "cookie": gen_auth_cookies(self.session_id, self.signature)
                }
            ) as resp:
                if resp.status >= 400:
                    error_data = await resp.json()
                    raise ValueError(error_data.get('detail', 'Invalid credentials or Pine ID'))

                data = await resp.json()
                return data.get('status', None)

    async def remove_user(self, username: str) -> str:
        """
        Remove an authorized user.

        Args:
            username: The username to remove.

        Returns:
            str: The status of the operation.
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://www.tradingview.com/pine_perm/remove/",
                data=f"pine_id={self.pine_id.replace(';', '%3B')}&username_recip={username}",
                headers={
                    "origin": "https://www.tradingview.com",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "cookie": gen_auth_cookies(self.session_id, self.signature)
                }
            ) as resp:
                if resp.status >= 400:
                    error_data = await resp.json()
                    raise ValueError(error_data.get('detail', 'Invalid credentials or Pine ID'))

                data = await resp.json()
                return data.get('status', None)
