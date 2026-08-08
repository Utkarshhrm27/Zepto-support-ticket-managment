import TicketCard from './TicketCard'

export default function Lane({ title, tickets, onUpdate, type, onTicketClick }) {
    const border = type === 'auto' ? 'border-green-600' : 'border-yellow-600'
    const shadow = type === 'auto' ? 'shadow-[4px_4px_0_0_rgba(22,163,74,1)]' : 'shadow-[4px_4px_0_0_rgba(202,138,4,1)]'

    return (
        <div className={`flex-1 flex flex-col bg-zinc-900 border-2 ${border} ${shadow} p-4`}>
            <h2 className="text-xl font-bold uppercase mb-4 tracking-widest border-b-2 border-zinc-800 pb-2">{title} ({tickets.length})</h2>
            <div className="flex-1 overflow-y-auto space-y-4 pr-2 custom-scrollbar">
                {tickets.length === 0 && <div className="text-zinc-600 italic">No entries found.</div>}
                {tickets.map(t => (
                    <TicketCard key={t.id} ticket={t} onUpdate={onUpdate} laneType={type} onClick={() => onTicketClick(t.id)} />
                ))}
            </div>
        </div>
    )
}
