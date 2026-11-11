import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import Signup from './Signup.jsx'

createRoot(document.getElementById('signup')).render(
  <StrictMode>
    <Signup />
  </StrictMode>,
)
