import { useState } from 'react'

export default function ScheduleSession({ isOpen, onClose, onSuccess }) {
  const [durationValue, setDurationValue] = useState(300)
  const [durationUnit, setDurationUnit] = useState('seconds')
  
  // Dr. Nine: no more than 2 pictures a minute, so at least 30 seconds apart
  const [intervalValue, setIntervalValue] = useState(60)
  const [intervalUnit, setIntervalUnit] = useState('seconds')

  const [scheduledFor, setScheduledFor] = useState('')
  const [errorMsg, setErrorMsg] = useState('')

  if (!isOpen) return null

  const handleCreateSession = async (e) => {
    e.preventDefault()
    setErrorMsg('')

    // Convert duration to seconds
    let durationMultiplier = durationUnit === 'minutes' ? 60 : durationUnit === 'hours' ? 3600 : 1
    const totalDurationSeconds = parseInt(durationValue, 10) * durationMultiplier

    // Convert interval to seconds
    let intervalMultiplier = intervalUnit === 'minutes' ? 60 : intervalUnit === 'hours' ? 3600 : 1
    const totalIntervalSeconds = parseInt(intervalValue, 10) * intervalMultiplier
    if (totalIntervalSeconds < 30) {
      setErrorMsg('Pictures must be at least 30 seconds apart (2 per minute at most).')
      return
    }

    // Convert local datetime input to UTC ISO string
    let scheduledIso = null
    if (scheduledFor) {
      scheduledIso = new Date(scheduledFor).toISOString()
    }

    try {
      const response = await fetch('/api/sessions/jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          duration_seconds: totalDurationSeconds,
          interval_seconds: totalIntervalSeconds,
          scheduled_for: scheduledIso,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Failed to create session job')
      }

      setScheduledFor('')
      onSuccess(`Successfully created job #${data.id}!`)
      onClose()
    } catch (err) {
      setErrorMsg(err.message)
    }
  }

  return (
    <div className="modal-overlay">
      <div className="modal-card">
        <div className="modal-header">
          <h3>Schedule Session</h3>
          <button type="button" className="close-btn" onClick={onClose}>&times;</button>
        </div>

        {errorMsg && <div className="modal-error">{errorMsg}</div>}

        <form onSubmit={handleCreateSession} className="modal-form">
          <label>
            Duration
            <span className="field">
              <input 
                type="number" 
                min="1" 
                value={durationValue} 
                onChange={(e) => setDurationValue(e.target.value)} 
                required
              />
              <select value={durationUnit} onChange={(e) => setDurationUnit(e.target.value)}>
                <option value="seconds">seconds</option>
                <option value="minutes">minutes</option>
                <option value="hours">hours</option>
              </select>
            </span>
          </label>

          <label>
            Interval
            <span className="field">
              <input 
                type="number" 
                min={intervalUnit === 'seconds' ? 30 : 1}
                value={intervalValue} 
                onChange={(e) => setIntervalValue(e.target.value)} 
                required
              />
              <select value={intervalUnit} onChange={(e) => setIntervalUnit(e.target.value)}>
                <option value="seconds">seconds</option>
                <option value="minutes">minutes</option>
                <option value="hours">hours</option>
              </select>
            </span>
          </label>

          <label>
            Scheduled Time
            <span className="field">
              <input 
                type="datetime-local" 
                value={scheduledFor} 
                onChange={(e) => setScheduledFor(e.target.value)} 
                required
              />
            </span>
          </label>

          <div className="modal-actions">
            <button type="button" className="secondary-btn" onClick={onClose}>Cancel</button>
            <button type="submit">Create session</button>
          </div>
        </form>
      </div>
    </div>
  )
}
