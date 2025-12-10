import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn('缺少 Supabase 环境变量 (VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY)。请检查 .env 文件。')
}

export const supabase = createClient(supabaseUrl || '', supabaseAnonKey || '')
