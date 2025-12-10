import { useState, useEffect } from 'react';
import { supabase } from './lib/supabase';
import { Session } from '@supabase/supabase-js';
import { Dashboard } from './components/Dashboard';
import { Analyzer } from './components/Analyzer';
import { StockKnowledgeBase } from './components/StockKnowledgeBase';
import { Auth } from './components/Auth';

type View = 'dashboard' | 'analyzer' | 'knowledgeBase';

export default function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [view, setView] = useState<View>('dashboard');
  const [selectedSymbol, setSelectedSymbol] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // DEV MODE: Bypass Auth
    // supabase.auth.getSession().then(({ data: { session } }) => {
    //   setSession(session);
    //   setLoading(false);
    // });

    // const {
    //   data: { subscription },
    // } = supabase.auth.onAuthStateChange((_event, session) => {
    //   setSession(session);
    // });

    // return () => subscription.unsubscribe();
    setLoading(false); 
  }, []);

  const navigateToAnalyzer = (symbol: string) => {
    setSelectedSymbol(symbol);
    setView('analyzer');
  };

  const navigateToKnowledgeBase = (symbol: string) => {
    setSelectedSymbol(symbol);
    setView('knowledgeBase');
  }

  const navigateToDashboard = () => {
    setView('dashboard');
    setSelectedSymbol('');
  };

  const handleLogout = async () => {
    // await supabase.auth.signOut();
    window.location.reload();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="font-mono text-xs font-bold tracking-widest animate-pulse">
          INITIALIZING SYSTEM...
        </div>
      </div>
    );
  }

  // DEV MODE: Always render main app
  // if (!session) { ... } 

  return (
    <div className="min-h-screen bg-white text-black font-sans selection:bg-neon selection:text-black">
      <div className="max-w-6xl mx-auto px-6 py-12">
        
        {/* Global Header / Branding */}
        <header className="mb-12 flex justify-between items-end border-b-4 border-black pb-4">
            <div>
                <h1 
                  className="text-4xl font-black font-serif tracking-tighter cursor-pointer hover:text-neon-dim transition-colors"
                  onClick={navigateToDashboard}
                >
                  智能投资组合系统
                </h1>
                <div className="text-xs font-mono font-bold tracking-widest mt-1 text-gray-400">
                  版本 2.5 / 专业版
                </div>
            </div>
            <div className="text-right">
                 <div className="text-xs font-bold font-serif tracking-widest mb-1">
                    用户: DEV_USER
                 </div>
                 <div className="flex items-center justify-end gap-4">
                    <div className="text-xs font-mono text-neon-dim">● DEV MODE</div>
                    <button 
                        onClick={handleLogout}
                        className="text-xs font-mono font-bold text-gray-400 hover:text-red-500 underline decoration-2 underline-offset-2 transition-colors"
                    >
                        RESET
                    </button>
                 </div>
            </div>
        </header>

        {view === 'dashboard' ? (
          <Dashboard 
            onNavigate={navigateToAnalyzer} 
            onNavigateKnowledgeBase={navigateToKnowledgeBase}
            userId="test-user-id" 
          />
        ) : view === 'knowledgeBase' ? (
          <StockKnowledgeBase 
            symbol={selectedSymbol} 
            onBack={navigateToDashboard} 
          />
        ) : (
          <Analyzer 
            initialSymbol={selectedSymbol} 
            onBack={navigateToDashboard} 
          />
        )}

      </div>
    </div>
  );
}
