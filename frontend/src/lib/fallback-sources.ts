// Neon DB 다운 시 /api/sources가 빈 목록이 되지 않도록 하는 폴백 스냅샷.
// 실제 매일 발송에 쓰이는 소스 목록(trend-letter-bot/config/urls.json)을 반영.
// 봇 urls.json을 수정하면 이 파일도 함께 맞춰줄 것. (DB 복구 시엔 DB 값이 우선)
export interface FallbackSource {
  id: string;
  name: string;
  url: string;
  category: string;
  isActive: boolean;
  lastCrawledAt: string | null;
}

const RAW = [
  { name: "오픈애즈 트렌드", url: "https://www.openads.co.kr/content?category=CC97", category: "광고" },
  { name: "아이보스 자료실(PDF)", url: "https://www.i-boss.co.kr/ab-3207", category: "광고" },
  { name: "아이보스 뉴스", url: "https://www.i-boss.co.kr/ab-7214", category: "광고" },
  { name: "TBWA DATALAB", url: "https://seo.tbwakorea.com/blog/", category: "광고" },
  { name: "비즈스프링", url: "https://blog.bizspring.co.kr/category/%ec%9d%b8%ec%82%ac%ec%9d%b4%ed%8a%b8/", category: "광고" },
  { name: "모비데이즈", url: "https://www.mobiinside.co.kr/", category: "광고" },
  { name: "매드타임즈", url: "https://www.madtimes.co.kr/news/articleList.html?sc_section_code=S1N35&view_type=sm", category: "광고" },
  { name: "어센트코리아", url: "https://www.ascentkorea.com/ascent-korea-official-blog-listeningmind/", category: "광고" },
  { name: "디지털 인사이트", url: "https://ditoday.com/", category: "광고" },
  { name: "제일기획", url: "https://magazine.cheil.com/", category: "광고" },
  { name: "마케팅 인사이트", url: "https://inside.ampm.co.kr/", category: "광고" },
  { name: "디지털 마케팅 큐레이션", url: "https://www.thedigitalmkt.com/", category: "광고" },
  { name: "콘텐타 M", url: "https://magazine.contenta.co/", category: "광고" },
  { name: "트렌드라이", url: "https://trendlite.stibee.com/", category: "광고" },
  { name: "인터비즈", url: "https://blog.naver.com/businessinsight", category: "HR" },
  { name: "이오플래", url: "https://eopla.net/", category: "기타" },
  { name: "브랜드브리프", url: "https://www.brandbrief.co.kr/news/articleList.html?view_type=sm", category: "광고" },
  { name: "디지털광고협회", url: "https://kodaa.or.kr/16?category=383QL5Q23o", category: "광고" },
];

export const FALLBACK_SOURCES: FallbackSource[] = RAW.map((s, i) => ({
  id: `urls-${i + 1}`,
  name: s.name,
  url: s.url,
  category: s.category,
  isActive: true,
  lastCrawledAt: null,
}));
