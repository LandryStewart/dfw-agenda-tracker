import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta
import time
import traceback

# ============================================================
# SFR KEYWORDS TO SEARCH FOR
# ============================================================
KEYWORDS = [
    "single family", "residential", "zoning change", "rezoning",
    "plat", "preliminary plat", "final plat", "replat",
    "subdivision", "planned development", "PD district",
    "specific use permit", "SUP", "dwelling",
    "detached", "annexation", "comprehensive plan",
    "land use", "density", "R-1", "R-2", "R-3",
    "development agreement", "impact fee", "site plan",
    "variance", "lot", "SFR", "SF-", "housing",
    "zoning case", "zone change"
]

# ============================================================
# MUNICIPALITIES DATABASE
# ============================================================
MUNICIPALITIES = [
    # TARRANT COUNTY
    {"name": "Arlington", "county": "Tarrant",
     "pz": "https://www.arlingtontx.gov/city_hall/boards_and_commissions/planning_and_zoning_commission",
     "cc": "https://www.arlingtontx.gov/city_hall/government/city_council/city_council_meetings"},
    {"name": "Fort Worth", "county": "Tarrant",
     "pz": "https://fortworthtexas.legistar.com/Calendar.aspx",
     "cc": "https://fortworthtexas.legistar.com/Calendar.aspx",
     "type": "legistar"},
    {"name": "Mansfield", "county": "Tarrant",
     "pz": "https://www.mansfieldtexas.gov/925/Planning-Zoning-Commission",
     "cc": "https://www.mansfieldtexas.gov/AgendaCenter"},
    {"name": "Keller", "county": "Tarrant",
     "pz": "https://www.cityofkeller.com/services/development-services/planning-zoning",
     "cc": "https://www.cityofkeller.com/government/city-council/agendas-minutes"},
    {"name": "Southlake", "county": "Tarrant",
     "pz": "https://www.cityofsouthlake.com/AgendaCenter",
     "cc": "https://www.cityofsouthlake.com/AgendaCenter"},
    {"name": "Colleyville", "county": "Tarrant",
     "pz": "https://www.colleyville.com/government/boards-commissions/planning-zoning-commission",
     "cc": "https://www.colleyville.com/government/city-council/agendas-minutes"},
    {"name": "Grapevine", "county": "Tarrant",
     "pz": "https://www.grapevinetexas.gov/AgendaCenter",
     "cc": "https://www.grapevinetexas.gov/AgendaCenter"},
    {"name": "Bedford", "county": "Tarrant",
     "pz": "https://www.bedfordtx.gov/AgendaCenter",
     "cc": "https://www.bedfordtx.gov/AgendaCenter"},
    {"name": "Euless", "county": "Tarrant",
     "pz": "https://www.eulesstx.gov/city-government/boards-commissions/planning-zoning-commission",
     "cc": "https://www.eulesstx.gov/city-government/city-council/agendas-minutes"},
    {"name": "Hurst", "county": "Tarrant",
     "pz": "https://www.hursttx.gov/government/boards-commissions/planning-zoning-commission",
     "cc": "https://www.hursttx.gov/government/city-council/agendas-minutes"},
    {"name": "North Richland Hills", "county": "Tarrant",
     "pz": "https://www.nrhtx.com/AgendaCenter",
     "cc": "https://www.nrhtx.com/AgendaCenter"},
    {"name": "Burleson", "county": "Tarrant",
     "pz": "https://www.burlesontx.com/AgendaCenter",
     "cc": "https://www.burlesontx.com/AgendaCenter"},
    {"name": "Saginaw", "county": "Tarrant",
     "pz": "https://www.ci.saginaw.tx.us/AgendaCenter",
     "cc": "https://www.ci.saginaw.tx.us/AgendaCenter"},
    {"name": "Benbrook", "county": "Tarrant",
     "pz": "https://www.benbrook-tx.gov/AgendaCenter",
     "cc": "https://www.benbrook-tx.gov/AgendaCenter"},
    {"name": "Crowley", "county": "Tarrant",
     "pz": "https://www.ci.crowley.tx.us/AgendaCenter",
     "cc": "https://www.ci.crowley.tx.us/AgendaCenter"},
    {"name": "Watauga", "county": "Tarrant",
     "pz": "https://www.cowtx.gov/AgendaCenter",
     "cc": "https://www.cowtx.gov/AgendaCenter"},
    {"name": "Kennedale", "county": "Tarrant",
     "pz": "https://www.kennedale.com/AgendaCenter",
     "cc": "https://www.kennedale.com/AgendaCenter"},
    {"name": "Azle", "county": "Tarrant",
     "pz": "https://www.cityofazle.com/AgendaCenter",
     "cc": "https://www.cityofazle.com/AgendaCenter"},
    {"name": "Haslet", "county": "Tarrant",
     "pz": "https://www.haslet.org/AgendaCenter",
     "cc": "https://www.haslet.org/AgendaCenter"},
    {"name": "Trophy Club", "county": "Tarrant",
     "pz": "https://www.trophyclub.org/AgendaCenter",
     "cc": "https://www.trophyclub.org/AgendaCenter"},

    # DALLAS COUNTY
    {"name": "Dallas", "county": "Dallas",
     "pz": "https://dallascityhall.com/government/cityplan/Pages/default.aspx",
     "cc": "https://dallascityhall.com/government/citycouncil/Pages/city-council-agendas.aspx",
     "type": "custom"},
    {"name": "Irving", "county": "Dallas",
     "pz": "https://www.cityofirving.org/AgendaCenter",
     "cc": "https://www.cityofirving.org/AgendaCenter"},
    {"name": "Grand Prairie", "county": "Dallas",
     "pz": "https://www.gptx.org/AgendaCenter",
     "cc": "https://www.gptx.org/AgendaCenter"},
    {"name": "Garland", "county": "Dallas",
     "pz": "https://www.garlandtx.gov/AgendaCenter",
     "cc": "https://www.garlandtx.gov/AgendaCenter"},
    {"name": "Mesquite", "county": "Dallas",
     "pz": "https://www.cityofmesquite.com/AgendaCenter",
     "cc": "https://www.cityofmesquite.com/AgendaCenter"},
    {"name": "Richardson", "county": "Dallas",
     "pz": "https://www.cor.net/government/boards-and-commissions/plan-commission",
     "cc": "https://www.cor.net/government/city-council/agendas-and-minutes"},
    {"name": "Carrollton", "county": "Dallas",
     "pz": "https://www.cityofcarrollton.com/government/boards-commissions/planning-zoning-commission",
     "cc": "https://www.cityofcarrollton.com/government/city-council/agendas-minutes"},
    {"name": "Farmers Branch", "county": "Dallas",
     "pz": "https://www.farmersbranchtx.gov/AgendaCenter",
     "cc": "https://www.farmersbranchtx.gov/AgendaCenter"},
    {"name": "DeSoto", "county": "Dallas",
     "pz": "https://www.ci.desoto.tx.us/AgendaCenter",
     "cc": "https://www.ci.desoto.tx.us/AgendaCenter"},
    {"name": "Cedar Hill", "county": "Dallas",
     "pz": "https://www.cedarhilltx.com/AgendaCenter",
     "cc": "https://www.cedarhilltx.com/AgendaCenter"},
    {"name": "Lancaster", "county": "Dallas",
     "pz": "https://www.lancaster-tx.com/AgendaCenter",
     "cc": "https://www.lancaster-tx.com/AgendaCenter"},
    {"name": "Duncanville", "county": "Dallas",
     "pz": "https://www.duncanville.com/AgendaCenter",
     "cc": "https://www.duncanville.com/AgendaCenter"},
    {"name": "Rowlett", "county": "Dallas",
     "pz": "https://www.ci.rowlett.tx.us/AgendaCenter",
     "cc": "https://www.ci.rowlett.tx.us/AgendaCenter"},
    {"name": "Seagoville", "county": "Dallas",
     "pz": "https://www.seagoville.us/AgendaCenter",
     "cc": "https://www.seagoville.us/AgendaCenter"},
    {"name": "Balch Springs", "county": "Dallas",
     "pz": "https://www.cityofbalchsprings.com/AgendaCenter",
     "cc": "https://www.cityofbalchsprings.com/AgendaCenter"},

    # COLLIN COUNTY
    {"name": "Plano", "county": "Collin",
     "pz": "https://www.plano.gov/AgendaCenter",
     "cc": "https://www.plano.gov/AgendaCenter"},
    {"name": "McKinney", "county": "Collin",
     "pz": "https://www.mckinneytexas.org/AgendaCenter",
     "cc": "https://www.mckinneytexas.org/AgendaCenter"},
    {"name": "Frisco", "county": "Collin",
     "pz": "https://www.friscotexas.gov/AgendaCenter",
     "cc": "https://www.friscotexas.gov/AgendaCenter"},
    {"name": "Allen", "county": "Collin",
     "pz": "https://www.cityofallen.org/AgendaCenter",
     "cc": "https://www.cityofallen.org/AgendaCenter"},
    {"name": "Wylie", "county": "Collin",
     "pz": "https://www.wylietexas.gov/AgendaCenter",
     "cc": "https://www.wylietexas.gov/AgendaCenter"},
    {"name": "Anna", "county": "Collin",
     "pz": "https://www.annatexas.gov/AgendaCenter",
     "cc": "https://www.annatexas.gov/AgendaCenter"},
    {"name": "Celina", "county": "Collin",
     "pz": "https://www.celina-tx.gov/AgendaCenter",
     "cc": "https://www.celina-tx.gov/AgendaCenter"},
    {"name": "Prosper", "county": "Collin",
     "pz": "https://www.prospertx.gov/AgendaCenter",
     "cc": "https://www.prospertx.gov/AgendaCenter"},
    {"name": "Princeton", "county": "Collin",
     "pz": "https://www.princetontx.gov/AgendaCenter",
     "cc": "https://www.princetontx.gov/AgendaCenter"},
    {"name": "Melissa", "county": "Collin",
     "pz": "https://www.melissatx.gov/AgendaCenter",
     "cc": "https://www.melissatx.gov/AgendaCenter"},
    {"name": "Sachse", "county": "Collin",
     "pz": "https://www.cityofsachse.com/AgendaCenter",
     "cc": "https://www.cityofsachse.com/AgendaCenter"},
    {"name": "Lucas", "county": "Collin",
     "pz": "https://www.lucastexas.us/AgendaCenter",
     "cc": "https://www.lucastexas.us/AgendaCenter"},
    {"name": "Farmersville", "county": "Collin",
     "pz": "https://www.farmersvilletx.com/AgendaCenter",
     "cc": "https://www.farmersvilletx.com/AgendaCenter"},

    # DENTON COUNTY
    {"name": "Denton", "county": "Denton",
     "pz": "https://www.cityofdenton.com/AgendaCenter",
     "cc": "https://www.cityofdenton.com/AgendaCenter"},
    {"name": "Lewisville", "county": "Denton",
     "pz": "https://www.cityoflewisville.com/government/boards-commissions/planning-zoning-commission",
     "cc": "https://www.cityoflewisville.com/government/city-council/agendas-minutes"},
    {"name": "Flower Mound", "county": "Denton",
     "pz": "https://www.flower-mound.com/AgendaCenter",
     "cc": "https://www.flower-mound.com/AgendaCenter"},
    {"name": "Little Elm", "county": "Denton",
     "pz": "https://www.littleelm.org/AgendaCenter",
     "cc": "https://www.littleelm.org/AgendaCenter"},
    {"name": "Corinth", "county": "Denton",
     "pz": "https://www.cityofcorinth.com/AgendaCenter",
     "cc": "https://www.cityofcorinth.com/AgendaCenter"},
    {"name": "The Colony", "county": "Denton",
     "pz": "https://www.thecolonytx.gov/AgendaCenter",
     "cc": "https://www.thecolonytx.gov/AgendaCenter"},
    {"name": "Argyle", "county": "Denton",
     "pz": "https://www.argyletx.com/AgendaCenter",
     "cc": "https://www.argyletx.com/AgendaCenter"},
    {"name": "Aubrey", "county": "Denton",
     "pz": "https://www.aubreytx.gov/AgendaCenter",
     "cc": "https://www.aubreytx.gov/AgendaCenter"},
    {"name": "Sanger", "county": "Denton",
     "pz": "https://www.sangertexas.org/AgendaCenter",
     "cc": "https://www.sangertexas.org/AgendaCenter"},
    {"name": "Pilot Point", "county": "Denton",
     "pz": "https://www.cityofpilotpoint.org/AgendaCenter",
     "cc": "https://www.cityofpilotpoint.org/AgendaCenter"},
    {"name": "Northlake", "county": "Denton",
     "pz": "https://www.northlaketx.org/AgendaCenter",
     "cc": "https://www.northlaketx.org/AgendaCenter"},
    {"name": "Justin", "county": "Denton",
     "pz": "https://www.cityofjustin.com/AgendaCenter",
     "cc": "https://www.cityofjustin.com/AgendaCenter"},
    {"name": "Roanoke", "county": "Denton",
     "pz": "https://www.roanoketexas.com/AgendaCenter",
     "cc": "https://www.roanoketexas.com/AgendaCenter"},
    {"name": "Cross Roads", "county": "Denton",
     "pz": "https://www.crossroadstx.gov/AgendaCenter",
     "cc": "https://www.crossroadstx.gov/AgendaCenter"},
    {"name": "Oak Point", "county": "Denton",
     "pz": "https://www.oakpointtexas.com/AgendaCenter",
     "cc": "https://www.oakpointtexas.com/AgendaCenter"},

    # ELLIS COUNTY
    {"name": "Waxahachie", "county": "Ellis",
     "pz": "https://www.waxahachie.com/AgendaCenter",
     "cc": "https://www.waxahachie.com/AgendaCenter"},
    {"name": "Midlothian", "county": "Ellis",
     "pz": "https://www.midlothian.tx.us/AgendaCenter",
     "cc": "https://www.midlothian.tx.us/AgendaCenter"},
    {"name": "Ennis", "county": "Ellis",
     "pz": "https://www.ennis-texas.com/AgendaCenter",
     "cc": "https://www.ennis-texas.com/AgendaCenter"},
    {"name": "Red Oak", "county": "Ellis",
     "pz": "https://www.redoaktx.org/AgendaCenter",
     "cc": "https://www.redoaktx.org/AgendaCenter"},

    # ROCKWALL COUNTY
    {"name": "Rockwall", "county": "Rockwall",
     "pz": "https://www.rockwall.com/AgendaCenter",
     "cc": "https://www.rockwall.com/AgendaCenter"},
    {"name": "Heath", "county": "Rockwall",
     "pz": "https://www.heathtx.com/AgendaCenter",
     "cc": "https://www.heathtx.com/AgendaCenter"},
    {"name": "Fate", "county": "Rockwall",
     "pz": "https://www.fatetx.gov/AgendaCenter",
     "cc": "https://www.fatetx.gov/AgendaCenter"},
    {"name": "Royse City", "county": "Rockwall",
     "pz": "https://www.roysecity.com/AgendaCenter",
     "cc": "https://www.roysecity.com/AgendaCenter"},

    # KAUFMAN COUNTY
    {"name": "Forney", "county": "Kaufman",
     "pz": "https://www.forneytx.gov/AgendaCenter",
     "cc": "https://www.forneytx.gov/AgendaCenter"},
    {"name": "Terrell", "county": "Kaufman",
     "pz": "https://www.cityofterrell.com/AgendaCenter",
     "cc": "https://www.cityofterrell.com/AgendaCenter"},
    {"name": "Crandall", "county": "Kaufman",
     "pz": "https://www.cityofcrandall.com/AgendaCenter",
     "cc": "https://www.cityofcrandall.com/AgendaCenter"},
    {"name": "Kaufman", "county": "Kaufman",
     "pz": "https://www.kaufmantx.org/AgendaCenter",
     "cc": "https://www.kaufmantx.org/AgendaCenter"},

    # JOHNSON COUNTY
    {"name": "Cleburne", "county": "Johnson",
     "pz": "https://www.cleburne.net/AgendaCenter",
     "cc": "https://www.cleburne.net/AgendaCenter"},
    {"name": "Joshua", "county": "Johnson",
     "pz": "https://www.cityofjoshua.us/AgendaCenter",
     "cc": "https://www.cityofjoshua.us/AgendaCenter"},
    {"name": "Alvarado", "county": "Johnson",
     "pz": "https://www.alvaradotx.gov/AgendaCenter",
     "cc": "https://www.alvaradotx.gov/AgendaCenter"},

    # PARKER COUNTY
    {"name": "Weatherford", "county": "Parker",
     "pz": "https://www.weatherfordtx.gov/AgendaCenter",
     "cc": "https://www.weatherfordtx.gov/AgendaCenter"},
    {"name": "Hudson Oaks", "county": "Parker",
     "pz": "https://www.hudsonoaks.com/AgendaCenter",
     "cc": "https://www.hudsonoaks.com/AgendaCenter"},
    {"name": "Willow Park", "county": "Parker",
     "pz": "https://www.willowpark.org/AgendaCenter",
     "cc": "https://www.willowpark.org/AgendaCenter"},
    {"name": "Aledo", "county": "Parker",
     "pz": "https://www.aledotx.gov/AgendaCenter",
     "cc": "https://www.aledotx.gov/AgendaCenter"},

    # WISE COUNTY
    {"name": "Decatur", "county": "Wise",
     "pz": "https://www.decaturtx.org/AgendaCenter",
     "cc": "https://www.decaturtx.org/AgendaCenter"},
    {"name": "Bridgeport", "county": "Wise",
     "pz": "https://www.cityofbridgeport.net/AgendaCenter",
     "cc": "https://www.cityofbridgeport.net/AgendaCenter"},
]


# ============================================================
# SCRAPING FUNCTIONS
# ============================================================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}


def keyword_match(text):
    text_lower = text.lower()
    return [kw for kw in KEYWORDS if kw.lower() in text_lower]


def extract_snippets(text, matched_keywords, context_chars=120):
    snippets = []
    text_lower = text.lower()
    seen = set()
    for kw in matched_keywords[:5]:
        idx = text_lower.find(kw.lower())
        if idx != -1:
            start = max(0, idx - context_chars)
            end = min(len(text), idx + len(kw) + context_chars)
            snippet = "..." + text[start:end].strip() + "..."
            snippet_key = snippet[:50]
            if snippet_key not in seen:
                seen.add(snippet_key)
                snippets.append(snippet)
    return snippets


def scrape_civicplus(url, city_name, agenda_type):
    results = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        agenda_links = []

        for row in soup.select("tr, .AgendaRow, .catAgendaRow"):
            text = row.get_text(separator=" ", strip=True)
            link_el = row.find("a", href=True)
            if link_el:
                href = link_el["href"]
                if not href.startswith("http"):
                    href = requests.compat.urljoin(url, href)
                agenda_links.append({"text": text, "url": href})

        for a_tag in soup.find_all("a", href=True):
            link_text = a_tag.get_text(strip=True)
            href = a_tag["href"]
            full_text = link_text + " " + href
            if any(term in full_text.lower() for term in
                   ["agenda", "packet", "minute", "planning", "zoning",
                    "council", "commission"]):
                if not href.startswith("http"):
                    href = requests.compat.urljoin(url, href)
                agenda_links.append({"text": link_text, "url": href})

        seen_urls = set()
        unique_links = []
        for item in agenda_links:
            if item["url"] not in seen_urls:
                seen_urls.add(item["url"])
                unique_links.append(item)

        for item in unique_links:
            matches = keyword_match(item["text"])
            if matches:
                results.append({
                    "title": item["text"][:300],
                    "url": item["url"],
                    "keywords_matched": matches,
                    "source_type": agenda_type
                })

        for item in unique_links[:10]:
            if any(ext in item["url"].lower() for ext in [".pdf", ".doc", ".xlsx"]):
                continue
            try:
                sub_resp = requests.get(item["url"], headers=HEADERS, timeout=15)
                if sub_resp.status_code == 200:
                    sub_soup = BeautifulSoup(sub_resp.text, "lxml")
                    page_text = sub_soup.get_text(separator=" ", strip=True)
                    matches = keyword_match(page_text)
                    if matches:
                        snippets = extract_snippets(page_text, matches)
                        results.append({
                            "title": item["text"][:200] or "Agenda Page",
                            "url": item["url"],
                            "keywords_matched": list(set(matches)),
                            "snippets": snippets[:5],
                            "source_type": agenda_type
                        })
                time.sleep(0.5)
            except Exception:
                continue

    except Exception as e:
        results.append({
            "title": f"[Scrape Error] {city_name}",
            "url": url,
            "keywords_matched": [],
            "error": str(e),
            "source_type": agenda_type
        })
    return results


def scrape_legistar(url, city_name, agenda_type):
    results = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        for row in soup.select("tr"):
            text = row.get_text(separator=" ", strip=True)
            matches = keyword_match(text)
            if matches:
                link = row.find("a", href=True)
                href = link["href"] if link else url
                if not href.startswith("http"):
                    href = requests.compat.urljoin(url, href)
                results.append({
                    "title": text[:300],
                    "url": href,
                    "keywords_matched": matches,
                    "source_type": agenda_type
                })
    except Exception as e:
        results.append({
            "title": f"[Scrape Error] {city_name}",
            "url": url,
            "keywords_matched": [],
            "error": str(e),
            "source_type": agenda_type
        })
    return results


def scrape_generic(url, city_name, agenda_type):
    results = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        for a_tag in soup.find_all("a", href=True):
            text = a_tag.get_text(strip=True)
            href = a_tag["href"]
            if not href.startswith("http"):
                href = requests.compat.urljoin(url, href)
            combined = text + " " + (a_tag.get("title", ""))
            matches = keyword_match(combined)
            if matches:
                results.append({
                    "title": text[:300],
                    "url": href,
                    "keywords_matched": matches,
                    "source_type": agenda_type
                })

        page_text = soup.get_text(separator=" ", strip=True)
        page_matches = keyword_match(page_text)
        if page_matches and not results:
            snippets = extract_snippets(page_text, page_matches)
            results.append({
                "title": f"{city_name} {agenda_type} Page",
                "url": url,
                "keywords_matched": list(set(page_matches)),
                "snippets": snippets[:5],
                "source_type": agenda_type
            })

    except Exception as e:
        results.append({
            "title": f"[Scrape Error] {city_name}",
            "url": url,
            "keywords_matched": [],
            "error": str(e),
            "source_type": agenda_type
        })
    return results


def scrape_municipality(muni):
    city_results = {
        "name": muni["name"],
        "county": muni["county"],
        "pz_url": muni["pz"],
        "cc_url": muni["cc"],
        "pz_items": [],
        "cc_items": [],
        "scrape_status": "success",
        "last_scraped": datetime.utcnow().isoformat() + "Z"
    }

    site_type = muni.get("type", "")

    for agenda_key, agenda_label in [("pz", "P&Z"), ("cc", "City Council")]:
        url = muni[agenda_key]
        try:
            if site_type == "legistar" or "legistar.com" in url:
                items = scrape_legistar(url, muni["name"], agenda_label)
            elif "/AgendaCenter" in url:
                items = scrape_civicplus(url, muni["name"], agenda_label)
            else:
                items = scrape_generic(url, muni["name"], agenda_label)

            if agenda_key == "pz":
                city_results["pz_items"] = items
            else:
                city_results["cc_items"] = items
        except Exception as e:
            err_item = [{"title": f"[Error] {muni['name']} {agenda_label}", "error": str(e)}]
            if agenda_key == "pz":
                city_results["pz_items"] = err_item
            else:
                city_results["cc_items"] = err_item
            city_results["scrape_status"] = "partial_error"

    return city_results


# ============================================================
# MAIN
# ============================================================
def main():
    print(f"Starting DFW Agenda Scrape - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Scanning {len(MUNICIPALITIES)} municipalities for {len(KEYWORDS)} keywords...\n")

    all_results = []
    total_matches = 0
    errors = 0

    for i, muni in enumerate(MUNICIPALITIES):
        print(f"  [{i+1}/{len(MUNICIPALITIES)}] {muni['name']} ({muni['county']} Co.)...", end=" ", flush=True)

        result = scrape_municipality(muni)
        all_results.append(result)

        pz_count = len([x for x in result["pz_items"] if x.get("keywords_matched")])
        cc_count = len([x for x in result["cc_items"] if x.get("keywords_matched")])
        err = any("error" in x for x in result["pz_items"] + result["cc_items"])

        total_matches += pz_count + cc_count
        if err:
            errors += 1

        print(f"P&Z: {pz_count} hits, Council: {cc_count} hits" + (" !!" if err else ""))
        time.sleep(1)

    output = {
        "metadata": {
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "municipalities_scanned": len(MUNICIPALITIES),
            "total_keyword_matches": total_matches,
            "errors": errors,
            "keywords_used": KEYWORDS
        },
        "results": all_results
    }

    with open("agenda_data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nDone! {total_matches} keyword matches across {len(MUNICIPALITIES)} cities.")
    print(f"Results saved to agenda_data.json")
    if errors:
        print(f"  {errors} cities had scrape errors")


if __name__ == "__main__":
    main()
