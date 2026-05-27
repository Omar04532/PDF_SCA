"""
Cache Manager - تخزين نتائج البحث محلياً
-----------------------------------------
يقلل الطلبات على أمازون بنسبة 90% إذا كنت تبحث عن نفس الكلمات
"""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)


def get_cache_key(seed_keyword: str, marketplace: str, depth: int) -> str:
    """إنشاء مفتاح فريد للبحث"""
    raw = f"{seed_keyword}_{marketplace}_{depth}".encode("utf-8")
    return hashlib.md5(raw).hexdigest()


def load_cache(cache_key: str, max_age_hours: int = 48) -> Optional[dict]:
    """تحميل نتيجة مخزنة إذا كانت حديثة"""
    cache_file = CACHE_DIR / f"{cache_key}.json"

    if not cache_file.exists():
        return None

    file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
    if file_age > timedelta(hours=max_age_hours):
        return None  # البيانات قديمة

    with open(cache_file, "r", encoding="utf-8") as f:
        return json.load(f)


def save_cache(cache_key: str, data: List[str]):
    """حفظ نتيجة البحث"""
    cache_file = CACHE_DIR / f"{cache_key}.json"
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump({
            "keywords": data,
            "saved_at": datetime.now().isoformat(),
            "count": len(data)
        }, f, ensure_ascii=False, indent=2)


def clear_all_cache() -> bool:
    """مسح كل الذاكرة المؤقتة"""
    for f in CACHE_DIR.glob("*.json"):
        f.unlink()
    return True


def get_cache_stats() -> dict:
    """إحصائيات الذاكرة المؤقتة"""
    files = list(CACHE_DIR.glob("*.json"))
    total_size = sum(f.stat().st_size for f in files)
    return {
        "files_count": len(files),
        "total_size_kb": round(total_size / 1024, 2)
    }
