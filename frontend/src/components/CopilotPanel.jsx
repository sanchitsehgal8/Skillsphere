import { useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { ArrowUp, Bot, Cpu, Sparkles, User as UserIcon } from 'lucide-react'
import { askCopilot } from '../api/client'
import { Badge } from './ui/badge'
import { cn } from '../lib/utils'

const SUGGESTED_QUERIES = [
  'Find strong backend engineers',
  'Compare the top two candidates',
  'What skills are missing for this JD?',
  'Why does the top candidate rank higher?',
]

function ThinkingDots() {
  return (
    <div className="flex items-center gap-2 text-sm text-muted-foreground">
      <span className="flex gap-1">
        {[0, 1, 2].map((i) => (
          <motion.span
            key={i}
            className="h-1.5 w-1.5 rounded-full bg-primary"
            animate={{ opacity: [0.3, 1, 0.3], y: [0, -2, 0] }}
            transition={{ duration: 1, repeat: Infinity, delay: i * 0.18 }}
          />
        ))}
      </span>
      Reasoning over the evidence…
    </div>
  )
}

export default function CopilotPanel({ jobId, candidateIds, emptyHint }) {
  const [query, setQuery] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const threadRef = useRef(null)

  useEffect(() => {
    threadRef.current?.scrollTo({ top: threadRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, loading])

  async function submit(e) {
    e?.preventDefault()
    const q = query.trim()
    if (!q || loading) return
    setLoading(true)
    setError('')
    setQuery('')
    setMessages((prev) => [...prev, { role: 'user', text: q }])
    try {
      const answer = await askCopilot(q, { jobId, candidateIds })
      setMessages((prev) => [...prev, { role: 'assistant', answer }])
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Copilot request failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col overflow-hidden rounded-2xl border border-border bg-surface/40">
      <div
        ref={threadRef}
        className="flex-1 space-y-4 overflow-y-auto p-4 sm:p-5"
        style={{ minHeight: 220, maxHeight: 440 }}
      >
        {messages.length === 0 && !loading && (
          <div className="flex h-full min-h-[180px] flex-col items-center justify-center gap-3 text-center">
            <div className="grid h-12 w-12 place-items-center rounded-2xl bg-primary/12 text-primary">
              <Sparkles className="h-6 w-6" />
            </div>
            <p className="max-w-md text-sm text-muted-foreground">
              {emptyHint || 'Ask anything about this candidate pool. Every answer cites the evidence behind it.'}
            </p>
          </div>
        )}

        <AnimatePresence initial={false}>
          {messages.map((m, i) =>
            m.role === 'user' ? (
              <motion.div
                key={`m-${i}`}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex justify-end gap-2.5"
              >
                <div className="max-w-[80%] rounded-2xl rounded-tr-sm bg-primary px-4 py-2.5 text-sm text-primary-foreground">
                  {m.text}
                </div>
                <div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-secondary text-muted-foreground">
                  <UserIcon className="h-4 w-4" />
                </div>
              </motion.div>
            ) : (
              <motion.div
                key={`m-${i}`}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex gap-2.5"
              >
                <div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-[linear-gradient(135deg,hsl(var(--primary)),hsl(var(--accent)))] text-primary-foreground">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="max-w-[85%] space-y-2 rounded-2xl rounded-tl-sm border border-border bg-surface px-4 py-3">
                  <Badge variant={m.answer.llm_assisted ? 'primary' : 'default'} size="sm">
                    <Cpu className="h-3 w-3" />
                    {m.answer.llm_assisted ? 'AI-assisted' : 'Deterministic'}
                  </Badge>
                  <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground/90">{m.answer.answer}</p>
                </div>
              </motion.div>
            ),
          )}
        </AnimatePresence>

        {loading && (
          <div className="flex gap-2.5">
            <div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-[linear-gradient(135deg,hsl(var(--primary)),hsl(var(--accent)))] text-primary-foreground">
              <Bot className="h-4 w-4" />
            </div>
            <div className="rounded-2xl rounded-tl-sm border border-border bg-surface px-4 py-3">
              <ThinkingDots />
            </div>
          </div>
        )}
      </div>

      <div className="border-t border-border p-3 sm:p-4">
        {error && <p className="mb-2 text-xs text-danger">{error}</p>}
        <div className="mb-2.5 flex flex-wrap gap-1.5">
          {SUGGESTED_QUERIES.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setQuery(s)}
              disabled={loading}
              className="rounded-full border border-border bg-surface/60 px-3 py-1 text-xs text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground disabled:opacity-50"
            >
              {s}
            </button>
          ))}
        </div>
        <form onSubmit={submit} className="flex items-center gap-2">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask the recruiter copilot…"
            disabled={loading}
            className="h-11 flex-1 rounded-xl border border-input bg-surface/60 px-4 text-sm text-foreground placeholder:text-muted-foreground/70 focus:border-primary/50 focus:bg-surface focus:outline-none focus:ring-4 focus:ring-primary/15"
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-primary text-primary-foreground transition-all hover:brightness-110 disabled:opacity-40"
            aria-label="Send"
          >
            <ArrowUp className="h-5 w-5" />
          </button>
        </form>
      </div>
    </div>
  )
}
