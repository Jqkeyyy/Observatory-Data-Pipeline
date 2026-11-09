import { useState } from 'react'
import './Admin.css'

// Fastest allowed is 2 pictures a minute
const maxPictures = { minute: 2, hour: 120 }

// Remove once hooked up, just for show
const users = [
  { id: 1, email: 'StudentUser@uww.edu', role: 'user' },
  { id: 2, email: 'OtherStudent@uww.edu', role: 'user' },
  { id: 3, email: 'nine@uww.edu', role: 'admin' },
]

// no handlers
function Admin() {
  const [start, setStart] = useState('')
  const [pictureUnit, setPictureUnit] = useState('minute')

  return (
    <>
      <header className="admin-bar">
        <h1>Admin</h1>
        <a href="/">Back to archive</a>
      </header>

      <section className="admin-section">
        <h2>Session settings</h2>
        <form className="settings" onSubmit={(e) => e.preventDefault()}>
          <label>
            Start
            <input type="datetime-local" required onChange={(e) => setStart(e.target.value)} />
          </label>
          <label>
            End
            <input type="datetime-local" required min={start} />
          </label>
          <label>
            Pictures
            <span className="field">
              <input type="number" min="0" max={maxPictures[pictureUnit]} required defaultValue="1" />
              <select value={pictureUnit} onChange={(e) => setPictureUnit(e.target.value)}>
                <option value="hour">per hour</option>
                <option value="minute">per minute</option>
              </select>
            </span>
          </label>
          <button type="submit">Save settings</button>
        </form>
      </section>

      <section className="admin-section">
        <h2>Users</h2>
        <table className="users">
          <thead>
            <tr>
              <th>Email</th>
              <th>Role</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td>{user.email}</td>
                <td>
                  <select defaultValue={user.role}>
                    <option value="user">User</option>
                    <option value="admin">Admin</option>
                  </select>
                </td>
                <td className="row-actions">
                  <button type="button" className="danger">Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  )
}

export default Admin
