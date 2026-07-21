import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs) {
  return twMerge(clsx(inputs))
}

export function scoreTone(score) {
  if (score >= 75) return 'success'
  if (score >= 55) return 'warning'
  return 'danger'
}

export function verdictMeta(verdict) {
  switch (verdict) {
    case 'strong':
      return { label: 'Strong match', tone: 'success' }
    case 'promising':
      return { label: 'Promising', tone: 'warning' }
    default:
      return { label: 'Developing', tone: 'danger' }
  }
}

export function initials(value = '') {
  const parts = value.trim().split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return value.slice(0, 2).toUpperCase()
}

export function formatBytes(n) {
  if (!n) return null
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / (1024 * 1024)).toFixed(1)} MB`
}

export function downloadCsv(filename, headers, rows) {
  const escape = (v) => {
    const s = v == null ? '' : String(v)
    return /[",\n]/.test(s) ? `"${s.replaceAll('"', '""')}"` : s
  }
  const csv = [headers.join(','), ...rows.map((r) => r.map(escape).join(','))].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
