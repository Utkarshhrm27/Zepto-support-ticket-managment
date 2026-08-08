import { useState } from 'react'
import { createTicket, processAll, uploadTickets } from '../api/client'
import { X, Loader2, UploadCloud } from 'lucide-react'

export default function CreateTicketModal({ onClose, onCreated }) {
    const [description, setDescription] = useState('')
    const [orderId, setOrderId] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [mode, setMode] = useState('single') // 'single' or 'bulk'
    const [file, setFile] = useState(null)

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)
        setError('')
        try {
            if (mode === 'single') {
                if (!description || !orderId) throw new Error("All fields are required")
                await createTicket({ description, order_id: orderId })
            } else {
                if (!file) throw new Error("Please select a CSV file")
                await uploadTickets(file)
            }
            // Immediately run the pipeline for pending tickets
            await processAll()
            onCreated()
            onClose()
        } catch (err) {
            setError(err.message)
            setLoading(false)
        }
    }

    return (
        <div className="fixed inset-0 bg-black/95 z-50 flex items-center justify-center p-4">
            <div className="vector-box border-red-600 shadow-[4px_4px_0_0_rgba(220,38,38,1)] p-6 max-w-md w-full relative">
                <button onClick={onClose} className="absolute top-4 right-4 text-zinc-500 hover:text-red-500">
                    <X size={24} />
                </button>
                
                <h2 className="text-2xl font-black uppercase mb-6 text-white border-b-2 border-red-900 pb-2">Inject New Ticket</h2>
                
                {error && <div className="text-red-500 text-sm mb-4 border border-red-900 p-2 bg-red-950/30">{error}</div>}
                <div className="flex gap-4 mb-4 border-b-2 border-zinc-800">
                    <button 
                        onClick={() => setMode('single')} 
                        className={`pb-2 text-sm font-bold uppercase tracking-widest ${mode === 'single' ? 'text-red-500 border-b-2 border-red-500' : 'text-zinc-500 hover:text-white'}`}>
                        Single Inject
                    </button>
                    <button 
                        onClick={() => setMode('bulk')} 
                        className={`pb-2 text-sm font-bold uppercase tracking-widest ${mode === 'bulk' ? 'text-red-500 border-b-2 border-red-500' : 'text-zinc-500 hover:text-white'}`}>
                        Bulk CSV
                    </button>
                </div>
                
                <form onSubmit={handleSubmit} className="space-y-4">
                    {mode === 'single' ? (
                        <>
                            <div>
                                <label className="block text-xs uppercase text-zinc-400 mb-1">Order ID</label>
                                <input 
                                    type="text" 
                                    className="w-full bg-black border-2 border-zinc-700 p-2 text-white outline-none focus:border-red-500 font-sans"
                                    value={orderId}
                                    onChange={e => setOrderId(e.target.value)}
                                    placeholder="e.g. ORD-9999"
                                />
                                <p className="text-[10px] text-zinc-600 mt-1">If order doesn't exist, a dummy one will be created automatically.</p>
                            </div>

                            <div>
                                <label className="block text-xs uppercase text-zinc-400 mb-1">Issue Description</label>
                                <textarea 
                                    className="w-full bg-black border-2 border-zinc-700 p-2 text-white outline-none focus:border-red-500 font-sans h-32"
                                    value={description}
                                    onChange={e => setDescription(e.target.value)}
                                    placeholder="e.g. Tomato was completely rotten."
                                />
                            </div>
                        </>
                    ) : (
                        <div className="border-2 border-dashed border-zinc-700 p-8 text-center bg-black hover:border-red-500 transition-colors">
                            <UploadCloud className="mx-auto text-zinc-500 mb-4" size={48} />
                            <label className="block text-sm font-bold text-white mb-2 cursor-pointer">
                                <span className="text-red-500 hover:underline">Click to browse</span> or drag and drop
                                <input 
                                    type="file" 
                                    accept=".csv"
                                    className="hidden" 
                                    onChange={e => setFile(e.target.files[0])}
                                />
                            </label>
                            <p className="text-xs text-zinc-500 font-sans">
                                {file ? file.name : "Upload new_tickets.csv"}
                            </p>
                        </div>
                    )}

                    <button disabled={loading} type="submit" className="w-full vector-btn mt-4 flex justify-center items-center gap-2">
                        {loading ? <Loader2 className="animate-spin" size={18} /> : null}
                        {loading ? 'PROCESSING THROUGH PIPELINE...' : (mode === 'single' ? 'CREATE & PROCESS TICKET' : 'UPLOAD & PROCESS BATCH')}
                    </button>
                </form>
            </div>
        </div>
    )
}
