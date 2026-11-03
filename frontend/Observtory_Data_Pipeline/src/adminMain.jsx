import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import Admin from './Admin.jsx'

createRoot(document.getElementById('admin')).render(
  <StrictMode>
    <Admin />
  </StrictMode>,
)
