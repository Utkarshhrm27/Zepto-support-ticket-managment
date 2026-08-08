import Lane from './Lane'

export default function Board({ tickets, onUpdate, onTicketClick }) {
    const autoTickets = tickets.filter(t => t.status === 'auto_resolved')
    const humanTickets = tickets.filter(t => ['needs_human', 'approved', 'overridden'].includes(t.status))

    return (
        <div className="flex flex-col md:flex-row gap-8 w-full max-w-6xl mx-auto h-[calc(100vh-200px)]">
            <Lane title="[SYS] AUTO_RESOLVED" tickets={autoTickets} onUpdate={onUpdate} onTicketClick={onTicketClick} type="auto" />
            <Lane title="[REQ] NEEDS_HUMAN" tickets={humanTickets} onUpdate={onUpdate} onTicketClick={onTicketClick} type="human" />
        </div>
    )
}
