import { useState, useEffect, useRef } from 'react';
import { Trash2, TrendingUp, Activity, PieChart as PieChartIcon } from 'lucide-react';
import { createChart, ColorType } from 'lightweight-charts';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip } from 'recharts';
import { cn } from '@/lib/utils';

// --- Types ---
interface Holding {
    symbol: string;
    name: string;
    shares: number;
    cost_basis: number;
    current_price: number;
    market_value: number;
    unrealized_pl: number;
    unrealized_pl_pct: number;
    day_change_pct: number;
    day_pl: number;
    currency: string;
}

interface PortfolioOverview {
    total_market_value: number;
    total_cost: number;
    total_pl: number;
    total_pl_pct: number;
    day_pl: number;
    currency: string;
}

interface AnalysisMetrics {
    total_return_pct: number;
    annual_return_pct: number;
    volatility_pct: number;
    sharpe_ratio: number;
    max_drawdown_pct: number;
}

interface AnalysisData {
    metrics: AnalysisMetrics;
    chart_data: { time: string; value: number }[];
    correlation: {
        symbols: string[];
        matrix: (number | null)[][];
    };
    period_days: number;
}

interface DashboardProps {
    onNavigate: (symbol: string) => void;
}

function CompanySummary({ symbol }: { symbol: string }) {
    const [summary, setSummary] = useState<string | null>(null);
    const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:5000';

    useEffect(() => {
        let mounted = true;
        fetch(`${apiBase}/api/stock_summary?symbol=${symbol}`)
            .then(res => res.json())
            .then(data => {
                if (mounted && data.summary) setSummary(data.summary);
            })
            .catch(() => { if(mounted) setSummary("无法获取简介"); });
        return () => { mounted = false; };
    }, [symbol]);

    if (!summary) return <div className="h-4 w-24 bg-gray-100 animate-pulse rounded"></div>;
    return <div className="text-xs text-gray-500 font-serif leading-tight max-w-[200px]">{summary}</div>;
}

function AnalyticsSection({ data, holdings }: { data: AnalysisData, holdings: Holding[] }) {
    const chartContainerRef = useRef<HTMLDivElement>(null);

    // Filter valid holdings for Pie Chart
    const pieData = holdings
        .filter(h => h.market_value > 0)
        .map(h => ({ name: h.symbol, value: h.market_value }));
    
    // Swiss Palette
    const COLORS = ['#000000', '#CCFF00', '#A3A3A3', '#E5E5E5', '#525252', '#F0F0F0'];

    useEffect(() => {
        if (!chartContainerRef.current || !data.chart_data.length) return;

        const chart = createChart(chartContainerRef.current, {
            layout: { background: { type: ColorType.Solid, color: 'transparent' }, textColor: '#999' },
            grid: { vertLines: { color: '#f0f0f0' }, horzLines: { color: '#f0f0f0' } },
            width: chartContainerRef.current.clientWidth,
            height: 300,
            rightPriceScale: { borderVisible: false },
            timeScale: { borderVisible: false, timeVisible: true },
        });

        const newSeries = chart.addAreaSeries({
            lineColor: '#000', 
            topColor: 'rgba(0, 0, 0, 0.2)', 
            bottomColor: 'rgba(0, 0, 0, 0)',
            lineWidth: 2,
        });
        
        // Sort data by time just in case
        const sorted = [...data.chart_data].sort((a,b) => new Date(a.time).getTime() - new Date(b.time).getTime());
        newSeries.setData(sorted);
        chart.timeScale().fitContent();

        const handleResize = () => chart.applyOptions({ width: chartContainerRef.current?.clientWidth });
        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            chart.remove();
        };
    }, [data]);

    return (
        <div className="mb-12 space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-1000">
            {/* Title */}
            <div className="flex items-center gap-2 mb-6 border-b-2 border-black pb-2">
                <Activity className="w-5 h-5" />
                <h3 className="text-xl font-black font-serif tracking-widest text-black">高级组合分析</h3>
            </div>

            {/* Metrics Cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-gray-50 p-6 border-l-4 border-black hover:bg-white transition-colors">
                    <div className="text-xs font-bold font-serif text-gray-500 mb-2">年化收益率 (CAGR)</div>
                    <div className={cn("text-3xl font-black font-mono", data.metrics.annual_return_pct >= 0 ? "text-green-600" : "text-red-600")}>
                        {data.metrics.annual_return_pct.toFixed(2)}%
                    </div>
                </div>
                <div className="bg-gray-50 p-6 border-l-4 border-black hover:bg-white transition-colors">
                    <div className="text-xs font-bold font-serif text-gray-500 mb-2">夏普比率 (Sharpe)</div>
                    <div className="text-3xl font-black font-mono text-black">
                        {data.metrics.sharpe_ratio.toFixed(2)}
                    </div>
                </div>
                <div className="bg-gray-50 p-6 border-l-4 border-black hover:bg-white transition-colors">
                    <div className="text-xs font-bold font-serif text-gray-500 mb-2">波动率 (Volatility)</div>
                    <div className="text-3xl font-black font-mono text-black">
                        {data.metrics.volatility_pct.toFixed(2)}%
                    </div>
                </div>
                <div className="bg-gray-50 p-6 border-l-4 border-black hover:bg-white transition-colors">
                    <div className="text-xs font-bold font-serif text-gray-500 mb-2">最大回撤 (Max Drawdown)</div>
                    <div className="text-3xl font-black font-mono text-red-600">
                        {data.metrics.max_drawdown_pct.toFixed(2)}%
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Chart */}
                <div className="lg:col-span-2 bg-white border-2 border-gray-100 p-6 shadow-sm">
                    <div className="text-sm font-bold font-serif text-gray-600 mb-6 flex items-center gap-2">
                        <TrendingUp size={16} /> 组合净值走势
                    </div>
                    <div ref={chartContainerRef} className="w-full h-[300px]" />
                </div>

                {/* Asset Allocation Pie Chart */}
                <div className="bg-white border-2 border-gray-100 p-6 shadow-sm">
                    <div className="text-sm font-bold font-serif text-gray-600 mb-6 flex items-center gap-2">
                        <PieChartIcon size={16} /> 组合资产分布 (Market Value)
                    </div>
                    <div className="w-full h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={pieData}
                                    innerRadius={60}
                                    outerRadius={100}
                                    paddingAngle={2}
                                    dataKey="value"
                                    stroke="none"
                                >
                                    {pieData.map((_entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <RechartsTooltip 
                                    formatter={(value: number) => `$${value.toLocaleString()}`}
                                    contentStyle={{ backgroundColor: '#000', border: 'none', color: '#fff', fontSize: '12px' }}
                                    itemStyle={{ color: '#fff' }}
                                />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                    {/* Legend */}
                    <div className="mt-4 grid grid-cols-2 gap-2 text-xs font-mono">
                        {pieData.map((entry, index) => (
                            <div key={entry.name} className="flex items-center gap-2">
                                <div className="w-2 h-2" style={{ backgroundColor: COLORS[index % COLORS.length] }} />
                                <span>{entry.name}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

export function Dashboard({ onNavigate }: DashboardProps) {
    const [holdings, setHoldings] = useState<Holding[]>([]);
    const [overview, setOverview] = useState<PortfolioOverview | null>(null);
    const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
    const [loading, setLoading] = useState(true);
    const [analysisLoading, setAnalysisLoading] = useState(false);
    
    const [showAddModal, setShowAddModal] = useState(false);
    
    // Form State
    const [newSymbol, setNewSymbol] = useState('');
    const [newShares, setNewShares] = useState('');
    const [newCost, setNewCost] = useState('');
    const [addError, setAddError] = useState('');
    const [isAdding, setIsAdding] = useState(false);

    const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:5000'; 

    const fetchPortfolio = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${apiBase}/api/portfolio`);
            const data = await res.json();
            if (data.error) throw new Error(data.error);
            setHoldings(data.holdings || []);
            setOverview(data.overview || null);

            // Fetch Analysis if holdings exist
            if (data.holdings && data.holdings.length > 0) {
                fetchAnalysis();
            }
        } catch (err) {
            console.error("Failed to fetch portfolio:", err);
        } finally {
            setLoading(false);
        }
    };

    const fetchAnalysis = async () => {
        setAnalysisLoading(true);
        try {
            const res = await fetch(`${apiBase}/api/portfolio/analysis`);
            const data = await res.json();
            if (!data.error) {
                setAnalysis(data);
            }
        } catch (err) {
            console.error("Analysis fetch failed:", err);
        } finally {
            setAnalysisLoading(false);
        }
    }

    useEffect(() => {
        fetchPortfolio();
    }, []);

    const handleAddStock = async () => {
        if (!newSymbol || !newShares || !newCost) {
            setAddError("请填写所有字段");
            return;
        }
        setIsAdding(true);
        setAddError("");
        try {
            const res = await fetch(`${apiBase}/api/portfolio/add`, {
                method: 'POST',
                body: JSON.stringify({
                    symbol: newSymbol,
                    quantity: Number(newShares),
                    cost: Number(newCost)
                })
            });
            const data = await res.json();
            if (data.error) throw new Error(data.error);
            
            // Success
            setShowAddModal(false);
            setNewSymbol('');
            setNewShares('');
            setNewCost('');
            fetchPortfolio(); // Refresh
        } catch (err: any) {
            setAddError(err.message);
        } finally {
            setIsAdding(false);
        }
    };

    const handleRemove = async (symbol: string, e: React.MouseEvent) => {
        e.stopPropagation();
        if(!confirm(`确认从组合中移除 ${symbol} 吗？`)) return;
        
        try {
            const res = await fetch(`${apiBase}/api/portfolio/remove?symbol=${symbol}`, { method: 'DELETE' });
            if (res.ok) fetchPortfolio();
        } catch (err) {
            console.error(err);
        }
    };

    const formatMoney = (val: number | undefined | null, currency: string = 'USD') => {
        if (val === undefined || val === null) return '---';
        return val.toLocaleString('zh-CN', { style: 'currency', currency: currency });
    };

    return (
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
            {/* Header / Overview Card */}
            <div className="grid grid-cols-12 gap-8 mb-12">
                <div className="col-span-12 lg:col-span-8">
                     <h2 className="text-sm font-bold font-serif text-gray-500 mb-2 tracking-widest">总资产净值 ({overview?.currency || 'USD'})</h2>
                     <div className="text-8xl font-black tracking-tighter leading-none mb-6 font-mono text-black">
                        {overview ? formatMoney(overview.total_market_value, overview.currency) : '---'}
                     </div>
                     <div className="flex gap-12 items-baseline border-t border-black pt-4">
                        <div>
                            <span className="text-xs font-bold text-gray-500 font-serif">总盈亏</span>
                            <div className={cn("text-3xl font-black font-mono mt-1", (overview?.total_pl || 0) >= 0 ? "text-neon-dim" : "text-red-600")}>
                                {overview ? `${overview.total_pl >= 0 ? '+' : ''}${formatMoney(overview.total_pl, overview.currency)}` : '---'}
                                <span className="ml-2 text-lg opacity-60 font-medium">
                                    ({overview?.total_pl_pct != null ? overview.total_pl_pct.toFixed(2) : '0.00'}%)
                                </span>
                            </div>
                        </div>
                        <div>
                            <span className="text-xs font-bold text-gray-500 font-serif">今日盈亏</span>
                            <div className={cn("text-3xl font-black font-mono mt-1", (overview?.day_pl || 0) >= 0 ? "text-neon-dim" : "text-red-600")}>
                                {overview ? `${overview.day_pl >= 0 ? '+' : ''}${formatMoney(overview.day_pl, overview.currency)}` : '---'}
                            </div>
                        </div>
                     </div>
                </div>

                <div className="col-span-12 lg:col-span-4 flex flex-col justify-end items-end gap-4">
                     <button 
                        onClick={() => setShowAddModal(true)}
                        className="bg-black text-white w-full py-4 text-xl font-bold font-serif tracking-widest hover:bg-neon hover:text-black transition-colors border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-none active:translate-x-[4px] active:translate-y-[4px]"
                     >
                        + 添加持仓
                     </button>
                     <div className="text-right text-xs text-gray-400 font-mono w-full">
                        实时估值 / 延时15分钟
                     </div>
                </div>
            </div>

            {/* Advanced Analytics Section */}
            {analysisLoading ? (
                <div className="mb-12 p-8 border-2 border-dashed border-gray-200 text-center text-gray-400 font-mono animate-pulse">
                    正在计算高级分析数据...
                </div>
            ) : analysis ? (
                <AnalyticsSection data={analysis} holdings={holdings} />
            ) : null}

            {/* Holdings Table */}
            <div className="border-t-4 border-black">
                <div className="grid grid-cols-12 border-b-2 border-black py-4 text-sm font-bold font-serif text-gray-500">
                    <div className="col-span-2 pl-2">资产名称</div>
                    <div className="col-span-3">公司简介</div>
                    <div className="col-span-2 text-right">现价</div>
                    <div className="col-span-1 text-right">数量</div>
                    <div className="col-span-2 text-right">市值</div>
                    <div className="col-span-1 text-right">盈亏</div>
                    <div className="col-span-1 text-center">操作</div>
                </div>
                
                {loading ? (
                    <div className="py-12 text-center text-gray-400 font-mono animate-pulse">正在加载资产数据...</div>
                ) : holdings.length === 0 ? (
                    <div className="py-12 text-center text-gray-400 font-mono">暂无持仓，请点击上方添加。</div>
                ) : (
                    holdings.map((h) => (
                        <div 
                            key={h.symbol} 
                            onClick={() => onNavigate(h.symbol)}
                            className="grid grid-cols-12 border-b border-gray-200 py-5 items-center hover:bg-gray-50 cursor-pointer group transition-colors"
                        >
                            <div className="col-span-2 pl-2">
                                <div className="font-black text-xl tracking-tight leading-none font-mono text-black">{h.symbol}</div>
                                <div className="text-xs text-gray-500 mt-1 font-serif">{h.name}</div>
                            </div>
                            <div className="col-span-3 pr-4">
                                <CompanySummary symbol={h.symbol} />
                            </div>
                            <div className="col-span-2 text-right font-mono text-lg">
                                <div>{formatMoney(h.current_price, h.currency)}</div>
                                <div className={cn("text-xs font-bold", h.day_change_pct >= 0 ? "text-green-600" : "text-red-600")}>
                                    {h.day_change_pct > 0 ? '+' : ''}{h.day_change_pct.toFixed(2)}%
                                </div>
                            </div>
                            <div className="col-span-1 text-right font-mono text-gray-600 text-lg font-bold">
                                {h.shares}
                            </div>
                            <div className="col-span-2 text-right font-mono font-black text-lg">
                                {formatMoney(h.market_value, h.currency)}
                            </div>
                            <div className="col-span-1 text-right font-mono">
                                <div className={cn("font-bold text-lg", h.unrealized_pl >= 0 ? "text-black" : "text-red-600")}>
                                    {h.unrealized_pl > 0 ? '+' : ''}{h.unrealized_pl_pct.toFixed(0)}%
                                </div>
                            </div>
                            <div className="col-span-1 flex justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                                <button 
                                    onClick={(e) => handleRemove(h.symbol, e)}
                                    className="text-gray-300 hover:text-red-600 p-2 transition-colors"
                                >
                                    <Trash2 size={18} />
                                </button>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Modal */}
            {showAddModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
                    <div className="bg-white w-full max-w-lg p-8 border-4 border-white shadow-2xl relative animate-in zoom-in-95 duration-200">
                        <h3 className="text-2xl font-black mb-8 font-serif border-b-2 border-black pb-4">添加新持仓</h3>
                        
                        <div className="space-y-6">
                            <div>
                                <label className="block text-xs font-bold font-serif text-gray-500 mb-2">股票代码 (Symbol)</label>
                                <input 
                                    className="w-full bg-gray-50 border-2 border-gray-200 p-4 text-xl font-bold font-mono focus:border-black focus:ring-0 outline-none uppercase placeholder:text-gray-300 transition-colors"
                                    placeholder="600519"
                                    value={newSymbol}
                                    onChange={e => setNewSymbol(e.target.value.toUpperCase())}
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs font-bold font-serif text-gray-500 mb-2">持仓数量 (Shares)</label>
                                    <input 
                                        type="number"
                                        className="w-full bg-gray-50 border-2 border-gray-200 p-4 text-xl font-bold font-mono focus:border-black focus:ring-0 outline-none transition-colors"
                                        placeholder="100"
                                        value={newShares}
                                        onChange={e => setNewShares(e.target.value)}
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-bold font-serif text-gray-500 mb-2">平均成本 (Cost)</label>
                                    <input 
                                        type="number"
                                        step="0.01"
                                        className="w-full bg-gray-50 border-2 border-gray-200 p-4 text-xl font-bold font-mono focus:border-black focus:ring-0 outline-none transition-colors"
                                        placeholder="1500.00"
                                        value={newCost}
                                        onChange={e => setNewCost(e.target.value)}
                                    />
                                </div>
                            </div>
                        </div>

                        {addError && <div className="mt-4 text-red-600 font-bold text-sm">{addError}</div>}

                        <div className="grid grid-cols-2 gap-4 mt-8">
                             <button 
                                onClick={() => setShowAddModal(false)}
                                className="bg-gray-100 text-gray-500 font-bold font-serif py-4 hover:bg-gray-200 transition-colors"
                             >
                                取消
                             </button>
                             <button 
                                onClick={handleAddStock}
                                disabled={isAdding}
                                className="bg-black text-white font-bold font-serif py-4 hover:bg-neon hover:text-black transition-colors"
                             >
                                {isAdding ? '保存中...' : '确认添加'}
                             </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
