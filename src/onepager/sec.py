import requests
import re
import pandas as pd
from bs4 import BeautifulSoup
import anthropic
from onepager.prompts import BUSINESS_PROMPT, RISKS_PROMPT, MDA_PROMPT
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

client = anthropic.Anthropic()

TENK_MODEL = "claude-opus-4-6"

headers = {'User-Agent': 'TJ research-tool btpx2025@mymail.pomona.edu'}

code_dictionary = {
    "1.01": "Material Agreement Entered",
    "1.02": "Material Agreement Terminated",
    "1.03": "Bankruptcy or Receivership",
    "2.01": "Completion of Acquisition or Disposition",
    "2.02": "Earnings / Results of Operations",
    "2.03": "New Material Financial Obligation",
    "2.04": "Debt Acceleration or Trigger Event",
    "2.05": "Costs from Exit or Disposal Activities",
    "2.06": "Material Asset Impairment",
    "3.01": "Delisting or Listing Standard Notice",
    "3.02": "Unregistered Equity Sale",
    "3.03": "Material Modification to Shareholder Rights",
    "4.01": "Change in Auditor",
    "4.02": "Non-Reliance on Prior Financials",
    "5.01": "Change in Control",
    "5.02": "Executive / Director Change",
    "5.03": "Change to Bylaws or Fiscal Year",
    "7.01": "Regulation FD Disclosure",
    "8.01": "Other Material Event",
}


# asking user input for ticker --> change ticker to lowercase
def build_cik_map():
    response = requests.get(
    "https://www.sec.gov/include/ticker.txt",
    headers=headers
    )
    response.raise_for_status()
    dictionary = {}
    companyTickers = response.text.split("\n")

    for row in companyTickers:
        if row == "":
            continue
        ticker, cik = row.split("\t")
        dictionary[ticker] = cik
    return dictionary

def ticker_to_cik(ticker, cik_map):
    ticker = ticker.lower()
    cik = cik_map.get(ticker)
    if cik is None:
        return None
    else:
        cik = cik.zfill(10)
        return cik

def get_submission(cik):
    Metadata = requests.get(
        f'https://data.sec.gov/submissions/CIK{cik}.json',
        headers=headers
        )
    Metadata.raise_for_status()
    allFilings = pd.DataFrame.from_dict(Metadata.json()['filings']['recent'])
    Metadata_json = Metadata.json()
    return Metadata_json, allFilings


def select_recent_filings(allFilings, cik):
    documents = {}
    filteredforms = allFilings[allFilings['form'].isin(
    ["10-K"])]
    detailedfilteredforms = filteredforms[[
    'filingDate', 'accessionNumber', 'primaryDocument', 'form']]
    groupedforms = detailedfilteredforms.groupby('form').head(1)
    if groupedforms.empty:
        raise ValueError("No 10-K filing found for this company")
    unpadded_cik = int(cik)
    for index, row in groupedforms.iterrows():
        accession = row['accessionNumber'].replace("-", "")
        primaryDocument = row['primaryDocument']
        htmlPerForm = requests.get(
            f"https://www.sec.gov/Archives/edgar/data/{unpadded_cik}/{accession}/{primaryDocument}",
            headers=headers
            )
        htmlPerForm.raise_for_status()
        documents[row['form']] = htmlPerForm.text
    return documents

#Starting the 10K extraction here
def clean_html(raw_html):
    soup = BeautifulSoup(raw_html, "html.parser")
    pattern = re.compile("display:none")
    xbrl = soup.find_all("div", style=pattern)
    for element in xbrl:
        element.decompose()
    readablesoup = soup.get_text()
    loweredsoup = readablesoup.lower()
    return loweredsoup, readablesoup

def extract_section(lowered, original, start_anchor, end_anchor, search_from):
    start_position = lowered.find(start_anchor, search_from)
    if start_position == -1:
        raise ValueError(f"Could not locate '{start_anchor}' in filing")
    end_position = lowered.find(end_anchor, start_position)
    if end_position == -1:
        raise ValueError(f"Could not locate '{end_anchor}' in filing")
    return original[start_position:end_position], end_position

def section_10k(loweredsoup, readablesoup):
    item1Start = loweredsoup.find("item 1")
    item1cut = -1
    count = 0
    while item1Start != -1:
        if "business" in loweredsoup[item1Start:item1Start+30]:
            count = count + 1
            if count == 2:
                item1cut = item1Start
                break
        item1Start = loweredsoup.find("item 1", item1Start +1)

    if item1cut == -1:
        raise ValueError("Could not locate the Item 1 (Business) section in filing")

    item1End = loweredsoup.find("item 1a", item1cut)
    if item1End == -1:
        raise ValueError("Could not locate the Item 1A (Risk Factors) section in filing")
    business = readablesoup[item1cut:item1End]

    risks, risks_end = extract_section(loweredsoup, readablesoup, "item 1a", "item 1b", item1End)
    mda, mda_end = extract_section(loweredsoup, readablesoup, "item 7", "item 7a", risks_end)
    return {"business": business, "risks": risks, "mda": mda}

#This is where we use our Claude API & prompts to summarize
def summarize_10k(text, prompt):
    response = client.messages.create(
        model = TENK_MODEL,
        max_tokens = 2000,
        temperature = 0.1,
        system = prompt,
        messages=[{"role":"user", "content": text}]
    )
    return response.content[0].text


#Starting 8-K extraction here
def filter_recent_8ks(allFilings):
    filteredforms = allFilings[allFilings['form'].isin(
        ["8-K"])].copy()
    filteredforms["filingDate"] = pd.to_datetime(filteredforms["filingDate"])
    now = datetime.now()
    cutoff = now - timedelta(days=365)
    filteredforms = filteredforms[filteredforms["filingDate"] >= cutoff]
    return filteredforms


def codes_to_labels(codes):
    labels = []
    for code in codes:
        if code in code_dictionary.keys():
            labels.append(code_dictionary[code])
    return ", ".join(labels)
    
def get_8k_events(filteredforms):
    #converting the items column into strings --> They're prob already strings but just to be safe
    filteredforms["items"] = filteredforms['items'].astype(str)
    #filtering 8ks based on item #
    filteredforms = filteredforms[filteredforms["items"].str.contains("1.01|1.03|2.01|2.02|2.06|4.01|4.02|5.01|5.02")]
    priority_group = filteredforms[[
        'filingDate', 'accessionNumber', 'items']]
    priority_group["items"] = priority_group['items'].str.split(",")
    priority_group["items"] = priority_group["items"].apply(codes_to_labels)
    return priority_group

def run_sec_pipeline(ticker):
    cik_map = build_cik_map()
    cik = ticker_to_cik(ticker, cik_map)
    if cik is None:
        return "Not a valid ticker"
    submissions_json, allFilings = get_submission(cik)
    documents = select_recent_filings(allFilings, cik)
    loweredsoup, readablesoup = clean_html(documents["10-K"])
    sections = section_10k(loweredsoup, readablesoup)
    business_summary = summarize_10k(sections["business"], BUSINESS_PROMPT)
    risks_summary = summarize_10k(sections["risks"], RISKS_PROMPT)
    mda_summary = summarize_10k(sections["mda"], MDA_PROMPT)
    filteredforms = filter_recent_8ks(allFilings)
    eightk_summary = get_8k_events(filteredforms)
    return {"business": business_summary, "risks": risks_summary, "mda": mda_summary, "events": eightk_summary}
