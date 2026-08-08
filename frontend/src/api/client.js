const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export async function fetchStats() {
    const res = await fetch(`${API_URL}/stats`);
    if (!res.ok) throw new Error("Failed to fetch stats");
    return res.json();
}

export async function fetchBoardTickets() {
    const res = await fetch(`${API_URL}/tickets?lane=all`);
    if (!res.ok) throw new Error("Failed to fetch tickets");
    return res.json();
}

export async function approveTicket(id) {
    const res = await fetch(`${API_URL}/tickets/${id}/approve`, { method: "POST" });
    if (!res.ok) throw new Error("Failed to approve ticket");
    return res.json();
}

export async function overrideTicket(id, payload) {
    const res = await fetch(`${API_URL}/tickets/${id}/override`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error("Failed to override ticket");
    return res.json();
}

export async function processAll() {
    const res = await fetch(`${API_URL}/tickets/process-all`, { method: "POST" });
    return res.json();
}
