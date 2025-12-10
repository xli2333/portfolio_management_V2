import ReactMarkdown from 'react-markdown';
import { useState, useEffect, useRef, forwardRef, useImperativeHandle } from 'react';
import { MessageCircle, X, Send, Trash2, Paperclip } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Message {
    role: 'user' | 'model';
    text: string;
    hasImage?: boolean;
}

interface StockChatProps {
    symbol: string;
}

export interface StockChatRef {
    openWithContext: (message: string, image?: string) => void;
}

export const StockChat = forwardRef<StockChatRef, StockChatProps>(({ symbol }, ref) => {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [pendingImage, setPendingImage] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:5000';
    const STORAGE_KEY = `chat_history_${symbol}`;
    const EXPIRY_KEY = `chat_expiry_${symbol}`;

    useImperativeHandle(ref, () => ({
        openWithContext: (message: string, image?: string) => {
            setIsOpen(true);
            
            // Sync load history to ensure we append to the latest
            const storedHistory = localStorage.getItem(STORAGE_KEY);
            let currentMessages: Message[] = [];
            if (storedHistory) {
                 const storedExpiry = localStorage.getItem(EXPIRY_KEY);
                 const now = new Date().getTime();
                 if (!storedExpiry || now <= parseInt(storedExpiry)) {
                     currentMessages = JSON.parse(storedHistory);
                 }
            }
            setMessages(currentMessages); // Update UI state

            if (message) {
                // Send immediately with the loaded history context
                sendMessageWithContext(message, image, currentMessages);
            } else if (image) {
                setPendingImage(image);
            }
        }
    }));

    const sendMessageWithContext = async (text: string, image: string | undefined, currentHistory: Message[]) => {
        const userMsg: Message = { 
            role: 'user', 
            text: text, 
            hasImage: !!image 
        };
        
        const updatedMessages = [...currentHistory, userMsg];
        setMessages(updatedMessages);
        saveHistory(updatedMessages); // Save immediately
        
        setLoading(true);

        try {
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
                    image_data: image
                })
            });

            if (!res.ok) throw new Error('Failed to send message');
            
            const data = await res.json();
            const aiMsg: Message = { role: 'model', text: data.reply };
            
            const finalMessages = [...updatedMessages, aiMsg];
            setMessages(finalMessages);
            saveHistory(finalMessages);

        } catch (error) {
            console.error(error);
            const errorMsg: Message = { role: 'model', text: 'Error: Could not connect to AI assistant.' };
            const finalMessages = [...updatedMessages, errorMsg];
            setMessages(finalMessages);
            saveHistory(finalMessages);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (isOpen) {
            loadHistory();
        }
    }, [isOpen, symbol]);

    useEffect(() => {
        scrollToBottom();
    }, [messages, isOpen]);

    const loadHistory = () => {
        const storedHistory = localStorage.getItem(STORAGE_KEY);
        const storedExpiry = localStorage.getItem(EXPIRY_KEY);

        if (storedHistory && storedExpiry) {
            const now = new Date().getTime();
            if (now > parseInt(storedExpiry)) {
                clearHistory();
            } else {
                setMessages(JSON.parse(storedHistory));
            }
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

    const clearHistory = () => {
        localStorage.removeItem(STORAGE_KEY);
        localStorage.removeItem(EXPIRY_KEY);
        setMessages([]);
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const sendMessage = async (textOverride?: string, imageOverride?: string) => {
        const textToSend = textOverride || input;
        const imageToSend = imageOverride || pendingImage;
        
        if (!textToSend.trim() && !imageToSend) return;

        const userMsg: Message = { 
            role: 'user', 
            text: textToSend,
            hasImage: !!imageToSend 
        };
        
        const updatedMessages = [...messages, userMsg];
        setMessages(updatedMessages);
        setInput('');
        setPendingImage(null); // Clear pending image
        setLoading(true);

        try {
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
                    image_data: imageToSend
                })
            });

            if (!res.ok) throw new Error('Failed to send message');
            
            const data = await res.json();
            const aiMsg: Message = { role: 'model', text: data.reply };
            
            const finalMessages = [...updatedMessages, aiMsg];
            setMessages(finalMessages);
            saveHistory(finalMessages);

        } catch (error) {
            console.error(error);
            const errorMsg: Message = { role: 'model', text: 'Error: Could not connect to AI assistant.' };
            setMessages([...updatedMessages, errorMsg]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            <button
                onClick={() => setIsOpen(true)}
                className="fixed bottom-8 right-8 z-50 bg-black text-white p-4 rounded-full shadow-2xl hover:bg-neon hover:text-black transition-all duration-300 group"
            >
                <MessageCircle size={24} className="group-hover:scale-110 transition-transform" />
            </button>

            {isOpen && (
                <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center pointer-events-none">
                    <div className="absolute inset-0 bg-black/20 pointer-events-auto" onClick={() => setIsOpen(false)} />
                    {/* Chat Window */}
                    <div className="pointer-events-auto bg-white w-full sm:w-[1000px] h-[85vh] sm:h-[750px] sm:rounded-lg shadow-2xl flex flex-col border-2 border-black animate-in slide-in-from-bottom-10 duration-300 absolute bottom-0 right-0 sm:relative sm:bottom-auto sm:right-auto">
                        
                        <div className="bg-black text-white p-4 flex justify-between items-center">
                            <div className="flex flex-col">
                                <h3 className="font-bold font-serif tracking-wide text-lg">AI 助手</h3>
                                <span className="text-xs text-gray-400 font-mono">{symbol}</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <button onClick={clearHistory} title="Clear History" className="text-gray-400 hover:text-red-500 transition-colors">
                                    <Trash2 size={18} />
                                </button>
                                <button onClick={() => setIsOpen(false)} className="text-white hover:text-neon transition-colors">
                                    <X size={24} />
                                </button>
                            </div>
                        </div>

                        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
                            {messages.length === 0 && (
                                <div className="text-center text-gray-400 text-sm mt-10 font-serif">
                                    Ask anything about {symbol}...<br/>
                                    (History saved for 24h)
                                </div>
                            )}
                            {messages.map((msg, idx) => (
                                <div key={idx} className={cn("flex", msg.role === 'user' ? "justify-end" : "justify-start")}>
                                    <div className={cn(
                                        "max-w-[80%] p-3 text-sm font-medium leading-relaxed rounded-lg shadow-sm flex flex-col gap-2",
                                        msg.role === 'user' 
                                            ? "bg-black text-white rounded-br-none" 
                                            : "bg-white border border-gray-200 text-gray-800 rounded-bl-none"
                                    )}>
                                        {msg.hasImage && (
                                            <div className="text-[10px] uppercase font-bold tracking-wider opacity-70 flex items-center gap-1 mb-1">
                                                <Paperclip size={10} /> Chart Snapshot
                                            </div>
                                        )}
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
                            ))}
                            {loading && (
                                <div className="flex justify-start">
                                    <div className="bg-gray-100 p-3 rounded-lg text-xs text-gray-500 animate-pulse">
                                        Thinking...
                                    </div>
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>

                        <div className="p-4 border-t border-gray-200 bg-white">
                            {pendingImage && (
                                <div className="mb-2 flex items-center gap-2 bg-gray-100 p-2 rounded text-xs">
                                    <Paperclip size={12} />
                                    <span>Chart Image Attached</span>
                                    <button onClick={() => setPendingImage(null)} className="ml-auto hover:text-red-500"><X size={12}/></button>
                                </div>
                            )}
                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                                    placeholder="Type your question..."
                                    className="flex-1 bg-gray-100 border-none outline-none px-4 py-2 text-sm focus:ring-1 focus:ring-black"
                                    autoFocus
                                />
                                <button 
                                    onClick={() => sendMessage()}
                                    disabled={loading || (!input.trim() && !pendingImage)}
                                    className="bg-black text-white p-2 hover:bg-neon hover:text-black transition-colors disabled:opacity-50"
                                >
                                    <Send size={20} />
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
});
