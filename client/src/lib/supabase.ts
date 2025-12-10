import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://placeholder.supabase.co'
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'placeholder'

if (!import.meta.env.VITE_SUPABASE_URL || !import.meta.env.VITE_SUPABASE_ANON_KEY) {
  console.warn('缺少 Supabase 环境变量 (VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY)。Auth 功能将无法正常工作。')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
