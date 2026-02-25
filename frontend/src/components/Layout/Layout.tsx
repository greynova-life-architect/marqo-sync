import { ReactNode } from 'react'
import Navbar from './Navbar'
import Sidebar from './Sidebar'

interface LayoutProps {
  children: ReactNode
}

function Layout({ children }: LayoutProps) {
  return (
    <div className="d-flex" style={{ minHeight: '100vh', backgroundColor: 'var(--clinical-bg-primary)' }}>
      <Sidebar />
      <div className="flex-grow-1" style={{ minHeight: '100vh', backgroundColor: 'var(--clinical-bg-primary)' }}>
        <Navbar />
        <main style={{ backgroundColor: 'var(--clinical-bg-primary)' }}>
          {children}
        </main>
      </div>
    </div>
  )
}

export default Layout

