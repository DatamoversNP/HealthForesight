import React from 'react'
import ReactDOM from 'react-dom/client'
import AppMarketing from './AppMarketing.tsx'
import './index.css'
import './marketing-animations.css'

// Add global error handler for unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason)
  // Prevent default browser error handling
  event.preventDefault()
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AppMarketing />
  </React.StrictMode>,
)
