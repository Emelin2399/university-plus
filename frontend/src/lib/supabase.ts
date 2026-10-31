import { createClient } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

/**
 * Cliente de Supabase para el navegador.
 * Usa SOLO la clave anónima (pública). Nunca la service key.
 */
export const supabase =
  url && anonKey ? createClient(url, anonKey) : null
