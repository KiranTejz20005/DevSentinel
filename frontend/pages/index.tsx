import React, { useEffect, useMemo, useState } from "react";

type Incident = {
    id: string;
    severity: string;
    status: string;
    summary?: string;
    detected_at?: string;
    resolved_at?: string;
};

type Action = {
    incident_id: string;
    action: string;
    status: string;
    notes?: string;
    diff?: string;
};

const cardStyle: React.CSSProperties = {
    border: "1px solid #e0e0e0",
    borderRadius: 10,
    padding: "1rem",
    background: "#fff",
    boxShadow: "0 4px 12px rgba(0,0,0,0.04)",
};

const tagColor = (status: string) => {
    const s = status.toLowerCase();
    if (s === "resolved") return "#18a999";
    if (s === "pending") return "#f6a609";
    return "#555";
};

export default function Home() {
    const [incidents, setIncidents] = useState<Incident[]>([]);
    const [actions, setActions] = useState<Action[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [busyIds, setBusyIds] = useState<Record<string, boolean>>({});
    const [createText, setCreateText] = useState("Synthetic error: DB timeout on checkout");
    const [toast, setToast] = useState<string | null>(null);

    const refresh = async () => {
        try {
            const [incResp, actResp] = await Promise.all([
                fetch("/incidents"),
                fetch("/actions"),
            ]);
            const incJson = await incResp.json();
            const actJson = await actResp.json();
            setIncidents(incJson.incidents || []);
            setActions(actJson.actions || []);
        } catch (e: any) {
            setError(e?.message || "Failed to load data");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        refresh();
        const id = setInterval(refresh, 4000);
        return () => clearInterval(id);
    }, []);

    const handleRepair = async (incidentId: string) => {
        setBusyIds((prev) => ({ ...prev, [incidentId]: true }));
        setToast(null);
        try {
            const resp = await fetch("/repair", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id: incidentId }),
            });
            if (!resp.ok) throw new Error(`Repair failed (${resp.status})`);
            const data = await resp.json();
            setToast(`Repaired ${incidentId}`);
            await refresh();
            return data;
        } catch (e: any) {
            setToast(e?.message || "Repair failed");
        } finally {
            setBusyIds((prev) => ({ ...prev, [incidentId]: false }));
        }
    };

    const handleCreate = async () => {
        setToast(null);
        try {
            const resp = await fetch("/incidents", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ signal: createText || "Synthetic incident" }),
            });
            if (!resp.ok) throw new Error(`Create failed (${resp.status})`);
            setToast("Incident created");
            await refresh();
        } catch (e: any) {
            setToast(e?.message || "Create failed");
        }
    };

    const latestAction = useMemo(() => actions[0], [actions]);

    return (
        <main style={{ fontFamily: "'Segoe UI', sans-serif", padding: "2rem", maxWidth: 1080, margin: "0 auto", background: "#f6f7fb" }}>
            <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.25rem" }}>
                <div>
                    <h1 style={{ margin: 0 }}>DevSentinel</h1>
                    <div style={{ color: "#5a5a5a" }}>AI-driven incident management (demo)</div>
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                    <button
                        onClick={refresh}
                        style={{ padding: "0.5rem 0.9rem", borderRadius: 8, border: "1px solid #ddd", background: "#fff", cursor: "pointer" }}
                    >
                        Refresh
                    </button>
                </div>
            </header>

            {toast && (
                <div style={{ marginBottom: "0.75rem", padding: "0.65rem 0.9rem", borderRadius: 8, background: "#e8f5e9", color: "#1b5e20", border: "1px solid #c8e6c9" }}>
                    {toast}
                </div>
            )}
            {loading && <p>Loading...</p>}
            {error && <p style={{ color: "red" }}>{error}</p>}

            <section style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "1rem" }}>
                <div style={cardStyle}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                        <h2 style={{ margin: 0 }}>Incidents</h2>
                        <small style={{ color: "#666" }}>{incidents.length} total</small>
                    </div>
                    {incidents.length === 0 && <p>No incidents yet.</p>}
                    <div style={{ display: "grid", gap: "0.75rem" }}>
                        {incidents.map((inc) => (
                            <div key={inc.id} style={{ border: "1px solid #eee", borderRadius: 8, padding: "0.85rem", background: "#fafafa" }}>
                                <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center" }}>
                                    <div style={{ fontWeight: 600 }}>{inc.id}</div>
                                    <span style={{ padding: "0.2rem 0.55rem", borderRadius: 999, background: tagColor(inc.status), color: "#fff", fontSize: 12 }}>
                                        {inc.status}
                                    </span>
                                </div>
                                <div style={{ fontSize: 13, color: "#666", marginTop: 4 }}>Severity: {inc.severity}</div>
                                {inc.summary && <div style={{ marginTop: 6 }}>{inc.summary}</div>}
                                <div style={{ fontSize: 12, color: "#777", marginTop: 6 }}>
                                    Detected: {inc.detected_at || "n/a"}
                                    {inc.resolved_at ? ` | Resolved: ${inc.resolved_at}` : ""}
                                </div>
                                <div style={{ marginTop: 10, display: "flex", gap: 8 }}>
                                    <button
                                        onClick={() => handleRepair(inc.id)}
                                        disabled={busyIds[inc.id]}
                                        style={{ padding: "0.45rem 0.9rem", borderRadius: 8, border: "1px solid #ccc", background: busyIds[inc.id] ? "#e0e0e0" : "#0f766e", color: busyIds[inc.id] ? "#555" : "#fff", cursor: busyIds[inc.id] ? "not-allowed" : "pointer" }}
                                    >
                                        {busyIds[inc.id] ? "Repairing..." : "Run repair"}
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div style={{ display: "grid", gap: "1rem" }}>
                    <div style={cardStyle}>
                        <h3 style={{ marginTop: 0 }}>Create synthetic incident</h3>
                        <textarea
                            value={createText}
                            onChange={(e) => setCreateText(e.target.value)}
                            style={{ width: "100%", minHeight: 90, padding: 10, borderRadius: 8, border: "1px solid #ddd" }}
                        />
                        <button
                            onClick={handleCreate}
                            style={{ marginTop: 8, padding: "0.5rem 0.9rem", borderRadius: 8, border: "1px solid #0f766e", background: "#0f766e", color: "#fff", cursor: "pointer" }}
                        >
                            Add incident
                        </button>
                    </div>

                    <div style={cardStyle}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                            <h3 style={{ margin: 0 }}>Latest action</h3>
                            <small style={{ color: "#666" }}>{actions.length} total</small>
                        </div>
                        {!latestAction && <p>No actions yet.</p>}
                        {latestAction && (
                            <>
                                <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                                    <strong>{latestAction.action}</strong>
                                    <span style={{ padding: "0.2rem 0.6rem", borderRadius: 999, background: tagColor(latestAction.status), color: "#fff", fontSize: 12 }}>
                                        {latestAction.status}
                                    </span>
                                </div>
                                <div style={{ fontSize: 13, color: "#555", marginTop: 6 }}>Incident: {latestAction.incident_id}</div>
                                {latestAction.notes && <div style={{ marginTop: 6 }}>{latestAction.notes}</div>}
                                {latestAction.diff && (
                                    <pre style={{ marginTop: 10, fontSize: 12, background: "#0b1021", color: "#a2fca2", padding: "0.65rem", borderRadius: 8, overflowX: "auto" }}>
                                        {latestAction.diff}
                                    </pre>
                                )}
                            </>
                        )}
                    </div>

                    <div style={cardStyle}>
                        <h3 style={{ marginTop: 0 }}>Recent actions</h3>
                        {actions.length === 0 && <p>No actions yet.</p>}
                        <div style={{ display: "grid", gap: "0.6rem" }}>
                            {actions.map((act, idx) => (
                                <div key={idx} style={{ border: "1px solid #eee", borderRadius: 8, padding: "0.75rem", background: "#fdfdfd" }}>
                                    <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                                        <strong>{act.action}</strong>
                                        <span style={{ padding: "0.15rem 0.55rem", borderRadius: 999, background: tagColor(act.status), color: "#fff", fontSize: 12 }}>
                                            {act.status}
                                        </span>
                                    </div>
                                    <div style={{ fontSize: 13, color: "#555", marginTop: 4 }}>Incident: {act.incident_id}</div>
                                    {act.notes && <div style={{ marginTop: 6 }}>{act.notes}</div>}
                                    {act.diff && (
                                        <pre style={{ marginTop: 8, fontSize: 12, background: "#0b1021", color: "#a2fca2", padding: "0.6rem", borderRadius: 8, overflowX: "auto" }}>
                                            {act.diff}
                                        </pre>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </section>
        </main>
    );
}
