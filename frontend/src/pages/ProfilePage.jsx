import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { RotateCcw, Save } from 'lucide-react'
import { PageHeading } from '../components/shell/PageHeading'
import { Button, Card, CardHeader, CardTitle, CardDescription, CardContent, Input, Textarea, Label, Badge, Avatar, StatusDot, useToast } from '../components/ui'
import { DEFAULT_PROFILE } from '../lib/useProfile'

const STORAGE_KEY = 'skillsphere-profile'

const FIELDS = [
  { key: 'fullName', label: 'Full name', type: 'text' },
  { key: 'role', label: 'Role', type: 'text' },
  { key: 'email', label: 'Email', type: 'email' },
  { key: 'phone', label: 'Phone', type: 'tel' },
  { key: 'location', label: 'Location', type: 'text' },
]

export default function ProfilePage() {
  const { toast } = useToast()
  const [profile, setProfile] = useState(DEFAULT_PROFILE)

  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) setProfile((prev) => ({ ...prev, ...JSON.parse(saved) }))
    } catch {
      /* ignore corrupted profile data */
    }
  }, [])

  function updateField(key, value) {
    setProfile((prev) => ({ ...prev, [key]: value }))
  }

  function saveProfile() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(profile))
    window.dispatchEvent(new Event('skillsphere-profile-updated'))
    toast({ title: 'Profile updated', description: 'Your recruiter profile was saved.', variant: 'success' })
  }

  function resetProfile() {
    setProfile(DEFAULT_PROFILE)
    toast({ title: 'Reset to defaults', description: 'Profile restored — save to keep it.', variant: 'info' })
  }

  return (
    <div>
      <PageHeading
        eyebrow="Account"
        title="Profile"
        subtitle="Manage your recruiter identity and contact information."
        actions={
          <>
            <Button variant="outline" onClick={resetProfile}>
              <RotateCcw className="h-4 w-4" /> Reset
            </Button>
            <Button onClick={saveProfile}>
              <Save className="h-4 w-4" /> Save
            </Button>
          </>
        }
      />

      <div className="mx-auto max-w-3xl space-y-6">
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
          <Card className="overflow-hidden">
            <div className="flex flex-col items-center gap-4 bg-[linear-gradient(135deg,hsl(var(--primary)/0.12),hsl(var(--accent)/0.1))] p-6 text-center sm:flex-row sm:text-left">
              <Avatar name={profile.fullName} size="xl" />
              <div className="min-w-0 flex-1">
                <h2 className="font-display text-xl font-bold tracking-tight text-foreground">{profile.fullName}</h2>
                <p className="text-sm text-muted-foreground">{profile.role}</p>
                <p className="mt-1 truncate text-sm text-muted-foreground">{profile.email}</p>
              </div>
              <Badge variant="success" className="gap-1.5">
                <StatusDot tone="success" />
                Active profile
              </Badge>
            </div>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, delay: 0.08 }}>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Basic information</CardTitle>
              <CardDescription>This is how you appear across the workspace.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-5 sm:grid-cols-2">
              {FIELDS.map(({ key, label, type }) => (
                <div key={key}>
                  <Label htmlFor={`profile-${key}`}>{label}</Label>
                  <Input
                    id={`profile-${key}`}
                    type={type}
                    value={profile[key]}
                    onChange={(e) => updateField(key, e.target.value)}
                  />
                </div>
              ))}
              <div className="sm:col-span-2">
                <Label htmlFor="profile-bio">Bio</Label>
                <Textarea
                  id="profile-bio"
                  rows={4}
                  value={profile.bio}
                  onChange={(e) => updateField('bio', e.target.value)}
                />
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  )
}
