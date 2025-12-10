import { useState } from 'react';
import { supabase } from '../lib/supabase';

export function Auth({ onLogin }: { onLogin: () => void }) {
  const [loading, setLoading] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (isRegistering) {
        const { error } = await supabase.auth.signUp({
          email,
          password,
        });
        if (error) throw error;
        alert('注册确认邮件已发送，请检查您的邮箱。');
      } else {
        const { error } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (error) throw error;
        onLogin();
      }
    } catch (err: any) {
      setError(err.message || '发生未知错误');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] w-full max-w-md mx-auto animate-in fade-in duration-700">
      
      {/* Avant-Garde Header */}
      <div className="w-full mb-20 relative">
        <div className="absolute -left-6 -top-6 w-12 h-12 border-t-8 border-l-8 border-black"></div>
        <h1 className="text-8xl font-black font-serif tracking-tighter leading-none mb-4">
          {isRegistering ? '加入' : '进入'}
          <br />
          <span className="text-neon bg-black px-2 text-white">系统</span>
        </h1>
        <p className="font-mono text-sm tracking-[0.3em] uppercase text-gray-400 pl-1">
          System Access Protocol v2.5
        </p>
      </div>

      {/* Auth Form */}
      <form onSubmit={handleAuth} className="w-full space-y-12">
        
        {/* Email Field */}
        <div className="group relative">
          <label className="absolute -top-3 left-0 font-mono text-xs font-bold tracking-widest text-gray-400 group-focus-within:text-black transition-colors">
            ACCOUNT / 账户
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full bg-transparent border-b-4 border-gray-200 py-2 text-2xl font-serif font-bold focus:border-neon outline-none transition-all placeholder:text-gray-200 text-black"
            placeholder="name@example.com"
            required
          />
        </div>

        {/* Password Field */}
        <div className="group relative">
          <label className="absolute -top-3 left-0 font-mono text-xs font-bold tracking-widest text-gray-400 group-focus-within:text-black transition-colors">
            PASSWORD / 密码
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full bg-transparent border-b-4 border-gray-200 py-2 text-2xl font-serif font-bold focus:border-neon outline-none transition-all placeholder:text-gray-200 text-black"
            placeholder="••••••••"
            required
          />
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border-l-4 border-red-500 p-4">
            <p className="font-mono text-xs text-red-600 font-bold">{error}</p>
          </div>
        )}

        {/* Action Button */}
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-black text-white font-mono text-xl py-8 hover:bg-neon hover:text-black transition-all duration-300 font-bold tracking-[0.2em] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 group"
        >
          {loading ? (
             <span className="animate-pulse">处理中...</span>
          ) : (
            <>
              {isRegistering ? '注册账户' : '登录系统'}
              <span className="group-hover:translate-x-1 transition-transform">→</span>
            </>
          )}
        </button>

      </form>

      {/* Toggle Mode */}
      <div className="mt-12 text-center">
        <button
          onClick={() => setIsRegistering(!isRegistering)}
          className="font-mono text-sm text-gray-400 hover:text-black hover:underline decoration-neon decoration-2 underline-offset-4 transition-colors uppercase tracking-widest"
        >
          {isRegistering ? '已有账号？立即登录' : '新用户？创建账户'}
        </button>
      </div>

    </div>
  );
}
