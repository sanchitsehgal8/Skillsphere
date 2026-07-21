import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  AnimatePresence,
  animate,
  motion,
  useInView,
  useMotionValue,
  useScroll,
  useSpring,
  useTransform,
} from 'framer-motion'
import {
  ArrowRight,
  BarChart3,
  Bot,
  Check,
  ChevronRight,
  Fingerprint,
  Github,
  Menu,
  ScrollText,
  ShieldCheck,
  Sparkles,
  Target,
  Trophy,
  X,
  Zap,
} from 'lucide-react'
import { Logo } from '../components/brand/Logo'
import { ThemeToggle } from '../components/brand/ThemeToggle'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { Meter, Ring } from '../components/ui/meter'
import { StatusDot } from '../components/ui/misc'
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from '../components/ui/controls'
import { cn } from '../lib/utils'

const EASE = [0.22, 1, 0.36, 1]

/* Cinematic scroll/inview reveal with blur + rise. */
function Reveal({ children, delay = 0, className, y = 28 }) {
  return (
    <motion.div
      initial={{ opacity: 0, y, filter: 'blur(10px)' }}
      whileInView={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
      viewport={{ once: true, margin: '-90px' }}
      transition={{ duration: 0.8, delay, ease: EASE }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

/* Count-up that preserves prefix/suffix like "<60s" or "100%". */
function StatValue({ value }) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '-40px' })
  const m = value.match(/^(\D*)(\d+)(\D*)$/)
  const [display, setDisplay] = useState(m ? `${m[1]}0${m[3]}` : value)

  useEffect(() => {
    if (!m || !inView) return
    const controls = animate(0, Number(m[2]), {
      duration: 1.4,
      ease: EASE,
      onUpdate: (v) => setDisplay(`${m[1]}${Math.round(v)}${m[3]}`),
    })
    return () => controls.stop()
  }, [inView]) // eslint-disable-line react-hooks/exhaustive-deps

  return <span ref={ref}>{m ? display : value}</span>
}

/* ------------------------ Cinematic light backdrop ----------------------- */
function Backdrop() {
  return (
    <div className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
      {/* rotating conic light */}
      <div className="absolute left-1/2 top-[-30%] h-[70rem] w-[70rem] -translate-x-1/2 animate-spin-slow opacity-[0.5] [mask-image:radial-gradient(circle,#000_30%,transparent_68%)]">
        <div
          className="h-full w-full"
          style={{
            background:
              'conic-gradient(from 0deg, transparent, hsl(var(--primary)/0.5), transparent 22%, hsl(var(--accent)/0.4), transparent 46%, hsl(var(--primary)/0.35), transparent 72%)',
          }}
        />
      </div>
      {/* floating orbs */}
      <div className="absolute -left-24 top-24 h-[30rem] w-[30rem] rounded-full bg-primary/20 blur-[130px] animate-glow-breathe" />
      <div className="absolute right-[-8rem] top-1/3 h-[26rem] w-[26rem] rounded-full bg-accent/15 blur-[130px] animate-float" />
      {/* panning grid */}
      <div className="absolute inset-0 bg-grid animate-grid-pan opacity-[0.28] [mask-image:radial-gradient(ellipse_at_top,#000_20%,transparent_70%)]" />
      {/* vignette to ground it */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_40%,hsl(var(--background))_92%)]" />
    </div>
  )
}

/* ---------------------------------- Nav ---------------------------------- */
const navLinks = [
  { label: 'Features', href: '#features' },
  { label: 'How it works', href: '#how' },
  { label: 'Pricing', href: '#pricing' },
  { label: 'FAQ', href: '#faq' },
]

function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [open, setOpen] = useState(false)
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <motion.header
      initial={{ y: -80, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.7, ease: EASE }}
      className="fixed inset-x-0 top-0 z-50"
    >
      <div
        className={cn(
          'mx-auto flex h-16 max-w-6xl items-center justify-between px-4 transition-all duration-300 sm:px-6',
          scrolled && 'mt-2 rounded-2xl border border-border bg-background/70 shadow-soft backdrop-blur-xl sm:mx-6',
        )}
      >
        <Link to="/"><Logo /></Link>
        <nav className="hidden items-center gap-1 md:flex">
          {navLinks.map((l) => (
            <a key={l.href} href={l.href} className="rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:text-foreground">
              {l.label}
            </a>
          ))}
        </nav>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <Link to="/login" className="hidden sm:block"><Button variant="ghost" size="sm">Sign in</Button></Link>
          <Link to="/login" className="hidden sm:block"><Button variant="gradient" size="sm">Get started <ArrowRight className="h-4 w-4" /></Button></Link>
          <button className="grid h-9 w-9 place-items-center rounded-lg border border-border md:hidden" onClick={() => setOpen((o) => !o)} aria-label="Menu">
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>
      <AnimatePresence>
        {open && (
          <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} className="mx-4 mt-2 rounded-2xl border border-border bg-background/95 p-3 backdrop-blur-xl md:hidden">
            {navLinks.map((l) => (
              <a key={l.href} href={l.href} onClick={() => setOpen(false)} className="block rounded-lg px-3 py-2.5 text-sm text-foreground/80 hover:bg-secondary">{l.label}</a>
            ))}
            <Link to="/login" className="mt-1 block"><Button variant="gradient" className="w-full">Get started</Button></Link>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.header>
  )
}

/* ------------------------- Hero product preview -------------------------- */
function ProductPreview({ style }) {
  const rx = useMotionValue(0)
  const ry = useMotionValue(0)
  const srx = useSpring(rx, { stiffness: 120, damping: 18 })
  const sry = useSpring(ry, { stiffness: 120, damping: 18 })

  function onMove(e) {
    const r = e.currentTarget.getBoundingClientRect()
    const px = (e.clientX - r.left) / r.width - 0.5
    const py = (e.clientY - r.top) / r.height - 0.5
    ry.set(px * 10)
    rx.set(-py * 10)
  }
  function onLeave() {
    rx.set(0)
    ry.set(0)
  }

  const dims = [
    { label: 'Backend', value: 92 },
    { label: 'System Design', value: 84 },
    { label: 'Code Quality', value: 78 },
    { label: 'Testing', value: 66 },
  ]

  return (
    <motion.div
      initial={{ opacity: 0, y: 60, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 1, delay: 0.5, ease: EASE }}
      style={style}
      className="relative mx-auto mt-16 max-w-4xl"
    >
      <motion.div
        onMouseMove={onMove}
        onMouseLeave={onLeave}
        style={{ rotateX: srx, rotateY: sry, transformPerspective: 1400 }}
        className="ring-gradient overflow-hidden rounded-2xl border border-border bg-card shadow-elevated"
      >
        <div className="flex items-center gap-2 border-b border-border px-4 py-3">
          <span className="h-2.5 w-2.5 rounded-full bg-danger/70" />
          <span className="h-2.5 w-2.5 rounded-full bg-warning/70" />
          <span className="h-2.5 w-2.5 rounded-full bg-success/70" />
          <span className="ml-3 font-mono text-xs text-muted-foreground">skillsphere.ai / analyze</span>
          <span className="ml-auto inline-flex items-center gap-1.5 text-xs text-success"><StatusDot tone="success" /> live</span>
        </div>
        <div className="grid gap-5 p-5 sm:grid-cols-[1.3fr_1fr]">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <span className="grid h-11 w-11 place-items-center rounded-full bg-primary text-sm font-semibold text-primary-foreground">DS</span>
              <div>
                <p className="text-sm font-semibold text-foreground">Dana Singh</p>
                <p className="text-xs text-muted-foreground">Senior Backend Engineer</p>
              </div>
              <Badge tone="success" className="ml-auto">Strong match</Badge>
            </div>
            <div className="space-y-3 rounded-xl border border-border bg-surface/50 p-4">
              {dims.map((d, i) => (
                <motion.div key={d.label} initial={{ opacity: 0, x: -10 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} transition={{ delay: 0.7 + i * 0.12 }}>
                  <div className="mb-1.5 flex justify-between text-xs">
                    <span className="text-muted-foreground">{d.label}</span>
                    <span className="font-mono font-semibold text-foreground">{d.value}</span>
                  </div>
                  <Meter value={d.value} tone={d.value >= 75 ? 'success' : d.value >= 55 ? 'warning' : 'danger'} />
                </motion.div>
              ))}
            </div>
            <div className="flex flex-wrap gap-2">
              {['Python', 'FastAPI', 'PostgreSQL', 'AWS'].map((t) => <Badge key={t} variant="primary" size="sm">{t}</Badge>)}
            </div>
          </div>
          <div className="flex flex-col items-center justify-center gap-4 rounded-xl border border-border bg-surface/50 p-5 text-center">
            <p className="text-xs uppercase tracking-widest text-muted-foreground">Role fit</p>
            <Ring value={91} size={132} stroke={9} tone="success" label="91%" />
            <p className="text-xs text-muted-foreground">Est. ramp-up <span className="font-medium text-foreground">18–24h</span></p>
            <div className="flex items-center gap-1.5 text-xs text-accent"><ShieldCheck className="h-3.5 w-3.5" /> No fairness flags</div>
          </div>
        </div>
      </motion.div>
      <div className="pointer-events-none absolute -inset-x-10 -bottom-12 -z-10 h-44 bg-primary/20 blur-[90px]" />
    </motion.div>
  )
}

const headlineLines = [
  [{ t: 'Hire engineers on the' }],
  [{ t: 'evidence', accent: true }, { t: ', not the' }],
  [{ t: 'résumé keywords.' }],
]

function Hero() {
  const ref = useRef(null)
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start start', 'end start'] })
  const headY = useTransform(scrollYProgress, [0, 1], [0, -140])
  const headOpacity = useTransform(scrollYProgress, [0, 0.55], [1, 0])
  const previewScale = useTransform(scrollYProgress, [0, 1], [1, 0.9])
  const previewY = useTransform(scrollYProgress, [0, 1], [0, 80])

  return (
    <section ref={ref} className="relative min-h-[92vh] overflow-hidden pt-36">
      <Backdrop />
      <motion.div style={{ y: headY, opacity: headOpacity }} className="mx-auto max-w-6xl px-4 text-center sm:px-6">
        <motion.a
          href="#features"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="inline-flex items-center gap-2 rounded-full border border-border bg-surface/70 px-3.5 py-1.5 text-xs text-muted-foreground backdrop-blur transition-colors hover:text-foreground"
        >
          <Badge variant="primary" size="sm">New</Badge>
          17-dimension explainable scoring
          <ChevronRight className="h-3.5 w-3.5" />
        </motion.a>

        <h1 className="mx-auto mt-7 max-w-4xl font-display text-4xl font-bold leading-[1.04] tracking-tightest text-foreground sm:text-6xl">
          {headlineLines.map((line, li) => (
            <span key={li} className="block overflow-hidden py-0.5">
              <motion.span
                className="block"
                initial={{ y: '115%' }}
                animate={{ y: 0 }}
                transition={{ duration: 0.9, delay: 0.35 + li * 0.12, ease: EASE }}
              >
                {line.map((seg, si) => (
                  <span key={si} className={seg.accent ? 'text-primary' : undefined}>{seg.t}</span>
                ))}
              </motion.span>
            </span>
          ))}
        </h1>

        <motion.p initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.7 }} className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-muted-foreground">
          SkillSphere turns real GitHub, résumé, and Codeforces signals into an explainable engineering scorecard —
          with role-fit, ramp-up estimates, and built-in fairness auditing.
        </motion.p>

        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.82 }} className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Link to="/login"><Button variant="gradient" size="lg">Start analyzing free <ArrowRight className="h-4 w-4" /></Button></Link>
          <a href="#how"><Button variant="outline" size="lg">See how it works</Button></a>
        </motion.div>
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1 }} className="mt-4 text-xs text-muted-foreground">
          No credit card · Evidence-based scoring in under a minute
        </motion.p>
      </motion.div>

      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <ProductPreview style={{ scale: previewScale, y: previewY }} />
      </div>
    </section>
  )
}

/* -------------------------------- Marquee -------------------------------- */
function Marquee() {
  const items = ['Python', 'TypeScript', 'Go', 'Rust', 'React', 'FastAPI', 'Kubernetes', 'PostgreSQL', 'AWS', 'GraphQL', 'System Design', 'Distributed Systems']
  return (
    <div className="border-y border-border bg-surface/40 py-6">
      <div className="mask-fade-x overflow-hidden">
        <div className="flex w-max animate-marquee gap-3">
          {[...items, ...items].map((t, i) => (
            <span key={i} className="whitespace-nowrap rounded-full border border-border bg-card px-4 py-2 text-sm text-muted-foreground">{t}</span>
          ))}
        </div>
      </div>
    </div>
  )
}

/* --------------------------------- Stats --------------------------------- */
function Stats() {
  const stats = [
    { value: '17', label: 'Scored dimensions' },
    { value: '3', label: 'Evidence sources' },
    { value: '<60s', label: 'Time to a scorecard' },
    { value: '100%', label: 'Traceable verdicts' },
  ]
  return (
    <section className="border-b border-border bg-surface/40">
      <div className="mx-auto grid max-w-6xl grid-cols-2 gap-px px-4 sm:px-6 md:grid-cols-4">
        {stats.map((s, i) => (
          <Reveal key={s.label} delay={i * 0.08} className="px-4 py-12 text-center">
            <p className="font-display text-4xl font-bold tracking-tight text-primary sm:text-5xl"><StatValue value={s.value} /></p>
            <p className="mt-2 text-sm text-muted-foreground">{s.label}</p>
          </Reveal>
        ))}
      </div>
    </section>
  )
}

/* -------------------------------- Features ------------------------------- */
const features = [
  { icon: BarChart3, title: 'Explainable scorecard', desc: 'Every one of 17 dimensions carries its own score, confidence, reasoning, and evidence — no black-box numbers.', span: 'md:col-span-2' },
  { icon: Github, title: 'Real repo mining', desc: 'We read actual commits, languages, and project complexity from GitHub — not self-reported skills.' },
  { icon: Target, title: 'Role-fit matching', desc: 'Direct, adjacent, and missing requirement coverage against your exact job description.' },
  { icon: ShieldCheck, title: 'Fairness auditing', desc: 'Automatic bias checks on every match, with severity-tagged flags you can act on.', span: 'md:col-span-2' },
  { icon: Bot, title: 'Recruiter copilot', desc: 'Ask natural-language questions about your pool — every answer cites its evidence.' },
  { icon: Trophy, title: 'Competitive signal', desc: 'Optional Codeforces benchmarking for algorithmic depth and consistency.' },
]

function Features() {
  return (
    <section id="features" className="mx-auto max-w-6xl scroll-mt-24 px-4 py-28 sm:px-6">
      <Reveal className="mx-auto max-w-2xl text-center">
        <Badge variant="primary">Capabilities</Badge>
        <h2 className="mt-4 font-display text-3xl font-bold tracking-tight text-foreground sm:text-4xl">Signal over noise, end to end</h2>
        <p className="mt-3 text-muted-foreground">Everything you need to evaluate engineering talent with confidence and defensibility.</p>
      </Reveal>
      <div className="mt-14 grid gap-4 md:grid-cols-3">
        {features.map((f, i) => (
          <Reveal key={f.title} delay={(i % 3) * 0.08} className={f.span}>
            <div className="group h-full rounded-2xl border border-border bg-card p-6 transition-all duration-300 hover:-translate-y-1 hover:border-primary/30 hover:shadow-elevated">
              <span className="mb-4 inline-grid h-11 w-11 place-items-center rounded-xl bg-primary/12 text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
                <f.icon className="h-5 w-5" />
              </span>
              <h3 className="font-display text-lg font-semibold text-foreground">{f.title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{f.desc}</p>
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  )
}

/* ------------------------------ How it works ----------------------------- */
const steps = [
  { icon: ScrollText, title: 'Add candidate & role', desc: 'Paste a job description (or a PDF) and drop in a GitHub username, résumé, and optional Codeforces handle.' },
  { icon: Fingerprint, title: 'We mine the evidence', desc: 'SkillSphere analyzes repositories, résumé content, and competitive history into 17 scored dimensions.' },
  { icon: Zap, title: 'Get an explainable verdict', desc: 'Role-fit %, ramp-up estimate, strengths, gaps, and fairness flags — each traceable to its source.' },
]

function HowItWorks() {
  return (
    <section id="how" className="scroll-mt-24 border-y border-border bg-surface/40 py-28">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <Reveal className="mx-auto max-w-2xl text-center">
          <Badge variant="accent">Workflow</Badge>
          <h2 className="mt-4 font-display text-3xl font-bold tracking-tight text-foreground sm:text-4xl">From handle to hire signal in three steps</h2>
        </Reveal>
        <div className="relative mt-14 grid gap-6 md:grid-cols-3">
          <div className="absolute left-0 right-0 top-7 hidden h-px bg-gradient-to-r from-transparent via-border to-transparent md:block" />
          {steps.map((s, i) => (
            <Reveal key={s.title} delay={i * 0.12} className="relative">
              <div className="relative rounded-2xl border border-border bg-card p-6">
                <div className="mb-5 flex items-center justify-between">
                  <span className="grid h-12 w-12 place-items-center rounded-xl bg-primary text-primary-foreground"><s.icon className="h-5 w-5" /></span>
                  <span className="font-display text-3xl font-bold text-muted-foreground/25">0{i + 1}</span>
                </div>
                <h3 className="font-display text-lg font-semibold text-foreground">{s.title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{s.desc}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  )
}

/* ---------------------------- AI pipeline viz ---------------------------- */
function Pipeline() {
  const sources = [{ icon: Github, label: 'GitHub repos' }, { icon: ScrollText, label: 'Résumé' }, { icon: Trophy, label: 'Codeforces' }]
  const outputs = ['Engineering scorecard', 'Role-fit & coverage', 'Fairness audit']
  return (
    <section className="mx-auto max-w-6xl px-4 py-28 sm:px-6">
      <Reveal className="mx-auto max-w-2xl text-center">
        <Badge variant="primary">Under the hood</Badge>
        <h2 className="mt-4 font-display text-3xl font-bold tracking-tight text-foreground sm:text-4xl">A transparent evidence pipeline</h2>
        <p className="mt-3 text-muted-foreground">Raw signals in, explainable verdicts out — with the reasoning attached at every hop.</p>
      </Reveal>
      <Reveal delay={0.1}>
        <div className="mt-14 grid items-center gap-4 rounded-2xl border border-border bg-card p-6 md:grid-cols-[1fr_auto_1.2fr_auto_1fr] md:p-8">
          <div className="space-y-3">
            {sources.map((s) => (
              <div key={s.label} className="flex items-center gap-3 rounded-xl border border-border bg-surface/50 px-4 py-3">
                <s.icon className="h-4 w-4 text-accent" /><span className="text-sm text-foreground">{s.label}</span>
              </div>
            ))}
          </div>
          <ArrowRight className="mx-auto hidden h-5 w-5 text-muted-foreground md:block" />
          <div className="ring-gradient rounded-2xl border border-border bg-surface/60 p-6 text-center">
            <span className="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-xl bg-primary text-primary-foreground"><Sparkles className="h-6 w-6" /></span>
            <p className="font-display font-semibold text-foreground">SkillSphere engine</p>
            <p className="mt-1 text-xs text-muted-foreground">Evidence weighting · confidence scoring · adjacency graph</p>
          </div>
          <ArrowRight className="mx-auto hidden h-5 w-5 text-muted-foreground md:block" />
          <div className="space-y-3">
            {outputs.map((o) => (
              <div key={o} className="flex items-center gap-3 rounded-xl border border-primary/25 bg-primary/8 px-4 py-3">
                <Check className="h-4 w-4 text-primary" /><span className="text-sm text-foreground">{o}</span>
              </div>
            ))}
          </div>
        </div>
      </Reveal>
    </section>
  )
}

/* ------------------------------ Testimonials ----------------------------- */
const testimonials = [
  { quote: 'We cut résumé-screening time in half and finally have a defensible reason behind every shortlist decision.', name: 'Ava Chen', role: 'Head of Talent, Fintech' },
  { quote: 'The evidence trail is the killer feature. Hiring managers stopped arguing with the scores once they could see the commits.', name: 'Marcus Reid', role: 'Eng Director' },
  { quote: 'Fairness auditing baked in meant our legal team signed off without a three-week review.', name: 'Priya Nair', role: 'People Ops Lead' },
]

function Testimonials() {
  return (
    <section className="border-y border-border bg-surface/40 py-28">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <Reveal className="mx-auto max-w-2xl text-center">
          <Badge variant="accent">Loved by talent teams</Badge>
          <h2 className="mt-4 font-display text-3xl font-bold tracking-tight text-foreground sm:text-4xl">Defensible decisions, faster</h2>
        </Reveal>
        <div className="mt-14 grid gap-4 md:grid-cols-3">
          {testimonials.map((t, i) => (
            <Reveal key={t.name} delay={i * 0.1}>
              <figure className="flex h-full flex-col rounded-2xl border border-border bg-card p-6">
                <div className="mb-3 flex gap-0.5 text-warning">{'★★★★★'.split('').map((s, j) => <span key={j}>{s}</span>)}</div>
                <blockquote className="flex-1 text-sm leading-relaxed text-foreground/90">“{t.quote}”</blockquote>
                <figcaption className="mt-5 flex items-center gap-3">
                  <span className="grid h-9 w-9 place-items-center rounded-full bg-secondary text-2xs font-semibold text-foreground">{t.name.split(' ').map((n) => n[0]).join('')}</span>
                  <span><span className="block text-sm font-medium text-foreground">{t.name}</span><span className="block text-xs text-muted-foreground">{t.role}</span></span>
                </figcaption>
              </figure>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  )
}

/* -------------------------------- Pricing -------------------------------- */
const tiers = [
  { name: 'Starter', price: '$0', period: '/mo', desc: 'For individual recruiters getting started.', features: ['25 candidate analyses / mo', '17-dimension scorecards', 'GitHub + résumé signals', 'CSV export'], cta: 'Start free', highlight: false },
  { name: 'Team', price: '$49', period: '/seat/mo', desc: 'For growing talent teams that hire often.', features: ['Unlimited analyses', 'Role-fit matching & adjacency', 'Recruiter copilot', 'Fairness auditing', 'Codeforces benchmarking'], cta: 'Start free trial', highlight: true },
  { name: 'Enterprise', price: 'Custom', period: '', desc: 'For orgs with compliance and scale needs.', features: ['SSO & audit logs', 'Custom scoring rubrics', 'API access', 'Dedicated support', 'Data residency'], cta: 'Contact sales', highlight: false },
]

function Pricing() {
  return (
    <section id="pricing" className="mx-auto max-w-6xl scroll-mt-24 px-4 py-28 sm:px-6">
      <Reveal className="mx-auto max-w-2xl text-center">
        <Badge variant="primary">Pricing</Badge>
        <h2 className="mt-4 font-display text-3xl font-bold tracking-tight text-foreground sm:text-4xl">Start free, scale when you do</h2>
        <p className="mt-3 text-muted-foreground">Transparent plans. No per-hire fees. Cancel anytime.</p>
      </Reveal>
      <div className="mt-14 grid gap-5 lg:grid-cols-3">
        {tiers.map((t, i) => (
          <Reveal key={t.name} delay={i * 0.1}>
            <div className={cn('relative flex h-full flex-col rounded-2xl border bg-card p-7 transition-transform duration-300 hover:-translate-y-1', t.highlight ? 'border-primary/40 shadow-glow' : 'border-border')}>
              {t.highlight && <Badge variant="primary" className="absolute -top-3 left-1/2 -translate-x-1/2">Most popular</Badge>}
              <p className="font-display text-lg font-semibold text-foreground">{t.name}</p>
              <p className="mt-1 text-sm text-muted-foreground">{t.desc}</p>
              <div className="mt-5 flex items-baseline gap-1">
                <span className="font-display text-4xl font-bold tracking-tight text-foreground">{t.price}</span>
                <span className="text-sm text-muted-foreground">{t.period}</span>
              </div>
              <ul className="mt-6 flex-1 space-y-3">
                {t.features.map((f) => <li key={f} className="flex items-start gap-2.5 text-sm text-foreground/85"><Check className="mt-0.5 h-4 w-4 shrink-0 text-primary" /> {f}</li>)}
              </ul>
              <Link to="/login" className="mt-7"><Button variant={t.highlight ? 'gradient' : 'outline'} className="w-full">{t.cta}</Button></Link>
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  )
}

/* ---------------------------------- FAQ ---------------------------------- */
const faqs = [
  { q: 'How does SkillSphere score candidates?', a: 'It analyzes observable evidence — GitHub repositories, résumé content, and optional Codeforces history — into 17 explainable dimensions. Each dimension carries its own score, confidence, reasoning, and cited evidence, and dimensions with little evidence contribute less to the overall score automatically.' },
  { q: 'Is the scoring a black box?', a: 'No. Every number traces back to a source signal. You can expand any dimension to see the reasoning and the exact evidence behind it, and the recruiter copilot cites evidence in every answer.' },
  { q: 'How does fairness auditing work?', a: 'When optional demographic context is provided, SkillSphere runs automatic bias checks across matches and surfaces severity-tagged flags so you can review potential disparities before making decisions.' },
  { q: 'Do candidates need to do anything?', a: 'No. You provide a GitHub username, résumé, and optionally a Codeforces handle. SkillSphere does the analysis — candidates never fill out a form.' },
  { q: 'Can I use my own job descriptions?', a: 'Yes. Paste a description or upload a PDF, and SkillSphere matches candidates against your exact requirements with direct, adjacent, and missing coverage.' },
]

function FAQ() {
  return (
    <section id="faq" className="scroll-mt-24 border-t border-border bg-surface/40 py-28">
      <div className="mx-auto max-w-3xl px-4 sm:px-6">
        <Reveal className="text-center">
          <Badge variant="accent">FAQ</Badge>
          <h2 className="mt-4 font-display text-3xl font-bold tracking-tight text-foreground sm:text-4xl">Questions, answered</h2>
        </Reveal>
        <Reveal delay={0.1}>
          <Accordion type="single" collapsible className="mt-10">
            {faqs.map((f) => (
              <AccordionItem key={f.q} value={f.q}>
                <AccordionTrigger>{f.q}</AccordionTrigger>
                <AccordionContent>{f.a}</AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </Reveal>
      </div>
    </section>
  )
}

/* --------------------------------- CTA ----------------------------------- */
function FinalCTA() {
  return (
    <section className="mx-auto max-w-6xl px-4 py-28 sm:px-6">
      <Reveal>
        <div className="ring-gradient relative overflow-hidden rounded-3xl border border-border bg-card px-6 py-20 text-center sm:px-12">
          <div className="pointer-events-none absolute inset-0 -z-10 bg-grid opacity-20" />
          <div className="pointer-events-none absolute left-1/2 top-0 -z-10 h-72 w-96 -translate-x-1/2 rounded-full bg-primary/20 blur-[100px] animate-glow-breathe" />
          <h2 className="mx-auto max-w-2xl font-display text-3xl font-bold tracking-tight text-foreground sm:text-4xl">Make your next hire on the evidence</h2>
          <p className="mx-auto mt-4 max-w-xl text-muted-foreground">Score your first candidate in under a minute. No credit card, no candidate friction.</p>
          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link to="/login"><Button variant="gradient" size="lg">Get started free <ArrowRight className="h-4 w-4" /></Button></Link>
            <a href="#features"><Button variant="outline" size="lg">Explore features</Button></a>
          </div>
        </div>
      </Reveal>
    </section>
  )
}

/* -------------------------------- Footer --------------------------------- */
function Footer() {
  const cols = [
    { title: 'Product', links: ['Features', 'Pricing', 'How it works', 'Changelog'] },
    { title: 'Company', links: ['About', 'Careers', 'Blog', 'Contact'] },
    { title: 'Legal', links: ['Privacy', 'Terms', 'Security', 'DPA'] },
  ]
  return (
    <footer className="border-t border-border">
      <div className="mx-auto max-w-6xl px-4 py-14 sm:px-6">
        <div className="grid gap-10 md:grid-cols-[1.5fr_1fr_1fr_1fr]">
          <div>
            <Logo />
            <p className="mt-4 max-w-xs text-sm text-muted-foreground">Evidence-based AI talent intelligence for engineering teams.</p>
          </div>
          {cols.map((c) => (
            <div key={c.title}>
              <p className="mb-3 text-sm font-semibold text-foreground">{c.title}</p>
              <ul className="space-y-2.5">
                {c.links.map((l) => <li key={l}><a href="#" className="text-sm text-muted-foreground transition-colors hover:text-foreground">{l}</a></li>)}
              </ul>
            </div>
          ))}
        </div>
        <div className="mt-12 flex flex-col items-center justify-between gap-3 border-t border-border pt-6 sm:flex-row">
          <p className="text-xs text-muted-foreground">© {new Date().getFullYear()} SkillSphere. All rights reserved.</p>
          <p className="flex items-center gap-1.5 text-xs text-muted-foreground"><StatusDot tone="success" /> All systems operational</p>
        </div>
      </div>
    </footer>
  )
}

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main>
        <Hero />
        <Marquee />
        <Stats />
        <Features />
        <HowItWorks />
        <Pipeline />
        <Testimonials />
        <Pricing />
        <FAQ />
        <FinalCTA />
      </main>
      <Footer />
    </div>
  )
}
