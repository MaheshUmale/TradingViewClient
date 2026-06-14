import React, { useEffect, useRef, useState } from 'react';
import { createChart, ColorType } from 'lightweight-charts';
import { useTradeDeskStore } from './useTradeDeskStore';

/**
 * TradeDeskChart - Enhanced with BRAIN Signal Overlays
 */
const TradeDeskChart = ({ instrumentKey, symbol }) => {
  const chartContainerRef = useRef();
  const candleSeriesRef = useRef();
  const pcrSeriesRef = useRef();

  const [isWsConnected, setIsWsConnected] = useState(false);
  const processBrainSignal = useTradeDeskStore((state) => state.processBrainSignal);
  const activeZone = useTradeDeskStore((state) => state.activeZone);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: { background: { type: ColorType.Solid, color: '#0d1117' }, textColor: '#d1d4dc' },
      grid: { vertLines: { color: '#161b22' }, horzLines: { color: '#161b22' } },
      width: chartContainerRef.current.clientWidth,
      height: 600,
      timeScale: { timeVisible: true, secondsVisible: true },
    });

    const candleSeries = chart.addCandlestickSeries({
      upColor: '#2ea043', downColor: '#f85149', borderVisible: false,
      wickUpColor: '#2ea043', wickDownColor: '#f85149',
    });

    // Secondary Axis for COI PCR
    const pcrSeries = chart.addLineSeries({
      color: '#58a6ff', lineWidth: 2, priceScaleId: 'left',
      title: 'COI PCR (Active Zone)',
    });

    chart.priceScale('left').applyOptions({
        visible: true,
        borderColor: '#30363d',
    });

    candleSeriesRef.current = candleSeries;
    pcrSeriesRef.current = pcrSeries;

    // WebSocket Listener for Unified Brain Feed
    let ws;
    const connectWS = () => {
      ws = new WebSocket('ws://localhost:8000/ws/stream');
      ws.onopen = () => setIsWsConnected(true);
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'TICK' && data.instrument === instrumentKey) {
            candleSeriesRef.current.update({
                time: data.time, open: data.o, high: data.h, low: data.l, close: data.c
            });
        } else if (data.type === 'BRAIN_SIGNAL') {
            processBrainSignal(data);
            // Update PCR line on the chart
            pcrSeriesRef.current.update({
                time: Math.floor(Date.now() / 1000),
                value: data.metrics.coi_pcr
            });
        }
      };
      ws.onclose = () => {
        setIsWsConnected(false);
        setTimeout(connectWS, 3000);
      };
    };

    connectWS();

    return () => {
        chart.remove();
        if (ws) ws.close();
    };
  }, [instrumentKey]);

  return (
    <div className="flex flex-col w-full bg-[#0d1117] border border-[#30363d] rounded-xl overflow-hidden shadow-2xl">
      <div className="flex justify-between items-center bg-[#161b22] px-6 py-3 border-b border-[#30363d]">
        <div className="flex items-center space-x-4">
            <span className="text-gray-200 font-bold text-lg">{symbol}</span>
            <span className={`px-2 py-1 rounded text-xs font-mono ${
                activeZone.current_signal === 'BULLISH_DOMINANCE' ? 'bg-green-900 text-green-400' :
                activeZone.current_signal === 'BEARISH_DOMINANCE' ? 'bg-red-900 text-red-400' : 'bg-gray-800 text-gray-400'
            }`}>
                {activeZone.current_signal}
            </span>
        </div>
        <div className="flex space-x-6 text-sm">
            <div className="flex flex-col items-end">
                <span className="text-gray-500 text-[10px] uppercase">COI PCR</span>
                <span className="text-blue-400 font-bold">{activeZone.coi_pcr.toFixed(2)}</span>
            </div>
            <div className="flex flex-col items-end">
                <span className="text-gray-500 text-[10px] uppercase">VOL PCR</span>
                <span className="text-purple-400 font-bold">{activeZone.vol_pcr.toFixed(2)}</span>
            </div>
        </div>
      </div>
      <div ref={chartContainerRef} className="w-full" />
    </div>
  );
};

export default TradeDeskChart;
