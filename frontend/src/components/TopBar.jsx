export default function TopBar({ title, subtitle }) {
  return (
    <header className="topbar">
      <div>
        <h2>{title}</h2>
        {subtitle && <p>{subtitle}</p>}
      </div>
      <div className="topbar-actions">
        <input className="search" placeholder="Quick find..." />
        <button className="ghost-btn">Export Report</button>
      </div>
    </header>
  )
}
