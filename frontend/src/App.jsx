import { useState, useEffect } from 'react'
import { fetchStats, fetchBoardTickets, processAll } from './api/client'
import StatsBar from './components/StatsBar'
import Board from './components/Board'

function App() {
  const [stats, setStats] = useState(null)
  const [tickets, setTickets] = useState([])
  const [loading, setLoading] = useState(true)

  const loadData = async () => {
    try {
      const [s, t] = await Promise.all([fetchStats(), fetchBoardTickets()])
      setStats(s)
      setTickets(t)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 5000) // Poll every 5s
    return () => clearInterval(interval)
  }, [])

  const handleProcessAll = async () => {
    await processAll()
    loadData()
  }

  if (loading) return <div className="min-h-screen flex items-center justify-center text-3xl font-bold animate-pulse">LOADING_SYSTEM...</div>

  return (
    <div className="min-h-screen p-8 max-w-7xl mx-auto">
      <header className="flex justify-between items-end mb-8 border-b-4 border-red-600 pb-4">
        <div>
          <h1 className="text-5xl font-black uppercase tracking-widest text-red-600 drop-shadow-[0_0_10px_rgba(220,38,38,0.8)]">
            Zepto <span className="text-white">Nexus</span>
          </h1>
          <p className="text-zinc-400 mt-2">Support Ticket Gamified Console</p>
        </div>
        <button onClick={handleProcessAll} className="vector-btn">
          EXECUTE ALL PENDING
        </button>
      </header>

      <StatsBar stats={stats} />
      
      <div className="mt-8">
        <Board tickets={tickets} onUpdate={loadData} />
      </div>
    </div>
  )
}

export default App
