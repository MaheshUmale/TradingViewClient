"""
Protocol Handling Module
"""
import json
import base64
import zipfile
import io
import binascii
from typing import Any

def parse_ws_packet(data: str) -> list:
    """
    Parses incoming TradingView WebSocket data packets.

    TradingView uses a custom framing protocol where messages are prefixed with
    length markers like `~m~<length>~m~`. Heartbeats are marked with `~h~`.
    Multiple messages can be bundled into a single WebSocket frame.

    Args:
        data (str): The raw string received from the WebSocket.

    Returns:
        list: A list of parsed objects, which can be dictionaries (standard messages),
              integers (heartbeat timestamps), or raw strings.
    """
    if not data:
        return []

    # Ensure data is a string
    if not isinstance(data, str):
        try:
            data = str(data)
        except Exception:
            return []

    # Remove ~h~ markers
    clean_data = data.replace('~h~', '')

    # Split data packets
    packets = []
    parts = []

    # Find all packet length markers
    length_markers = []
    pos = 0

    while True:
        pos = clean_data.find('~m~', pos)
        if pos == -1:
            break
        length_markers.append(pos)
        pos += 3  # Skip ~m~

    # If no length markers, try parsing the entire data directly
    if not length_markers:
        try:
            # Could be a valid JSON string
            packet = json.loads(clean_data)
            return [packet]
        except json.JSONDecodeError:
            # If it's a digit, it might be a ping packet
            if clean_data.isdigit():
                return [int(clean_data)]
            # Not valid JSON or digit
            return []

    # Process each marker
    for i in range(len(length_markers)):
        start = length_markers[i]
        # Find packet length
        length_end = clean_data.find('~m~', start + 3)
        if length_end == -1:
            continue

        try:
            # Get length value
            length = int(clean_data[start + 3:length_end])

            # Get packet content
            content_start = length_end + 3
            content_end = content_start + length

            if content_end <= len(clean_data):
                content = clean_data[content_start:content_end]
                parts.append(content)
        except (ValueError, IndexError):
            continue

    # Parse each part
    for part in parts:
        if not part:
            continue

        # Handle ping packets
        if part.isdigit():
            try:
                packets.append(int(part))
                continue
            except ValueError:
                # Skip if conversion fails
                continue

        try:
            # Parse JSON
            packet = json.loads(part)
            packets.append(packet)
        except json.JSONDecodeError:
            # Not valid JSON, try as plain string
            packets.append(part)

    return packets

def format_ws_packet(packet: Any, raw: bool = False) -> str:
    """
    Formats a packet for transmission over the TradingView WebSocket.

    Standard messages are wrapped in the `~m~<length>~m~` format.
    Heartbeats (`~h~<ts>`) should be sent with `raw=True` as they do not use
    the length-prefixed framing.

    Args:
        packet (any): The data to format. Can be a dict or string.
        raw (bool): If True, returns the string representation without framing.

    Returns:
        str: The formatted message string, ready to be sent.
    """
    try:
        if isinstance(packet, dict):
            # Use compact JSON representation to match TradingView expectations
            msg = json.dumps(packet, separators=(',', ':'))
        else:
            msg = str(packet)

        if raw:
            return msg
        return f'~m~{len(msg)}~m~{msg}'
    except Exception:
        # Formatting failed, return None
        return None

async def parse_compressed(data):
    """
    Parse compressed data.

    Args:
        data: Compressed data

    Returns:
        dict: Parsed data, or empty dict if parsing fails
    """
    if not data:
        return {}

    try:
        # Decode base64
        decoded = base64.b64decode(data)

        # Create in-memory file object
        zip_data = io.BytesIO(decoded)

        # Open zip file
        try:
            with zipfile.ZipFile(zip_data) as zf:
                # Get file list
                file_list = zf.namelist()

                if not file_list:
                    # No files present
                    return {}

                # Read the first file
                try:
                    with zf.open(file_list[0]) as f:
                        content = f.read().decode('utf-8')

                    # Parse JSON
                    return json.loads(content)
                except (UnicodeDecodeError, zipfile.BadZipFile):
                    # Decoding or reading error
                    return {}
        except zipfile.BadZipFile:
            # Not a valid ZIP file
            return {}
    except (ValueError, binascii.Error, TypeError):
        # base64 decoding error
        return {}
    except json.JSONDecodeError:
        # JSON parsing error
        return {}
    except Exception:
        # Other unknown error
        return {}
