import json
import re
import urllib.request
import urllib.parse
from datetime import datetime

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def roc_date_to_number(date_str):
    if not date_str:
        return 0
    m = re.search(r'(\d+)\s*年\s*(\d+)\s*月\s*(\d+)\s*日', str(date_str))
    if not m:
        return 0
    return int(m.group(1)) * 10000 + int(m.group(2)) * 100 + int(m.group(3))

def extract_roc_date(html_content):
    if not html_content:
        return ""
    text = re.sub(r'<[^>]+>', ' ', html_content)
    text = re.sub(r'\s+', ' ', text)
    
    patterns = [
        r'修正日期\s*[:：]?\s*民國\s*(\d{2,3})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日',
        r'公布日期\s*[:：]?\s*民國\s*(\d{2,3})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日',
        r'發布日期\s*[:：]?\s*民國\s*(\d{2,3})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日',
        r'發佈日期\s*[:：]?\s*民國\s*(\d{2,3})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日'
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            y, month, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            return f"民國 {y} 年 {month:02d} 月 {d:02d} 日"
    return ""

def fetch_url(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9"
        }
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        return response.read().decode('utf-8', errors='ignore')

def main():
    with open('regulations.json', 'r', encoding='utf-8') as f:
        items = json.load(f)
        
    results = []
    review_count = 0
    
    for item in items:
        entry = {
            "no": item["no"],
            "name": item["name"],
            "announcementDate": item["announcementDate"],
            "source": item["source"],
            "url": item["url"],
            "latestAnnouncementDate": "",
            "checkSuccess": False,
            "needsReview": False,
            "message": ""
        }
        
        try:
            print(f"Fetching [{item['no']}] {item['name']} ...")
            html = fetch_url(item["url"])
            official_date = extract_roc_date(html)
            if official_date:
                entry["latestAnnouncementDate"] = official_date
                entry["checkSuccess"] = True
                if roc_date_to_number(official_date) > roc_date_to_number(item["announcementDate"]):
                    entry["needsReview"] = True
                    review_count += 1
                print(f"  -> Official: {official_date} (NeedsReview: {entry['needsReview']})")
            else:
                entry["message"] = "查無官方日期"
                print("  -> Date not found")
        except Exception as ex:
            entry["message"] = str(ex)
            print(f"  -> Error: {ex}")
            
        results.append(entry)
        
    output_data = {
        "updatedAt": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "reviewCount": review_count,
        "data": results
    }
    
    with open('dates.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    print(f"\nDone! Saved to dates.json (NeedsReview Count: {review_count})")

if __name__ == "__main__":
    main()
