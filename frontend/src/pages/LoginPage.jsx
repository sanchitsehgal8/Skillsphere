import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function LoginPage({ theme, onToggleTheme }) {
	const navigate = useNavigate()
	const { user, signIn, signUp } = useAuth()
	const [tab, setTab] = useState('signin')
	const [signInEmail, setSignInEmail] = useState('')
	const [signInPassword, setSignInPassword] = useState('')
	const [signUpEmail, setSignUpEmail] = useState('')
	const [signUpPassword, setSignUpPassword] = useState('')
	const [confirmPassword, setConfirmPassword] = useState('')
	const [showSignInPassword, setShowSignInPassword] = useState(false)
	const [showSignUpPassword, setShowSignUpPassword] = useState(false)
	const [error, setError] = useState('')
	const [message, setMessage] = useState('')
	const [submitting, setSubmitting] = useState(false)

	if (user) {
		return <Navigate to="/dashboard" replace />
	}

	async function handleSignIn(e) {
		e.preventDefault()
		setSubmitting(true)
		setError('')
		setMessage('')
		const { error: authError } = await signIn(signInEmail, signInPassword)
		if (authError) {
			setError(authError.message)
			setSubmitting(false)
			return
		}
		navigate('/dashboard')
	}

	async function handleSignUp(e) {
		e.preventDefault()
		setSubmitting(true)
		setError('')
		setMessage('')

		if (signUpPassword !== confirmPassword) {
			setError('Passwords do not match.')
			setSubmitting(false)
			return
		}

		const { error: authError } = await signUp(signUpEmail, signUpPassword)
		if (authError) {
			setError(authError.message)
			setSubmitting(false)
			return
		}

		setMessage('Check your email to confirm your account.')
		setSubmitting(false)
	}

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

				<div className="social-row" role="tablist" aria-label="Auth tabs">
					<button
						type="button"
						className="google-btn social-btn"
						onClick={() => {
							setTab('signin')
							setError('')
							setMessage('')
						}}
					>
						Sign in
					</button>
					<button
						type="button"
						className="google-btn social-btn"
						onClick={() => {
							setTab('signup')
							setError('')
							setMessage('')
						}}
					>
						Sign up
					</button>
				</div>

				{tab === 'signin' ? (
					<form onSubmit={handleSignIn}>
						<label className="field-label">Email Address</label>
						<input
							placeholder="name@company.com"
							type="email"
							value={signInEmail}
							onChange={(e) => setSignInEmail(e.target.value)}
							required
						/>

						<div className="password-row">
							<label className="field-label">Password</label>
							<button
								type="button"
								className="forgot-link"
								onClick={() => setShowSignInPassword((prev) => !prev)}
							>
								{showSignInPassword ? 'Hide' : 'See'} password
							</button>
						</div>
						<input
							placeholder="••••••••"
							type={showSignInPassword ? 'text' : 'password'}
							value={signInPassword}
							onChange={(e) => setSignInPassword(e.target.value)}
							required
						/>

						<button className="primary-btn full login-submit" type="submit" disabled={submitting}>
							{submitting ? 'Signing in...' : 'Sign In to Workspace'}
						</button>
					</form>
				) : (
					<form onSubmit={handleSignUp}>
						<label className="field-label">Email Address</label>
						<input
							placeholder="name@company.com"
							type="email"
							value={signUpEmail}
							onChange={(e) => setSignUpEmail(e.target.value)}
							required
						/>

						<div className="password-row">
							<label className="field-label">Password</label>
							<button
								type="button"
								className="forgot-link"
								onClick={() => setShowSignUpPassword((prev) => !prev)}
							>
								{showSignUpPassword ? 'Hide' : 'See'} password
							</button>
						</div>
						<input
							placeholder="••••••••"
							type={showSignUpPassword ? 'text' : 'password'}
							value={signUpPassword}
							onChange={(e) => setSignUpPassword(e.target.value)}
							required
						/>

						<label className="field-label">Confirm Password</label>
						<input
							placeholder="••••••••"
							type={showSignUpPassword ? 'text' : 'password'}
							value={confirmPassword}
							onChange={(e) => setConfirmPassword(e.target.value)}
							required
						/>

						<button className="primary-btn full login-submit" type="submit" disabled={submitting}>
							{submitting ? 'Signing up...' : 'Create account'}
						</button>
					</form>
				)}

				{error && <p className="error">{error}</p>}
				{message && <p className="subtle-copy">{message}</p>}
			</section>
		</div>
	)
}

