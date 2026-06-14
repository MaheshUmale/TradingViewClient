"""
Type Definitions Module
"""
from enum import Enum
from typing import List, Dict, Any, Union, Callable, Optional

# Market Symbol Type
MarketSymbol = str  # 'BTCEUR' or 'KRAKEN:BTCEUR'

# Timezone Type
Timezone = str  # 'Etc/UTC', 'exchange', 'Europe/Moscow', etc.

# Valid Timeframe Constants
VALID_TIMEFRAMES = {
    "1", "3", "5", "15", "30", "45",
    "60", "120", "180", "240",
    "1D", "1W", "1M", "D", "W", "M"
}

# Timeframe Type (string value)
TimeFrameStr = str  # Should be one of the values in VALID_TIMEFRAMES

def validate_timeframe(timeframe: TimeFrameStr) -> bool:
    """Validate if the given timeframe is valid."""
    return timeframe in VALID_TIMEFRAMES

class TimeFrame(str, Enum):
    """Timeframe enumeration"""
    MIN_1 = "1"      # 1 minute
    MIN_3 = "3"      # 3 minutes
    MIN_5 = "5"      # 5 minutes
    MIN_15 = "15"    # 15 minutes
    MIN_30 = "30"    # 30 minutes
    MIN_45 = "45"    # 45 minutes
    MIN_60 = "60"    # 1 hour
    MIN_120 = "120"  # 2 hours
    MIN_180 = "180"  # 3 hours
    MIN_240 = "240"  # 4 hours
    DAY = "1D"       # Daily
    WEEK = "1W"      # Weekly
    MONTH = "1M"     # Monthly
    DAY_ALT = "D"    # Daily (alternative representation)
    WEEK_ALT = "W"   # Weekly (alternative representation)
    MONTH_ALT = "M"  # Monthly (alternative representation)

# Indicator Type
IndicatorType = str  # 'Script@tv-scripting-101!', 'StrategyScript@tv-scripting-101!'

# Built-in Indicator Type
BuiltInIndicatorType = str  # 'Volume@tv-basicstudies-241', etc.

# Built-in Indicator Option Type
BuiltInIndicatorOption = str  # 'rowsLayout', 'rows', 'volume', etc.

# Graphic Drawing Extension Type
ExtendValue = str  # 'right', 'left', 'both', 'none'

# Y-axis Location Type
YLocValue = str  # 'price', 'abovebar', 'belowbar'

# Label Style Type
LabelStyleValue = str  # 'none', 'xcross', 'cross', etc.

# Line Style Type
LineStyleValue = str  # 'solid', 'dotted', 'dashed', etc.

# Box Style Type
BoxStyleValue = str  # 'solid', 'dotted', 'dashed'

# Size Value Type
SizeValue = str  # 'auto', 'huge', 'large', 'normal', 'small', 'tiny'

# Vertical Alignment Type
VAlignValue = str  # 'top', 'center', 'bottom'

# Horizontal Alignment Type
HAlignValue = str  # 'left', 'center', 'right'

# Text Wrap Type
TextWrapValue = str  # 'none', 'auto'

# Table Position Type
TablePositionValue = str  # 'top_left', 'top_center', etc.

# Client Event Type
ClientEvent = str  # 'connected', 'disconnected', etc.

# Market Event Type
MarketEvent = str  # 'loaded', 'data', 'error'

# Update Change Type
UpdateChangeType = str  # 'plots', 'report.currency', etc.
