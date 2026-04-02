import { useEffect, useState } from 'react'
import TopBar from '../components/TopBar'

const DEFAULT_PROFILE = {
  fullName: 'Alex Rivers',
  role: 'Recruitment Lead',
  email: 'alex.rivers@skillsphere.ai',
  phone: '+1 (415) 555-0198',
  location: 'San Francisco, CA',
  bio: 'Talent leader focused on evidence-driven hiring, faster shortlisting, and fair candidate evaluation.',
}

export default function ProfilePage({ theme, onToggleTheme }) {
  const [profile, setProfile] = useState(DEFAULT_PROFILE)

  useEffect(() => {
    try {
      const saved = localStorage.getItem('skillsphere-profile')
      if (!saved) return
      const parsed = JSON.parse(saved)
      setProfile((prev) => ({ ...prev, ...parsed }))
    } catch {
      // ignore corrupted profil
      // e data
    }
  }, [])

  function updateField(key, value) {
    setProfile((prev) => ({ ...prev, [key]: value }))
  }

  function saveProfile() {
    localStorage.setItem('skillsphere-profile', JSON.stringify(profile))
    window.alert('Profile updated successfully.')
  }

  function resetProfile() {
    setProfile(DEFAULT_PROFILE)
  }

  return (
    <div className="page profile-page">
      <TopBar
        title="Profile"
        subtitle="Manage your recruiter identity and contact information"
        theme={theme}
        onToggleTheme={onToggleTheme}
      />

      <section className="card profile-hero-card">
        <div className="profile-hero">
          <div className="profile-avatar">{profile.fullName.slice(0, 2).toUpperCase()}</div>
          <div>
            <h3>{profile.fullName}</h3>
            <p className="subtle-copy">{profile.role}</p>
          </div>
          <span className="status-pill">Active profile</span>
        </div>
      </section>

      <section className="card profile-form-card">
        <div className="filter-head">
          <h3>Basic Information</h3>
          <span className="badge-soft">Recruiter</span>
        </div>

        <div className="profile-grid">
          <label>
            Full Name
            <input value={profile.fullName} onChange={(e) => updateField('fullName', e.target.value)} />
          </label>
          <label>
            Role
            <input value={profile.role} onChange={(e) => updateField('role', e.target.value)} />
          </label>
          <label>
            Email
            <input value={profile.email} onChange={(e) => updateField('email', e.target.value)} />
          </label>
          <label>
            Phone
            <input value={profile.phone} onChange={(e) => updateField('phone', e.target.value)} />
          </label>
          <label>
            Location
            <input value={profile.location} onChange={(e) => updateField('location', e.target.value)} />
          </label>
          <label className="profile-bio-row">
            Bio
            <textarea
              rows={4}
              value={profile.bio}
              onChange={(e) => updateField('bio', e.target.value)}
            />
          </label>
        </div>

        <div className="settings-actions profile-actions">
          <button type="button" className="ghost-btn" onClick={resetProfile}>Reset</button>
          <button type="button" className="primary-btn" onClick={saveProfile}>Save Profile</button>
        </div>
      </section>
    </div>
  )
}
