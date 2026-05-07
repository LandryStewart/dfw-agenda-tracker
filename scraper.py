import requests
from bs4 import BeautifulSoup
import json
import re
import time
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}

SFR_KEYWORDS = [
    "single family","single-family","residential","subdivision",
    "dwelling","detached","density","lot","SFR","SF-","housing",
    "home","acre","unit","R-1","R-2","R-3","PD","planned development"
]

ACTION_SIGNALS = [
    "rezone","rezoning","zone change","zoning change","zoning case","ZC-",
    "final plat","FP-",
    "preliminary plat","PP-",
    "comprehensive plan","comp plan","future land use","land use plan"
]

NOISE_PHRASES = [
    "agenda center tools","rss notify me","search agendas by","time period",
    "export export","export to excel","export to pdf","export to word",
    "click the subscriptions","notify me","subscribe","last week last month",
    "beautiful board","advisory committee","stakeholder",
    "tax increment","reinvestment zone","tirz","board of adjustment",
    "zoning board of","select the groups","would like to receive",
    "sign up for notification","get notified","alert me",
    "powered by","civicplus","granicus","legistar","municode",
    "call to order","roll call","quorum","pledge of allegiance","invocation",
    "moment of silence","adjournment","adjourn","recess","reconvene",
    "approval of minutes","approve minutes","minutes of previous",
    "citizen comment","public comment","visitor comment",
    "audience participation","hear visitor","staff report",
    "city manager report","mayor report","council report",
    "proclamation","recognition","consent agenda",
    "regular agenda","new business","old business","unfinished business",
    "future agenda","items for future","agenda review","announcement",
    "correspondence","informational item","discussion only","no action",
    "sign-in","attendance","welcome","copyright","privacy policy",
    "all rights reserved","work session","workshop",
    "planning department community profile",
    "development process development review",
    "building inspection health division",
    "planning & development services"
]

DATE_PATS = [
    re.compile(r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+20\d{2})', re.IGNORECASE),
    re.compile(r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+20\d{2})', re.IGNORECASE),
    re.compile(r'(\d{1,2}/\d{1,2}/20\d{2})'),
    re.compile(r'(\d{1,2}-\d{1,2}-20\d{2})'),
    re.compile(r'(20\d{2}-\d{1,2}-\d{1,2})'),
    re.compile(r'(20\d{2}/\d{1,2}/\d{1,2})'),
]

VOTE_PATS = [
    re.compile(r'(approved|denied|tabled|continued|withdrawn|passed|failed)\s*(?:by a vote of\s*)?(\d+\s*[-to]+\s*\d+)?', re.IGNORECASE),
    re.compile(r'(unanimous(?:ly)?)\s*(approved|passed|denied)?', re.IGNORECASE),
    re.compile(r'motion\s+carried\s*(\d+\s*[-to]+\s*\d+)?', re.IGNORECASE),
    re.compile(r'vote:\s*(\d+\s*[-to]+\s*\d+)', re.IGNORECASE),
]

PZ_TERMS = ['planning','zoning','p&z','p & z','plan commission']
CC_TERMS = ['city council','town council','council meeting','regular meeting']

def parse_date(raw):
    for fmt in ['%B %d, %Y','%B %d %Y','%b %d, %Y','%b %d %Y',
                '%m/%d/%Y','%m-%d-%Y','%Y-%m-%d','%Y/%m/%d']:
        try:
            return datetime.strptime(raw.strip().replace(',',''), fmt.replace(',','')).strftime('%Y-%m-%d')
        except:
            continue
    return raw.strip()

def find_date_in_text(text):
    for pat in DATE_PATS:
        m = pat.search(text)
        if m:
            return parse_date(m.group(1))
    return ''

def find_all_dates(text):
    dates = []
    for pat in DATE_PATS:
        for m in pat.finditer(text):
            d = parse_date(m.group(1))
            if d > '2025-01-01':
                dates.append(d)
    return sorted(set(dates), reverse=True)

def fetch(url, timeout=25):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        r.raise_for_status()
        return r
    except:
        return None

def get_pdf_text(pdf_url):
    try:
        import pdfplumber
        import io
        r = requests.get(pdf_url, headers=HEADERS, timeout=45)
        r.raise_for_status()
        ct = r.headers.get('content-type','').lower()
        if 'pdf' not in ct and not pdf_url.lower().endswith('.pdf'):
            if 'ViewFile' not in pdf_url:
                return '', []
        full_text = ''
        lines = []
        with pdfplumber.open(io.BytesIO(r.content)) as pdf:
            for page in pdf.pages[:20]:
                text = page.extract_text()
                if text:
                    full_text += text + '\n'
                    for line in text.split('\n'):
                        line = line.strip()
                        if 20 < len(line) < 800:
                            lines.append(line)
        return full_text, lines
    except Exception as e:
        return '', []

def is_noise(text):
    if len(text) < 20 or len(text) > 1000:
        return True
    t = text.lower()
    for phrase in NOISE_PHRASES:
        if phrase in t:
            return True
    if re.match(r'^[\d\s:/.,-]+$', t):
        return True
    if re.match(r'^(www\.|http|tel:|fax:|email:|phone:)', t):
        return True
    return False

def is_board_name_only(text):
    t = text.lower()
    board_words = ['committee','board','commission','subcommittee','task force']
    action_words = ['amend','change','update','request','case','hearing',
                    'rezone','plat','approve','consider','recommend','deny',
                    'acres','lots','district','from','to']
    if any(bw in t for bw in board_words) and not any(aw in t for aw in action_words):
        return True
    return False

def is_action_item(text):
    if is_board_name_only(text):
        return False
    t = text.lower()
    for signal in ACTION_SIGNALS:
        if signal.lower() in t:
            return True
    return False

def find_sfr(text):
    t = text.lower()
    return [kw for kw in SFR_KEYWORDS if kw.lower() in t]

def clean(text):
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'^\d+\.\s*', '', text)
    text = re.sub(r'^[a-zA-Z]\.\s*', '', text)
    return text.strip()

def filter_items(lines):
    out = []
    seen = set()
    for line in lines:
        line = clean(line)
        if is_noise(line):
            continue
        if not is_action_item(line):
            continue
        key = line[:80].lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(line)
    return out

def merge_short_lines(lines):
    merged = []
    buf = ''
    for line in lines:
        if len(line) < 60 and not any(s in line.lower() for s in ACTION_SIGNALS):
            buf += ' ' + line
        else:
            if buf:
                merged.append(buf.strip())
            buf = line
    if buf:
        merged.append(buf.strip())
    return merged

# ============================================================
# LEVEL 1-3: CivicPlus AgendaCenter deep crawl
# ============================================================

def find_civicplus_pdfs(soup, base_url):
    pdfs = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if not href.startswith('http'):
            href = requests.compat.urljoin(base_url, href)
        text = a.get_text(strip=True)
        parent_text = ''
        for parent in a.parents:
            if parent.name in ['tr','div','li','section','td']:
                parent_text = parent.get_text(separator=' ', strip=True)[:300]
                break
        is_agenda_pdf = ('ViewFile/Agenda' in href or
                        'ViewFile/Item' in href or
                        (href.lower().endswith('.pdf') and 'agenda' in (text + parent_text).lower()))
        is_minutes_pdf = ('ViewFile/Minutes' in href or
                         (href.lower().endswith('.pdf') and 'minute' in (text + parent_text).lower()))
        if is_agenda_pdf or is_minutes_pdf:
            date = find_date_in_text(text + ' ' + href + ' ' + parent_text)
            context = (text + ' ' + parent_text).lower()
            board = 'unknown'
            if any(t in context for t in PZ_TERMS):
                board = 'pz'
            elif any(t in context for t in CC_TERMS):
                board = 'cc'
            pdfs.append({
                'url': href,
                'text': text,
                'date': date,
                'board': board,
                'context': context[:200],
                'type': 'minutes' if is_minutes_pdf else 'agenda'
            })
    return pdfs

def find_civicplus_categories(soup, base_url):
    cats = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        text = a.get_text(strip=True).lower()
        if not href.startswith('http'):
            href = requests.compat.urljoin(base_url, href)
        if '/AgendaCenter/' in href and href != base_url:
            if any(t in text for t in PZ_TERMS):
                cats.append({'url': href, 'board': 'pz', 'text': text})
            elif any(t in text for t in CC_TERMS):
                cats.append({'url': href, 'board': 'cc', 'text': text})
    return cats

def scrape_civicplus(base_url, board_type):
    result = {'agenda_url':'','meeting_date':'','items':[],'raw_count':0}
    resp = fetch(base_url)
    if not resp:
        return result
    soup = BeautifulSoup(resp.text, 'lxml')
    all_pdfs = find_civicplus_pdfs(soup, base_url)
    cats = find_civicplus_categories(soup, base_url)
    for cat in cats:
        if cat['board'] == board_type:
            cat_resp = fetch(cat['url'])
            if cat_resp:
                cat_soup = BeautifulSoup(cat_resp.text, 'lxml')
                all_pdfs.extend(find_civicplus_pdfs(cat_soup, cat['url']))
                time.sleep(0.5)
    target = board_type
    agenda_pdfs = [p for p in all_pdfs if p['type'] == 'agenda' and
                   (p['board'] == target or p['board'] == 'unknown') and
                   p['date'] > '2025-01-01']
    if not agenda_pdfs:
        agenda_pdfs = [p for p in all_pdfs if p['type'] == 'agenda' and p['date'] > '2025-01-01']
    if not agenda_pdfs:
        agenda_pdfs = [p for p in all_pdfs if p['type'] == 'agenda']
    agenda_pdfs.sort(key=lambda x: x['date'] if x['date'] else '', reverse=True)
    for pdf_info in agenda_pdfs[:3]:
        full_text, lines = get_pdf_text(pdf_info['url'])
        if lines:
            merged = merge_short_lines(lines)
            actions = filter_items(merged)
            if not actions:
                actions = filter_items(lines)
            if actions:
                result['items'] = actions
                result['meeting_date'] = pdf_info['date']
                result['agenda_url'] = pdf_info['url']
                result['raw_count'] = len(lines)
                break
        time.sleep(0.5)
    if not result['items'] and agenda_pdfs:
        best = agenda_pdfs[0]
        result['meeting_date'] = best['date']
        result['agenda_url'] = best['url']
    minutes_pdfs = [p for p in all_pdfs if p['type'] == 'minutes' and
                    p['date'] == result['meeting_date']]
    if not minutes_pdfs:
        minutes_pdfs = [p for p in all_pdfs if p['type'] == 'minutes']
        minutes_pdfs.sort(key=lambda x: x['date'] if x['date'] else '', reverse=True)
    for mp in minutes_pdfs[:1]:
        full_text, mlines = get_pdf_text(mp['url'])
        if mlines and result['items']:
            decisions = get_votes(mlines, result['items'])
            if decisions:
                new_items = []
                for item in result['items']:
                    if item in decisions:
                        new_items.append(item + ' [' + decisions[item] + ']')
                    else:
                        new_items.append(item)
                result['items'] = new_items
        time.sleep(0.5)
    return result

# ============================================================
# Generic / non-CivicPlus scraper
# ============================================================

def scrape_generic(url, board_type):
    result = {'agenda_url': url,'meeting_date':'','items':[],'raw_count':0}
    resp = fetch(url)
    if not resp:
        return result
    soup = BeautifulSoup(resp.text, 'lxml')
    pdf_links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        text = a.get_text(strip=True)
        if not href.startswith('http'):
            href = requests.compat.urljoin(url, href)
        full = (text + ' ' + href).lower()
        if href.lower().endswith('.pdf') or 'ViewFile' in href:
            if 'agenda' in full or 'packet' in full or 'meeting' in full:
                date = find_date_in_text(text + ' ' + href)
                pdf_links.append({'url': href, 'date': date, 'text': text})
    pdf_links.sort(key=lambda x: x['date'] if x['date'] else '', reverse=True)
    recent = [p for p in pdf_links if p['date'] > '2025-01-01']
    if not recent:
        recent = pdf_links[:3]
    for pl in recent[:3]:
        full_text, lines = get_pdf_text(pl['url'])
        if lines:
            merged = merge_short_lines(lines)
            actions = filter_items(merged)
            if not actions:
                actions = filter_items(lines)
            if actions:
                result['items'] = actions
                result['meeting_date'] = pl['date']
                result['agenda_url'] = pl['url']
                result['raw_count'] = len(lines)
                break
        time.sleep(0.5)
    if not result['items']:
        html_links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text(strip=True)
            if not href.startswith('http'):
                href = requests.compat.urljoin(url, href)
            full = (text + ' ' + href).lower()
            if ('agenda' in full or 'meeting' in full) and not href.lower().endswith('.pdf'):
                date = find_date_in_text(text + ' ' + href)
                if date > '2025-01-01':
                    html_links.append({'url': href, 'date': date})
        html_links.sort(key=lambda x: x['date'], reverse=True)
        for hl in html_links[:2]:
            sub = fetch(hl['url'])
            if sub:
                sub_soup = BeautifulSoup(sub.text, 'lxml')
                sub_pdfs = []
                for a2 in sub_soup.find_all('a', href=True):
                    h2 = a2['href']
                    if not h2.startswith('http'):
                        h2 = requests.compat.urljoin(hl['url'], h2)
                    if h2.lower().endswith('.pdf') or 'ViewFile' in h2:
                        sub_pdfs.append(h2)
                for sp in sub_pdfs[:2]:
                    ft, lines = get_pdf_text(sp)
                    if lines:
                        merged = merge_short_lines(lines)
                        actions = filter_items(merged)
                        if not actions:
                            actions = filter_items(lines)
                        if actions:
                            result['items'] = actions
                            result['meeting_date'] = hl['date']
                            result['agenda_url'] = sp
                            result['raw_count'] = len(lines)
                            break
                    time.sleep(0.3)
                if result['items']:
                    break
            time.sleep(0.5)
    return result

def get_votes(minutes_lines, action_items):
    decisions = {}
    for item in action_items:
        words = [w for w in item.lower().split() if len(w) > 4][:5]
        near = ''
        for ml in minutes_lines:
            if any(w in ml.lower() for w in words[:3]):
                near += ' ' + ml
        for vp in VOTE_PATS:
            vm = vp.search(near)
            if vm:
                parts = [g for g in vm.groups() if g]
                if parts:
                    decisions[item] = ' '.join(parts).upper().strip()
                    break
    return decisions

# ============================================================
# Main scrape function per board
# ============================================================

def scrape_board(url, city_name, board_name):
    board_type = 'pz' if 'Zoning' in board_name else 'cc'
    result = {'board': board_name, 'agenda_url': url, 'meeting_date': '',
              'items': [], 'sfr_items': [], 'status': 'success'}
    try:
        if '/AgendaCenter' in url:
            data = scrape_civicplus(url, board_type)
        else:
            data = scrape_generic(url, board_type)
        result['items'] = data['items']
        result['meeting_date'] = data.get('meeting_date', '')
        result['agenda_url'] = data.get('agenda_url', url)
        for item in result['items']:
            kw = find_sfr(item)
            if kw:
                result['sfr_items'].append(item + ' [Keywords: ' + ', '.join(kw[:5]) + ']')
        if not result['items']:
            result['status'] = 'no matching items found (PDF parsed: ' + str(data.get('raw_count',0)) + ' lines)'
    except Exception as e:
        result['status'] = 'error: ' + str(e)[:120]
    return result

MUNICIPALITIES = [
    {"name":"Arlington","county":"Tarrant","pz":"https://www.arlingtontx.gov/city_hall/boards_and_commissions/planning_and_zoning_commission","cc":"https://www.arlingtontx.gov/city_hall/government/city_council/city_council_meetings"},
    {"name":"Fort Worth","county":"Tarrant","pz":"https://fortworthtexas.legistar.com/Calendar.aspx","cc":"https://fortworthtexas.legistar.com/Calendar.aspx"},
    {"name":"Mansfield","county":"Tarrant","pz":"https://www.mansfieldtexas.gov/925/Planning-Zoning-Commission","cc":"https://www.mansfieldtexas.gov/AgendaCenter"},
    {"name":"Keller","county":"Tarrant","pz":"https://www.cityofkeller.com/services/development-services/planning-zoning","cc":"https://www.cityofkeller.com/government/city-council/agendas-minutes"},
    {"name":"Southlake","county":"Tarrant","pz":"https://www.cityofsouthlake.com/AgendaCenter","cc":"https://www.cityofsouthlake.com/AgendaCenter"},
    {"name":"Colleyville","county":"Tarrant","pz":"https://www.colleyville.com/government/boards-commissions/planning-zoning-commission","cc":"https://www.colleyville.com/government/city-council/agendas-minutes"},
    {"name":"Grapevine","county":"Tarrant","pz":"https://www.grapevinetexas.gov/AgendaCenter","cc":"https://www.grapevinetexas.gov/AgendaCenter"},
    {"name":"Bedford","county":"Tarrant","pz":"https://www.bedfordtx.gov/AgendaCenter","cc":"https://www.bedfordtx.gov/AgendaCenter"},
    {"name":"Euless","county":"Tarrant","pz":"https://www.eulesstx.gov/city-government/boards-commissions/planning-zoning-commission","cc":"https://www.eulesstx.gov/city-government/city-council/agendas-minutes"},
    {"name":"Hurst","county":"Tarrant","pz":"https://www.hursttx.gov/government/boards-commissions/planning-zoning-commission","cc":"https://www.hursttx.gov/government/city-council/agendas-minutes"},
    {"name":"North Richland Hills","county":"Tarrant","pz":"https://www.nrhtx.com/AgendaCenter","cc":"https://www.nrhtx.com/AgendaCenter"},
    {"name":"Burleson","county":"Tarrant","pz":"https://www.burlesontx.com/AgendaCenter","cc":"https://www.burlesontx.com/AgendaCenter"},
    {"name":"Saginaw","county":"Tarrant","pz":"https://www.ci.saginaw.tx.us/AgendaCenter","cc":"https://www.ci.saginaw.tx.us/AgendaCenter"},
    {"name":"Benbrook","county":"Tarrant","pz":"https://www.benbrook-tx.gov/AgendaCenter","cc":"https://www.benbrook-tx.gov/AgendaCenter"},
    {"name":"Crowley","county":"Tarrant","pz":"https://www.ci.crowley.tx.us/AgendaCenter","cc":"https://www.ci.crowley.tx.us/AgendaCenter"},
    {"name":"Watauga","county":"Tarrant","pz":"https://www.cowtx.gov/AgendaCenter","cc":"https://www.cowtx.gov/AgendaCenter"},
    {"name":"Kennedale","county":"Tarrant","pz":"https://www.kennedale.com/AgendaCenter","cc":"https://www.kennedale.com/AgendaCenter"},
    {"name":"Azle","county":"Tarrant","pz":"https://www.cityofazle.com/AgendaCenter","cc":"https://www.cityofazle.com/AgendaCenter"},
    {"name":"Haslet","county":"Tarrant","pz":"https://www.haslet.org/AgendaCenter","cc":"https://www.haslet.org/AgendaCenter"},
    {"name":"Trophy Club","county":"Tarrant","pz":"https://www.trophyclub.org/AgendaCenter","cc":"https://www.trophyclub.org/AgendaCenter"},
    {"name":"Dallas","county":"Dallas","pz":"https://dallascityhall.com/government/cityplan/Pages/default.aspx","cc":"https://dallascityhall.com/government/citycouncil/Pages/city-council-agendas.aspx"},
    {"name":"Irving","county":"Dallas","pz":"https://www.cityofirving.org/AgendaCenter","cc":"https://www.cityofirving.org/AgendaCenter"},
    {"name":"Grand Prairie","county":"Dallas","pz":"https://www.gptx.org/AgendaCenter","cc":"https://www.gptx.org/AgendaCenter"},
    {"name":"Garland","county":"Dallas","pz":"https://www.garlandtx.gov/AgendaCenter","cc":"https://www.garlandtx.gov/AgendaCenter"},
    {"name":"Mesquite","county":"Dallas","pz":"https://www.cityofmesquite.com/AgendaCenter","cc":"https://www.cityofmesquite.com/AgendaCenter"},
    {"name":"Richardson","county":"Dallas","pz":"https://www.cor.net/government/boards-and-commissions/plan-commission","cc":"https://www.cor.net/government/city-council/agendas-and-minutes"},
    {"name":"Carrollton","county":"Dallas","pz":"https://www.cityofcarrollton.com/government/boards-commissions/planning-zoning-commission","cc":"https://www.cityofcarrollton.com/government/city-council/agendas-minutes"},
    {"name":"Farmers Branch","county":"Dallas","pz":"https://www.farmersbranchtx.gov/AgendaCenter","cc":"https://www.farmersbranchtx.gov/AgendaCenter"},
    {"name":"DeSoto","county":"Dallas","pz":"https://www.ci.desoto.tx.us/AgendaCenter","cc":"https://www.ci.desoto.tx.us/AgendaCenter"},
    {"name":"Cedar Hill","county":"Dallas","pz":"https://www.cedarhilltx.com/AgendaCenter","cc":"https://www.cedarhilltx.com/AgendaCenter"},
    {"name":"Lancaster","county":"Dallas","pz":"https://www.lancaster-tx.com/AgendaCenter","cc":"https://www.lancaster-tx.com/AgendaCenter"},
    {"name":"Duncanville","county":"Dallas","pz":"https://www.duncanville.com/AgendaCenter","cc":"https://www.duncanville.com/AgendaCenter"},
    {"name":"Rowlett","county":"Dallas","pz":"https://www.ci.rowlett.tx.us/AgendaCenter","cc":"https://www.ci.rowlett.tx.us/AgendaCenter"},
    {"name":"Seagoville","county":"Dallas","pz":"https://www.seagoville.us/AgendaCenter","cc":"https://www.seagoville.us/AgendaCenter"},
    {"name":"Balch Springs","county":"Dallas","pz":"https://www.cityofbalchsprings.com/AgendaCenter","cc":"https://www.cityofbalchsprings.com/AgendaCenter"},
    {"name":"Plano","county":"Collin","pz":"https://www.plano.gov/AgendaCenter","cc":"https://www.plano.gov/AgendaCenter"},
    {"name":"McKinney","county":"Collin","pz":"https://www.mckinneytexas.org/AgendaCenter","cc":"https://www.mckinneytexas.org/AgendaCenter"},
    {"name":"Frisco","county":"Collin","pz":"https://www.friscotexas.gov/AgendaCenter","cc":"https://www.friscotexas.gov/AgendaCenter"},
    {"name":"Allen","county":"Collin","pz":"https://www.cityofallen.org/AgendaCenter","cc":"https://www.cityofallen.org/AgendaCenter"},
    {"name":"Wylie","county":"Collin","pz":"https://www.wylietexas.gov/AgendaCenter","cc":"https://www.wylietexas.gov/AgendaCenter"},
    {"name":"Anna","county":"Collin","pz":"https://www.annatexas.gov/AgendaCenter","cc":"https://www.annatexas.gov/AgendaCenter"},
    {"name":"Celina","county":"Collin","pz":"https://www.celina-tx.gov/AgendaCenter","cc":"https://www.celina-tx.gov/AgendaCenter"},
    {"name":"Prosper","county":"Collin","pz":"https://www.prospertx.gov/AgendaCenter","cc":"https://www.prospertx.gov/AgendaCenter"},
    {"name":"Princeton","county":"Collin","pz":"https://www.princetontx.gov/AgendaCenter","cc":"https://www.princetontx.gov/AgendaCenter"},
    {"name":"Melissa","county":"Collin","pz":"https://www.melissatx.gov/AgendaCenter","cc":"https://www.melissatx.gov/AgendaCenter"},
    {"name":"Sachse","county":"Collin","pz":"https://www.cityofsachse.com/AgendaCenter","cc":"https://www.cityofsachse.com/AgendaCenter"},
    {"name":"Lucas","county":"Collin","pz":"https://www.lucastexas.us/AgendaCenter","cc":"https://www.lucastexas.us/AgendaCenter"},
    {"name":"Farmersville","county":"Collin","pz":"https://www.farmersvilletx.com/AgendaCenter","cc":"https://www.farmersvilletx.com/AgendaCenter"},
    {"name":"Denton","county":"Denton","pz":"https://www.cityofdenton.com/AgendaCenter","cc":"https://www.cityofdenton.com/AgendaCenter"},
    {"name":"Lewisville","county":"Denton","pz":"https://www.cityoflewisville.com/government/boards-commissions/planning-zoning-commission","cc":"https://www.cityoflewisville.com/government/city-council/agendas-minutes"},
    {"name":"Flower Mound","county":"Denton","pz":"https://www.flower-mound.com/AgendaCenter","cc":"https://www.flower-mound.com/AgendaCenter"},
    {"name":"Little Elm","county":"Denton","pz":"https://www.littleelm.org/AgendaCenter","cc":"https://www.littleelm.org/AgendaCenter"},
    {"name":"Corinth","county":"Denton","pz":"https://www.cityofcorinth.com/AgendaCenter","cc":"https://www.cityofcorinth.com/AgendaCenter"},
    {"name":"The Colony","county":"Denton","pz":"https://www.thecolonytx.gov/AgendaCenter","cc":"https://www.thecolonytx.gov/AgendaCenter"},
    {"name":"Argyle","county":"Denton","pz":"https://www.argyletx.com/AgendaCenter","cc":"https://www.argyletx.com/AgendaCenter"},
    {"name":"Aubrey","county":"Denton","pz":"https://www.aubreytx.gov/AgendaCenter","cc":"https://www.aubreytx.gov/AgendaCenter"},
    {"name":"Sanger","county":"Denton","pz":"https://www.sangertexas.org/AgendaCenter","cc":"https://www.sangertexas.org/AgendaCenter"},
    {"name":"Pilot Point","county":"Denton","pz":"https://www.cityofpilotpoint.org/AgendaCenter","cc":"https://www.cityofpilotpoint.org/AgendaCenter"},
    {"name":"Northlake","county":"Denton","pz":"https://www.northlaketx.org/AgendaCenter","cc":"https://www.northlaketx.org/AgendaCenter"},
    {"name":"Justin","county":"Denton","pz":"https://www.cityofjustin.com/AgendaCenter","cc":"https://www.cityofjustin.com/AgendaCenter"},
    {"name":"Roanoke","county":"Denton","pz":"https://www.roanoketexas.com/AgendaCenter","cc":"https://www.roanoketexas.com/AgendaCenter"},
    {"name":"Cross Roads","county":"Denton","pz":"https://www.crossroadstx.gov/AgendaCenter","cc":"https://www.crossroadstx.gov/AgendaCenter"},
    {"name":"Oak Point","county":"Denton","pz":"https://www.oakpointtexas.com/AgendaCenter","cc":"https://www.oakpointtexas.com/AgendaCenter"},
    {"name":"Waxahachie","county":"Ellis","pz":"https://www.waxahachie.com/AgendaCenter","cc":"https://www.waxahachie.com/AgendaCenter"},
    {"name":"Midlothian","county":"Ellis","pz":"https://www.midlothian.tx.us/AgendaCenter","cc":"https://www.midlothian.tx.us/AgendaCenter"},
    {"name":"Ennis","county":"Ellis","pz":"https://www.ennis-texas.com/AgendaCenter","cc":"https://www.ennis-texas.com/AgendaCenter"},
    {"name":"Red Oak","county":"Ellis","pz":"https://www.redoaktx.org/AgendaCenter","cc":"https://www.redoaktx.org/AgendaCenter"},
    {"name":"Rockwall","county":"Rockwall","pz":"https://www.rockwall.com/AgendaCenter","cc":"https://www.rockwall.com/AgendaCenter"},
    {"name":"Heath","county":"Rockwall","pz":"https://www.heathtx.com/AgendaCenter","cc":"https://www.heathtx.com/AgendaCenter"},
    {"name":"Fate","county":"Rockwall","pz":"https://www.fatetx.gov/AgendaCenter","cc":"https://www.fatetx.gov/AgendaCenter"},
    {"name":"Royse City","county":"Rockwall","pz":"https://www.roysecity.com/AgendaCenter","cc":"https://www.roysecity.com/AgendaCenter"},
    {"name":"Forney","county":"Kaufman","pz":"https://www.forneytx.gov/AgendaCenter","cc":"https://www.forneytx.gov/AgendaCenter"},
    {"name":"Terrell","county":"Kaufman","pz":"https://www.cityofterrell.com/AgendaCenter","cc":"https://www.cityofterrell.com/AgendaCenter"},
    {"name":"Crandall","county":"Kaufman","pz":"https://www.cityofcrandall.com/AgendaCenter","cc":"https://www.cityofcrandall.com/AgendaCenter"},
    {"name":"Kaufman","county":"Kaufman","pz":"https://www.kaufmantx.org/AgendaCenter","cc":"https://www.kaufmantx.org/AgendaCenter"},
    {"name":"Cleburne","county":"Johnson","pz":"https://www.cleburne.net/AgendaCenter","cc":"https://www.cleburne.net/AgendaCenter"},
    {"name":"Joshua","county":"Johnson","pz":"https://www.cityofjoshua.us/AgendaCenter","cc":"https://www.cityofjoshua.us/AgendaCenter"},
    {"name":"Alvarado","county":"Johnson","pz":"https://www.alvaradotx.gov/AgendaCenter","cc":"https://www.alvaradotx.gov/AgendaCenter"},
    {"name":"Weatherford","county":"Parker","pz":"https://www.weatherfordtx.gov/AgendaCenter","cc":"https://www.weatherfordtx.gov/AgendaCenter"},
    {"name":"Hudson Oaks","county":"Parker","pz":"https://www.hudsonoaks.com/AgendaCenter","cc":"https://www.hudsonoaks.com/AgendaCenter"},
    {"name":"Willow Park","county":"Parker","pz":"https://www.willowpark.org/AgendaCenter","cc":"https://www.willowpark.org/AgendaCenter"},
    {"name":"Aledo","county":"Parker","pz":"https://www.aledotx.gov/AgendaCenter","cc":"https://www.aledotx.gov/AgendaCenter"},
    {"name":"Decatur","county":"Wise","pz":"https://www.decaturtx.org/AgendaCenter","cc":"https://www.decaturtx.org/AgendaCenter"},
    {"name":"Bridgeport","county":"Wise","pz":"https://www.cityofbridgeport.net/AgendaCenter","cc":"https://www.cityofbridgeport.net/AgendaCenter"}
]

def scrape_city(muni):
    data = {'name':muni['name'],'county':muni['county'],'boards':[]}
    for key, bname in [('pz','Planning & Zoning'),('cc','City Council')]:
        url = muni[key]
        print(f"    {bname}...", end=' ', flush=True)
        r = scrape_board(url, muni['name'], bname)
        print(f"{len(r['items'])} items | {r['status']}")
        data['boards'].append(r)
        time.sleep(1)
    return data

def main():
    print(f"DFW Agenda Scraper v6 (3-Level Deep PDF Crawl)")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Scanning {len(MUNICIPALITIES)} cities...\n")
    summaries = []
    ti = 0
    ts = 0
    for i, m in enumerate(MUNICIPALITIES):
        print(f"[{i+1}/{len(MUNICIPALITIES)}] {m['name']} ({m['county']} Co.)")
        cd = scrape_city(m)
        for b in cd['boards']:
            ti += len(b['items'])
            ts += len(b['sfr_items'])
            summaries.append({
                'county':cd['county'],'city':cd['name'],'board':b['board'],
                'meeting_date':b.get('meeting_date',''),
                'agenda_url':b.get('agenda_url',''),
                'items':b['items'],'sfr_items':b['sfr_items'],
                'status':b.get('status','success')
            })
    out = {
        'metadata':{
            'last_updated':datetime.utcnow().isoformat()+'Z',
            'cities_scanned':len(MUNICIPALITIES),
            'total_action_items':ti,
            'total_sfr_items':ts
        },
        'summaries':summaries
    }
    with open('agenda_data.json','w',encoding='utf-8') as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\nDone! Actions: {ti} | SFR: {ts}")
    print(f"Saved to agenda_data.json")

if __name__ == '__main__':
    main()
