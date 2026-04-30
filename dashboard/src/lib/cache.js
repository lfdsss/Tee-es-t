const cache = new Map()
const CACHE_TTL = 30_000

function cacheKey(params) {
  return JSON.stringify(params)
}

function getCache(key) {
  const entry = cache.get(key)
  if (!entry) return null
  if (Date.now() - entry.ts > CACHE_TTL) { cache.delete(key); return null }
  return entry.data
}

function setCache(key, data) {
  cache.set(key, { data, ts: Date.now() })
  if (cache.size > 50) {
    const oldest = [...cache.entries()].sort((a, b) => a[1].ts - b[1].ts)[0]
    cache.delete(oldest[0])
  }
}

export { cacheKey, getCache, setCache }
