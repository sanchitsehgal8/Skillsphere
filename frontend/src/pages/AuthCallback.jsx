import { motion } from 'framer-motion'
import { LogoMark } from '../components/brand/Logo'

export default function AuthCallback() {
  return (
    <div className="grid min-h-screen place-items-center bg-background px-6">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex flex-col items-center gap-6 text-center"
      >
        <motion.div
          animate={{ scale: [1, 1.06, 1], rotate: [0, 4, -4, 0] }}
          transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
        >
          <LogoMark size={64} />
        </motion.div>

        <div className="space-y-1.5">
          <h1 className="font-display text-xl font-semibold tracking-tight text-foreground">Signing you in…</h1>
          <p className="text-sm text-muted-foreground">Securing your session — this only takes a moment.</p>
        </div>

        <div className="relative h-1 w-48 overflow-hidden rounded-full bg-muted">
          <motion.div
            className="absolute inset-y-0 w-1/3 rounded-full bg-[linear-gradient(90deg,hsl(var(--primary)),hsl(var(--accent)))]"
            animate={{ x: ['-100%', '350%'] }}
            transition={{ duration: 1.3, repeat: Infinity, ease: 'easeInOut' }}
          />
        </div>
      </motion.div>
    </div>
  )
}
