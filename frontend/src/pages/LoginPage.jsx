import { useState } from 'react'
import { Navigate, useNavigate, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowLeft, Eye, EyeOff, ShieldCheck, Sparkles, TrendingUp } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { Logo } from '../components/brand/Logo'
import { ThemeToggle } from '../components/brand/ThemeToggle'
import { Button } from '../components/ui/button'
import { Input, Label } from '../components/ui/input'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/ui/tabs'
import { StatusDot } from '../components/ui/misc'

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
      <path fill="#EA4335" d="M9 7.03v3.95h5.49c-.24 1.27-.96 2.35-2.04 3.07l3.3 2.56c1.92-1.77 3.03-4.38 3.03-7.49 0-.72-.06-1.4-.19-2.09H9Z" />
      <path fill="#34A853" d="M3.64 10.71l-.74.56-2.61 2.03A8.99 8.99 0 0 0 9 18c2.43 0 4.47-.8 5.96-2.16l-3.3-2.56c-.91.61-2.08.97-3.66.97-2.35 0-4.33-1.58-5.04-3.71l-.32.17Z" />
      <path fill="#4A90E2" d="M.29 4.7A8.98 8.98 0 0 0 0 9c0 1.56.37 3.03 1.03 4.3l3.35-2.59A5.41 5.41 0 0 1 4.08 9c0-.6.1-1.18.3-1.71L1.03 4.7Z" />
      <path fill="#FBBC05" d="M9 3.58c1.32 0 2.5.45 3.43 1.33l2.57-2.57C13.46.9 11.42 0 9 0A8.99 8.99 0 0 0 .29 4.7l3.35 2.59C4.35 5.16 6.33 3.58 9 3.58Z" />
    </svg>
  )
}

export default function LoginPage() {
  const navigate = useNavigate()
  const { user, signIn, signUp, signInWithGoogle } = useAuth()
  const [tab, setTab] = useState('signin')
  const [form, setForm] = useState({ email: '', password: '', confirm: '' })
  const [show, setShow] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (user) return <Navigate to="/dashboard" replace />

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))
  const clearNotices = () => {
    setError('')
    setMessage('')
  }

  async function handleSignIn(e) {
    e.preventDefault()
    setSubmitting(true)
    clearNotices()
    const { error: authError } = await signIn(form.email, form.password)
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
    clearNotices()
    if (form.password !== form.confirm) {
      setError('Passwords do not match.')
      setSubmitting(false)
      return
    }
    const { error: authError } = await signUp(form.email, form.password)
    if (authError) {
      setError(authError.message)
      setSubmitting(false)
      return
    }
    setMessage('Check your email to confirm your account.')
    setSubmitting(false)
  }

  async function handleGoogle() {
    clearNotices()
    try {
      await signInWithGoogle()
    } catch (err) {
      setError(err?.message || 'Google sign-in failed')
    }
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      {/* Brand / editorial panel */}
      <div className="relative hidden overflow-hidden bg-[hsl(var(--surface))] lg:block">
        <div className="absolute inset-0 bg-grid opacity-40 mask-fade-b" />
        <div className="pointer-events-none absolute -left-24 top-1/4 h-[28rem] w-[28rem] rounded-full bg-primary/12 blur-[120px]" />
        <div className="pointer-events-none absolute -right-16 bottom-0 h-[24rem] w-[24rem] rounded-full bg-primary/8 blur-[120px]" />

        <div className="relative flex h-full flex-col justify-between p-12">
          <Logo size={36} />

          <div className="max-w-md">
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="mb-8 inline-flex items-center gap-2 rounded-full border border-border bg-surface/60 px-3 py-1.5 text-xs text-muted-foreground backdrop-blur"
            >
              <Sparkles className="h-3.5 w-3.5 text-primary" /> Evidence-based hiring intelligence
            </motion.div>
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="font-display text-4xl font-bold leading-[1.1] tracking-tightest text-foreground"
            >
              Hire the exceptional,
              <br />
              <span className="text-gradient-brand">on the evidence.</span>
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="mt-4 text-base leading-relaxed text-muted-foreground"
            >
              SkillSphere scores engineers on 17 explainable dimensions from real GitHub, résumé, and Codeforces
              signals — every verdict traceable to its source.
            </motion.p>

            <div className="mt-10 grid gap-3">
              {[
                { icon: TrendingUp, text: '17-dimension explainable scorecard' },
                { icon: ShieldCheck, text: 'Built-in fairness & bias auditing' },
              ].map(({ icon: Icon, text }, i) => (
                <motion.div
                  key={text}
                  initial={{ opacity: 0, x: -12 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.5, delay: 0.3 + i * 0.1 }}
                  className="flex items-center gap-3 text-sm text-foreground/80"
                >
                  <span className="grid h-8 w-8 place-items-center rounded-lg bg-primary/12 text-primary">
                    <Icon className="h-4 w-4" />
                  </span>
                  {text}
                </motion.div>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <div className="flex -space-x-2">
              {['AR', 'DS', 'KM'].map((a) => (
                <span key={a} className="grid h-7 w-7 place-items-center rounded-full border-2 border-surface bg-secondary text-2xs font-semibold text-foreground">
                  {a}
                </span>
              ))}
            </div>
            Trusted by forward-thinking talent teams
          </div>
        </div>
      </div>

      {/* Form panel */}
      <div className="relative flex flex-col bg-background">
        <div className="flex items-center justify-between p-6">
          <Link to="/" className="inline-flex items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-foreground">
            <ArrowLeft className="h-4 w-4" /> Back
          </Link>
          <div className="flex items-center gap-3">
            <span className="hidden items-center gap-2 text-xs text-muted-foreground sm:inline-flex">
              <StatusDot tone="success" /> System live
            </span>
            <ThemeToggle />
          </div>
        </div>

        <div className="flex flex-1 items-center justify-center px-6 pb-12">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="w-full max-w-sm"
          >
            <div className="mb-8 lg:hidden">
              <Logo size={32} />
            </div>

            <h2 className="font-display text-2xl font-bold tracking-tight text-foreground">
              {tab === 'signin' ? 'Welcome back' : 'Create your workspace'}
            </h2>
            <p className="mt-1.5 text-sm text-muted-foreground">
              {tab === 'signin' ? 'Sign in to your talent intelligence dashboard.' : 'Start scoring candidates on the evidence.'}
            </p>

            <Tabs value={tab} onValueChange={(v) => { setTab(v); clearNotices() }} className="mt-6">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="signin">Sign in</TabsTrigger>
                <TabsTrigger value="signup">Sign up</TabsTrigger>
              </TabsList>

              <TabsContent value="signin">
                <form onSubmit={handleSignIn} className="space-y-4">
                  <div>
                    <Label htmlFor="si-email">Email address</Label>
                    <Input id="si-email" type="email" placeholder="name@company.com" value={form.email} onChange={set('email')} required />
                  </div>
                  <div>
                    <Label htmlFor="si-pw">Password</Label>
                    <div className="relative">
                      <Input id="si-pw" type={show ? 'text' : 'password'} placeholder="••••••••" value={form.password} onChange={set('password')} required className="pr-10" />
                      <button type="button" onClick={() => setShow((s) => !s)} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground" aria-label="Toggle password">
                        {show ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>
                  <Button type="submit" variant="gradient" size="lg" className="w-full" loading={submitting}>
                    Sign in to workspace
                  </Button>
                </form>
              </TabsContent>

              <TabsContent value="signup">
                <form onSubmit={handleSignUp} className="space-y-4">
                  <div>
                    <Label htmlFor="su-email">Email address</Label>
                    <Input id="su-email" type="email" placeholder="name@company.com" value={form.email} onChange={set('email')} required />
                  </div>
                  <div>
                    <Label htmlFor="su-pw">Password</Label>
                    <div className="relative">
                      <Input id="su-pw" type={show ? 'text' : 'password'} placeholder="••••••••" value={form.password} onChange={set('password')} required className="pr-10" />
                      <button type="button" onClick={() => setShow((s) => !s)} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground" aria-label="Toggle password">
                        {show ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>
                  <div>
                    <Label htmlFor="su-confirm">Confirm password</Label>
                    <Input id="su-confirm" type={show ? 'text' : 'password'} placeholder="••••••••" value={form.confirm} onChange={set('confirm')} required />
                  </div>
                  <Button type="submit" variant="gradient" size="lg" className="w-full" loading={submitting}>
                    Create account
                  </Button>
                </form>
              </TabsContent>
            </Tabs>

            <div className="my-5 flex items-center gap-3 text-xs text-muted-foreground">
              <span className="h-px flex-1 bg-border" /> or <span className="h-px flex-1 bg-border" />
            </div>

            <Button type="button" variant="outline" size="lg" className="w-full" onClick={handleGoogle}>
              <GoogleIcon /> Continue with Google
            </Button>

            {error && <p className="mt-4 rounded-lg border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">{error}</p>}
            {message && <p className="mt-4 rounded-lg border border-success/30 bg-success/10 px-3 py-2 text-sm text-success">{message}</p>}
          </motion.div>
        </div>
      </div>
    </div>
  )
}
