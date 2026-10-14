import { useRef, useState } from 'react'
import './Search.css'

// Every image in /images pulls
const images = Object.entries(
  import.meta.glob('/images/*.{jpg,jpeg,png,gif,webp,svg}', {
    eager: true,
    import: 'default',
  }),
).map(([path, url]) => ({ name: path.split('/').pop(), url }))

function Search() {
  const dialog = useRef(null)
  const [big, setBig] = useState(null)

  function open(image) {
    setBig(image)
    dialog.current.showModal()
  }
// Buttons and image open
  return (
    <>
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
          <li key={name}>
            <button type="button" onClick={() => open({ name, url })}>
              <img src={url} alt={name} />
            </button>
          </li>
        ))}
      </ul>
      <dialog ref={dialog} onClick={() => dialog.current.close()}>
        {big && <img src={big.url} alt={big.name} />}
      </dialog>
    </>
  )
}

export default Search
