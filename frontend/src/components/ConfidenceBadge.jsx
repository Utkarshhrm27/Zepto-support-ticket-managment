export default function ConfidenceBadge({ confidence }) {
    if (confidence === null || confidence === undefined) return null;
    
    const confValue = (confidence * 100).toFixed(0);
    const isHigh = confidence >= 0.55;
    
    const color = isHigh ? "text-green-400 border-green-400" : "text-yellow-400 border-yellow-400";
    
    return (
        <span className={`px-2 py-0.5 text-xs font-bold border-2 ${color} bg-black/50 ml-2 shadow-[2px_2px_0_0_currentColor]`}>
            CONF: {confValue}%
        </span>
    )
}
