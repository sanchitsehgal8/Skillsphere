import { useNavigate } from 'react-router-dom'

export default function LoginPage({ theme, onToggleTheme }) {
  const navigate = useNavigate()

  return (
    <div className="login-shell">
      <section className="login-left">
        <div className="login-branding">
          <div className="login-logo-row">
            <div className="login-logo-mark" aria-hidden>
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2 3 7v10l9 5 9-5V7l-9-5Zm0 2.18L19 8l-7 3.82L5 8l7-3.82ZM4 9.45l7 3.82V21l-7-3.82V9.45Zm9 11.55v-7.73l7-3.82v7.73L13 21Z" />
              </svg>
            </div>
            <div>
              <h1 className="login-brand-title">SkillSphere</h1>
              <p className="login-brand-caption">Recruitment Portal</p>
            </div>
          </div>
        </div>

        <div className="login-copy-block">
          <p className="page-eyebrow">Hiring Intelligence</p>
          <h2 className="login-title">Hire for what they’ve built, not what they’ve written.</h2>
          <p className="login-copy">
            Evidence-first recruitment workspace for modern teams. Analyze GitHub signals,
            benchmark learning velocity, and reduce hiring bias with auditable insights.
          </p>
          <ul className="login-points">
            <li>GitHub and coding profile intelligence, unified in one scorecard</li>
            <li>Bias-aware ranking with transparent reasoning trails</li>
            <li>Time-to-productivity estimates for faster hiring decisions</li>
          </ul>
        </div>
      </section>

      <section className="login-right">
        <div className="login-theme-row">
          <span className="status-pill">
            <span className="status-dot" />
            System live
          </span>
          <button
            className={`theme-toggle ${theme === 'dark' ? 'is-dark' : 'is-light'}`}
            onClick={onToggleTheme}
            aria-label="Toggle dark/light mode"
          >
            <span className="theme-knob">{theme === 'dark' ? '☾' : '☼'}</span>
          </button>
        </div>

        <h2 className="login-form-title">Welcome back</h2>
        <p className="login-form-subtitle">Sign in to your SkillSphere workspace</p>

        <button className="google-btn" onClick={() => navigate('/dashboard')}>Continue with Google</button>
        <div className="divider">OR CONTINUE WITH EMAIL</div>

        <label className="field-label">Email address</label>
        <input placeholder="name@company.com" />

        <label className="field-label">Password</label>
        <input placeholder="••••••••" type="password" />

        <button className="primary-btn full" onClick={() => navigate('/dashboard')}>Sign In</button>
      </section>
    </div>
  )
}
