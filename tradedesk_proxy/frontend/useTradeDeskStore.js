import { create } from 'zustand';

/**
 * useTradeDeskStore - Enhanced for Dual-Speed Brain Signals
 */
export const useTradeDeskStore = create((set, get) => ({
  prices: {},
  indicators: {},
  brainSignals: [], // Log of latest micro-signals

  // Active Zone Summary
  activeZone: {
    coi_pcr: 1.0,
    vol_pcr: 1.0,
    current_signal: 'NEUTRAL'
  },

  updateTick: (instrumentKey, data) => set((state) => ({
    prices: {
      ...state.prices,
      [instrumentKey]: { ...data, lastUpdated: Date.now() }
    }
  })),

  updateIndicator: (instrumentKey, name, values) => set((state) => ({
    indicators: {
      ...state.indicators,
      [`${instrumentKey}:${name}`]: { values, timestamp: Date.now() }
    }
  })),

  /**
   * processBrainSignal - Handles high-conviction execution signals
   */
  processBrainSignal: (signalData) => set((state) => ({
    activeZone: {
      coi_pcr: signalData.metrics.coi_pcr,
      vol_pcr: signalData.metrics.vol_pcr,
      current_signal: signalData.signal
    },
    brainSignals: [
        { ...signalData, id: Date.now() },
        ...state.brainSignals.slice(0, 49) // Keep last 50
    ]
  })),

  /**
   * Selector for Chart: Get real-time PCR for overlay
   */
  getPCR: () => get().activeZone.coi_pcr
}));
