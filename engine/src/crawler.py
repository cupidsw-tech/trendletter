import logging
import re
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse, quote

import feedparser
import requests
from bs4 import BeautifulSoup

from .utils import polite_sleep, truncate

logger = logging.getLogger("trend-letter")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate",
}

TIMEOUT = 30


@dataclass
class Article:
    title: str
    url: str
    date: str = ""
    body: str = ""
    source_name: str = ""
    category: str = ""
    pdf_urls: list[str] = field(default_factory=list)


# ──────────────────────────────────────
# 사이트 유형 판별
# ──────────────────────────────────────

def _is_daum_cafe(url: str) -> bool:
    return "cafe.daum.net" in url


def _is_playd(url: str) -> bool:
    return "playd.com" in url


def _is_openads(url: str) -> bool:
    return "openads.co.kr" in url


def _is_iboss(url: str) -> bool:
    return "i-boss.co.kr" in url


def _needs_playwright(url: str) -> bool:
    return _is_daum_cafe(url) or _is_playd(url) or _is_openads(url) or _is_iboss(url)


# ──────────────────────────────────────
# RSS
# ──────────────────────────────────────

def _try_rss(url: str) -> list[Article] | None:
    if _needs_playwright(url):
        return None

    rss_url = _discover_rss(url)
    if rss_url:
        articles = _parse_feed(rss_url)
        if articles:
            return articles

    base = "/".join(url.rstrip("/").split("/")[:3])
    for path in ("/rss", "/feed", "/rss.xml", "/atom.xml"):
        articles = _parse_feed(base + path)
        if articles:
            return articles
    return None


def _discover_rss(url: str) -> str | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        link = soup.find("link", type=re.compile(r"(rss|atom)\+xml", re.I))
        if link and link.get("href"):
            return urljoin(url, link["href"])
    except Exception:
        pass
    return None


def _parse_feed(feed_url: str) -> list[Article] | None:
    try:
        feed = feedparser.parse(feed_url)
        if not feed.entries:
            return None
        articles = []
        for entry in feed.entries[:15]:
            body = ""
            if hasattr(entry, "summary"):
                body = BeautifulSoup(entry.summary, "html.parser").get_text(strip=True)
            elif hasattr(entry, "content") and entry.content:
                body = BeautifulSoup(entry.content[0].value, "html.parser").get_text(strip=True)

            date = getattr(entry, "published", "") or getattr(entry, "updated", "")
            articles.append(Article(
                title=entry.get("title", "제목 없음"),
                url=entry.get("link", ""),
                date=date,
                body=truncate(body, 2000),
            ))
        return articles
    except Exception:
        return None


# ──────────────────────────────────────
# 다음 카페 전용 크롤러 (Playwright)
# ──────────────────────────────────────

def _crawl_daum_cafe(url: str) -> list[Article]:
    """다음 카페 게시판을 Playwright로 크롤링."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error("Playwright 미설치 — pip install playwright && playwright install chromium")
        return []

    articles = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000)

            # iframe 내부에서 게시글 목록 추출
            frame = None
            for f in page.frames:
                if "_c21_/bbs_list" in f.url:
                    frame = f
                    break

            if not frame:
                logger.warning(f"다음 카페 iframe을 찾을 수 없음: {url}")
                browser.close()
                return []

            rows = frame.query_selector_all("tr")
            for tr in rows:
                a = tr.query_selector("a")
                if not a:
                    continue
                text = (a.inner_text() or "").strip()
                href = a.get_attribute("href") or ""

                if not text or len(text) < 5:
                    continue
                # 공지 제외, 실제 게시글만
                if "bbs_read" not in href:
                    continue

                full_url = urljoin("https://cafe.daum.net", href)
                articles.append(Article(title=text, url=full_url))

            browser.close()
    except Exception as e:
        logger.error(f"다음 카페 크롤링 실패 ({url}): {e}")

    return articles[:15]


# ──────────────────────────────────────
# PLAYD 전용 크롤러 (Playwright)
# ──────────────────────────────────────

def _crawl_playd(url: str) -> list[Article]:
    """PLAYD 리포트 페이지를 Playwright로 크롤링."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error("Playwright 미설치")
        return []

    articles = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000)

            for a in page.query_selector_all("a"):
                text = (a.inner_text() or "").strip()
                href = a.get_attribute("href") or ""
                if "report-detail" in href and text and len(text) > 5:
                    # 날짜 추출 (형제/부모 요소에서)
                    date = ""
                    parent = a.evaluate_handle("el => el.closest('.report-item, .card, [class*=item], li, div')")
                    if parent:
                        parent_text = parent.as_element().inner_text() if parent.as_element() else ""
                        import re as _re
                        date_match = _re.search(r"(\d{4}\.\d{2})", parent_text)
                        if date_match:
                            date = date_match.group(1)

                    full_url = urljoin(url, href)
                    # 중복 제거
                    if not any(art.url == full_url for art in articles):
                        articles.append(Article(title=text, url=full_url, date=date))

            browser.close()
    except Exception as e:
        logger.error(f"PLAYD 크롤링 실패 ({url}): {e}")

    return articles[:15]


def _fetch_playd_pdf(article: Article) -> Article:
    """PLAYD 리포트 상세에서 Playwright로 PDF 다운로드."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return article

    import os
    dl_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "downloads")
    os.makedirs(dl_path, exist_ok=True)

    try:
        polite_sleep(1.5)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(article.url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)

            # 본문 추출
            body_el = page.query_selector(".report-content, .content-area, article, .detail-content, main")
            if body_el:
                article.body = truncate(body_el.inner_text().strip(), 3000)

            # 다운로드 버튼에서 onclick 파라미터 추출
            dl_btns = page.query_selector_all("[onclick*='download']")
            for btn in dl_btns:
                onclick = btn.get_attribute("onclick") or ""
                match = re.search(r"download\('(\d+)','([^']*)','(\d+)'\)", onclick)
                if not match:
                    continue

                val, url_param, seq = match.group(1), match.group(2), match.group(3)

                # 폼 채우고 다운로드 트리거
                page.evaluate(f"download('{val}','{url_param}','{seq}')")
                page.wait_for_timeout(1000)

                page.evaluate("""() => {
                    const r = document.querySelector('#report');
                    if (!r) return;
                    const name = r.querySelector('#user-name');
                    const mail = r.querySelector('#user-mail');
                    const company = r.querySelector('#user-company');
                    const chk = r.querySelector('#sub-checkbox--personal2');
                    if (name) name.value = '트렌드봇';
                    if (mail) mail.value = 'trend@bot.com';
                    if (company) company.value = 'trend';
                    if (chk) chk.checked = true;
                }""")
                page.wait_for_timeout(500)

                try:
                    with page.expect_download(timeout=15000) as dl_info:
                        page.evaluate("reportWriteProc()")
                    download = dl_info.value
                    save_path = os.path.join(dl_path, download.suggested_filename)
                    download.save_as(save_path)
                    article.pdf_urls.append(f"local:{save_path}")
                    logger.info(f"  PLAYD PDF 다운로드: {download.suggested_filename}")
                except Exception as e:
                    logger.warning(f"  PLAYD PDF 다운로드 실패: {e}")

                break  # 첫 번째 다운로드만

            browser.close()
    except Exception as e:
        logger.warning(f"PLAYD 상세 페이지 실패 ({article.url}): {e}")

    return article


# ──────────────────────────────────────
# 네이버 로그인 공통
# ──────────────────────────────────────

def _naver_login_popup(ctx, page):
    """아이보스 스타일: 팝업으로 네이버 로그인."""
    import os
    naver_id = os.getenv("NAVER_ID", "")
    naver_pw = os.getenv("NAVER_PW", "")
    if not naver_id or not naver_pw:
        return False

    try:
        with ctx.expect_page() as popup_info:
            page.get_by_text("네이버로 시작하기").click()
        popup = popup_info.value
        popup.wait_for_load_state("domcontentloaded")

        id_input = popup.query_selector("#id")
        pw_input = popup.query_selector("#pw")
        if id_input and pw_input:
            id_input.click()
            popup.keyboard.type(naver_id, delay=100)
            popup.wait_for_timeout(500)
            pw_input.click()
            popup.keyboard.type(naver_pw, delay=100)
            popup.wait_for_timeout(500)
            popup.click(".btn_login")
            try:
                popup.wait_for_event("close", timeout=15000)
            except Exception:
                pass
            page.wait_for_timeout(3000)
            return True
    except Exception as e:
        logger.warning(f"네이버 팝업 로그인 실패: {e}")
    return False


def _naver_login_redirect(page):
    """오픈애즈 스타일: 리다이렉트로 네이버 로그인."""
    import os
    naver_id = os.getenv("NAVER_ID", "")
    naver_pw = os.getenv("NAVER_PW", "")
    if not naver_id or not naver_pw:
        return False

    try:
        page.get_by_text("네이버로 시작하기").click()
        page.wait_for_timeout(5000)

        if "nid.naver.com" in page.url:
            page.fill("#id", naver_id)
            page.wait_for_timeout(300)
            page.fill("#pw", naver_pw)
            page.wait_for_timeout(300)
            page.click(".btn_login")
            page.wait_for_timeout(8000)
            return True
    except Exception as e:
        logger.warning(f"네이버 리다이렉트 로그인 실패: {e}")
    return False


def _make_stealth_context(p):
    """봇 감지 우회 브라우저 + 컨텍스트 생성."""
    browser = p.chromium.launch(
        headless=True,
        args=["--disable-blink-features=AutomationControlled"],
    )
    ctx = browser.new_context(user_agent=HEADERS["User-Agent"])
    page = ctx.new_page()
    page.add_init_script('Object.defineProperty(navigator, "webdriver", {get: () => undefined})')
    return browser, ctx, page


# ──────────────────────────────────────
# 아이보스 전용 크롤러 (Playwright + 네이버 로그인)
# ──────────────────────────────────────

def _crawl_iboss(url: str) -> list[Article]:
    """아이보스 게시판을 Playwright로 크롤링 (봇 감지 우회)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error("Playwright 미설치")
        return []

    articles = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"],
            )
            context = browser.new_context(
                user_agent=HEADERS["User-Agent"],
            )
            page = context.new_page()
            page.add_init_script('Object.defineProperty(navigator, "webdriver", {get: () => undefined})')

            page.goto(url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000)

            for a in page.query_selector_all("a"):
                text = (a.inner_text() or "").strip()
                href = a.get_attribute("href") or ""
                # ab-3208-숫자 형태의 자료실 게시글 링크
                if text and len(text) > 10 and "/ab-3208-" in href:
                    full_url = urljoin("https://www.i-boss.co.kr", href)
                    if not any(art.url == full_url for art in articles):
                        articles.append(Article(title=text, url=full_url))

            browser.close()
    except Exception as e:
        logger.error(f"아이보스 크롤링 실패 ({url}): {e}")

    return articles[:15]


def _fetch_iboss_detail(article: Article) -> Article:
    """아이보스 상세 페이지: 네이버 로그인 → 본문 + PDF 다운로드."""
    import os
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return article

    dl_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "downloads")
    os.makedirs(dl_path, exist_ok=True)

    try:
        polite_sleep(1.5)
        with sync_playwright() as p:
            browser, ctx, page = _make_stealth_context(p)

            # 로그인
            page.goto("https://www.i-boss.co.kr/ab-login", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)
            _naver_login_popup(ctx, page)

            # 상세 페이지
            page.goto(article.url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)

            # 본문
            body = page.inner_text("body")
            if body and len(body) > 50:
                article.body = truncate(body, 3000)

            # PDF 다운로드
            for a in page.query_selector_all("a"):
                text = (a.inner_text() or "").strip()
                if ".pdf" in text.lower():
                    logger.info(f"  아이보스 PDF: {text}")
                    try:
                        with page.expect_download(timeout=15000) as dl_info:
                            a.click()
                        download = dl_info.value
                        save_path = os.path.join(dl_path, download.suggested_filename)
                        download.save_as(save_path)
                        article.pdf_urls.append(f"local:{save_path}")
                        logger.info(f"  다운로드 완료: {download.suggested_filename}")
                    except Exception as e:
                        logger.warning(f"  아이보스 PDF 다운로드 실패: {e}")

            browser.close()
    except Exception as e:
        logger.warning(f"아이보스 상세 페이지 실패 ({article.url}): {e}")

    return article


# ──────────────────────────────────────
# 오픈애즈 전용 크롤러 (Playwright)
# ──────────────────────────────────────

def _crawl_openads(url: str) -> list[Article]:
    """오픈애즈 콘텐츠 페이지를 Playwright로 크롤링."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error("Playwright 미설치")
        return []

    articles = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000)

            for a in page.query_selector_all("a"):
                text = (a.inner_text() or "").strip()
                href = a.get_attribute("href") or ""
                if "contentDetail" in href and text and len(text) > 5:
                    full_url = urljoin(url, href)
                    if not any(art.url == full_url for art in articles):
                        articles.append(Article(title=text, url=full_url))

            browser.close()
    except Exception as e:
        logger.error(f"오픈애즈 크롤링 실패 ({url}): {e}")

    return articles[:15]


def _fetch_openads_detail(article: Article) -> Article:
    """오픈애즈 상세 페이지: (로그인 불필요) 본문 + PDF 다운로드."""
    import os
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return article

    dl_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "downloads")
    os.makedirs(dl_path, exist_ok=True)

    try:
        polite_sleep(1.5)
        with sync_playwright() as p:
            browser, ctx, page = _make_stealth_context(p)

            # 상세 페이지 (로그인 없이 바로 접근)
            page.goto(article.url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)

            # 본문
            body_el = page.query_selector("article, .content-area, main")
            if body_el:
                article.body = truncate(body_el.inner_text().strip(), 3000)

            # PDF 다운로드
            dl_btn = page.query_selector("a:has-text('파일 다운로드')")
            if dl_btn:
                logger.info("  오픈애즈 PDF 다운로드 시도")
                try:
                    with page.expect_download(timeout=15000) as dl_info:
                        dl_btn.click()
                    download = dl_info.value
                    save_path = os.path.join(dl_path, download.suggested_filename)
                    download.save_as(save_path)
                    article.pdf_urls.append(f"local:{save_path}")
                    logger.info(f"  다운로드 완료: {download.suggested_filename}")
                except Exception as e:
                    logger.warning(f"  오픈애즈 PDF 다운로드 실패: {e}")

            browser.close()
    except Exception as e:
        logger.warning(f"오픈애즈 상세 페이지 실패 ({article.url}): {e}")

    return article


# ──────────────────────────────────────
# HTML 크롤링
# ──────────────────────────────────────

_BOARD_SELECTORS = [
    "table.board-list a", "table.bbs a", "ul.board-list a",
    "div.board-list a", ".post-list a", ".article-list a",
    ".list-body a", ".bbs_list a", "table tbody tr td a",
    ".news-list a", ".trend-list a", ".report-list a",
    "article a", ".card a", ".item a",
    ".view-list a", "div.list a",
]


def _crawl_html(url: str) -> list[Article]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        logger.error(f"페이지 접근 실패 ({url}): {e}")
        return []

    found = []
    for sel in _BOARD_SELECTORS:
        links = soup.select(sel)
        if links:
            found = links
            break

    if not found:
        main = (
            soup.find("main")
            or soup.find("div", id=re.compile(r"(content|main|board|list)", re.I))
            or soup.find("div", class_=re.compile(r"(content|main|board|list)", re.I))
            or soup.body
        )
        if main:
            found = main.find_all("a", href=True)

    seen = set()
    articles = []
    for a in found[:30]:
        href = a.get("href", "")
        if not href or href.startswith(("#", "javascript:")):
            continue
        full_url = urljoin(url, href)
        text = a.get_text(strip=True)
        if not text or len(text) < 4 or full_url in seen:
            continue
        seen.add(full_url)
        articles.append(Article(title=text, url=full_url))

    return articles[:15]


# ──────────────────────────────────────
# 상세 페이지
# ──────────────────────────────────────

def fetch_detail(article: Article) -> Article:
    """개별 게시글 상세 페이지에서 본문 + PDF 링크 추출."""
    if not article.url:
        return article

    # Playwright 필요 사이트
    if _is_daum_cafe(article.url):
        return _fetch_daum_cafe_detail(article)
    if _is_playd(article.url):
        return _fetch_playd_pdf(article)
    if _is_iboss(article.url):
        return _fetch_iboss_detail(article)
    if _is_openads(article.url):
        return _fetch_openads_detail(article)

    try:
        polite_sleep(1.5)
        resp = requests.get(article.url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        logger.warning(f"상세 페이지 접근 실패 ({article.url}): {e}")
        return article

    # 본문
    area = (
        soup.find("div", class_=re.compile(
            r"(view.?content|article.?body|post.?body|entry.?content|board.?content|detail.?content)", re.I))
        or soup.find("article")
        or soup.find("div", class_=re.compile(r"(content|body|view)", re.I))
        or soup.find("main")
    )
    if area:
        for tag in area.find_all(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        article.body = truncate(area.get_text(separator="\n", strip=True), 3000)

    # PDF 링크
    for a in soup.find_all("a", href=re.compile(r"\.pdf(\?|$)", re.I)):
        pdf_url = urljoin(article.url, a["href"])
        if pdf_url not in article.pdf_urls:
            article.pdf_urls.append(pdf_url)

    return article


def _fetch_daum_cafe_detail(article: Article) -> Article:
    """다음 카페 게시글 상세 페이지를 Playwright로 읽기."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return article

    try:
        polite_sleep(1.0)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(article.url, wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(1500)

            # 본문 iframe 찾기
            frame = None
            for f in page.frames:
                if "_c21_/bbs_read" in f.url:
                    frame = f
                    break

            if frame:
                body_el = frame.query_selector("div.article_view") or frame.query_selector("div#user_contents")
                if body_el:
                    article.body = truncate(body_el.inner_text().strip(), 3000)

                # PDF 링크
                for a in frame.query_selector_all("a"):
                    href = a.get_attribute("href") or ""
                    if ".pdf" in href.lower():
                        pdf_url = urljoin(article.url, href)
                        if pdf_url not in article.pdf_urls:
                            article.pdf_urls.append(pdf_url)

            browser.close()
    except Exception as e:
        logger.warning(f"다음 카페 상세 페이지 실패 ({article.url}): {e}")

    return article


# ──────────────────────────────────────
# 통합 크롤링
# ──────────────────────────────────────

def crawl_site(site: dict) -> list[Article]:
    """사이트 한 곳을 크롤링해서 Article 리스트 반환."""
    url = site["url"]
    name = site.get("name", url)
    category = site.get("category", "")

    logger.info(f"[크롤링] {name} ({url})")

    if _is_daum_cafe(url):
        articles = _crawl_daum_cafe(url)
        logger.info(f"  -> Playwright(카페)로 {len(articles)}건 수집")
    elif _is_playd(url):
        articles = _crawl_playd(url)
        logger.info(f"  -> Playwright(PLAYD)로 {len(articles)}건 수집")
    elif _is_openads(url):
        articles = _crawl_openads(url)
        logger.info(f"  -> Playwright(오픈애즈)로 {len(articles)}건 수집")
    elif _is_iboss(url):
        articles = _crawl_iboss(url)
        logger.info(f"  -> Playwright(아이보스)로 {len(articles)}건 수집")
    else:
        articles = _try_rss(url)
        if articles:
            logger.info(f"  -> RSS로 {len(articles)}건 수집")
        else:
            articles = _crawl_html(url)
            logger.info(f"  -> HTML로 {len(articles)}건 수집")

    for a in articles:
        a.source_name = name
        a.category = category

    polite_sleep(2.0)
    return articles
