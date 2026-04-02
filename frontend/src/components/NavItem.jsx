import { NavLink } from 'react-router-dom'

export default function NavItem({ to, label, onClick, asButton = false, className = '' }) {
  const base = `ss-nav-item ${className}`.trim()

  if (asButton || !to) {
    return (
      <button type="button" className={base} onClick={onClick}>
        {label}
      </button>
    )
  }

  return (
    <NavLink
      to={to}
      onClick={onClick}
      className={({ isActive }) => `${base} ${isActive ? 'active' : ''}`.trim()}
    >
      {label}
    </NavLink>
  )
}
