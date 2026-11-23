#!/usr/bin/env python3
"""Build a review-gated iCalendar feed from official recruitment portals."""
import argparse, hashlib, html, json, re, sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SOURCES, VERIFIED, PENDING = (ROOT/'data/sources.json', ROOT/'data/verified_events.json', ROOT/'data/pending_events.json')
CALENDAR, STATUS = ROOT/'docs/kaogong.ics', ROOT/'docs/status.json'
DATE = re.compile(r'(20\d{2})\s*[年./-]\s*(\d{1,2})\s*[月./-]\s*(\d{1,2})\s*(?:日|号)?')
KEYWORDS = re.compile(r'公告|报名|笔试|面试|准考证|打印|成绩|资格复审|体检')
TAG, SPACE = re.compile(r'<[^>]+>'), re.compile(r'\s+')

def load(path): return json.loads(path.read_text(encoding='utf-8'))
def clean(s): return SPACE.sub(' ', html.unescape(TAG.sub(' ', s))).strip()
def fetch(url):
    req = Request(url, headers={'User-Agent':'KaogongCalendarBot/1.0'})
    with urlopen(req, timeout=25) as r: return r.read().decode(r.headers.get_content_charset() or 'utf-8', errors='replace')
def stage(text):
    for word, value in [('准考证','准考证打印'),('打印','准考证打印'),('报名','报名'),('笔试','笔试'),('面试','面试'),('成绩','成绩查询'),('资格复审','资格复审'),('体检','体检')]:
        if word in text: return value
    return '公告'
def candidates(source, page):
    text, result = clean(page), []
    for m in DATE.finditer(text):
        excerpt = text[max(0,m.start()-120):min(len(text),m.end()+120)]
        if not KEYWORDS.search(excerpt): continue
        try: date = datetime(*map(int,m.groups())).date().isoformat()
        except ValueError: continue
        kind = stage(excerpt); uid = hashlib.sha256((source['url']+date+kind).encode()).hexdigest()[:16]
        result.append({'id':uid,'title':f"{source['region']}{source['kind']}：{kind}（待核验）",'date':date,'region':source['region'],'kind':source['kind'],'stage':kind,'url':source['url'],'source':source['name'],'evidence':excerpt[:220]})
    return result
def esc(value): return value.replace('\\','\\\\').replace(';','\\;').replace(',','\\,').replace('\n','\\n')
def ics(events):
    lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Kaogong Calendar//CN','CALSCALE:GREGORIAN','X-WR-CALNAME:公考考试日历']; stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    for e in sorted(events,key=lambda x:(x['date'],x['title'])):
        uid=hashlib.sha256((e['date']+e['title']+e['url']).encode()).hexdigest()+'@kaogong-calendar'
        desc=f"{e.get('source','')}\n官方原文：{e['url']}\n考前请以原公告为准。"
        lines += ['BEGIN:VEVENT',f'UID:{uid}',f'DTSTAMP:{stamp}',f"DTSTART;VALUE=DATE:{e['date'].replace('-','')}",f"SUMMARY:{esc(e['title'])}",f'DESCRIPTION:{esc(desc)}',f"URL:{e['url']}",'STATUS:CONFIRMED','END:VEVENT']
    return '\r\n'.join(lines+['END:VCALENDAR',''])
def main():
    validate=argparse.ArgumentParser(); validate.add_argument('--validate',action='store_true'); args=validate.parse_args(); verified=load(VERIFIED)
    errors=[f"第{i+1}条缺少{key}" for i,e in enumerate(verified) for key in ('title','date','url') if not e.get(key)]
    if errors: print('\n'.join(errors),file=sys.stderr); return 1
    CALENDAR.write_text(ics(verified),encoding='utf-8')
    if args.validate: print(f'验证通过：{len(verified)} 个已核验事件'); return 0
    pending=load(PENDING); known={e['id'] for e in pending}; failures=[]
    for source in load(SOURCES):
        try:
            for event in candidates(source,fetch(source['url'])):
                if event['id'] not in known: pending.append(event); known.add(event['id'])
        except (HTTPError,URLError,TimeoutError,UnicodeError) as error: failures.append({'source':source['name'],'error':str(error)})
    PENDING.write_text(json.dumps(pending,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    STATUS.write_text(json.dumps({'updated_at':datetime.now(timezone.utc).isoformat(),'verified_events':len(verified),'pending_events':len(pending),'fetch_failures':failures},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'已生成 {len(verified)} 个订阅事件；待核验 {len(pending)} 条'); return 0
if __name__ == '__main__': raise SystemExit(main())
