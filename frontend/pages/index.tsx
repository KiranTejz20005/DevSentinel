import React, { useEffect, useState } from "react";

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

export default function Home() {
    const [incidents, setIncidents] = useState<Incident[]>([]);
    const [actions, setActions] = useState<Action[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const load = async () => {
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

        load();
    }, []);

    return (
        <main style={{ fontFamily: "'Segoe UI', sans-serif", padding: "2rem", maxWidth: 900 }}>
            <h1>DevSentinel</h1>
            <p style={{ color: "#555" }}>
                AI-driven incident management prototype. Data is mocked; wire to Kestra/Cline in production.
            </p>

            {loading && <p>Loading...</p>}
            {error && <p style={{ color: "red" }}>{error}</p>}

            <section style={{ marginTop: "1.5rem" }}>
                <h2>Incidents</h2>
                {incidents.length === 0 && <p>No incidents yet.</p>}
                <div style={{ display: "grid", gap: "0.75rem" }}>
                    {incidents.map((inc) => (
                        <div key={inc.id} style={{ border: "1px solid #ddd", borderRadius: 8, padding: "0.75rem" }}>
                            <div style={{ display: "flex", justifyContent: "space-between" }}>
                                <strong>{inc.id}</strong>
                                <span>{inc.status}</span>
                            </div>
                            <div style={{ fontSize: 14, color: "#666" }}>Severity: {inc.severity}</div>
                            {inc.summary && <div style={{ marginTop: 6 }}>{inc.summary}</div>}
                            <div style={{ fontSize: 12, color: "#777", marginTop: 4 }}>
                                Detected: {inc.detected_at || "n/a"}
                                {inc.resolved_at ? ` | Resolved: ${inc.resolved_at}` : ""}
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            <section style={{ marginTop: "1.5rem" }}>
                <h2>Recent Actions</h2>
                {actions.length === 0 && <p>No actions yet.</p>}
                <div style={{ display: "grid", gap: "0.75rem" }}>
                    {actions.map((act, idx) => (
                        <div key={idx} style={{ border: "1px solid #eee", borderRadius: 8, padding: "0.75rem", background: "#fafafa" }}>
                            <div style={{ display: "flex", justifyContent: "space-between" }}>
                                <strong>{act.action}</strong>
                                <span>{act.status}</span>
                            </div>
                            <div style={{ fontSize: 14, color: "#555" }}>Incident: {act.incident_id}</div>
                            {act.notes && <div style={{ marginTop: 6 }}>{act.notes}</div>}
                            {act.diff && (
                                <pre style={{ marginTop: 8, fontSize: 12, background: "#111", color: "#0f0", padding: "0.5rem", borderRadius: 6, overflowX: "auto" }}>
                                    {act.diff}
                                </pre>
                            )}
                        </div>
                    ))}
                </div>
            </section>
        </main>
    );
}
