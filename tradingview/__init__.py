"""
TradingView API Client Main Module

This module provides access to the TradingView API for retrieving market data,
chart data, and technical indicators.
"""

# Client Core
from .client import Client

# Chart Module
from .chart import ChartSession, Study

# Quote Module
from .quote import QuoteSession, QuoteMarket

# Indicators and Technical Analysis
from .classes.builtin_indicator import BuiltInIndicator
from .classes.pine_indicator import PineIndicator
from .classes.pine_perm_manager import PinePermManager

# Utilities and Helper Functions
from .misc_requests import (
    fetch_scan_data,
    get_ta,
    search_market,
    search_market_v3,
    search_indicator,
    get_indicator,
    login_user,
    get_private_indicators,
    get_chart_token,
    get_drawings
)

# Tool Modules
from . import utils
from . import protocol
from . import tradingview_types as types

# Version Information
__version__ = '1.0.0'

__all__ = [
    'Client',
    'ChartSession', 'Study',
    'QuoteSession', 'QuoteMarket',
    'BuiltInIndicator', 'PineIndicator', 'PinePermManager',
    'fetch_scan_data', 'get_ta', 'search_market', 'search_market_v3',
    'search_indicator', 'get_indicator', 'login_user',
    'get_private_indicators', 'get_chart_token', 'get_drawings',
    'utils', 'protocol', 'types'
]
