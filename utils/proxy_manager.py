"""
Proxy Manager - إدارة البروكسيات الدوارة
-------------------------------------------
الاستخدام: يمكنك إضافة بروكسيات مجانية من مواقع مثل:
- free-proxy-list.net
- proxy-list.download
أو استخدام خدمات API مثل ScrapingBee / ZenRows (لها باقات مجانية)
"""

import random
import requests
from typing import Optional, Dict, List

# قائمة بروكسيات تجريبية (استبدلها ببروكسيات حقيقية)
DEFAULT_PROXIES: List[Optional[str]] = [
    None,  # بدون بروكسي (الاتصال المباشر)
]


class ProxyManager:
    """يدير قائمة بروكسيات ويدور بينها تلقائياً"""

    def __init__(self, proxy_list: List[Optional[str]] = None):
        self.proxies = proxy_list if proxy_list else DEFAULT_PROXIES
        self.current_index = 0
        self.failed_proxies = set()

    def get_proxy(self) -> Optional[Dict[str, str]]:
        """إرجاع بروكسي عشوائي من القائمة"""
        available = [p for p in self.proxies if p not in self.failed_proxies]
        if not available:
            # إذا فشلت كل البروكسيات، ارجع للاتصال المباشر
            self.failed_proxies.clear()
            available = [None]

        proxy = random.choice(available)
        if proxy is None:
            return None
        return {"http": proxy, "https": proxy}

    def rotate(self) -> Optional[Dict[str, str]]:
        """الانتقال للبروكسي التالي"""
        self.current_index = (self.current_index + 1) % len(self.proxies)
        proxy = self.proxies[self.current_index]
        if proxy is None:
            return None
        return {"http": proxy, "https": proxy}

    def mark_failed(self, proxy_dict: Optional[Dict[str, str]]):
        """تسجيل بروكسي فاشل"""
        if proxy_dict and proxy_dict.get("http"):
            self.failed_proxies.add(proxy_dict["http"])


def validate_proxy(proxy_dict: Optional[Dict[str, str]], timeout: int = 5) -> bool:
    """التحقق من صلاحية البروكسي"""
    if proxy_dict is None:
        try:
            response = requests.get("https://httpbin.org/ip", timeout=timeout)
            return response.status_code == 200
        except Exception:
            return False

    try:
        response = requests.get(
            "https://httpbin.org/ip",
            proxies=proxy_dict,
            timeout=timeout
        )
        return response.status_code == 200
    except Exception:
        return False


def get_free_proxies_from_api() -> List[str]:
    """
    جلب بروكسيات مجانية من API خارجي.
    استخدم بحذر - قد تكون بطيئة أو غير موثوقة.
    """
    try:
        response = requests.get(
            "https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
            timeout=10
        )
        if response.status_code == 200:
            proxies = [p.strip() for p in response.text.strip().split("\n") if p.strip()]
            return [f"http://{p}" for p in proxies[:10]]  # أخذ أول 10 فقط
    except Exception:
        pass
    return []
