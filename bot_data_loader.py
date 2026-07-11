"""
bot_data_loader.py
──────────────────────────────────────────────────────────────────
Fetch donhang và vitien từ Vercel (phuongthaovip) thay vì đọc file local.
da_nhan_by_subid.json vẫn đọc/ghi local như cũ — không đổi.

[MỚI] push_danhan_remote(): sau khi bot ghi da_nhan cục bộ (ví dụ sau
lệnh #ruttien), gọi hàm này để đẩy dữ liệu da_nhan mới nhất lên CẢ HAI web:
  1. phuongthaovip (Vercel + Upstash Redis) — qua POST /api/data/danhan
  2. hoan-vi-web   (Vercel + Supabase)       — qua POST /api/sync-data
Hai lần gửi độc lập nhau: một bên lỗi không ảnh hưởng bên còn lại.
──────────────────────────────────────────────────────────────────
"""

import json
import logging
import urllib.request
import urllib.error

log = logging.getLogger(__name__)

# ── CẤU HÌNH ────────────────────────────────────────────────────
# Web quản lý dữ liệu chính (phuongthaovip) — bot đọc donhang/vitien tại đây
VERCEL_BASE_URL = "https://phuongthaovip.vercel.app"

# Web hiển thị cho khách (hoan-vi-web) — nhận đồng bộ donhang/vitien/da_nhan
HOANVI_BASE_URL = "https://hoan-vi-web.vercel.app"

# Secret dùng để xác thực khi bot/phuongthaovip ghi dữ liệu lên (phải khớp
# với biến môi trường BOT_SECRET trên phuongthaovip và SYNC_SECRET trên hoan-vi-web).
BOT_SECRET = ""    # để trống nếu phuongthaovip không đặt BOT_SECRET
SYNC_SECRET = "meozzcutemeozzcutemeozzcutemeozzcutemeozzcutemeozzcutemeozzcutemeozzcutemeozzcutemeozzcute9999"
# ────────────────────────────────────────────────────────────────

_CACHE: dict = {}


def _fetch_json(url: str, timeout: int = 10) -> dict:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "ZaloBot/1.0", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _post_json(url: str, payload: dict, headers: dict, timeout: int = 10) -> bool:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "User-Agent": "ZaloBot/1.0",
            "Content-Type": "application/json",
            **headers,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return 200 <= resp.status < 300


def _load_remote(type_: str, fallback_path: str) -> dict:
    url = f"{VERCEL_BASE_URL}/api/data/{type_}"
    try:
        data = _fetch_json(url)
        _CACHE[type_] = data
        log.info(f"[Remote] Đã tải {len(data)} sub_id ({type_}) từ Vercel")
        return data
    except Exception as e:
        log.warning(f"⚠️ Không lấy được {type_} từ Vercel ({e}), thử đọc file local...")
        try:
            with open(fallback_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            log.info(f"[Local fallback] Đọc {len(data)} sub_id từ {fallback_path}")
            return data
        except FileNotFoundError:
            log.warning(f"⚠️ Không tìm thấy {fallback_path} — dùng cache cũ hoặc rỗng")
            return _CACHE.get(type_, {})


def load_donhang_remote(fallback_path: str = "donhang_by_subid.json") -> dict:
    return _load_remote("donhang", fallback_path)


def load_vitien_remote(fallback_path: str = "vitien_by_subid.json") -> dict:
    return _load_remote("vitien", fallback_path)


def push_danhan_remote(data: dict) -> dict:
    """Đẩy da_nhan_by_subid mới nhất lên phuongthaovip VÀ hoan-vi-web.

    Trả về {"phuongthaovip": bool, "hoanvi": bool} để bot log/biết bên nào lỗi.
    Không raise — lỗi mạng ở 1 bên không làm hỏng bên kia hay crash bot.
    """
    result = {"phuongthaovip": False, "hoanvi": False}

    # 1) phuongthaovip — POST /api/data/danhan  (đã có sẵn trong web)
    try:
        headers = {"X-Bot-Secret": BOT_SECRET} if BOT_SECRET else {}
        result["phuongthaovip"] = _post_json(
            f"{VERCEL_BASE_URL}/api/data/danhan",
            {"data": data},
            headers,
        )
        log.info("📤 Đã đẩy da_nhan lên phuongthaovip")
    except Exception as e:
        log.warning(f"⚠️ Đẩy da_nhan lên phuongthaovip thất bại: {e}")

    # 2) hoan-vi-web — POST /api/sync-data
    try:
        headers = {"X-Sync-Secret": SYNC_SECRET} if SYNC_SECRET else {}
        result["hoanvi"] = _post_json(
            f"{HOANVI_BASE_URL}/api/sync-data",
            {"type": "danhan", "data": data},
            headers,
        )
        log.info("📤 Đã đẩy da_nhan lên hoan-vi-web")
    except Exception as e:
        log.warning(f"⚠️ Đẩy da_nhan lên hoan-vi-web thất bại: {e}")

    return result
