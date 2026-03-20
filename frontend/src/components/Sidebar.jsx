import { NavLink } from 'react-router-dom'

const navItems = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/candidates', label: 'Candidates' },
  { to: '/analyze', label: 'Analyze Candidate' },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-top">
        <h1 className="brand">SkillSphere</h1>
        <p className="brand-sub">Real signals. Better hiring.</p>
        <nav className="nav">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>

    </aside>
  )
}
