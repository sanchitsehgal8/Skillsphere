import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Bell, Download, Mail, Moon, RotateCcw, Save } from 'lucide-react'
import { PageHeading } from '../components/shell/PageHeading'
import { Button, Card, CardHeader, CardTitle, CardDescription, CardContent, Switch, Separator, useToast } from '../components/ui'
import { ThemeToggle } from '../components/brand/ThemeToggle'

const STORAGE_KEY = 'skillsphere-settings'
const DEFAULTS = { emailAlerts: true, weeklyDigest: true, autoExport: false }

const NOTIFICATION_ROWS = [
  { key: 'emailAlerts', icon: Mail, title: 'Email alerts', description: 'Get notified when a candidate scorecard updates.' },
  { key: 'weeklyDigest', icon: Bell, title: 'Weekly pipeline digest', description: 'A Monday summary of pipeline movement and top matches.' },
  { key: 'autoExport', icon: Download, title: 'Auto-export weekly report', description: 'Automatically download a CSV of your pipeline each week.' },
]

export default function SettingsPage() {
  const { toast } = useToast()
  const [settings, setSettings] = useState(DEFAULTS)

  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) setSettings((prev) => ({ ...prev, ...JSON.parse(saved) }))
    } catch {
      /* ignore corrupted settings */
    }
  }, [])

  function setFlag(key, value) {
    setSettings((prev) => ({ ...prev, [key]: value }))
  }

  function saveSettings() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
    toast({ title: 'Settings saved', description: 'Your workspace preferences were updated.', variant: 'success' })
  }

  function resetSettings() {
    setSettings(DEFAULTS)
    toast({ title: 'Reset to defaults', description: 'Preferences restored — save to keep them.', variant: 'info' })
  }

  return (
    <div>
      <PageHeading
        eyebrow="Workspace"
        title="Settings"
        subtitle="Control workspace preferences, notifications, and appearance."
        actions={
          <>
            <Button variant="outline" onClick={resetSettings}>
              <RotateCcw className="h-4 w-4" /> Reset
            </Button>
            <Button onClick={saveSettings}>
              <Save className="h-4 w-4" /> Save
            </Button>
          </>
        }
      />

      <div className="mx-auto max-w-2xl space-y-6">
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Notifications</CardTitle>
              <CardDescription>Choose what SkillSphere sends your way.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-1">
              {NOTIFICATION_ROWS.map(({ key, icon: Icon, title, description }, i) => (
                <div key={key}>
                  {i > 0 && <Separator className="my-1" />}
                  <label
                    htmlFor={`setting-${key}`}
                    className="flex cursor-pointer items-center gap-4 rounded-xl py-3 transition-colors"
                  >
                    <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-primary/12 text-primary">
                      <Icon className="h-4 w-4" />
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block text-sm font-medium text-foreground">{title}</span>
                      <span className="block text-sm text-muted-foreground">{description}</span>
                    </span>
                    <Switch
                      id={`setting-${key}`}
                      checked={settings[key]}
                      onCheckedChange={(v) => setFlag(key, v)}
                    />
                  </label>
                </div>
              ))}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, delay: 0.08 }}>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Appearance</CardTitle>
              <CardDescription>Match SkillSphere to your environment.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-4 py-1">
                <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-accent/12 text-accent">
                  <Moon className="h-4 w-4" />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block text-sm font-medium text-foreground">Theme</span>
                  <span className="block text-sm text-muted-foreground">Toggle between light and dark mode.</span>
                </span>
                <ThemeToggle />
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  )
}
