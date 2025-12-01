'use client'

import { useAuth } from '@/contexts/AuthContext'
import Logo from '@/components/Logo'
import Link from 'next/link'

export default function Navbar() {
    const { user, logout } = useAuth()

    return (
        <nav className="modern-nav rounded-2xl mb-8">
            <div className='max-w-7xl mx-auto px-6 py-4'>
                <div className='flex justify-between items-center'>
                
                {/* logo */}
                <div>
                    <Logo/>
                </div>
                
                {user && (
                    <div className='flex space-x-4'>
                        <Link href="/dashboard" className="btn-modern">Dashboard</Link>
                        <Link href="/images" className="btn-modern">Images</Link>
                        <Link href="/containers" className="btn-modern">Containers</Link>
                        <Link href="/billing" className="btn-modern">Billing</Link>
                    </div>
                )}

                {user ? (
                    
                    <div className='flex items-center space-x-4'>
                        <span className="text-gray-700">Hello, {user.username}</span>
                        <button onClick={logout} className="btn-modern">Logout</button>
                    </div>
                ) : (
                    <Link href="/login" className="btn-modern">Login</Link>
                    
                )}
                </div>
            </div>
       
        </nav>
    )
}
