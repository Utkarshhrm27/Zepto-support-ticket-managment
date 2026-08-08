import { useState } from 'react'
import ConfidenceBadge from './ConfidenceBadge'
import OverrideModal from './OverrideModal'
import { approveTicket } from '../api/client'
import { ArrowRight } from 'lucide-react'

export default function TicketCard({ ticket, onUpdate, laneType, onClick }) {
    const [showOverride, setShowOverride] = useState(false)

    const handleApprove = async () => {
        try {
            await approveTicket(ticket.id)
            onUpdate()
        } catch(e) {
            console.error(e)
        }
    }

    const isPendingHuman = ticket.status === 'needs_human'
    const isHumanResolved = ['approved', 'overridden'].includes(ticket.status)

    return (
        <div className="bg-black border border-zinc-700 p-4 shadow-[4px_4px_0_0_rgba(255,255,255,0.05)] hover:border-zinc-500 transition-colors">
            <div className="flex justify-between items-start mb-2">
                <span className="font-bold text-red-500">{ticket.id}</span>
                <span className="text-xs text-zinc-500">{new Date(ticket.created_at).toLocaleTimeString()}</span>
            </div>
            
            <p className="text-sm text-zinc-300 mb-4 font-sans">{ticket.description}</p>
            
            <div className="bg-zinc-900 border border-zinc-800 p-2 text-xs mb-4">
                <div className="flex items-center justify-between mb-1">
                    <span className="uppercase text-zinc-500">Predicted Action</span>
                    <ConfidenceBadge confidence={ticket.confidence} />
                </div>
                <div className="font-bold text-white uppercase">{ticket.predicted_action || 'NONE'}</div>
                {ticket.refund_amount_inr > 0 && (
                    <div className="text-green-400 mt-1">₹ {ticket.refund_amount_inr} REFUND</div>
                )}
                {isPendingHuman && (
                    <div className="mt-4 border-t border-yellow-900 pt-3">
                        <button onClick={onClick} className="w-full text-xs uppercase tracking-widest text-yellow-500 hover:text-white flex items-center justify-between">
                            <span>Review Required</span>
                            <ArrowRight size={14} />
                        </button>
                    </div>
                )}
                {ticket.status === 'auto_resolved' && (
                    <div className="mt-4 border-t border-green-900 pt-3">
                        <button onClick={onClick} className="w-full text-xs uppercase tracking-widest text-green-500 hover:text-white flex items-center justify-between">
                            <span>View Details</span>
                            <ArrowRight size={14} />
                        </button>
                    </div>
                )}
            </div>

            {isHumanResolved && (
                <div className="bg-red-950/30 border-l-2 border-red-500 p-2 mb-4 text-xs">
                    <span className="uppercase text-zinc-400 mr-2">Final Action:</span>
                    <span className="font-bold text-red-400">{ticket.final_action}</span>
                </div>
            )}

        </div>
    )
}
