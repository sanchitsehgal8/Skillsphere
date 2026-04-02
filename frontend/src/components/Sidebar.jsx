import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import MobileTopNav from './MobileTopNav'
import NavItem from './NavItem'

const navItems = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/candidates', label: 'Candidates' },
  { to: '/analyze', label: 'Analyze Candidate' },
  { to: '/profile', label: 'Profile' },
]

export default function Sidebar() {
  const navigate = useNavigate()
  const { signOut } = useAuth()

  function handleSettings() {
    navigate('/settings')
  }

  async function handleLogout() {
    await signOut()
    navigate('/login')
  }

  return (
    <>
      <MobileTopNav onLogout={handleLogout} />

      <aside className="sidebar desktop-sidebar">
        <div className="sidebar-top">
          <div className="logo-area">
            <div className="brand-wrap">
              <h1 className="brand">SkillSphere</h1>
            </div>
          </div>

          <nav className="nav">
            {navItems.map((item) => (
              <NavItem
                key={item.to}
                to={item.to}
                label={item.label}
              />
            ))}
          </nav>

          <p className="nav-section-label">System</p>
          <nav className="nav nav-system">
            <NavItem asButton label="Settings" onClick={handleSettings} />
            <NavItem asButton label="Logout" onClick={handleLogout} />
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
    </>
  )
}
