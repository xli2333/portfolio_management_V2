import { useState, useEffect } from 'react';
import { supabase } from './lib/supabase';
import { Session } from '@supabase/supabase-js';
import { Dashboard } from './components/Dashboard';
import { Analyzer } from './components/Analyzer';
import { StockKnowledgeBase } from './components/StockKnowledgeBase';
import { Auth } from './components/Auth';

type View = 'dashboard' | 'analyzer' | 'knowledgeBase';
type DashboardTab = 'portfolio' | 'advisor';

export default function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [view, setView] = useState<View>('dashboard');
  const [selectedSymbol, setSelectedSymbol] = useState<string>('');
  const [dashboardTab, setDashboardTab] = useState<DashboardTab>('portfolio');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setLoading(false);
    });

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });

    return () => subscription.unsubscribe();
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
    await supabase.auth.signOut();
    setSession(null);
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

  // Show auth screen if not logged in
  if (!session) {
    return (
      <div className="min-h-screen bg-white text-black font-sans">
        <Auth onLogin={() => {}} />
      </div>
    );
  }

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
                    用户: {session?.user?.email?.split('@')[0] || 'USER'}
                 </div>
                 <div className="flex items-center justify-end gap-4">
                    <div className="text-xs font-mono text-green-500">● ONLINE</div>
                    <button
                        onClick={handleLogout}
                        className="text-xs font-mono font-bold text-gray-400 hover:text-red-500 underline decoration-2 underline-offset-2 transition-colors"
                    >
                        LOGOUT
                    </button>
                 </div>
            </div>
        </header>

        <div style={{ display: view === 'dashboard' ? 'block' : 'none' }}>
          <Dashboard
            onNavigate={navigateToAnalyzer}
            onNavigateKnowledgeBase={navigateToKnowledgeBase}
            userId={session?.user?.id || ''}
            initialTab={dashboardTab}
            onTabChange={setDashboardTab}
          />
        </div>
        {view === 'knowledgeBase' && (
          <StockKnowledgeBase
            symbol={selectedSymbol}
            onBack={navigateToDashboard}
          />
        )}
        {view === 'analyzer' && (
          <Analyzer
            initialSymbol={selectedSymbol}
            onBack={navigateToDashboard}
          />
        )}

      </div>
    </div>
  );
}
