export default function StatsBar({ stats }) {
    if (!stats) return null;
    return (
        <div className="grid grid-cols-4 gap-4 vector-box p-4 mb-8">
            <div className="text-center border-r-2 border-red-900 last:border-0">
                <div className="text-4xl font-black">{stats.total}</div>
                <div className="text-xs uppercase text-zinc-500">Total</div>
            </div>
            <div className="text-center border-r-2 border-red-900 last:border-0">
                <div className="text-4xl font-black text-green-500">{stats.auto_resolved}</div>
                <div className="text-xs uppercase text-zinc-500">Auto Resolved</div>
            </div>
            <div className="text-center border-r-2 border-red-900 last:border-0">
                <div className="text-4xl font-black text-yellow-500">{stats.needs_human}</div>
                <div className="text-xs uppercase text-zinc-500">Needs Human</div>
            </div>
            <div className="text-center">
                <div className="text-4xl font-black text-blue-500">{stats.auto_resolve_rate}%</div>
                <div className="text-xs uppercase text-zinc-500">Automation Rate</div>
            </div>
        </div>
    )
}
