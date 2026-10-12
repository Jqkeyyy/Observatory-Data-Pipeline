import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import Search from './Search.jsx'

createRoot(document.getElementById('search')).render(
  <StrictMode>
    <Search />
  </StrictMode>,
)
