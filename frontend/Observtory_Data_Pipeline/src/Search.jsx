import { useEffect, useRef, useState } from 'react'
import './Search.css'
import AuthLinks from './AuthLinks.jsx'

// Don't touch until we get auth working here, if you want to see it as an admin add ?admin after the search.html, admin panel is found at admin.html
const isAdmin = new URLSearchParams(location.search).has('admin')

// Static tag choices, needs to be connected to backend
const tagChoices = ['Moon', 'Planet', 'Star']

function Search() {
  const dialog = useRef(null)
  const [big, setBig] = useState(null)
  const [images, setImages] = useState([])
  const [page, setPage] = useState(0)
  const [tag, setTag] = useState('')
  const [newTag, setNewTag] = useState('')

  const tags = [...new Set(images.flatMap((img) => img.tags))].sort()
  const shown = tag ? images.filter((img) => img.tags.includes(tag)) : images
  const perPage = 24
  const totalPages = Math.ceil(shown.length / perPage)

  const start = page * perPage
  const pageImages = shown.slice(start, start + perPage)

  let firstNumber = page - 2
  if (firstNumber > totalPages - 5) {
    firstNumber = totalPages - 5
  }
  if (firstNumber < 0) {
    firstNumber = 0
  }

  const pageNumbers = []
  for (let i = firstNumber; i < firstNumber + 5 && i < totalPages; i++) {
    pageNumbers.push(i)
  }

  // Get every image from the database (newest first)
  useEffect(() => {
    fetch('/api/images/thumbnails')
      .then((res) => res.json())
      .then((data) =>
        setImages(data.map((img) => ({ 
          name: `${img.target} ${img.night_of}`, 
          url: img.url,
          original_url: img.original_url,
          tags: [].concat(img.tags ?? []),
        })))
      )
      .catch((err) => console.error('Could not load images:', err))
  }, [])

  function open(image) {
    setBig(image)
    dialog.current.showModal()
  }

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
          <AuthLinks />
        </div>
      </nav>
      
      <div className="controls">
        <input type="search" placeholder="Search" />
        <input type="date" id="startDate"/>
        <input type="date" id="endDate"/>
        <input type="time" id="timeframeStart"/>
        <input type="time" id="timeframeEnd"/>
        <select value={tag} onChange={(e) => { setTag(e.target.value); setPage(0) }}>
          <option value="">All tags</option>
          {tags.map((t) => <option key={t}>{t}</option>)}
        </select>
        <button type="button">Search</button>
      </div>

      <ul className="results">
        {pageImages.map((image) => (
          <li key={image.url}>
            <button type="button" onClick={() => open(image)}>
              <img src={image.url} alt={image.name} />
            </button>
          </li>
        ))}
      </ul>

      <div className="pager">
        <button type="button" disabled={page === 0} onClick={() => setPage(page - 1)}>Prev</button>
        {pageNumbers.map((number) => (
          <button type="button" key={number} className={number === page ? 'on' : ''} onClick={() => setPage(number)}>
            {number + 1}
          </button>
        ))}
        <button type="button" disabled={page >= totalPages - 1} onClick={() => setPage(page + 1)}>Next</button>
      </div>

      <dialog ref={dialog} onClick={() => dialog.current.close()}>
        {big && (
          <>
            <a className="download" href={big.original_url} download onClick={(e) => e.stopPropagation()}>
              Download Original 4K
            </a>
            <img src={big.original_url} alt={big.name} />
            {isAdmin && (
              <div className="admin-tools" onClick={(e) => e.stopPropagation()}>
                <select value={newTag} onChange={(e) => setNewTag(e.target.value)}>
                  <option value="" disabled>Choose a tag</option>
                  {tagChoices.map((t) => <option key={t}>{t}</option>)}
                  <option>Other</option>
                </select>
                {newTag === 'Other' && <input type="text" placeholder="Custom tag" autoFocus />}
                <button type="button">Add tag</button>
                <button type="button" className="danger">Delete</button>
              </div>
            )}
          </>
        )}
      </dialog>
    </>
  )
}

export default Search