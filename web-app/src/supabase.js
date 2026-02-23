import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://tttyeluyutbpczbslgwi.supabase.co'
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR0dHllbHV5dXRicGN6YnNsZ3dpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE3Nzg5NTIsImV4cCI6MjA4NzM1NDk1Mn0.kdcJtU_LHkZv20MFxDQZGkn2iz4ZBuZC3dQjLxWoaTs'

export const supabase = createClient(supabaseUrl, supabaseKey)
