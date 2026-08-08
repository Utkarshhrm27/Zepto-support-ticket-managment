import { useState } from 'react'
import { overrideTicket } from '../api/client'

const ACTIONS = [
    "redelivery", "full_refund", "partial_refund", "coupon", 
    "refund_reissue", "apology_no_action", "escalation"
]

export default function OverrideModal({ ticket, onClose, onUpdate }) {
    const [action, setAction] = useState(ACTIONS[0])
    const [reason, setReason] = useState("")

    const handleSubmit = async (e) => {
        e.preventDefault()
        try {
            await overrideTicket(ticket.id, { action, reason, resolved_by: "human" })
            onUpdate()
            onClose()
        } catch (err) {
            console.error(err)
        }
    }

    return (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
            <div className="bg-zinc-900 border-2 border-red-600 shadow-[8px_8px_0_0_rgba(220,38,38,1)] p-6 w-[400px]">
                <h3 className="text-xl font-bold uppercase mb-4 text-white">Override Protocol: {ticket.id}</h3>
                <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                    <div>
                        <label className="block text-xs uppercase text-zinc-400 mb-1">New Action</label>
                        <select 
                            value={action} 
                            onChange={e => setAction(e.target.value)}
                            className="w-full bg-black border-2 border-zinc-700 p-2 text-white outline-none focus:border-red-500"
                        >
                            {ACTIONS.map(a => <option key={a} value={a}>{a.toUpperCase()}</option>)}
                        </select>
                    </div>
                    <div>
                        <label className="block text-xs uppercase text-zinc-400 mb-1">Reason</label>
                        <textarea 
                            required
                            value={reason}
                            onChange={e => setReason(e.target.value)}
                            className="w-full bg-black border-2 border-zinc-700 p-2 text-white outline-none focus:border-red-500 h-24"
                        ></textarea>
                    </div>
                    <div className="flex gap-2 justify-end mt-4">
                        <button type="button" onClick={onClose} className="vector-btn-outline">Cancel</button>
                        <button type="submit" className="vector-btn">Execute</button>
                    </div>
                </form>
            </div>
        </div>
    )
}
