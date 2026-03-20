import { useNavigate } from 'react-router-dom'

export default function LoginPage() {
  const navigate = useNavigate()

  return (
    <div className="login-shell">
      <section className="login-left">
        <h1>SkillSphere</h1>
        <h2>Hire for what they've built, not what they've written.</h2>
        <ul>
          <li>GitHub signal analysis across repositories</li>
          <li>Bias-resistant scoring by architecture</li>
          <li>Evidence-traced skill verification</li>
        </ul>
      </section>

      <section className="login-right">
        <h2>Welcome back</h2>
        <p>Sign in to your SkillSphere workspace</p>
        <button className="google-btn" onClick={() => navigate('/dashboard')}>Continue with Google</button>
        <div className="divider">OR CONTINUE WITH EMAIL</div>
        <input placeholder="Email address" />
        <input placeholder="Password" type="password" />
        <button className="primary-btn" onClick={() => navigate('/dashboard')}>Sign In</button>
      </section>
    </div>
  )
}
