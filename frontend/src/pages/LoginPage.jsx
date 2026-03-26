import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function LoginPage({ theme, onToggleTheme }) {
	const navigate = useNavigate()
	const { user, signIn, signUp, signInWithGoogle } = useAuth()
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

	async function handleGoogleSignIn() {
		setError('')
		setMessage('')
		try {
			await signInWithGoogle()
		} catch (e) {
			setError(e?.message || 'Google sign-in failed')
		}
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
						className="ghost-btn social-btn"
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
						className="ghost-btn social-btn"
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

				<div className="divider-or" aria-hidden>
					<span />
					<em>or</em>
					<span />
				</div>

				<button type="button" className="google-btn" onClick={handleGoogleSignIn}>
					<svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
						<path fill="#EA4335" d="M9 7.03v3.95h5.49c-.24 1.27-.96 2.35-2.04 3.07l3.3 2.56c1.92-1.77 3.03-4.38 3.03-7.49 0-.72-.06-1.4-.19-2.09H9Z" />
						<path fill="#34A853" d="M3.64 10.71l-.74.56-2.61 2.03A8.99 8.99 0 0 0 9 18c2.43 0 4.47-.8 5.96-2.16l-3.3-2.56c-.91.61-2.08.97-3.66.97-2.35 0-4.33-1.58-5.04-3.71l-.32.17Z" />
						<path fill="#4A90E2" d="M.29 4.7A8.98 8.98 0 0 0 0 9c0 1.56.37 3.03 1.03 4.3l3.35-2.59A5.41 5.41 0 0 1 4.08 9c0-.6.1-1.18.3-1.71L1.03 4.7.29 4.7Z" />
						<path fill="#FBBC05" d="M9 3.58c1.32 0 2.5.45 3.43 1.33l2.57-2.57C13.46.9 11.42 0 9 0A8.99 8.99 0 0 0 .29 4.7l3.35 2.59C4.35 5.16 6.33 3.58 9 3.58Z" />
					</svg>
					<span>Continue with Google</span>
				</button>

				{error && <p className="error">{error}</p>}
				{message && <p className="subtle-copy">{message}</p>}
			</section>
		</div>
	)
}

