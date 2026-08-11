"""
خدمات البحث الخارجي في الويب (المرحلة 3+ — وضع المقارنة).

بحث في المقالات والمواد المنشورة خارج نبراس (دلائل، مقالات قانونية، نصوص
موازية) عبر محركات بحث HTML عامة — بلا مفتاح API ولا تبعيات إضافية (httpx +
bs4). المحرك الأساسي: Yahoo (أقل حجبًا للمراجع)، والاحتياطي: DuckDuckGo HTML.

البحث الخارجي يُستعمل حصريًا في وضع المقارنة (research) حيث تُسترجَع مقالات
الويب وتُعرض على مزوّد الذكاء الاصطناعي إلى جانب مواد نبراس للتحقق والمقارنة —
لا يُستعمل مصدر خارجي أبدًا كمصدر موثوق وحيد، ولا تُدمج نصوصه في المكتبة.
"""
import re
import urllib.parse

from bs4 import BeautifulSoup

from . import config

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
_HEADERS = {"User-Agent": _UA, "Accept-Language": "ar,fr;q=0.8,en;q=0.5"}


def _decode_redirect_url(url: str) -> str:
    """فك رابط إعادة التوجيه الذي يغلّفه DuckDuckGo (معامل uddg)."""
    m = re.search(r"[?&]uddg=([^&]+)", url)
    if m:
        return urllib.parse.unquote(m.group(1))
    return url


def _decode_yahoo_url(url: str) -> str:
    """فك رابط نتائج Yahoo المغلف (معامل RU مشفّر بـ percent-encoding)."""
    m = re.search(r"/RU=([^/]+)", url)
    if not m:
        return url
    ru = urllib.parse.unquote(m.group(1))
    if ru.startswith(("http://", "https://")):
        return ru
    return url


def _yahoo_search(query: str, limit: int, timeout: int) -> list:
    """بحث عبر Yahoo Search (HTML) — أقل حجبًا للمراجع من Bing/DDG.

    Yahoo يعيد 500 بشكل عابر أحيانًا — نعيد المحاولة مرة واحدة قبل الاستسلام.
    """
    import httpx

    resp = None
    for _ in range(2):
        try:
            resp = httpx.get(
                "https://search.yahoo.com/search",
                params={"p": query, "ei": "UTF-8"},
                timeout=timeout,
                follow_redirects=True,
                headers=_HEADERS,
            )
            if resp.status_code != 500:
                break
        except Exception:  # noqa: BLE001 — شبكة/موقت: يُجرب المحرك الاحتياطي
            resp = None
            break
        import time as _time

        _time.sleep(0.8)
    if resp is None or resp.status_code in (403, 429, 500):
        return []
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    for li in soup.select("div.dd.algo"):
        anchor = li.select_one("a[href*='RU=']") or li.select_one("h3 a") or li.select_one("a h3")
        if anchor is None or anchor.name != "a":
            if anchor is not None and anchor.parent is not None and anchor.parent.name == "a":
                anchor = anchor.parent
            else:
                continue
        title_el = anchor.select_one("h3") or anchor.select_one("h2")
        title = title_el.get_text(" ", strip=True) if title_el else anchor.get_text(" ", strip=True)
        url = _decode_yahoo_url(anchor.get("href") or "")
        if not url or not url.startswith(("http://", "https://")):
            continue
        snippet_el = li.select_one("p.fc-dustygray") or li.select_one("p")
        snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""
        source_el = li.select_one("span[class*='fc-141414']") or li.select_one(".fc-dustygray span")
        source = source_el.get_text(strip=True) if source_el else urllib.parse.urlparse(url).netloc
        results.append(
            {
                "title": title,
                "url": url,
                "snippet": snippet,
                "source": source,
            }
        )
        if len(results) >= limit:
            break
    return results


def _duckduckgo_search(query: str, limit: int, timeout: int) -> list:
    """بحث احتياطي عبر DuckDuckGo HTML (قد يعيد 202 حظرًا — فنتحمل ذلك)."""
    import httpx

    resp = httpx.get(
        "https://html.duckduckgo.com/html/",
        params={"q": query, "ia": "web"},
        timeout=timeout,
        follow_redirects=True,
        headers=_HEADERS,
    )
    if resp.status_code in (202, 403, 429):
        return []
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    for res in soup.select(".result"):
        link = res.select_one("a.result__a")
        snippet_el = res.select_one(".result__snippet")
        if not link:
            continue
        title = link.get_text(strip=True)
        url = _decode_redirect_url(link.get("href") or "")
        if not url or not url.startswith(("http://", "https://")):
            continue
        snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""
        results.append(
            {
                "title": title,
                "url": url,
                "snippet": snippet,
                "source": urllib.parse.urlparse(url).netloc,
            }
        )
        if len(results) >= limit:
            break
    return results


def search_web(query: str, limit: int | None = None, timeout: int | None = None) -> list:
    """يبحث في الويب ويعيد قائمة نتائج موحّدة.

    كل نتيجة: {"title", "url", "snippet", "source"}. تُتجاهل النتائج بلا رابط
    صالح. على أي فشل (شبكة/تحليل) تُعاد قائمة فارغة — البحث الخارجي ترفٌ
    تحسيني لا يجب أن يكسر الإجابة الأساسية.
    """
    if not query or not query.strip():
        return []
    limit = limit or config.AI_WEBSEARCH_LIMIT
    timeout = timeout or config.AI_WEBSEARCH_TIMEOUT

    try:
        import httpx  # noqa: F401
    except ImportError:
        return []

    # المحرك الأساسي: Yahoo. الاحتياطي: DuckDuckGo.
    for engine in (_yahoo_search, _duckduckgo_search):
        try:
            results = engine(query, limit, timeout)
            if results:
                return results
        except Exception:  # noqa: BLE001,S112 — فشل محرك: يُجرَّب التالي
            continue
    return []
