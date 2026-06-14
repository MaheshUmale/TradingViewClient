import React, { useEffect, useRef, useState } from 'react';
import { createChart, ColorType } from 'lightweight-charts';
import { useTradeDeskStore } from './useTradeDeskStore';

/**
 * TradeDeskChart - Production-Ready Canvas Charting Component
 */
const TradeDeskChart = ({ instrumentKey, symbol }) => {
  const chartContainerRef = useRef();
  const chartRef = useRef();
  const candleSeriesRef = useRef();
  const indicatorSeriesRef = useRef();

  const [isWsConnected, setIsWsConnected] = useState(false);
  const updateTick = useTradeDeskStore((state) => state.updateTick);
  const updateIndicator = useTradeDeskStore((state) => state.updateIndicator);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // 1. Initialize Chart
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#131722' },
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: 'rgba(42, 46, 57, 0.2)' },
        horzLines: { color: 'rgba(42, 46, 57, 0.2)' },
      },
      width: chartContainerRef.current.clientWidth,
      height: 500,
      timeScale: { timeVisible: true, secondsVisible: false },
    });

    const candleSeries = chart.addCandlestickSeries({
      upColor: '#26a69a', downColor: '#ef5350', borderVisible: false,
      wickUpColor: '#26a69a', wickDownColor: '#ef5350',
    });

    const indicatorSeries = chart.addLineSeries({
      color: '#2196F3', lineWidth: 2, priceLineVisible: false,
      title: 'Pine Indicator',
    });

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    indicatorSeriesRef.current = indicatorSeries;

    // 2. WebSocket Connection with Auto-Reconnect
    let ws;
    const connectWS = () => {
      ws = new WebSocket('ws://localhost:8000/ws/stream');

      ws.onopen = () => {
        setIsWsConnected(true);
        console.info(`Connected to TradeDesk Proxy for ${symbol}`);
      };

      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        if (message.instrument !== instrumentKey) return;

        if (message.type === 'TICK') {
          // Update Chart
          candleSeriesRef.current.update({
            time: message.time,
            open: message.o,
            high: message.h,
            low: message.l,
            close: message.c,
          });
          // Update Store
          updateTick(instrumentKey, { ltp: message.c, oi: message.oi, volume: message.v });

        } else if (message.type === 'PINE_INDICATOR') {
          // Update Overlay
          indicatorSeriesRef.current.update({
            time: message.time,
            value: message.values.basis,
          });
          // Update Store
          updateIndicator(instrumentKey, message.name, message.values);
        }
      };

      ws.onclose = () => {
        setIsWsConnected(false);
        setTimeout(connectWS, 3000); // Reconnect after 3s
      };
    };

    connectWS();

    const handleResize = () => {
      chart.applyOptions({ width: chartContainerRef.current.clientWidth });
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
      if (ws) ws.close();
    };
  }, [instrumentKey, symbol]);

  return (
    <div className="flex flex-col w-full bg-[#1e222d] border border-gray-800 rounded-lg overflow-hidden">
      <div className="flex justify-between items-center bg-[#2a2e39] px-4 py-2">
        <div className="flex items-center space-x-3">
            <span className="text-white font-bold">{symbol}</span>
            <span className={`w-2 h-2 rounded-full ${isWsConnected ? 'bg-green-500' : 'bg-red-500'}`}></span>
        </div>
        <div className="text-xs text-gray-400">
            Real-time Feed: {isWsConnected ? 'Active' : 'Reconnecting...'}
        </div>
      </div>
      <div ref={chartContainerRef} className="w-full" />
    </div>
  );
};

export default TradeDeskChart;
