
import sys
import json
import time
from playwright.sync_api import sync_playwright

def fetch_bensbites():
    results = []
    with sync_playwright() as p:
        try:
            # Launch Chromium (headless)
            browser = p.chromium.launch(headless=True)
            
            # Use specific context with real UA
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            # Go to homepage
            url = "https://bensbites.beehiiv.com/"
            print(f"Navigating to {url}...", file=sys.stderr)
            
            try:
                page.goto(url, timeout=60000, wait_until="domcontentloaded")
            except Exception as e:
                print(f"Navigation error: {e}", file=sys.stderr)
            
            # Wait a bit for cloudflare or dynamic content
            page.wait_for_timeout(5000)
            
            # Debug title
            title = page.title()
            print(f"Page Title: {title}", file=sys.stderr)
            
            if "Just a moment" in title:
                print("Still stuck in Cloudflare. Waiting 10s...", file=sys.stderr)
                page.wait_for_timeout(10000)

            # Extract posts from Homepage
            # Beehiiv themes vary. Often have a "latest-posts" section or just a list of <a> tags
            # Let's try to get ALL links and filter for likely posts
            
            links = page.query_selector_all('a')
            seen_urls = set()
            
            for link in links:
                try:
                    href = link.get_attribute('href')
                    if not href: continue
                    
                    # Normalize URL
                    if href.startswith("/"):
                        full_url = f"https://bensbites.beehiiv.com{href}"
                    elif href.startswith("https://bensbites.beehiiv.com"):
                        full_url = href
                    else: 
                        continue
                     
                    # Filter for post-like URLs. Beehiiv usually uses /p/slug
                    if "/p/" not in full_url: continue
                        
                    if full_url in seen_urls: continue
                    seen_urls.add(full_url)
                    
                    # Title extraction
                    link_text = link.inner_text().strip()
                    if len(link_text) < 10: 
                        # Try to find a header child
                        h_tag = link.query_selector("h1, h2, h3, h4")
                        if h_tag: link_text = h_tag.inner_text().strip()
                    
                    if len(link_text) < 10: continue

                    results.append({
                        "source": "Ben's Bites",
                        "title": link_text,
                        "url": full_url,
                        "time": "Recent", 
                        "summary": "AI News & Tools",
                    })
                    
                    if len(results) >= 5: break
                except: continue
            
            if not results:
                # Fallback: try to grab the first big header as a single item if no list found (e.g. single landing page)
                h1 = page.query_selector("h1")
                title = h1.inner_text().strip() if h1 else "Ben's Bites Newsletter"
                
                # Check for meta description
                try:
                    meta_desc = page.get_attribute('meta[name="description"]', 'content')
                    summary = meta_desc if meta_desc else "Daily AI Digest. Content protected, visit link."
                except: summary = "Daily AI Digest. Content protected, visit link."
                
                results.append({
                    "source": "Ben's Bites",
                    "title": f"{title} (Latest)",
                    "url": url,
                    "time": "Today", 
                    "summary": summary,
                })

            browser.close()
            
        except Exception as e:
            # sys.stderr.write(f"Playwright Error: {str(e)}\n")
            # Return a safe fallback instead of failing
            if not results:
                results.append({
                    "source": "Ben's Bites",
                    "title": "Ben's Bites (Visit Site)",
                    "url": "https://bensbites.beehiiv.com/",
                    "time": "Today",
                    "summary": "Unable to fetch content. Please verify on site.",
                })
            try:
                if 'browser' in locals(): browser.close()
            except: pass
            
    print(json.dumps(results, indent=2))
    
if __name__ == "__main__":
    fetch_bensbites()
