import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout/Layout'
import Dashboard from './pages/Dashboard'
import Configuration from './pages/Configuration'
import Indexes from './pages/Indexes'
import IndexManagement from './pages/IndexManagement'
import Logs from './pages/Logs'
import Onboarding from './pages/Onboarding'
import Profiles from './pages/Profiles'
import Memories from './pages/Memories'
import Conversations from './pages/Conversations'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/onboarding" element={<Onboarding />} />
        <Route path="/*" element={
          <Layout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/configuration" element={<Configuration />} />
              <Route path="/index-management" element={<IndexManagement />} />
              <Route path="/indexes" element={<IndexManagement />} />
              <Route path="/profiles" element={<Profiles />} />
              <Route path="/memories" element={<Memories />} />
              <Route path="/conversations" element={<Conversations />} />
              <Route path="/logs" element={<Logs />} />
            </Routes>
          </Layout>
        } />
      </Routes>
    </BrowserRouter>
  )
}

export default App

