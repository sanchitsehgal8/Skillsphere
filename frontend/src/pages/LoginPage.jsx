import { useNavigate } from 'react-router-dom'

export default function LoginPage({ theme, onToggleTheme }) {
  const navigate = useNavigate()

  return (
    <div className="login-shell login-shell-v2">
      <section className="login-left login-left-v2">
        <div className="login-left-top">
          <div className="login-logo-row">
            <div className="login-logo-mark" aria-hidden>
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2 3 7v10l9 5 9-5V7l-9-5Zm0 2.18L19 8l-7 3.82L5 8l7-3.82ZM4 9.45l7 3.82V21l-7-3.82V9.45Zm9 11.55v-7.73l7-3.82v7.73L13 21Z" />
              </svg>
            </div>
            <h1 className="login-brand-title">SkillSphere</h1>
          </div>
        </div>

        <div className="constellation">
          <div className="dot dot-a" />
          <div className="dot dot-b" />
          <div className="dot dot-c" />
          <div className="dot dot-d" />
          <div className="dot dot-e" />
          <svg viewBox="0 0 300 180" className="constellation-lines" aria-hidden>
            <path d="M40 70 L110 30 L170 95 L95 145 L40 70 L170 95 L240 65 L260 110 L170 95 L210 155 L95 145" />
          </svg>
          <span className="score-chip">MATCH SCORE: 98%</span>
        </div>

        <div className="login-hero-copy">
          <p className="kicker">Recruitment</p>
          <h2>
            Intelligence,
            <br />
            <span>Redefined.</span>
          </h2>
          <p>
            A high-fidelity editorial approach to talent acquisition. Leverage neural analytics to
            find the exceptional.
          </p>
        </div>

        <div className="login-left-footer">
          <div className="trust-strip">
            <div className="trust-avatars" aria-hidden>
              <span className="trust-avatar a">AR</span>
              <span className="trust-avatar b">DS</span>
              <span className="trust-avatar c">KM</span>
            </div>
            <span className="trust-text">Trusted by 500+ global enterprises</span>
            <span className="trust-version">v.4.0.2</span>
          </div>
        </div>
      </section>

      <section className="login-right login-right-v2">
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

        <h2 className="login-form-title">Welcome Back</h2>
        <p className="login-form-subtitle">Enter your credentials to access the curator dashboard.</p>

        <label className="field-label">Email Address</label>
        <input placeholder="name@company.com" />

        <div className="password-row">
          <label className="field-label">Password</label>
          <button type="button" className="forgot-link">Forgot password?</button>
        </div>
        <input placeholder="••••••••" type="password" />

        <label className="remember-row">
          <input type="checkbox" />
          Keep me signed in for 30 days
        </label>

        <button className="primary-btn full login-submit" onClick={() => navigate('/dashboard')}>
          Sign In to Workspace
        </button>

        <div className="divider">OR CONTINUE WITH</div>

        <div className="social-row">
          <button className="google-btn social-btn" onClick={() => navigate('/dashboard')}>Google</button>
          <button className="google-btn social-btn" onClick={() => navigate('/dashboard')}>GitHub</button>
        </div>
      </section>
    </div>
  )
}
