import { useEffect, useRef, useState } from 'react'
import './Search.css'

function Search() {
  const dialog = useRef(null)
  const [big, setBig] = useState(null)
  const [images, setImages] = useState([])

  // Get every image from the database (newest first)
  useEffect(() => {
    fetch('/api/images')
      .then((res) => res.json())
      .then((data) =>
        setImages(data.map((img) => ({ name: `${img.target} - ${img.night_of}`, url: img.url })))
      )
      .catch((err) => console.error('Could not load images:', err))
  }, [])

  function open(image) {
    setBig(image)
    dialog.current.showModal()
  }
// Buttons and image open
  return (
    <>

      {/*Navigation bar that will sit at the top of every page to navigate from page to page. */}
      <nav className="navbar">
        <div className="nav-logo">
          Whitewater Observatory
        </div>

        <div className="nav-links">
          <a href="/">Home</a>
          <a href="/search.html">Search</a>
          <a href="/signin.html">Sign In</a>
          <a href="/signup.html">Sign Up</a>
        </div>
      </nav>
      
      <div className="controls">
        <input type="search" placeholder="Search" />
        <input type="date" id="startDate"/>
        <input type="date" id="endDate"/>
        <input type="time" id="timeframeStart"/>
        <input type="time" id="timeframeEnd"/>
        <button type="button">Search</button>
      </div>
      <ul className="results">
        {images.map(({ name, url }) => (
          <li key={url}>
            <button type="button" onClick={() => open({ name, url })}>
              <img src={url} alt={name} />
            </button>
          </li>
        ))}
      </ul>
      <dialog ref={dialog} onClick={() => dialog.current.close()}>
        {big && (
          <>
            <a className="download" href={big.url} download onClick={(e) => e.stopPropagation()}>
              Download
            </a>
            <img src={big.url} alt={big.name} />
          </>
        )}
      </dialog>
    </>
  )
}

export default Search
