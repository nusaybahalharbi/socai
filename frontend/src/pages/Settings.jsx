export default function Settings() {
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold font-display">Settings</h1>
        <p className="text-sm text-soc-mute">Configuration is environment-driven (.env on the backend).</p>
      </div>
      <div className="panel p-5 space-y-3">
        <div>
          <div className="label">Data Mode</div>
          <div className="text-sm font-mono">DATA_MODE = mock | splunk (set in backend/.env)</div>
        </div>
        <div>
          <div className="label">Splunk Endpoint</div>
          <div className="text-sm font-mono">SPLUNK_HOST, SPLUNK_PORT, SPLUNK_USERNAME, SPLUNK_PASSWORD</div>
        </div>
        <div>
          <div className="label">Polling Interval</div>
          <div className="text-sm font-mono">SPLUNK_POLL_INTERVAL_SECONDS / MOCK_ALERT_INTERVAL_SECONDS</div>
        </div>
      </div>
      <div className="panel p-5">
        <div className="label">Demo Notes</div>
        <ul className="text-sm text-soc-mute mt-2 list-disc list-inside space-y-1">
          <li>In mock mode, the backend generates 5 synthetic alerts every 30s.</li>
          <li>Switch to splunk mode by setting <span className="font-mono text-soc-text">DATA_MODE=splunk</span> and Splunk creds, then restart the backend.</li>
          <li>Trigger a brute-force from Kali to see end-to-end ingestion → classification → MITRE → recommendation.</li>
        </ul>
      </div>
    </div>
  )
}
