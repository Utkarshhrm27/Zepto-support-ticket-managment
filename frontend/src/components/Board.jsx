import Lane from './Lane'

export default function Board({ tickets, onUpdate }) {
    const autoTickets = tickets.filter(t => t.status === 'auto_resolved')
    const humanTickets = tickets.filter(t => ['needs_human', 'approved', 'overridden'].includes(t.status))

    return (
        <div className="flex gap-8">
            <Lane title="[SYS] AUTO_RESOLVED" tickets={autoTickets} onUpdate={onUpdate} type="auto" />
            <Lane title="[REQ] NEEDS_HUMAN" tickets={humanTickets} onUpdate={onUpdate} type="human" />
        </div>
    )
}
