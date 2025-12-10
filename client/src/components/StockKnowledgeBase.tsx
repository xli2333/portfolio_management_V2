import { useState, useEffect, useRef } from 'react';
import { ArrowLeft, Upload, FileText, Bot, Trash2, Send, Paperclip, CheckSquare, Square } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { cn } from '@/lib/utils';

interface StockKnowledgeBaseProps {
    symbol: string;
    onBack: () => void;
}

interface Document {
    id: string;
    filename: string;
    created_at: string;
    file_size: number;
    type: string;
}

interface Message {
    role: 'user' | 'model';
    text: string;
}

export function StockKnowledgeBase({ symbol, onBack }: StockKnowledgeBaseProps) {
    const [documents, setDocuments] = useState<Document[]>([]);
    const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
    const [model, setModel] = useState('gemini-2.5-flash');
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [generatingReport, setGeneratingReport] = useState(false);
    const [selectedMessageIndices, setSelectedMessageIndices] = useState<Set<number>>(new Set());
    
    const fileInputRef = useRef<HTMLInputElement>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:5000';
    
    const STORAGE_KEY = `kb_chat_${symbol}`;
    const EXPIRY_KEY = `kb_chat_expiry_${symbol}`;

    useEffect(() => {
        fetchDocuments();
        loadHistory();
    }, [symbol]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const loadHistory = () => {
        const storedHistory = localStorage.getItem(STORAGE_KEY);
        const storedExpiry = localStorage.getItem(EXPIRY_KEY);

        if (storedHistory && storedExpiry) {
            const now = new Date().getTime();
            if (now > parseInt(storedExpiry)) {
                localStorage.removeItem(STORAGE_KEY);
                localStorage.removeItem(EXPIRY_KEY);
                setMessages([]);
            } else {
                setMessages(JSON.parse(storedHistory));
            }
        } else {
            setMessages([]);
        }
    };

    const saveHistory = (newMessages: Message[]) => {
        const now = new Date().getTime();
        const oneDay = 24 * 60 * 60 * 1000;
        localStorage.setItem(STORAGE_KEY, JSON.stringify(newMessages));
        if (!localStorage.getItem(EXPIRY_KEY)) {
             localStorage.setItem(EXPIRY_KEY, (now + oneDay).toString());
        }
    };

    const fetchDocuments = async () => {
        try {
            const res = await fetch(`${apiBase}/api/knowledge/list?symbol=${symbol}`);
            const data = await res.json();
            if (Array.isArray(data)) {
                setDocuments(data);
            }
        } catch (e) {
            console.error(e);
        }
    };

    const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!e.target.files || e.target.files.length === 0) return;
        
        setUploading(true);
        const formData = new FormData();
        formData.append('file', e.target.files[0]);
        formData.append('symbol', symbol);

        try {
            const res = await fetch(`${apiBase}/api/knowledge/upload`, {
                method: 'POST',
                body: formData,
            });
            if (!res.ok) throw new Error('Upload failed');
            fetchDocuments();
        } catch (err) {
            alert('上传失败，请重试');
        } finally {
            setUploading(false);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    const handleDelete = async (docId: string, e: React.MouseEvent) => {
        e.stopPropagation();
        if (!confirm('确定删除此文档吗？')) return;
        try {
            await fetch(`${apiBase}/api/knowledge/delete?doc_id=${docId}`, { method: 'DELETE' });
            fetchDocuments();
            const newSelected = new Set(selectedIds);
            newSelected.delete(docId);
            setSelectedIds(newSelected);
        } catch (err) {
            console.error(err);
        }
    };

    const toggleSelection = (docId: string) => {
        const newSet = new Set(selectedIds);
        if (newSet.has(docId)) newSet.delete(docId);
        else newSet.add(docId);
        setSelectedIds(newSet);
    };

    const toggleMessageSelection = (index: number) => {
        const newSet = new Set(selectedMessageIndices);
        if (newSet.has(index)) newSet.delete(index);
        else newSet.add(index);
        setSelectedMessageIndices(newSet);
    };

    const handleSaveChat = async () => {
        if (selectedMessageIndices.size === 0) return;
        
        const selectedMsgs = messages.filter((_, idx) => selectedMessageIndices.has(idx));
        const formattedMsgs = selectedMsgs.map(m => `[${m.role.toUpperCase()}]: ${m.text}`);
        
        try {
            const res = await fetch(`${apiBase}/api/knowledge/save_chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    symbol,
                    messages: formattedMsgs
                })
            });
            if (res.ok) {
                alert('对话已保存到知识库');
                setSelectedMessageIndices(new Set());
                fetchDocuments();
            } else {
                throw new Error('Save failed');
            }
        } catch (e) {
            alert('保存失败');
        }
    };

    const handleGenerateReport = async () => {
        if (generatingReport) return;
        setGeneratingReport(true);
        
        // Add a temporary system message to show status
        const loadingMsg: Message = { role: 'model', text: '正在进行深度研究并生成报告，请稍候（可能需要1-2分钟）...' };
        const tempMessages = [...messages, loadingMsg];
        setMessages(tempMessages);

        try {
            const res = await fetch(`${apiBase}/api/agent/generate_report`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    symbol: symbol,
                    model: model,
                    selected_file_ids: Array.from(selectedIds)
                })
            });

            if (!res.ok) throw new Error('Generation failed');
            const data = await res.json();

            // Replace loading message with success
            const successMsg: Message = { 
                role: 'model', 
                text: `**深度研究报告已生成**\n\n已自动保存至左侧文档列表：\`${data.file_record.filename}\`\n\n您现在可以勾选该报告并针对其内容进行提问。` 
            };
            
            // Remove the last loading message and add success message
            const finalMessages = [...messages, successMsg];
            setMessages(finalMessages);
            saveHistory(finalMessages);
            fetchDocuments(); // Refresh list to show new report

        } catch (e) {
            const errorMsg: Message = { role: 'model', text: '报告生成失败，请稍后重试。' };
            setMessages([...messages, errorMsg]);
        } finally {
            setGeneratingReport(false);
        }
    };

    const sendMessage = async () => {
        if (!input.trim()) return;

        const userMsg: Message = { role: 'user', text: input };
        const updatedMessages = [...messages, userMsg];
        setMessages(updatedMessages);
        saveHistory(updatedMessages);
        setInput('');
        setLoading(true);

        try {
            // Standard Chat History format
            const historyForApi = updatedMessages.slice(0, -1).map(m => ({
                role: m.role,
                parts: [m.text]
            }));

            const res = await fetch(`${apiBase}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    symbol: symbol,
                    message: userMsg.text,
                    history: historyForApi,
                    // Extra params for RAG/Context
                    selected_file_ids: Array.from(selectedIds),
                    model: model
                })
            });

            if (!res.ok) throw new Error('Failed to send message');
            const data = await res.json();
            
            const aiMsg: Message = { role: 'model', text: data.reply };
            const finalMessages = [...updatedMessages, aiMsg];
            setMessages(finalMessages);
            saveHistory(finalMessages);
        } catch (error) {
            const errorMsg: Message = { role: 'model', text: 'Error: Connection failed.' };
            const finalMessages = [...updatedMessages, errorMsg];
            setMessages(finalMessages);
            saveHistory(finalMessages);
        } finally {
            setLoading(false);
        }
    };

    const formatSize = (bytes: number) => {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    };

    return (
        <div className="animate-in slide-in-from-right-8 duration-500 flex flex-col h-[calc(100vh-200px)]">
            {/* Top Bar */}
            <div className="flex justify-between items-center mb-6">
                <button 
                    onClick={onBack}
                    className="flex items-center gap-2 text-sm font-bold font-serif tracking-widest text-gray-400 hover:text-black transition-colors"
                >
                    <ArrowLeft size={16} /> 返回 AI 投顾中心
                </button>
                <div className="text-right">
                    <div className="text-4xl font-black font-mono tracking-tighter leading-none">{symbol}</div>
                    <div className="text-xs font-serif font-bold text-gray-400">KNOWLEDGE BASE</div>
                </div>
            </div>

            <div className="grid grid-cols-12 gap-6 flex-1 min-h-0">
                {/* Left: Upload & Files */}
                <div className="col-span-4 flex flex-col gap-4 min-h-0">
                    {/* Upload Box */}
                    <div 
                        onClick={() => fileInputRef.current?.click()}
                        className={cn(
                            "bg-gray-50 border-2 border-dashed border-gray-300 rounded-none p-6 flex flex-col items-center justify-center text-gray-400 hover:bg-gray-100 hover:border-black hover:text-black transition-all cursor-pointer group shrink-0",
                            uploading && "opacity-50 pointer-events-none"
                        )}
                    >
                        <input 
                            type="file" 
                            ref={fileInputRef} 
                            onChange={handleUpload} 
                            accept=".pdf" 
                            className="hidden" 
                        />
                        <Upload size={32} className={cn("mb-2 group-hover:scale-110 transition-transform", uploading && "animate-bounce")} />
                        <div className="font-bold font-serif text-sm">{uploading ? '上传中...' : '上传 PDF 资料'}</div>
                    </div>

                    {/* File List */}
                    <div className="flex-1 border-2 border-black p-0 overflow-hidden flex flex-col bg-white">
                        <div className="p-3 border-b-2 border-gray-100 bg-gray-50 flex justify-between items-center">
                            <h3 className="font-bold font-serif text-sm flex items-center gap-2">
                                <FileText size={14} /> 文档列表 ({documents.length})
                            </h3>
                            <span className="text-[10px] text-neon-dark font-mono font-bold">
                                已选 {selectedIds.size}
                            </span>
                        </div>
                        
                        <div className="flex-1 overflow-y-auto p-2 space-y-2">
                            {documents.length === 0 && (
                                <div className="text-center text-gray-300 text-xs mt-10">暂无文档</div>
                            )}
                            {documents.map(doc => {
                                const isSelected = selectedIds.has(doc.id);
                                return (
                                    <div 
                                        key={doc.id}
                                        onClick={() => toggleSelection(doc.id)}
                                        className={cn(
                                            "p-3 border flex items-start gap-3 cursor-pointer transition-all hover:shadow-md",
                                            isSelected ? "border-black bg-black text-white" : "border-gray-200 bg-white hover:border-gray-400"
                                        )}
                                    >
                                        <div className="mt-0.5">
                                            {isSelected ? <CheckSquare size={16} className="text-neon" /> : <Square size={16} className="text-gray-300" />}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className={cn("font-bold text-sm truncate", isSelected ? "text-white" : "text-black")}>
                                                {doc.filename}
                                            </div>
                                            <div className={cn("text-[10px] font-mono mt-1 flex justify-between", isSelected ? "text-gray-400" : "text-gray-400")}>
                                                <span>{formatSize(doc.file_size)}</span>
                                                <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                                            </div>
                                        </div>
                                        <button 
                                            onClick={(e) => handleDelete(doc.id, e)}
                                            className={cn("p-1 hover:text-red-500 transition-colors", isSelected ? "text-gray-600" : "text-gray-300")}
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>

                {/* Right: Embedded AI Chat */}
                <div className="col-span-8 border-2 border-black flex flex-col bg-white relative shadow-lg h-full overflow-hidden">
                    {/* Chat Header / Controls */}
                    <div className="p-3 border-b-2 border-black bg-gray-50 flex justify-between items-center shrink-0">
                        <div className="flex items-center gap-2">
                            <Bot size={20} className="text-black" />
                            <span className="font-bold font-serif text-sm">AI 分析师</span>
                        </div>
                        <div className="flex gap-2">
                            {selectedMessageIndices.size > 0 && (
                                <button 
                                    onClick={handleSaveChat}
                                    className="bg-black text-white text-xs font-bold px-3 py-1 hover:bg-neon hover:text-black transition-colors flex items-center gap-1"
                                >
                                    <Paperclip size={12} /> 保存 ({selectedMessageIndices.size})
                                </button>
                            )}
                            <button 
                                onClick={handleGenerateReport}
                                disabled={generatingReport}
                                className={cn(
                                    "text-xs font-black uppercase tracking-wider px-3 py-1 transition-colors flex items-center gap-1",
                                    generatingReport ? "bg-gray-200 text-gray-400 cursor-not-allowed" : "bg-neon text-black hover:bg-neon-dim"
                                )}
                            >
                                {generatingReport ? "生成中..." : "生成深度研报"}
                            </button>
                            <select 
                                value={model}
                                onChange={(e) => setModel(e.target.value)}
                                className="bg-white border-2 border-gray-200 text-xs font-bold px-2 py-1 outline-none cursor-pointer hover:border-black transition-colors"
                            >
                                <option value="gemini-2.5-flash">Gemini 2.5 Flash (快速)</option>
                                <option value="gemini-2.5-pro">Gemini 2.5 Pro (深度)</option>
                            </select>
                        </div>
                    </div>
                    
                    {/* Messages Area */}
                    <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-white">
                        {messages.length === 0 && (
                            <div className="h-full flex flex-col items-center justify-center text-gray-300 opacity-50">
                                <div className="text-6xl font-black font-serif mb-4">AI</div>
                                <p className="text-sm font-mono">选择左侧文档，开始深度分析...</p>
                            </div>
                        )}
                        {messages.map((msg, idx) => {
                            const isSelected = selectedMessageIndices.has(idx);
                            return (
                                <div key={idx} className={cn("flex w-full items-start gap-2", msg.role === 'user' ? "flex-row-reverse" : "")}>
                                    {/* Selection Checkbox */}
                                    <button 
                                        onClick={() => toggleMessageSelection(idx)}
                                        className="mt-2 text-gray-300 hover:text-black transition-colors"
                                    >
                                        {isSelected ? <CheckSquare size={16} className="text-neon-dark" /> : <Square size={16} />}
                                    </button>

                                    <div className={cn(
                                        "max-w-[85%] p-4 text-sm font-medium leading-relaxed shadow-sm overflow-hidden",
                                        msg.role === 'user' 
                                            ? "bg-black text-white" 
                                            : "bg-gray-50 border border-gray-100 text-gray-800"
                                    )}>
                                        <div className={cn(
                                            "prose prose-sm max-w-none break-words font-serif",
                                            msg.role === 'user' 
                                                ? "prose-invert prose-p:text-white prose-headings:text-white prose-strong:text-white" 
                                                : "prose-headings:font-black prose-headings:font-sans prose-strong:font-black prose-strong:text-black prose-li:marker:text-black"
                                        )}>
                                            <ReactMarkdown 
                                                components={{
                                                    strong: ({node, ...props}) => <span className="font-black bg-neon/20 px-1 rounded-sm" {...props} />,
                                                    h3: ({node, ...props}) => <h3 className="text-lg font-black mt-4 mb-2 border-l-4 border-neon pl-2" {...props} />,
                                                    h4: ({node, ...props}) => <h4 className="text-base font-bold mt-3 mb-1 uppercase tracking-wider" {...props} />,
                                                    li: ({node, ...props}) => <li className="my-1" {...props} />
                                                }}
                                            >
                                                {msg.text}
                                            </ReactMarkdown>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                        {loading && (
                            <div className="flex justify-start ml-6">
                                <div className="bg-gray-50 p-4 text-xs font-mono text-gray-500 animate-pulse border border-gray-100">
                                    {selectedIds.size > 0 ? `正在阅读 ${selectedIds.size} 份文档并思考...` : 'AI 正在思考...'}
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Input Area */}
                    <div className="p-4 border-t-2 border-black bg-white shrink-0">
                        {selectedIds.size > 0 && (
                            <div className="mb-2 flex items-center gap-1 text-[10px] font-bold text-neon-dark uppercase tracking-wider">
                                <Paperclip size={10} />
                                已附加 {selectedIds.size} 份资料作为上下文
                            </div>
                        )}
                        <div className="flex gap-2 relative">
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                                placeholder={selectedIds.size > 0 ? "基于选定资料提问..." : "输入问题..."}
                                className="flex-1 bg-gray-50 border-2 border-gray-200 px-4 py-3 text-sm focus:border-black focus:ring-0 outline-none transition-colors font-medium placeholder:text-gray-400"
                                autoFocus
                            />
                            <button 
                                onClick={sendMessage}
                                disabled={loading || !input.trim()}
                                className="bg-black text-white px-6 hover:bg-neon hover:text-black transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <Send size={18} />
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
