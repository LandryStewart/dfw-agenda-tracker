import requests
from bs4 import BeautifulSoup
import json
import re
import time
from datetime import datetime
import traceback

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}

KEYWORDS = [
    "single family","single-family","residential","zoning change","rezoning",
    "plat","preliminary plat","final plat","replat","subdivision",
    "planned development","PD district","specific use permit","SUP",
    "dwelling","detached","annexation","comprehensive plan","land use",
    "density","R-1","R-2","R-3","development agreement","impact fee",
    "site plan","variance","lot","SFR","SF-","housing","zone change",
    "zoning case","home","acre","unit"
]

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

# ============================================================
# EXTRACTION FUNCTIONS
# ============================================================

def fetch_page(url, timeout=20):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        return resp
    except Exception as e:
        return None

def find_keyword_matches(text):
    text_lower = text.lower()
    return [kw for kw in KEYWORDS if kw.lower() in text_lower]

def clean_text(text):
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'^\d+\.\s*', '', text)
    return text

def extract_agenda_items_from_html(soup):
    items = []
    # Strategy 1: Look for numbered/lettered list items in agenda structure
    for el in soup.select('li, .AgendaItemTitle, .agenda-item, [class*="agenda"], [class*="item"]'):
        text = clean_text(el.get_text(separator=' ', strip=True))
        if len(text) > 20 and len(text) < 1000:
            items.append(text)
    # Strategy 2: Look for <p> and <td> with substantial text
    if len(items) < 3:
        for el in soup.select('p, td'):
            text = clean_text(el.get_text(separator=' ', strip=True))
            if len(text) > 30 and len(text) < 800:
                skip_words = ['copyright','privacy','click here','sign up','subscribe','footer','navigation']
                if not any(sw in text.lower() for sw in skip_words):
                    items.append(text)
    # Strategy 3: Look for heading + paragraph patterns
    if len(items) < 3:
        for el in soup.select('h2, h3, h4, h5, strong, b'):
            text = clean_text(el.get_text(separator=' ', strip=True))
            if len(text) > 15 and len(text) < 500:
                items.append(text)
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for item in items:
        key = item[:80].lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique[:50]  # Cap at 50 items

def extract_pdf_text(pdf_url):
    try:
        import pdfplumber
        import io
        resp = requests.get(pdf_url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        if 'pdf' not in resp.headers.get('content-type','').lower() and not pdf_url.lower().endswith('.pdf'):
            return []
        pdf_bytes = io.BytesIO(resp.content)
        items = []
        with pdfplumber.open(pdf_bytes) as pdf:
            for page in pdf.pages[:15]:  # First 15 pages max
                text = page.extract_text()
                if text:
                    lines = text.split('\n')
                    for line in lines:
                        line = clean_text(line)
                        if len(line) > 25 and len(line) < 800:
                            items.append(line)
        seen = set()
        unique = []
        for item in items:
            key = item[:80].lower()
            if key not in seen:
                seen.add(key)
                unique.append(item)
        return unique[:60]
    except Exception as e:
        return []

def find_most_recent_agenda_link(soup, base_url, board_hint=""):
    agenda_links = []
    date_pattern = re.compile(r'(20\d{2}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]20\d{2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+20\d{2})', re.IGNORECASE)
    for a in soup.find_all('a', href=True):
        text = a.get_text(strip=True)
        href = a['href']
        if not href.startswith('http'):
            href = requests.compat.urljoin(base_url, href)
        full_text = text + ' ' + href
        # Look for agenda-related links
        agenda_words = ['agenda','packet','meeting','minute']
        if any(w in full_text.lower() for w in agenda_words):
            date_match = date_pattern.search(full_text)
            date_str = date_match.group(0) if date_match else ''
            agenda_links.append({'text': text, 'url': href, 'date_str': date_str, 'is_pdf': href.lower().endswith('.pdf')})
    # Sort: prioritize ones with dates, then most recent
    agenda_links.sort(key=lambda x: x['date_str'], reverse=True)
    return agenda_links[:5]  # Return top 5 candidates

def scrape_civicplus(url, city_name, board_name):
    result = {
        'board': board_name,
        'agenda_url': url,
        'meeting_date': '',
        'items': [],
        'sfr_items': [],
        'status': 'success'
    }
    resp = fetch_page(url)
    if not resp:
        result['status'] = 'error: could not reach site'
        return result
    soup = BeautifulSoup(resp.text, 'lxml')
    # Find most recent agenda links
    candidates = find_most_recent_agenda_link(soup, url, board_name)
    all_items = []
    best_date = ''
    best_url = url
    for cand in candidates[:3]:  # Try top 3
        if cand['is_pdf']:
            pdf_items = extract_pdf_text(cand['url'])
            if pdf_items:
                all_items = pdf_items
                best_date = cand['date_str']
                best_url = cand['url']
                break
        else:
            sub_resp = fetch_page(cand['url'])
            if sub_resp:
                sub_soup = BeautifulSoup(sub_resp.text, 'lxml')
                html_items = extract_agenda_items_from_html(sub_soup)
                if len(html_items) > len(all_items):
                    all_items = html_items
                    best_date = cand['date_str']
                    best_url = cand['url']
        time.sleep(0.5)
    # If no sub-pages worked, try main page
    if not all_items:
        all_items = extract_agenda_items_from_html(soup)
    result['items'] = all_items
    result['meeting_date'] = best_date
    result['agenda_url'] = best_url
    # Filter for SFR items
    for item in all_items:
        matches = find_keyword_matches(item)
        if matches:
            result['sfr_items'].append(item + ' [Keywords: ' + ', '.join(matches[:5]) + ']')
    return result

def scrape_generic(url, city_name, board_name):
    result = {
        'board': board_name,
        'agenda_url': url,
        'meeting_date': '',
        'items': [],
        'sfr_items': [],
        'status': 'success'
    }
    resp = fetch_page(url)
    if not resp:
        result['status'] = 'error: could not reach site'
        return result
    soup = BeautifulSoup(resp.text, 'lxml')
    candidates = find_most_recent_agenda_link(soup, url, board_name)
    all_items = []
    best_date = ''
    best_url = url
    for cand in candidates[:3]:
        if cand['is_pdf']:
            pdf_items = extract_pdf_text(cand['url'])
            if pdf_items:
                all_items = pdf_items
                best_date = cand['date_str']
                best_url = cand['url']
                break
        else:
            sub_resp = fetch_page(cand['url'])
            if sub_resp:
                sub_soup = BeautifulSoup(sub_resp.text, 'lxml')
                html_items = extract_agenda_items_from_html(sub_soup)
                if len(html_items) > len(all_items):
                    all_items = html_items
                    best_date = cand['date_str']
                    best_url = cand['url']
        time.sleep(0.5)
    if not all_items:
        all_items = extract_agenda_items_from_html(soup)
    result['items'] = all_items
    result['meeting_date'] = best_date
    result['agenda_url'] = best_url
    for item in all_items:
        matches = find_keyword_matches(item)
        if matches:
            result['sfr_items'].append(item + ' [Keywords: ' + ', '.join(matches[:5]) + ']')
    return result

def scrape_city(muni):
    city_data = {
        'name': muni['name'],
        'county': muni['county'],
        'boards': []
    }
    for key, board_name in [('pz', 'Planning & Zoning'), ('cc', 'City Council')]:
        url = muni[key]
        print(f"    {board_name}...", end=' ', flush=True)
        try:
            if '/AgendaCenter' in url:
                result = scrape_civicplus(url, muni['name'], board_name)
            else:
                result = scrape_generic(url, muni['name'], board_name)
            print(f"{len(result['items'])} items, {len(result['sfr_items'])} SFR")
        except Exception as e:
            result = {
                'board': board_name,
                'agenda_url': url,
                'meeting_date': '',
                'items': [],
                'sfr_items': [],
                'status': 'error: ' + str(e)[:100]
            }
            print(f"ERROR: {str(e)[:60]}")
        city_data['boards'].append(result)
        time.sleep(1)
    return city_data

# ============================================================
# MAIN
# ============================================================
def main():
    print(f"DFW Agenda Summary Scraper")
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
                'county': city_data['county'],
                'city': city_data['name'],
                'board': board['board'],
                'meeting_date': board.get('meeting_date', ''),
                'agenda_url': board.get('agenda_url', ''),
                'items': board['items'],
                'sfr_items': board['sfr_items'],
                'status': board.get('status', 'success')
            })

    output = {
        'metadata': {
            'last_updated': datetime.utcnow().isoformat() + 'Z',
            'cities_scanned': len(MUNICIPALITIES),
            'total_agenda_items': total_items,
            'total_sfr_items': total_sfr
        },
        'summaries': all_summaries
    }

    with open('agenda_data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nDone!")
    print(f"Total agenda items found: {total_items}")
    print(f"Total SFR-relevant items: {total_sfr}")
    print(f"Saved to agenda_data.json")

if __name__ == '__main__':
    main()
