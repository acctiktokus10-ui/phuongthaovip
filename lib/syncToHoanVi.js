// lib/syncToHoanVi.js
const HOANVI_SYNC_URL = process.env.HOANVI_SYNC_URL || ''
const SYNC_SECRET = process.env.SYNC_SECRET || ''

export async function syncToHoanVi(type, data) {
  if (!HOANVI_SYNC_URL) {
    console.warn('[syncToHoanVi] Chưa cấu hình HOANVI_SYNC_URL — bỏ qua đồng bộ')
    return false
  }
  try {
    const res = await fetch(HOANVI_SYNC_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(SYNC_SECRET ? { 'X-Sync-Secret': SYNC_SECRET } : {}),
      },
      body: JSON.stringify({ type, data }),
      signal: AbortSignal.timeout(25000),
    })
    if (!res.ok) {
      const errText = await res.text().catch(() => '')
      console.warn(`[syncToHoanVi] hoan-vi-web trả lỗi ${res.status}: ${errText}`)
      return false
    }
    console.log(`[syncToHoanVi] Đồng bộ ${type} thành công`)
    return true
  } catch (e) {
    console.warn(`[syncToHoanVi] Không gửi được sang hoan-vi-web: ${e}`)
    return false
  }
}
