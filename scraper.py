 

 

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

    "comprehensive plan amendment","comp plan amendment", 

    "future land use amendment","land use plan amendment", 

    "amend the comprehensive plan","amend the comp plan", 

    "update to the comprehensive plan","change to the comprehensive plan" 

] 

 

NOISE_PATTERNS = [ 

    r"^call to order",r"^roll call",r"^quorum",r"^pledge",r"^invocation", 

    r"^moment of silence",r"^adjournment",r"^adjourn",r"^recess",r"^reconvene", 

    r"^approval of (?:the )?minutes",r"^approve minutes",r"^minutes of", 

    r"^citizen(?:s)?(?:'s)? comment",r"^public comment(?:s)?$", 

    r"^visitor(?:s)?(?:'s)? comment",r"^audience participation",r"^hear visitor", 

    r"^staff report(?:s)?$",r"^city manager(?:'s)? report", 

    r"^mayor(?:'s)? report",r"^council(?:member)?(?:'s)? report", 

    r"^proclamation",r"^presentation(?:s)?$",r"^recognition",r"^award(?:s)?$", 

    r"^consent agenda$",r"^regular agenda$",r"^new business$",r"^old business$", 

    r"^unfinished business$",r"^future agenda",r"^items for future", 

    r"^agenda review",r"^announcements?$",r"^correspondence$", 

    r"^information(?:al)? item",r"^discussion only",r"^no action", 

    r"^sign[- ]?in",r"^attendance",r"^welcome$",r"^introduction(?:s)?$", 

    r"^copyright",r"^privacy",r"^all rights reserved",r"^page \d", 

    r"^city of ",r"^town of ",r"^planning (?:and|&) zoning commission$", 

    r"^city council$",r"^regular (?:session|meeting)$",r"^special (?:session|meeting)$", 

    r"^work session$",r"^workshop$",r"^\d{1,2}[:/]\d{2}", 

    r"^(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)", 

    r"^(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d", 

    r"^www\.",r"^http",r"^tel:",r"^fax:",r"^email:",r"^phone:", 

    r"^executive session",r"^closed session" 

] 

 

NOISE_PHRASES = [ 

    "agenda center tools","rss notify me","search agendas by","time period", 

    "export export","export to excel","export to pdf","export to word", 

    "click the subscriptions","notify me","subscribe","last week last month", 

    "beautiful board","keep.*beautiful","advisory committee","stakeholder", 

    "tax increment","reinvestment zone","TIRZ","board of adjustment", 

    "zoning board of","select the groups","would like to receive", 

    "sign up for notifications","get notified","alert me", 

    "powered by","civicplus","granicus","legistar","municode" 

] 

 

NOISE_COMPILED = [re.compile(p, re.IGNORECASE) for p in NOISE_PATTERNS] 

PHRASE_COMPILED = [re.compile(p, re.IGNORECASE) for p in NOISE_PHRASES] 

 

VOTE_PATTERNS = [ 

    re.compile(r'(approved|denied|tabled|continued|withdrawn|passed|failed)\s*(?:by a vote of\s*)?(\d+\s*[-to]+\s*\d+)?', re.IGNORECASE), 

    re.compile(r'(unanimous(?:ly)?)\s*(approved|passed|denied)?', re.IGNORECASE), 

    re.compile(r'motion\s+carried\s*(\d+\s*[-to]+\s*\d+)?', re.IGNORECASE), 

    re.compile(r'vote:\s*(\d+\s*[-to]+\s*\d+)', re.IGNORECASE), 

    re.compile(r'(\d+-\d+)\s*(?:vote|motion)', re.IGNORECASE), 

] 

 

DATE_PATTERNS = [ 

    re.compile(r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+20\d{2})', re.IGNORECASE), 

    re.compile(r'(\d{1,2}/\d{1,2}/20\d{2})'), 

    re.compile(r'(\d{1,2}-\d{1,2}-20\d{2})'), 

    re.compile(r'(20\d{2}-\d{1,2}-\d{1,2})'), 

    re.compile(r'(20\d{2}/\d{1,2}/\d{1,2})'), 

] 

 

def parse_date_str(raw): 

    for fmt in ['%B %d, %Y','%B %d %Y','%b %d, %Y','%b %d %Y', 

                '%m/%d/%Y','%m-%d-%Y','%Y-%m-%d','%Y/%m/%d']: 

        try: 

            dt = datetime.strptime(raw.strip().replace(',',''), fmt.replace(',','')) 

            return dt.strftime('%Y-%m-%d') 

        except: 

            continue 

    return raw.strip() 

 

def extract_meeting_date(soup, url): 

    for tag in soup.select('title, h1, h2, h3, .meeting-date, .MeetingDate, [class*="date"]'): 

        text = tag.get_text(strip=True) 

        for pat in DATE_PATTERNS: 

            m = pat.search(text) 

            if m: 

                return parse_date_str(m.group(1)) 

    for pat in DATE_PATTERNS: 

        m = pat.search(url) 

        if m: 

            return parse_date_str(m.group(1)) 

    body_text = soup.get_text()[:2000] 

    for pat in DATE_PATTERNS: 

        m = pat.search(body_text) 

        if m: 

            return parse_date_str(m.group(1)) 

    return '' 

 

def is_noise(text): 

    text = text.strip() 

    if len(text) < 20 or len(text) > 1000: 

        return True 

    t = text.lower().strip() 

    for pat in NOISE_COMPILED: 

        if pat.search(t): 

            return True 

    for pat in PHRASE_COMPILED: 

        if pat.search(t): 

            return True 

    if re.match(r'^[\d\s:/.,-]+$', t): 

        return True 

    return False 

 

def is_board_name_only(text): 

    t = text.lower().strip() 

    board_words = ['committee','board','commission','subcommittee','task force'] 

    action_words = ['amend','change','update','request','case','hearing', 

                    'rezone','plat','approve','consider','recommend'] 

    has_board = any(bw in t for bw in board_words) 

    has_action = any(aw in t for aw in action_words) 

    if has_board and not has_action: 

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

 

def find_sfr_keywords(text): 

    t = text.lower() 

    return [kw for kw in SFR_KEYWORDS if kw.lower() in t] 

 

def clean_text(text): 

    text = re.sub(r'\s+', ' ', text).strip() 

    text = re.sub(r'^\d+\.\s*', '', text) 

    text = re.sub(r'^[a-zA-Z]\.\s*', '', text) 

    text = re.sub(r'^[\u2022\u2023\u25e6\u2043\u2219\-\*]\s*', '', text) 

    return text.strip() 

 

def filter_items(raw_items): 

    filtered = [] 

    seen = set() 

    for item in raw_items: 

        item = clean_text(item) 

        if is_noise(item): 

            continue 

        if not is_action_item(item): 

            continue 

        key = item[:80].lower() 

        if key in seen: 

            continue 

        seen.add(key) 

        filtered.append(item) 

    return filtered 

 

def fetch_page(url, timeout=20): 

    try: 

        resp = requests.get(url, headers=HEADERS, timeout=timeout) 

        resp.raise_for_status() 

        return resp 

    except: 

        return None 

 

def extract_items_from_html(soup): 

    items = [] 

    for el in soup.select('li, .AgendaItemTitle, .agenda-item, [class*="agenda"], [class*="item"]'): 

        text = el.get_text(separator=' ', strip=True) 

        if 20 < len(text) < 1000: 

            items.append(text) 

    if len(items) < 3: 

        for el in soup.select('p, td'): 

            text = el.get_text(separator=' ', strip=True) 

            if 25 < len(text) < 800: 

                items.append(text) 

    if len(items) < 3: 

        for el in soup.select('h2, h3, h4, h5, strong, b'): 

            text = el.get_text(separator=' ', strip=True) 

            if 15 < len(text) < 500: 

                items.append(text) 

    return items 

 

def extract_pdf_text(pdf_url): 

    try: 

        import pdfplumber, io 

        resp = requests.get(pdf_url, headers=HEADERS, timeout=30) 

        resp.raise_for_status() 

        if 'pdf' not in resp.headers.get('content-type','').lower() and not pdf_url.lower().endswith('.pdf'): 

            return [] 

        items = [] 

        with pdfplumber.open(io.BytesIO(resp.content)) as pdf: 

            for page in pdf.pages[:15]: 

                text = page.extract_text() 

                if text: 

                    for line in text.split('\n'): 

                        line = line.strip() 

                        if 20 < len(line) < 800: 

                            items.append(line) 

        return items 

    except: 

        return [] 

 

def find_recent_links(soup, base_url, link_type='agenda'): 

    links = [] 

    search_terms = ['agenda','packet'] if link_type == 'agenda' else ['minutes','action','result'] 

    for a in soup.find_all('a', href=True): 

        text = a.get_text(strip=True) 

        href = a['href'] 

        if not href.startswith('http'): 

            href = requests.compat.urljoin(base_url, href) 

        full = text + ' ' + href 

        if any(w in full.lower() for w in search_terms): 

            date_str = '' 

            for pat in DATE_PATTERNS: 

                dm = pat.search(full) 

                if dm: 

                    date_str = parse_date_str(dm.group(1)) 

                    break 

            links.append({'text':text,'url':href,'date_str':date_str,'is_pdf':href.lower().endswith('.pdf')}) 

    links.sort(key=lambda x: x['date_str'], reverse=True) 

    return links[:5] 

 

def find_votes_in_minutes(minutes_items, action_items): 

    decisions = {} 

    minutes_text = ' '.join(minutes_items).lower() 

    for item in action_items: 

        search_words = [w for w in item.lower().split() if len(w) > 4][:5] 

        nearby_text = '' 

        for mitem in minutes_items: 

            mlow = mitem.lower() 

            if any(w in mlow for w in search_words[:3]): 

                nearby_text += ' ' + mitem 

        if not nearby_text: 

            nearby_text = minutes_text 

        for vpat in VOTE_PATTERNS: 

            vm = vpat.search(nearby_text) 

            if vm: 

                groups = [g for g in vm.groups() if g] 

                decision = ' '.join(groups).upper().strip() 

                if decision: 

                    decisions[item] = decision 

                    break 

    return decisions 

 

def scrape_board(url, city_name, board_name): 

    result = {'board':board_name,'agenda_url':url,'meeting_date':'', 

              'items':[],'sfr_items':[],'status':'success'} 

    resp = fetch_page(url) 

    if not resp: 

        result['status'] = 'error: could not reach site' 

        return result 

    soup = BeautifulSoup(resp.text, 'lxml') 

    candidates = find_recent_links(soup, url, 'agenda') 

    raw_items = [] 

    best_date = '' 

    best_url = url 

    for cand in candidates[:3]: 

        if cand['is_pdf']: 

            pdf_items = extract_pdf_text(cand['url']) 

            if pdf_items: 

                raw_items = pdf_items 

                best_date = cand['date_str'] 

                best_url = cand['url'] 

                break 

        else: 

            sub = fetch_page(cand['url']) 

            if sub: 

                sub_soup = BeautifulSoup(sub.text, 'lxml') 

                html_items = extract_items_from_html(sub_soup) 

                if len(html_items) > len(raw_items): 

                    raw_items = html_items 

                    best_date = cand['date_str'] 

                    best_url = cand['url'] 

                    if not best_date: 

                        best_date = extract_meeting_date(sub_soup, cand['url']) 

        time.sleep(0.5) 

    if not raw_items: 

        raw_items = extract_items_from_html(soup) 

    if not best_date: 

        best_date = extract_meeting_date(soup, url) 

    action_items = filter_items(raw_items) 

    minutes_links = find_recent_links(soup, url, 'minutes') 

    decisions = {} 

    for mlink in minutes_links[:2]: 

        try: 

            if mlink['is_pdf']: 

                m_items = extract_pdf_text(mlink['url']) 

            else: 

                m_resp = fetch_page(mlink['url']) 

                if m_resp: 

                    m_soup = BeautifulSoup(m_resp.text, 'lxml') 

                    m_items = extract_items_from_html(m_soup) 

                else: 

                    m_items = [] 

            if m_items: 

                decisions = find_votes_in_minutes(m_items, action_items) 

                if decisions: 

                    break 

            time.sleep(0.5) 

        except: 

            pass 

    final_items = [] 

    for item in action_items: 

        if item in decisions: 

            final_items.append(item + ' [' + decisions[item] + ']') 

        else: 

            final_items.append(item) 

    result['items'] = final_items 

    result['meeting_date'] = best_date 

    result['agenda_url'] = best_url 

    for item in final_items: 

        matches = find_sfr_keywords(item) 

        if matches: 

            result['sfr_items'].append(item + ' [Keywords: ' + ', '.join(matches[:5]) + ']') 

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

    city_data = {'name':muni['name'],'county':muni['county'],'boards':[]} 

    for key, board_name in [('pz','Planning & Zoning'),('cc','City Council')]: 

        url = muni[key] 

        print(f"    {board_name}...", end=' ', flush=True) 

        try: 

            result = scrape_board(url, muni['name'], board_name) 

            print(f"{len(result['items'])} items, {len(result['sfr_items'])} SFR") 

        except Exception as e: 

            result = {'board':board_name,'agenda_url':url,'meeting_date':'','items':[],'sfr_items':[],'status':'error: '+str(e)[:100]} 

            print(f"ERROR: {str(e)[:60]}") 

        city_data['boards'].append(result) 

        time.sleep(1) 

    return city_data 

 

def main(): 

    print(f"DFW Agenda Scraper v5 (Rezone | Plats | Comp Plan Amendments + Votes)") 

    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M')}") 

    print(f"Scanning {len(MUNICIPALITIES)} cities...\n") 

    all_summaries = [] 

    total_items = 0 

    total_sfr = 0 

    for i, muni in enumerate(MUNICIPALITIES): 

        print(f"[{i+1}/{len(MUNICIPALITIES)}] {muni['name']} ({muni['county']} Co.)") 

        city_data = scrape_city(muni) 

        for board in city_data['boards']: 

            total_items += len(board['items']) 

            total_sfr += len(board['sfr_items']) 

            all_summaries.append({ 

                'county':city_data['county'], 

                'city':city_data['name'], 

                'board':board['board'], 

                'meeting_date':board.get('meeting_date',''), 

                'agenda_url':board.get('agenda_url',''), 

                'items':board['items'], 

                'sfr_items':board['sfr_items'], 

                'status':board.get('status','success') 

            }) 

    output = { 

        'metadata': { 

            'last_updated': datetime.utcnow().isoformat() + 'Z', 

            'cities_scanned': len(MUNICIPALITIES), 

            'total_action_items': total_items, 

            'total_sfr_items': total_sfr 

        }, 

        'summaries': all_summaries 

    } 

    with open('agenda_data.json', 'w', encoding='utf-8') as f: 

        json.dump(output, f, indent=2, ensure_ascii=False) 

    print(f"\nDone!") 

    print(f"Action items found: {total_items}") 

    print(f"SFR-relevant items: {total_sfr}") 

    print(f"Saved to agenda_data.json") 

 

if __name__ == '__main__': 

    main() 

 
