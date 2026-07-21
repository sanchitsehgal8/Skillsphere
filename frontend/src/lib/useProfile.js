import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'

export const DEFAULT_PROFILE = {
  fullName: 'Alex Rivers',
  role: 'Recruitment Lead',
  email: 'alex.rivers@skillsphere.ai',
  phone: '+1 (415) 555-0198',
  location: 'San Francisco, CA',
  bio: 'Talent leader focused on evidence-driven hiring, faster shortlisting, and fair candidate evaluation.',
}

function readProfile(authEmail) {
  const base = { ...DEFAULT_PROFILE, ...(authEmail ? { email: authEmail } : {}) }
  try {
    const saved = localStorage.getItem('skillsphere-profile')
    if (saved) return { ...base, ...JSON.parse(saved) }
  } catch {
    /* ignore corrupted profile */
  }
  return base
}

/** Reactive recruiter profile from localStorage, kept in sync across tabs and saves. */
export function useProfile() {
  const { user } = useAuth()
  const [profile, setProfile] = useState(() => readProfile(user?.email))

  useEffect(() => {
    setProfile(readProfile(user?.email))
    function onChange() {
      setProfile(readProfile(user?.email))
    }
    window.addEventListener('storage', onChange)
    window.addEventListener('skillsphere-profile-updated', onChange)
    return () => {
      window.removeEventListener('storage', onChange)
      window.removeEventListener('skillsphere-profile-updated', onChange)
    }
  }, [user?.email])

  return profile
}
