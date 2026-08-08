import { useState, useEffect } from 'react'
import { fetchStats, fetchBoardTickets, processAll } from './api/client'
import StatsBar from './components/StatsBar'
import Board from './components/Board'
import TicketDetail from './components/TicketDetail'
import CreateTicketModal from './components/CreateTicketModal'
import { Plus, Zap, Search, Package } from 'lucide-react'

function App() {
  const [stats, setStats] = useState(null)
  const [tickets, setTickets] = useState([])
  const [selectedTicketId, setSelectedTicketId] = useState(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResult, setSearchResult] = useState(null)

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

  const handleSearch = async (e) => {
    if (e.key === 'Enter' && searchQuery) {
        try {
            const res = await fetch(`http://127.0.0.1:8000/api/orders/${searchQuery}`)
            if (res.ok) {
                const data = await res.json()
                setSearchResult(data)
            } else {
                setSearchResult({ error: 'Order not found' })
            }
        } catch (err) {
            setSearchResult({ error: 'Network error' })
        }
    }
  }

  if (loading) return <div className="min-h-screen flex items-center justify-center text-3xl font-bold animate-pulse">LOADING_SYSTEM...</div>

  return (
    <div className="min-h-screen p-8 max-w-7xl mx-auto">
      <header className="flex flex-col md:flex-row justify-between items-center mb-8 border-b-4 border-red-900 pb-6 gap-4">
        <div>
          <h1 className="text-4xl md:text-5xl font-black tracking-tighter text-white uppercase drop-shadow-[2px_2px_0_rgba(220,38,38,1)]">
            Zepto Nexus
          </h1>
          <p className="text-red-500 font-bold uppercase tracking-widest text-sm mt-1">AI-Powered Resolution Matrix</p>
        </div>
        <div className="flex gap-4">
          <div className="relative flex items-center">
             <Search size={16} className="absolute left-3 text-zinc-500" />
             <input 
                type="text" 
                placeholder="Search Order (e.g. ORD-9924)" 
                className="bg-zinc-900 border border-zinc-700 text-sm text-white pl-9 pr-4 py-2 outline-none focus:border-red-500 font-sans w-64"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                onKeyDown={handleSearch}
             />
          </div>
          <button onClick={() => setShowCreateModal(true)} className="vector-btn bg-zinc-800 text-white shadow-[4px_4px_0_0_rgba(82,82,91,1)] hover:border-zinc-500 flex items-center gap-2">
            <Plus size={18} /> INJECT TICKET
          </button>
          <button onClick={handleProcessAll} className="vector-btn flex items-center gap-2">
            <Zap size={18} className="fill-current" /> EXECUTE PENDING
          </button>
        </div>
      </header>

      {searchResult && (
        <div className="mb-8 p-4 vector-box border-blue-600 shadow-[4px_4px_0_0_rgba(37,99,235,1)] flex items-center justify-between">
            {searchResult.error ? (
                <div className="text-red-500 font-bold">{searchResult.error}</div>
            ) : (
                <div className="flex gap-8 items-center w-full">
                    <div className="flex items-center gap-2">
                        <Package size={24} className="text-blue-500" />
                        <div>
                            <div className="text-xs text-zinc-500 uppercase">Order ID</div>
                            <div className="text-xl font-bold text-white">{searchResult.id}</div>
                        </div>
                    </div>
                    <div>
                        <div className="text-xs text-zinc-500 uppercase">Value</div>
                        <div className="font-bold text-white">₹{searchResult.value_inr}</div>
                    </div>
                    <div>
                        <div className="text-xs text-zinc-500 uppercase">Items</div>
                        <div className="font-bold text-white">{searchResult.items}</div>
                    </div>
                    <div>
                        <div className="text-xs text-zinc-500 uppercase">Status</div>
                        <div className={`font-bold uppercase ${searchResult.delivery_status === 'cancelled' ? 'text-red-500' : 'text-green-500'}`}>
                            {searchResult.delivery_status}
                        </div>
                    </div>
                </div>
            )}
            <button onClick={() => setSearchResult(null)} className="text-zinc-500 hover:text-white">✕</button>
        </div>
      )}

      <StatsBar stats={stats} />
      
      <div className="mt-8">
        <Board tickets={tickets} onUpdate={loadData} onTicketClick={(id) => setSelectedTicketId(id)} />
      </div>

      {selectedTicketId && (
        <TicketDetail 
            ticketId={selectedTicketId} 
            onClose={() => setSelectedTicketId(null)} 
            onUpdate={loadData} 
        />
      )}

      {showCreateModal && (
        <CreateTicketModal 
            onClose={() => setShowCreateModal(false)}
            onCreated={loadData}
        />
      )}
    </div>
  )
}

export default App
