import { NavLink, useNavigate } from 'react-router-dom'

const navItems = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/candidates', label: 'Candidates' },
  { to: '/analyze', label: 'Analyze Candidate' },
  { to: '/profile', label: 'Profile' },
]

export default function Sidebar({ onLogout }) {
  const navigate = useNavigate()

  function handleSettings() {
    navigate('/settings')
  }

  function handleLogout() {
    onLogout?.()
    navigate('/')
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-top">
        <div className="logo-area">
          <div className="brand-wrap">
            <h1 className="brand">SkillSphere</h1>
          </div>
        </div>

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

        <p className="nav-section-label">System</p>
        <nav className="nav nav-system">
          <button type="button" className="nav-item nav-plain" onClick={handleSettings}>Settings</button>
          <button type="button" className="nav-item nav-plain" onClick={handleLogout}>Logout</button>
        </nav>
      </div>

      <button type="button" className="sidebar-foot sidebar-profile-trigger" onClick={() => navigate('/profile')}>
        <div className="avatar">AR</div>
        <div>
          <div className="user-name">Alex Rivers</div>
          <div className="user-role">Recruitment Lead</div>
        </div>
      </button>
    </aside>
  )
}
