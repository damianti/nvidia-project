import { redirect } from 'next/navigation'

export default function HomePage() {
  // For now, redirect to login
  // Later we'll check authentication status
  redirect('/login')
} 