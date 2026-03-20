export default function TopBar({ title, subtitle, onExport, theme, onToggleTheme }) {
  return (
    <header className="topbar">
      <div>
        <h2>{title}</h2>
        {subtitle && <p>{subtitle}</p>}
      </div>
      <div className="topbar-actions">
        <button
          className={`theme-toggle ${theme === 'dark' ? 'is-dark' : 'is-light'}`}
          onClick={onToggleTheme}
          title="Toggle dark/light mode"
          aria-label="Toggle dark/light mode"
        >
          <span className="theme-knob">{theme === 'dark' ? '☾' : '☼'}</span>
        </button>
        <input className="search" placeholder="Quick find..." />
        <button className="ghost-btn" onClick={onExport} disabled={!onExport}>Export Report</button>
      </div>
    </header>
  )
}
