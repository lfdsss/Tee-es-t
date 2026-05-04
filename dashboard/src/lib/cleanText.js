const parser = typeof DOMParser !== 'undefined' ? new DOMParser() : null

export default function cleanText(text) {
  if (!text) return ''
  if (!parser) return text

  let clean = text
  for (let i = 0; i < 3; i++) {
    const doc = parser.parseFromString(clean, 'text/html')
    const decoded = doc.body.textContent || ''
    if (decoded === clean) break
    clean = decoded
  }
  return clean
}
