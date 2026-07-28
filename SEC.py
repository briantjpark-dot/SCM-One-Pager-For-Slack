import requests
import re
import pandas as pd
from bs4 import BeautifulSoup
import anthropic
from prompts import BUSINESS_PROMPT, RISKS_PROMMPT, MDA_PROMPT
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

client = anthropic.Anthropic()

TENK_MODEL = "claude-opus-4-6"

headers = {'User-Agent': 'TJ research-tool btpx2025@mymail.pomona.edu'}

companyTickers = requests.get(
    "https://www.sec.gov/include/ticker.txt",
    headers=headers
)

# asking user input for ticker --> change ticker to lowercase
def ticker_to_cik(companyTickers):
    dictionary = {}
    companyTickers = companyTickers.text.split("\n")

    for row in companyTickers:
        if row == "":
            continue
        ticker, cik = row.split("\t")
        dictionary[ticker] = cik
    return dictionary


stock = input("Please provide a valid stock ticker:")
stock = stock.lower()

result = ticker_to_cik(companyTickers)
cik = result.get(stock)
if cik is None:
    print("Not a valid ticker")
else:
    cik = cik.zfill(10)

Metadata = requests.get(f'https://data.sec.gov/submissions/CIK{cik}.json',
                        headers=headers
                        )

allFilings = pd.DataFrame.from_dict(Metadata.json()['filings']['recent'])

filteredforms = allFilings[allFilings['form'].isin(
    ["10-K", "8-K", "DEF 14A"])]

detailedfilteredforms = filteredforms[[
    'filingDate', 'accessionNumber', 'primaryDocument', 'form']]

groupedforms = detailedfilteredforms.groupby('form').head(1)

unpadded_cik = int(cik)

documents = {}

for index, row in groupedforms.iterrows():
    accession = row['accessionNumber'].replace("-", "")
    primaryDocument = row['primaryDocument']
    htmlPerForm = requests.get(f"https://www.sec.gov/Archives/edgar/data/{unpadded_cik}/{accession}/{primaryDocument}",
                               headers=headers)

    documents[row['form']] = htmlPerForm.text


#Starting the 10K extraction here
soup = BeautifulSoup(documents['10-K'], "html.parser")

pattern = re.compile("display:none")

xbrl = soup.find_all("div", style=pattern)

for element in xbrl:
    element.decompose()

readablesoup = soup.get_text()

loweredsoup = readablesoup.lower()

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

item1End = loweredsoup.find("item 1a", item1cut)

business = readablesoup[item1cut:item1End]


def extract_section(text, start_anchor, end_anchor, search_from):
    start_position = text.find(start_anchor, search_from)
    end_position = text.find(end_anchor, start_position)
    return text[start_position:end_position], end_position


#Two things on the lefthand side b/c we return two different things, both the text and ending position
risks, risks_end = extract_section(loweredsoup, "item 1a", "item 1b", item1End)
mda, mda_end = extract_section(loweredsoup, "item 7", "item 7a", risks_end)


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

business_summary = summarize_10k(business, BUSINESS_PROMPT)
risks_summary = summarize_10k(risks, RISKS_PROMMPT)
mda_summary = summarize_10k(mda, MDA_PROMPT)

print(business_summary, risks_summary, mda_summary)


#Starting 8-K extraction here

filteredforms = allFilings[allFilings['form'] == "8-K"]

filteredforms["filingDate"] = pd.to_datetime(filteredforms["filingDate"])

now = datetime.now()

cutoff = now - timedelta(days=365)

filteredforms = filteredforms[filteredforms["filingDate"] >= cutoff]

#converting the items column into strings --> They're prob already strings but just to be safe
filteredforms["items"] = filteredforms['items'].astype(str)

#filtering 8ks based on item #
filteredforms = filteredforms[filteredforms["items"].str.contains("1.01|2.02|5.02")]

priority_group = filteredforms[[
    'filingDate', 'accessionNumber', 'items']]

#print(priority_group)

#So now we have to remove all the codes that are not prioritized (deleted) and then use a dictionary to map each code to a string

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

#split its codes → look each up in the dictionary → keep the labels that exist → join them into a readable string.

priority_group["items"] = priority_group['items'].astype(str).str.split(",")

def codes_to_labels(codes):
    labels = []
    for code in codes:
        if code in code_dictionary.keys():
            labels.append(code_dictionary[code])
    return ", ".join(labels)

priority_group["items"] = priority_group["items"].apply(codes_to_labels)

print(priority_group)


#Cost: $10.03 - $9.89 = $0.14
#damn in like a minute, ts was FAST
#make sure to test with other companies
#make sure to check the numbers across their sources (just plug and chug into Claude)

#use yfinance to not only find financial data but also the chief officers --> might need to an authority check with the 14A though
