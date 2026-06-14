import { create } from 'zustand';

/**
 * useTradeDeskStore - Optimized Atomic State Manager
 * Handles high-frequency market ticks and indicator updates.
 */
export const useTradeDeskStore = create((set, get) => ({
  // Real-time price data matrix { [instrumentKey]: { ltp, oi, volume, timestamp } }
  prices: {},

  // Custom Indicator data { [instrumentKey:indicatorName]: { values, timestamp } }
  indicators: {},

  // Global connection status
  connectionStatus: 'DISCONNECTED',

  /**
   * updateTick - Called on every WebSocket market feed packet.
   * Minimizes UI churn by updating only the relevant instrument segment.
   */
  updateTick: (instrumentKey, data) => set((state) => ({
    prices: {
      ...state.prices,
      [instrumentKey]: {
        ...data,
        lastUpdated: Date.now()
      }
    }
  })),

  /**
   * updateIndicator - Called when a Pine Script webhook broadcast is received.
   */
  updateIndicator: (instrumentKey, name, values) => set((state) => ({
    indicators: {
      ...state.indicators,
      [`${instrumentKey}:${name}`]: {
        values,
        timestamp: Date.now()
      }
    }
  })),

  /**
   * setConnectionStatus - Tracks backend proxy availability.
   */
  setConnectionStatus: (status) => set({ connectionStatus: status }),

  /**
   * Selector: Get LTP for a specific instrument
   */
  getLTP: (instrumentKey) => {
    const priceData = get().prices[instrumentKey];
    return priceData ? priceData.ltp : null;
  }
}));
