import { useState, useEffect } from 'react'
import { fetchTicketDetail } from '../api/client'
import ConfidenceBadge from './ConfidenceBadge'
import OverrideModal from './OverrideModal'
import { approveTicket } from '../api/client'
import { X, CheckCircle, AlertTriangle, ArrowLeft } from 'lucide-react'

export default function TicketDetail({ ticketId, onClose, onUpdate }) {
    const [detail, setDetail] = useState(null)
    const [loading, setLoading] = useState(true)
    const [showOverride, setShowOverride] = useState(false)

    useEffect(() => {
        fetchTicketDetail(ticketId).then(data => {
            setDetail(data)
            setLoading(false)
        }).catch(err => {
            console.error(err)
            setLoading(false)
        })
    }, [ticketId])

    if (loading) {
        return (
            <div className="fixed inset-0 bg-black/90 z-40 flex items-center justify-center">
                <div className="text-red-500 font-bold animate-pulse text-2xl tracking-widest">LOADING_DATA...</div>
            </div>
        )
    }

    if (!detail) return null

    const handleApprove = async () => {
        try {
            await approveTicket(ticketId)
            onUpdate()
            onClose()
        } catch(e) {
            console.error(e)
        }
    }

    const isPendingHuman = detail.status === 'needs_human'
    const isHumanResolved = ['approved', 'overridden'].includes(detail.status)
    const isCancelled = detail.order.delivery_status === 'cancelled'

    return (
        <div className="fixed inset-0 bg-black/95 z-40 overflow-y-auto p-4 md:p-8">
            <div className="max-w-6xl mx-auto">
                
                {/* Header */}
                <div className="flex justify-between items-center border-b-2 border-red-900 pb-4 mb-6">
                    <div>
                        <button onClick={onClose} className="text-zinc-400 hover:text-white flex items-center gap-2 mb-2 uppercase text-xs tracking-widest">
                            <ArrowLeft size={16} /> Back to Board
                        </button>
                        <h2 className="text-3xl font-black text-white">{detail.id}</h2>
                        <p className="text-zinc-400">{detail.description}</p>
                    </div>
                    <button onClick={onClose} className="p-2 bg-red-950/50 hover:bg-red-600 text-red-500 hover:text-white border border-red-900 transition-colors">
                        <X size={24} />
                    </button>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    
                    {/* Left Column: Context & Decision */}
                    <div className="lg:col-span-1 space-y-6">
                        
                        {/* Order Context */}
                        <div className="vector-box p-4 border-zinc-700 shadow-[4px_4px_0_0_rgba(113,113,122,1)] hover:shadow-[4px_4px_0_0_rgba(113,113,122,1)]">
                            <h3 className="text-lg font-bold text-white mb-4 uppercase border-b border-zinc-800 pb-2">Order Context</h3>
                            <div className="space-y-2 text-sm">
                                <div className="flex justify-between"><span className="text-zinc-500">Order ID</span><span className="font-bold text-zinc-300">{detail.order.id}</span></div>
                                <div className="flex justify-between"><span className="text-zinc-500">Items</span><span className="font-bold text-zinc-300">{detail.order.items}</span></div>
                                <div className="flex justify-between"><span className="text-zinc-500">Value</span><span className="font-bold text-zinc-300">₹{detail.order.value_inr}</span></div>
                                <div className="flex justify-between"><span className="text-zinc-500">Delivery Status</span>
                                    <span className={`font-bold ${isCancelled ? 'text-red-500' : 'text-green-500'}`}>
                                        {detail.order.delivery_status.toUpperCase()}
                                    </span>
                                </div>
                            </div>
                            {isCancelled && (
                                <div className="mt-4 p-2 bg-red-950 border border-red-500 text-red-400 text-xs flex items-start gap-2">
                                    <AlertTriangle size={16} className="shrink-0 mt-0.5" />
                                    <span>ORDER CANCELLED. Redelivery is unavailable for this order.</span>
                                </div>
                            )}
                        </div>

                        {/* AI Decision */}
                        <div className={`vector-box p-4 ${detail.status === 'auto_resolved' ? 'border-green-600 shadow-[4px_4px_0_0_rgba(22,163,74,1)]' : 'border-yellow-600 shadow-[4px_4px_0_0_rgba(202,138,4,1)]'}`}>
                            <h3 className="text-lg font-bold text-white mb-2 uppercase border-b border-zinc-800 pb-2 flex items-center gap-2">
                                AI Decision 
                                {detail.status === 'auto_resolved' ? <CheckCircle size={18} className="text-green-500"/> : <AlertTriangle size={18} className="text-yellow-500"/>}
                            </h3>
                            
                            <div className="flex items-center gap-4 my-4">
                                <div>
                                    <div className="text-xs text-zinc-500 uppercase">Confidence</div>
                                    <div className="text-3xl font-black text-white">{(detail.confidence * 100).toFixed(0)}%</div>
                                </div>
                                <div>
                                    <div className="text-xs text-zinc-500 uppercase">Action</div>
                                    <div className="text-xl font-bold text-red-500 uppercase">{detail.predicted_action || 'NONE'}</div>
                                </div>
                            </div>

                            <div className="text-sm bg-black p-3 border border-zinc-800 text-zinc-400">
                                <span className="block text-xs uppercase text-zinc-600 mb-1">Reasoning</span>
                                {detail.reasoning}
                            </div>
                        </div>

                        {/* Human Controls */}
                        {isPendingHuman && (
                            <div className="vector-box p-4 border-yellow-600 bg-yellow-950/20">
                                <h3 className="text-sm font-bold text-yellow-500 mb-4 uppercase">Human Review Required</h3>
                                <div className="flex flex-col gap-3">
                                    <button onClick={handleApprove} className="w-full vector-btn bg-green-600 hover:text-green-600 shadow-[4px_4px_0_0_rgba(21,128,61,1)]">
                                        APPROVE SUGGESTION
                                    </button>
                                    <button onClick={() => setShowOverride(true)} className="w-full vector-btn-outline border-yellow-600 text-yellow-500 hover:bg-yellow-600 shadow-[4px_4px_0_0_rgba(202,138,4,1)]">
                                        OVERRIDE ACTION
                                    </button>
                                </div>
                            </div>
                        )}

                        {isHumanResolved && (
                            <div className="vector-box p-4 border-blue-600 shadow-[4px_4px_0_0_rgba(37,99,235,1)]">
                                <div className="text-xs uppercase text-zinc-500 mb-1">Final Human Action</div>
                                <div className="text-xl font-bold text-blue-400">{detail.final_action}</div>
                            </div>
                        )}

                    </div>

                    {/* Right Column: Precedents & Reply */}
                    <div className="lg:col-span-2 space-y-6">
                        
                        {/* Drafted Reply */}
                        <div className="vector-box p-6 border-zinc-700 shadow-[4px_4px_0_0_rgba(113,113,122,1)]">
                            <h3 className="text-lg font-bold text-white mb-4 uppercase border-b border-zinc-800 pb-2">Drafted Customer Reply</h3>
                            <div className="bg-black border border-zinc-800 p-4 font-sans text-zinc-300 text-lg">
                                {detail.drafted_reply}
                            </div>
                        </div>

                        {/* Precedents */}
                        <div className="vector-box p-6 border-zinc-700 shadow-[4px_4px_0_0_rgba(113,113,122,1)]">
                            <h3 className="text-lg font-bold text-white mb-4 uppercase border-b border-zinc-800 pb-2">Top Similar Precedents</h3>
                            
                            {detail.precedents.length === 0 ? (
                                <div className="text-zinc-500 italic">No historical precedents found for this ticket.</div>
                            ) : (
                                <div className="space-y-4">
                                    {detail.precedents.map((p, idx) => (
                                        <div key={p.id} className="bg-black border border-zinc-800 p-4 flex flex-col md:flex-row gap-4 justify-between items-start">
                                            <div className="flex-1">
                                                <div className="flex items-center gap-3 mb-2">
                                                    <span className="font-bold text-white">{p.id}</span>
                                                    <span className="text-xs px-2 py-1 bg-red-950 text-red-500 border border-red-900">
                                                        {(p.score * 100).toFixed(0)}% MATCH
                                                    </span>
                                                </div>
                                                <p className="text-sm text-zinc-400 font-sans mb-3">"{p.description}"</p>
                                                <div className="text-xs text-zinc-500">
                                                    <span className="uppercase mr-2">Resolution:</span> 
                                                    <span className="text-zinc-300">{p.resolution_note}</span>
                                                </div>
                                            </div>
                                            <div className="text-right shrink-0">
                                                <div className="text-xs uppercase text-zinc-500 mb-1">Action</div>
                                                <div className="font-bold text-red-500">{p.resolution_action}</div>
                                                <div className="mt-2 text-yellow-500 text-xs">
                                                    {'★'.repeat(p.csat)}{'☆'.repeat(5 - p.csat)}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                    </div>
                </div>
                
                {showOverride && <OverrideModal ticket={detail} onClose={() => setShowOverride(false)} onUpdate={() => { onUpdate(); onClose(); }} />}
            </div>
        </div>
    )
}
