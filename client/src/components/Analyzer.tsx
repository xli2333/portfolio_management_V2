import { useState, useEffect, useRef } from 'react';
import { createChart, ColorType, IChartApi, ISeriesApi } from 'lightweight-charts';
import { cn } from '@/lib/utils';
import { ArrowLeft } from 'lucide-react';

// --- Types ---

interface Signal {
  signal: string;
  strength: number;
  description: string;
  category: string;
}

interface AnalysisResult {
  stock_info: {
      code: string;
      name: string;
  };
  price_info: {
      close: number;
      change: number;
      change_pct: number;
      volume: number;
  };
  comprehensive_score: {
    score: number;
    recommendation: string;
    buy_signals: number;
    sell_signals: number;
    regime: string;
  };
  signals: Record<string, Signal>;
  ohlcv: {
      date: string;
      open: number;
      high: number;
      low: number;
      close: number;
      volume: number;
  }[];
  advanced_indicators: any;
}

// --- Components ---

function BigSwissGauge({ score }: { score: number }) {
  const radius = 80;
  const strokeWidth = 8;
  const safeScore = Math.max(-100, Math.min(100, score));
  const rotation = (safeScore / 100) * 90;
  const isPositive = safeScore >= 0;
  const color = isPositive ? '#CCFF00' : '#FF3333';
  const angleRad = (Math.abs(rotation) * Math.PI) / 180;
  const endX = 100 + (isPositive ? 1 : -1) * Math.sin(angleRad) * radius;
  const endY = 100 - Math.cos(angleRad) * radius;
  const largeArcFlag = 0; 
  const sweepFlag = isPositive ? 1 : 0; 
  const arcPath = Math.abs(safeScore) < 1 ? "" : `M 100 20 A ${radius} ${radius} 0 ${largeArcFlag} ${sweepFlag} ${endX} ${endY}`;

  return (
    <div className="w-full h-full min-h-[200px] flex flex-col items-center justify-center relative -translate-y-4 -translate-x-6">
        <div className="relative w-[360px] h-[180px]">
            <svg viewBox="0 0 200 110" className="w-full h-full overflow-visible">
                <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="#F0F0F0" strokeWidth={strokeWidth} strokeLinecap="butt" />
                <path d={arcPath} fill="none" stroke={color} strokeWidth={strokeWidth} strokeLinecap="butt" className="transition-all duration-1000 ease-out" />
                <line x1="43.4" y1="43.4" x2="48" y2="48" stroke="black" strokeWidth="1" />
                <line x1="156.6" y1="43.4" x2="152" y2="48" stroke="black" strokeWidth="1" />
                <line x1="100" y1="10" x2="100" y2="18" stroke="black" strokeWidth="2" />
                <g transform={`rotate(${rotation}, 100, 100)`} className="transition-transform duration-1000 cubic-bezier(0.2, 0.8, 0.2, 1)">
                    <path d="M 100 15 L 97 100 L 103 100 Z" fill="black" />
                </g>
                <circle cx="100" cy="100" r="6" fill="black" />
                <circle cx="100" cy="100" r="2" fill="white" />
            </svg>
            <div className="absolute bottom-0 left-0 text-[10px] font-bold text-gray-300 font-mono">-100</div>
            <div className="absolute bottom-0 right-0 text-[10px] font-bold text-gray-300 font-mono">+100</div>
        </div>
        <div className="flex flex-col items-center mt-2">
             <div className="text-5xl font-black tracking-tighter leading-none flex items-start">
                <span className="text-2xl mt-1 opacity-50 mr-1">{score > 0 ? '+' : ''}</span>
                {Math.round(Math.abs(score))}
             </div>
        </div>
    </div>
  );
}

function SignalGrid({ signals }: { signals: Record<string, Signal> }) {
    const buySignals = Object.entries(signals).filter(([_, s]) => s.signal === 'buy').sort((a, b) => b[1].strength - a[1].strength);
    const sellSignals = Object.entries(signals).filter(([_, s]) => s.signal === 'sell').sort((a, b) => b[1].strength - a[1].strength);

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 mt-12">
            <div>
                <h3 className="text-4xl font-black font-serif tracking-tighter mb-6 flex items-center gap-4 text-black">
                    买入信号
                    <span className="text-sm font-normal font-sans bg-neon text-black px-2 py-1 rounded-none">
                        {buySignals.length} 个
                    </span>
                </h3>
                <div className="grid grid-cols-1 gap-4">
                    {buySignals.map(([name, s]) => (
                        <div key={name} className="border-t-2 border-black pt-2 pb-4 flex flex-col gap-2 group hover:bg-[#F5F5F5] transition-colors px-2">
                            <div className="flex justify-between items-baseline">
                                <div>
                                    <div className="text-2xl font-bold tracking-tight font-serif">{name}</div>
                                    <div className="text-xs text-gray-500 uppercase tracking-widest mt-1">{s.category}</div>
                                </div>
                                <div className="flex flex-col items-end">
                                    <div className="text-lg font-bold font-mono">{s.strength}%</div>
                                    <div className="flex gap-1 mt-1">
                                        {[...Array(5)].map((_, i) => (
                                            <div key={i} className={cn("w-2 h-2", i < (s.strength/20) ? "bg-neon" : "bg-[#E5E5E5]")} />
                                        ))}
                                    </div>
                                </div>
                            </div>
                            <p className="text-sm text-gray-600 font-medium leading-snug max-w-[90%] font-serif">
                                {s.description}
                            </p>
                        </div>
                    ))}
                    {buySignals.length === 0 && <div className="text-gray-400 font-mono">暂无数据</div>}
                </div>
            </div>
            <div>
                <h3 className="text-4xl font-black font-serif tracking-tighter mb-6 flex items-center gap-4 text-gray-400">
                    卖出信号
                    <span className="text-sm font-normal font-sans bg-gray-200 text-black px-2 py-1 rounded-none">
                        {sellSignals.length} 个
                    </span>
                </h3>
                <div className="grid grid-cols-1 gap-4">
                    {sellSignals.map(([name, s]) => (
                        <div key={name} className="border-t-2 border-gray-300 pt-2 pb-4 flex flex-col gap-2 group hover:bg-[#F5F5F5] transition-colors px-2">
                             <div className="flex justify-between items-baseline">
                                 <div>
                                    <div className="text-2xl font-bold tracking-tight text-gray-700 font-serif">{name}</div>
                                    <div className="text-xs text-gray-400 uppercase tracking-widest mt-1">{s.category}</div>
                                </div>
                                 <div className="flex flex-col items-end">
                                    <div className="text-lg font-bold font-mono text-gray-700">{s.strength}%</div>
                                    <div className="flex gap-1 mt-1">
                                        {[...Array(5)].map((_, i) => (
                                            <div key={i} className={cn("w-2 h-2", i < (s.strength/20) ? "bg-black" : "bg-[#E5E5E5]")} />
                                        ))}
                                    </div>
                                </div>
                            </div>
                            <p className="text-sm text-gray-500 font-medium leading-snug max-w-[90%] font-serif">
                                {s.description}
                            </p>
                        </div>
                    ))}
                     {sellSignals.length === 0 && <div className="text-gray-400 font-mono">暂无数据</div>}
                </div>
            </div>
        </div>
    )
}

function StockChart({ ohlcv }: { ohlcv: AnalysisResult['ohlcv'] }) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#FFFFFF' },
        textColor: '#000000',
        fontSize: 11,
        fontFamily: "'Inter', sans-serif",
      },
      grid: { vertLines: { color: '#F0F0F0' }, horzLines: { color: '#F0F0F0' } },
      width: chartContainerRef.current.clientWidth,
      height: 400,
      autoSize: true,
      rightPriceScale: { borderColor: '#000000', borderVisible: true },
      timeScale: { borderColor: '#000000', borderVisible: true },
      crosshair: {
          vertLine: { color: '#CCFF00', width: 2, labelBackgroundColor: '#000' },
          horzLine: { color: '#CCFF00', width: 2, labelBackgroundColor: '#000' },
      }
    });
    const candlestickSeries = chart.addCandlestickSeries({
        upColor: '#CCFF00', downColor: '#000000', borderVisible: true, borderColor: '#000000', wickUpColor: '#000000', wickDownColor: '#000000',
    });
    chartRef.current = chart;
    candleSeriesRef.current = candlestickSeries;
    const resizeObserver = new ResizeObserver((entries) => {
        for (const entry of entries) {
            if (entry.contentRect.width > 0) {
                 chart.applyOptions({ width: entry.contentRect.width });
            }
        }
    });
    resizeObserver.observe(chartContainerRef.current);
    return () => { resizeObserver.disconnect(); chart.remove(); };
  }, []);

  useEffect(() => {
    if (ohlcv && candleSeriesRef.current && chartRef.current) {
        const data = ohlcv.map((item) => ({
            time: item.date, open: item.open, high: item.high, low: item.low, close: item.close,
        }));
        candleSeriesRef.current.setData(data);
        chartRef.current.timeScale().fitContent();
    }
  }, [ohlcv]);

  return <div ref={chartContainerRef} className="w-full h-[400px] bg-white" />;
}

// --- Analyzer App ---

interface AnalyzerProps {
    initialSymbol?: string;
    onBack: () => void;
}

export function Analyzer({ initialSymbol, onBack }: AnalyzerProps) {
  const [symbol, setSymbol] = useState(initialSymbol || '');
  const [period, setPeriod] = useState('daily');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState('');
  
  const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:5000'; 

  const fetchAnalysis = async (searchSymbol?: string) => {
    const s = searchSymbol || symbol;
    if (!s) return;
    
    setLoading(true);
    setError('');
    setResult(null);
    const url = `${apiBase}/analyze?symbol=${s}&period=${period}`;
    try {
      const res = await fetch(url);
      if (!res.ok) {
        const contentType = res.headers.get("content-type");
        if (contentType && contentType.indexOf("application/json") !== -1) {
            const errorData = await res.json();
            throw new Error(errorData.error || `Server Error: ${res.status}`);
        } else {
            const text = await res.text();
            throw new Error(`Request failed (${res.status}): ${text.substring(0, 100)}...`);
        }
      }
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      setResult(data);
    } catch (err: any) {
      console.error("Fetch error:", err);
      setError(err.message || 'Network error or timeout');
    } finally {
      setLoading(false);
    }
  };

  // Initial fetch if symbol provided
  useEffect(() => {
      if(initialSymbol) fetchAnalysis(initialSymbol);
  }, [initialSymbol]);

  return (
    <div className="animate-in slide-in-from-right-8 duration-500">
        
        {/* Back Button */}
        <button 
            onClick={onBack}
            className="mb-8 flex items-center gap-2 text-sm font-bold font-serif tracking-widest text-gray-400 hover:text-black transition-colors"
        >
            <ArrowLeft size={16} /> 返回首页 (Dashboard)
        </button>

        {/* --- Header Section --- */}
        <header className="mb-16 grid grid-cols-12 gap-4 items-end">
            
            {/* Search Input - Bold & Massive */}
            <div className="col-span-12 lg:col-span-6">
                    <div className="flex items-baseline gap-4">
                    <span className="text-xl font-bold text-gray-400">#</span>
                    <input 
                        type="text" 
                        value={symbol}
                        onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                        onKeyDown={(e) => e.key === 'Enter' && fetchAnalysis()}
                        placeholder="CODE"
                        className="text-7xl font-black tracking-tighter w-full bg-transparent border-none outline-none placeholder:text-gray-200 focus:placeholder:text-transparent p-0 m-0 leading-none uppercase font-mono"
                    />
                    </div>
                    <div className="flex gap-4 mt-4">
                        <button 
                        onClick={() => fetchAnalysis()} 
                        disabled={loading}
                        className="bg-black text-white text-sm font-bold font-serif px-6 py-3 hover:bg-neon hover:text-black transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? '分析中...' : '开始分析'}
                        </button>
                        <select 
                        value={period} 
                        onChange={(e) => setPeriod(e.target.value)}
                        className="bg-gray-100 border-none text-sm font-bold font-serif px-4 py-3 cursor-pointer focus:ring-2 focus:ring-black outline-none"
                        >
                        <option value="daily">日线 (Daily)</option>
                        <option value="weekly">周线 (Weekly)</option>
                        <option value="monthly">月线 (Monthly)</option>
                    </select>
                    </div>
            </div>

            {/* Key Metrics Display */}
            {result && (
                <div className="col-span-12 lg:col-span-6 flex flex-col items-end justify-end text-right">
                    <div className="text-7xl font-black tracking-tighter leading-none font-mono">
                        {result.price_info.close.toFixed(2)}
                    </div>
                    <div className={cn("text-xl font-bold mt-2 bg-black text-white px-2 inline-block font-mono", 
                        result.price_info.change_pct >= 0 ? "bg-neon text-black" : "bg-black text-white"
                    )}>
                        {result.price_info.change_pct > 0 ? '+' : ''}{result.price_info.change_pct.toFixed(2)}%
                    </div>
                    <div className="text-sm font-serif text-gray-500 mt-2 uppercase tracking-widest">
                        {result.stock_info.name} / {result.stock_info.code}
                    </div>
                </div>
            )}
        </header>
        
        {/* Error Message Display */}
        {error && (
            <div className="mb-8 p-4 bg-red-600 text-white font-bold tracking-tight">
                错误: {error}
            </div>
        )}
        
        {/* Loading / Empty State Messages */}
        {result === null && !error && (
                <div className="mb-8">
                {loading && (
                    <div className="p-4 bg-gray-100 text-gray-500 font-mono text-sm animate-pulse">
                        正在获取数据... (Akshare API) 可能需要 10-20 秒。
                    </div>
                )}
                </div>
        )}

        {/* --- Dashboard Content --- */}
        {result ? (
            <main className="animate-in fade-in slide-in-from-bottom-8 duration-700">
                
                {/* Top Grid: Recommendation, Gauge, Regime */}
                <div className="grid grid-cols-12 gap-8 mb-16 border-b border-gray-200 pb-16 items-stretch">
                    
                    {/* Recommendation Text */}
                    <div className="col-span-12 md:col-span-4 flex flex-col justify-between">
                        <h2 className="text-xs font-bold uppercase tracking-widest text-gray-400 font-serif">智能投顾建议 (Recommendation)</h2>
                        <div>
                            <div className="text-5xl font-black tracking-tighter leading-none mb-2 font-serif">
                                {result.comprehensive_score.recommendation}
                            </div>
                            <div className="text-sm font-mono bg-black text-white px-3 py-1 inline-block">
                                评分: {Math.round(result.comprehensive_score.score)}
                            </div>
                        </div>
                    </div>

                    {/* Big Swiss Gauge - Filling the center card */}
                    <div className="col-span-12 md:col-span-4">
                        <BigSwissGauge score={result.comprehensive_score.score} />
                    </div>

                    {/* Regime Analysis */}
                    <div className="col-span-12 md:col-span-4 flex flex-col justify-between text-right">
                            <h2 className="text-xs font-bold uppercase tracking-widest text-gray-400 font-serif">市场状态分析 (Regime)</h2>
                            <div>
                            <div className="text-3xl font-bold uppercase font-serif">
                                {result.comprehensive_score.regime}
                            </div>
                            <div className="text-sm text-gray-500 mt-2 leading-snug font-serif">
                                基于波动率与动量因子，当前市场呈现强烈的 {result.comprehensive_score.regime} 特征。
                            </div>
                            </div>
                    </div>
                </div>

                {/* Chart Section */}
                <div className="mb-16">
                    <div className="flex justify-between items-end mb-4">
                        <h2 className="text-2xl font-black tracking-tight font-serif">价格走势 (PRICE ACTION)</h2>
                        <div className="flex items-center gap-4">
                            <div className="text-xs font-mono text-gray-400">OHLCV / {period.toUpperCase()}</div>
                        </div>
                    </div>
                    <div className="border-4 border-black p-1 bg-white">
                        <StockChart ohlcv={result.ohlcv} />
                    </div>
                </div>

                {/* Signals Grid */}
                <SignalGrid signals={result.signals} />

            </main>
        ) : (
            null
        )}
    </div>
  );
}
