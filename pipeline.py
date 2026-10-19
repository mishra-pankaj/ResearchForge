import re

from tools import scrape_url
from agents import build_search_agent, writer_chain, critic_chain

STEPS = ("search", "scrape", "write", "critique")

SKIP_DOMAINS = (
    "youtube.com", "youtu.be", "twitter.com", "x.com",
    "facebook.com", "instagram.com", "tiktok.com",
)
BLOCKED_MARKERS = ("Access Denied", "CLOUDFLARE", "Error scraping URL", "Reference number")
MIN_CHARS = 500
MAX_CANDIDATES = 8
TARGET_PAGES = 3


def extract_urls(text: str, limit: int = MAX_CANDIDATES) -> list[str]:
    urls = re.findall(r"https?://[^\s)\]>\"']+", text)
    urls = [u.rstrip(".,;:") for u in urls]
    urls = [u for u in urls if not any(d in u for d in SKIP_DOMAINS)]
    unique = list(dict.fromkeys(urls))
    return unique[:limit]


def is_usable(text: str) -> bool:
    if any(marker in text for marker in BLOCKED_MARKERS):
        return False
    return len(text) >= MIN_CHARS


def search_step(topic: str) -> str:
    agent = build_search_agent()
    result = agent.invoke({
        "messages": [("user",
            f"Find recent, reliable and detailed information about: {topic}")]
    })
    return result["messages"][-1].text


def scrape_step(search_text: str) -> list[dict]:
    scraped = []
    usable_count = 0
    for url in extract_urls(search_text):
        if usable_count == TARGET_PAGES:
            break
        text = scrape_url.invoke(url)
        ok = is_usable(text)
        if ok:
            usable_count += 1
            scraped.append({"url": url, "text": text, "ok": True})
        else:
            # Keep a short note of why it was skipped, not the full error page.
            scraped.append({"url": url, "text": text[:300], "ok": False})
    return scraped


def write_step(topic: str, scraped: list[dict]) -> str:
    usable = [s for s in scraped if s["ok"]]
    if not usable:
        research = "No usable sources were found for this topic."
    else:
        research = "\n\n".join(f"Source: {s['url']}\n{s['text']}" for s in usable)

    raw = writer_chain.invoke({"topic": topic, "research": research})

    body = re.split(r"\n[#*\s]*Sources\b.*", raw,
                    flags=re.IGNORECASE | re.DOTALL)[0].rstrip()
    return body

def build_sources_section(scraped: list[dict]) -> str:
    usable_urls = [s["url"] for s in scraped if s["ok"]]
    if not usable_urls:
        return "#### Sources\nNo usable sources were found."
    lines = "\n".join(f"{i}. {url}" for i, url in enumerate(usable_urls, 1))
    return f"#### Sources\n{lines}"


def parse_score(critic_text: str) -> int | None:
    match = re.search(r"Score:\s*(\d+)", critic_text)
    return int(match.group(1)) if match else None


def run_research(topic: str, on_step=None) -> dict:
    notify = on_step or (lambda step: None)

    notify("search")
    search_text = search_step(topic)

    notify("scrape")
    scraped = scrape_step(search_text)

    notify("write")
    body = write_step(topic, scraped)
    report = f"{body}\n\n{build_sources_section(scraped)}"

    notify("critique")
    critic_text = critic_chain.invoke({"report": report})

    return {
        "search_results": search_text,
        "scraped": scraped,
        "report": report,
        "review": {"score": parse_score(critic_text), "text": critic_text},
    }


if __name__ == "__main__":
    topic = input("\nEnter a research topic: ").strip()

    result = run_research(topic, on_step=lambda step: print(f"\n[step] {step}"))

    print("\nScraped pages:")
    for item in result["scraped"]:
        print(f"  {'OK     ' if item['ok'] else 'SKIPPED'} {item['url']}")

    print("\nREPORT\n", result["report"])
    print("\nREVIEW\n", result["review"]["text"])