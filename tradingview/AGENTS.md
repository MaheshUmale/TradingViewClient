# Purpose
Enterprise-grade TradingView WebSocket integration and data management.

# Ownership
- TradingView Integration Team

# Local Contracts
- Protocol: Custom ~m~ and ~h~ framing.
- Dependencies: `websockets`, `aiohttp`.

# Work Guidance
- Use `separators=(',', ':')` in `json.dumps` for all outgoing packets.
- Always send heartbeats (`~h~`) as `raw` packets.
- Ensure non-critical protocol errors (e.g., `unknown_session_id`) do not kill the connection.

# Verification
- `python3 -m tradingview.integration_test`
