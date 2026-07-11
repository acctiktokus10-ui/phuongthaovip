// pages/api/upload.js
import { syncToHoanVi } from '../../lib/syncToHoanVi'
import { waitUntil } from '@vercel/functions'

export const config = {
  api: { bodyParser: { sizeLimit: '10mb' } },
  maxDuration: 30,
}

const PASSWORD = process.env.UPLOAD_PASSWORD || 'phuongthaovip9999'

let _store = {}

async function kvSet(key, value) {
  if (process.env.UPSTASH_REDIS_REST_URL && process.env.UPSTASH_REDIS_REST_TOKEN) {
    const url = `${process.env.UPSTASH_REDIS_REST_URL}/set/${encodeURIComponent(key)}`
    const valueStr = typeof value === 'string' ? value : JSON.stringify(value)
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${process.env.UPSTASH_REDIS_REST_TOKEN}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(valueStr),
    })
    if (!res.ok) {
      const errText = await res.text().catch(() => '')
      console.error(`[kvSet] Upstash error key=${key}: ${res.status} ${errText}`)
    }
    return res.ok
  }
  _store[key] = typeof value === 'string' ? value : JSON.stringify(value)
  return true
}

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' })

  const { password, type, data } = req.body
  const headerPwd = req.headers['x-password']

  if (password !== PASSWORD && headerPwd !== PASSWORD) {
    return res.status(401).json({ error: 'Sai mật khẩu' })
  }

  if (!['donhang', 'vitien'].includes(type)) {
    return res.status(400).json({ error: 'type phải là donhang hoặc vitien' })
  }

  if (!data || typeof data !== 'object') {
    return res.status(400).json({ error: 'data không hợp lệ' })
  }

  const key = `${type}_by_subid`
  const count = Object.keys(data).length
  const now = new Date().toISOString()

  const ok = await kvSet(key, data)
  if (!ok) return res.status(500).json({ error: 'Lưu dữ liệu thất bại' })

  await kvSet(`meta_${type}`, { updated_at: now, count })

  waitUntil(syncToHoanVi(type, data))

  return res.status(200).json({
    success: true,
    message: `Đã cập nhật ${count} sub_id vào ${key}`,
    updated_at: now,
  })
}
