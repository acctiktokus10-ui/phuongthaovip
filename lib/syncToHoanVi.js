// lib/syncToHoanVi.js
// Đẩy dữ liệu donhang / vitien / danhan sang hoan-vi-web (Supabase) mỗi khi
// có cập nhật ở đây, để web hoan-vi-web hiển thị đơn hàng & ví tiền cho khách.
//
// Không throw ra ngoài — nếu hoan-vi-web đang lỗi/chưa deploy, việc upload ở
// phuongthaovip vẫn phải thành công bình thường.

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
      signal: AbortSignal.timeout(8000),
    })
    if (!res.ok) {
      const errText = await res.text().catch(() => '')
      console.warn(`[syncToHoanVi] hoan-vi-web trả lỗi ${res.status}: ${errText}`)
      return false
    }
    return true
  } catch (e) {
    console.warn(`[syncToHoanVi] Không gửi được sang hoan-vi-web: ${e}`)
    return false
  }
}
