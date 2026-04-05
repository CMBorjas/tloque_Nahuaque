import { useCallback, useEffect, useState } from "react";
import {
  API_BASE,
  apiGet,
  apiPatch,
  apiPost,
  type AuditLogRow,
  type ContainerRow,
  type HealthResponse,
  type InventoryItem,
  type Task,
} from "./api";
import { SysAdminChat } from "./components/SysAdminChat";
import "./App.css";

type NavId = "dashboard" | "orchestration" | "inventory" | "compliance" | "chat";

const NAV_ITEMS: { id: NavId; label: string; hint: string }[] = [
  { id: "dashboard", label: "Dashboard", hint: "Health & telemetry" },
  { id: "orchestration", label: "Orchestration", hint: "Deploy, containers, backup" },
  { id: "inventory", label: "Inventory", hint: "Stock & procurement tasks" },
  { id: "compliance", label: "Compliance", hint: "Audit log" },
  { id: "chat", label: "SysAdmin AI", hint: "Conversational control" },
];

export default function App() {
  const [nav, setNav] = useState<NavId>("dashboard");
  const [backendOk, setBackendOk] = useState<boolean | null>(null);

  const pingHealth = useCallback(() => {
    fetch(`${API_BASE}/health`)
      .then((r) => r.ok)
      .then(setBackendOk)
      .catch(() => setBackendOk(false));
  }, []);

  useEffect(() => {
    pingHealth();
    const t = setInterval(pingHealth, 30000);
    return () => clearInterval(t);
  }, [pingHealth]);

  return (
    <div className="app-layout">
      <aside className="sidebar" aria-label="Main navigation">
        <div className="sidebar-brand">
          <span className="brand-mark" aria-hidden />
          <div>
            <h1>Tloque Nahuaque</h1>
            <p className="tagline">Orchestrator</p>
          </div>
        </div>
        <nav className="nav-rail">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`nav-item ${nav === item.id ? "active" : ""}`}
              onClick={() => setNav(item.id)}
              title={item.hint}
            >
              <span className="nav-item-label">{item.label}</span>
              <span className="nav-item-hint">{item.hint}</span>
            </button>
          ))}
        </nav>
        <div
          className={`sidebar-status ${backendOk === true ? "ok" : backendOk === false ? "bad" : "unk"}`}
        >
          {backendOk === true
            ? "API online"
            : backendOk === false
              ? "API offline"
              : "…"}
        </div>
      </aside>

      <div className="app-main">
        <header className="main-header">
          <h2 className="page-title">
            {NAV_ITEMS.find((n) => n.id === nav)?.label ?? nav}
          </h2>
          <p className="page-sub">
            {NAV_ITEMS.find((n) => n.id === nav)?.hint}
          </p>
        </header>

        <div className="page-body">
          {nav === "dashboard" && <DashboardPage onRefreshHealth={pingHealth} />}
          {nav === "orchestration" && <OrchestrationPage />}
          {nav === "inventory" && <InventoryPage />}
          {nav === "compliance" && <CompliancePage />}
          {nav === "chat" && <SysAdminChat />}
        </div>
      </div>
    </div>
  );
}

function DashboardPage({ onRefreshHealth }: { onRefreshHealth: () => void }) {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [metrics, setMetrics] = useState<{
    cpu_percent: number;
    memory_percent: number;
    disk_usage: number;
  } | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const [h, tel] = await Promise.all([
        apiGet<HealthResponse>("/health"),
        apiGet<{
          status: string;
          metrics: {
            cpu_percent: number;
            memory_percent: number;
            disk_usage: number;
          };
        }>("/api/system/telemetry"),
      ]);
      setHealth(h);
      setMetrics(tel.metrics);
      onRefreshHealth();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Failed to load");
      setHealth(null);
      setMetrics(null);
    } finally {
      setLoading(false);
    }
  }, [onRefreshHealth]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <section className="panel">
      {err && <p className="banner error">{err}</p>}
      <div className="toolbar">
        <button type="button" className="btn secondary" onClick={() => void load()} disabled={loading}>
          {loading ? "Refreshing…" : "Refresh"}
        </button>
      </div>
      <div className="card-grid">
        <article className="card">
          <h3>API health</h3>
          {health ? (
            <dl className="stat-list">
              <dt>Status</dt>
              <dd>{health.status}</dd>
              <dt>Services (reported)</dt>
              <dd>{health.services_running}</dd>
            </dl>
          ) : (
            <p className="muted">{loading ? "Loading…" : "—"}</p>
          )}
        </article>
        <article className="card">
          <h3>Host telemetry</h3>
          {metrics ? (
            <dl className="stat-list">
              <dt>CPU</dt>
              <dd>{metrics.cpu_percent.toFixed(1)}%</dd>
              <dt>RAM used</dt>
              <dd>{metrics.memory_percent.toFixed(1)}%</dd>
              <dt>Disk (root)</dt>
              <dd>{metrics.disk_usage.toFixed(1)}%</dd>
            </dl>
          ) : (
            <p className="muted">{loading ? "Loading…" : "—"}</p>
          )}
        </article>
      </div>
      <p className="footnote">
        Open the <strong>Orchestration</strong> page for Docker container tables, <strong>Inventory</strong> for stock, <strong>Compliance</strong> for audit logs, or <strong>SysAdmin AI</strong> for natural language.
      </p>
    </section>
  );
}

function OrchestrationPage() {
  const [containers, setContainers] = useState<ContainerRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [deployBusy, setDeployBusy] = useState(false);
  const [deployMsg, setDeployMsg] = useState<string | null>(null);
  const [volumeName, setVolumeName] = useState("");
  const [backupBusy, setBackupBusy] = useState(false);

  const loadContainers = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const data = await apiGet<{ status: string; containers: ContainerRow[] }>(
        "/api/orchestration/status"
      );
      setContainers(data.containers);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Failed to load containers");
      setContainers([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadContainers();
  }, [loadContainers]);

  const runDeploy = async () => {
    setDeployMsg(null);
    setDeployBusy(true);
    try {
      const res = await apiPost<Record<string, unknown>>("/api/orchestration/deploy", {});
      setDeployMsg(JSON.stringify(res, null, 2));
      await loadContainers();
    } catch (e) {
      setDeployMsg(e instanceof Error ? e.message : "Deploy failed");
    } finally {
      setDeployBusy(false);
    }
  };

  const runBackup = async () => {
    const v = volumeName.trim();
    if (!v) return;
    setBackupBusy(true);
    try {
      const res = await apiPost<Record<string, unknown>>("/api/orchestration/backup", {
        volume_name: v,
      });
      setDeployMsg(JSON.stringify(res, null, 2));
    } catch (e) {
      setDeployMsg(e instanceof Error ? e.message : "Backup failed");
    } finally {
      setBackupBusy(false);
    }
  };

  return (
    <section className="panel">
      {err && <p className="banner error">{err}</p>}
      <div className="toolbar wrap">
        <button
          type="button"
          className="btn secondary"
          onClick={() => void loadContainers()}
          disabled={loading}
        >
          Refresh containers
        </button>
        <button
          type="button"
          className="btn warn"
          onClick={() => void runDeploy()}
          disabled={deployBusy}
        >
          {deployBusy ? "Deploying…" : "Deploy stack (catalog.yml)"}
        </button>
      </div>
      {deployMsg && (
        <pre className="code-block">{deployMsg}</pre>
      )}

      <h3 className="section-title">Containers</h3>
      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Status</th>
              <th>ID</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={3} className="muted">
                  Loading…
                </td>
              </tr>
            ) : containers.length === 0 ? (
              <tr>
                <td colSpan={3} className="muted">
                  No containers (or Docker unavailable).
                </td>
              </tr>
            ) : (
              [...containers]
                .sort((a, b) => (a.name || "").localeCompare(b.name || ""))
                .map((c) => (
                  <tr key={c.id}>
                    <td>{c.name}</td>
                    <td>
                      <span className={`pill ${c.status === "running" ? "ok" : ""}`}>
                        {c.status}
                      </span>
                    </td>
                    <td className="mono">{c.id}</td>
                  </tr>
                ))
            )}
          </tbody>
        </table>
      </div>

      <h3 className="section-title">Backup volume</h3>
      <div className="inline-form">
        <input
          type="text"
          className="input"
          placeholder="Docker volume name"
          value={volumeName}
          onChange={(e) => setVolumeName(e.target.value)}
          aria-label="Volume name"
        />
        <button
          type="button"
          className="btn secondary"
          disabled={backupBusy || !volumeName.trim()}
          onClick={() => void runBackup()}
        >
          {backupBusy ? "Running…" : "Run backup"}
        </button>
      </div>
    </section>
  );
}

function InventoryPage() {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [newItem, setNewItem] = useState({
    item_id: "",
    name: "",
    quantity: "0",
    threshold: "0",
    unit: "",
  });
  const [consumeItemId, setConsumeItemId] = useState("");
  const [consumeAmount, setConsumeAmount] = useState("1");
  const [msg, setMsg] = useState<string | null>(null);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const [inv, t] = await Promise.all([
        apiGet<InventoryItem[]>("/api/inventory"),
        apiGet<Task[]>("/api/inventory/tasks"),
      ]);
      setItems(inv);
      setTasks(t);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Load failed");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const addItem = async () => {
    setMsg(null);
    try {
      await apiPost("/api/inventory", {
        item_id: newItem.item_id.trim(),
        name: newItem.name.trim(),
        quantity: parseInt(newItem.quantity, 10) || 0,
        threshold: parseInt(newItem.threshold, 10) || 0,
        unit: newItem.unit.trim() || "unit",
      });
      setMsg("Item saved.");
      void load();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Save failed");
    }
  };

  const consume = async () => {
    setMsg(null);
    try {
      await apiPost("/api/inventory/consume", {
        item_id: consumeItemId.trim(),
        amount: parseInt(consumeAmount, 10) || 0,
      });
      setMsg("Consumption recorded.");
      void load();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Consume failed");
    }
  };

  const patchTask = async (taskId: number, status: string) => {
    setMsg(null);
    try {
      await apiPatch(`/api/inventory/tasks/${taskId}`, { status });
      setMsg("Task updated.");
      void load();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Update failed");
    }
  };

  return (
    <section className="panel">
      {err && <p className="banner error">{err}</p>}
      {msg && <p className="banner ok">{msg}</p>}
      <div className="toolbar">
        <button type="button" className="btn secondary" onClick={() => void load()} disabled={loading}>
          Refresh
        </button>
      </div>

      <h3 className="section-title">Add / update item</h3>
      <div className="form-grid">
        <label>
          Item ID
          <input
            className="input"
            value={newItem.item_id}
            onChange={(e) => setNewItem((m) => ({ ...m, item_id: e.target.value }))}
            placeholder="paper_01"
          />
        </label>
        <label>
          Name
          <input
            className="input"
            value={newItem.name}
            onChange={(e) => setNewItem((m) => ({ ...m, name: e.target.value }))}
          />
        </label>
        <label>
          Quantity
          <input
            className="input"
            type="number"
            value={newItem.quantity}
            onChange={(e) => setNewItem((m) => ({ ...m, quantity: e.target.value }))}
          />
        </label>
        <label>
          Threshold
          <input
            className="input"
            type="number"
            value={newItem.threshold}
            onChange={(e) => setNewItem((m) => ({ ...m, threshold: e.target.value }))}
          />
        </label>
        <label>
          Unit
          <input
            className="input"
            value={newItem.unit}
            onChange={(e) => setNewItem((m) => ({ ...m, unit: e.target.value }))}
            placeholder="boxes"
          />
        </label>
        <div className="form-actions">
          <button type="button" className="btn primary" onClick={() => void addItem()}>
            Save item
          </button>
        </div>
      </div>

      <h3 className="section-title">Consume stock</h3>
      <div className="inline-form">
        <input
          className="input"
          placeholder="item_id"
          value={consumeItemId}
          onChange={(e) => setConsumeItemId(e.target.value)}
        />
        <input
          className="input short"
          type="number"
          placeholder="amount"
          value={consumeAmount}
          onChange={(e) => setConsumeAmount(e.target.value)}
        />
        <button type="button" className="btn secondary" onClick={() => void consume()}>
          Consume
        </button>
      </div>

      <h3 className="section-title">Inventory</h3>
      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Qty</th>
              <th>Threshold</th>
              <th>Unit</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={5} className="muted">
                  Loading…
                </td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={5} className="muted">
                  No items yet.
                </td>
              </tr>
            ) : (
              items.map((it) => (
                <tr key={it.item_id}>
                  <td className="mono">{it.item_id}</td>
                  <td>{it.name}</td>
                  <td>{it.quantity}</td>
                  <td>{it.threshold}</td>
                  <td>{it.unit}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <h3 className="section-title">Procurement tasks</h3>
      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Title</th>
              <th>Status</th>
              <th>Created</th>
              <th>Update</th>
            </tr>
          </thead>
          <tbody>
            {tasks.length === 0 ? (
              <tr>
                <td colSpan={5} className="muted">
                  No tasks.
                </td>
              </tr>
            ) : (
              tasks.map((t) => (
                <tr key={t.task_id ?? `${t.title}-${t.created_at}`}>
                  <td className="mono">{t.task_id ?? "—"}</td>
                  <td>{t.title}</td>
                  <td>{t.status}</td>
                  <td className="mono small">{t.created_at}</td>
                  <td>
                    {t.task_id != null ? (
                      <TaskStatusEditor
                        taskId={t.task_id}
                        current={t.status}
                        onSave={patchTask}
                      />
                    ) : (
                      "—"
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function TaskStatusEditor({
  taskId,
  current,
  onSave,
}: {
  taskId: number;
  current: string;
  onSave: (id: number, s: string) => void;
}) {
  const [val, setVal] = useState(current);
  useEffect(() => setVal(current), [current]);
  return (
    <div className="task-edit">
      <input
        className="input small"
        value={val}
        onChange={(e) => setVal(e.target.value)}
        aria-label="Task status"
      />
      <button type="button" className="btn tiny" onClick={() => onSave(taskId, val)}>
        Save
      </button>
    </div>
  );
}

function CompliancePage() {
  const [limit, setLimit] = useState(100);
  const [logs, setLogs] = useState<AuditLogRow[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const data = await apiGet<{ status: string; logs: AuditLogRow[] }>(
        `/api/compliance/audit?limit=${encodeURIComponent(String(limit))}`
      );
      setLogs(data.logs);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Load failed");
    } finally {
      setLoading(false);
    }
  }, [limit]);

  return (
    <section className="panel">
      {err && <p className="banner error">{err}</p>}
      <div className="toolbar wrap">
        <label className="inline-label">
          Limit
          <input
            type="number"
            className="input short"
            value={limit}
            min={1}
            max={500}
            onChange={(e) => setLimit(parseInt(e.target.value, 10) || 100)}
          />
        </label>
        <button type="button" className="btn secondary" onClick={() => void load()} disabled={loading}>
          {loading ? "Loading…" : "Load audit log"}
        </button>
      </div>
      <p className="muted small">Load entries from the orchestrator audit store (may be empty until events are logged).</p>
      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Time</th>
              <th>Service</th>
              <th>Event</th>
              <th>User</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {logs.length === 0 ? (
              <tr>
                <td colSpan={6} className="muted">
                  {loading ? "Loading…" : "No audit entries yet."}
                </td>
              </tr>
            ) : (
              logs.map((r) => (
                <tr key={r.id}>
                  <td className="mono">{r.id}</td>
                  <td className="mono small">{r.timestamp}</td>
                  <td>{r.service}</td>
                  <td>{r.event_type}</td>
                  <td>{r.user}</td>
                  <td className="details-cell">{r.details}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
