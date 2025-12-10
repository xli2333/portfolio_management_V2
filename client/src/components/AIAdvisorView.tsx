import { useState } from 'react';

export function AIAdvisorView({ holdings, onNavigate }: { holdings: any[], onNavigate: (symbol: string) => void }) {
    return (
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="mb-12 border-b-4 border-black pb-6">
                <h2 className="text-3xl font-black font-serif tracking-tighter">AI 投顾中心 (Knowledge Base)</h2>
                <p className="text-gray-500 font-mono mt-2">智能分析 / 研报生成 / 深度问答</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {holdings.map(h => (
                    <div 
                        key={h.symbol}
                        onClick={() => onNavigate(h.symbol)}
                        className="border-2 border-black p-6 hover:bg-black hover:text-white transition-all cursor-pointer group relative overflow-hidden"
                    >
                        <div className="relative z-10">
                            <div className="text-2xl font-black font-mono mb-2">{h.symbol}</div>
                            <div className="text-sm font-serif opacity-70 mb-4 group-hover:opacity-100">{h.name}</div>
                            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest border-t border-current pt-4 opacity-50 group-hover:opacity-100">
                                进入知识库 <span>→</span>
                            </div>
                        </div>
                        {/* Decorative background element */}
                        <div className="absolute -bottom-4 -right-4 text-9xl font-black opacity-5 group-hover:opacity-10 select-none">
                            AI
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
