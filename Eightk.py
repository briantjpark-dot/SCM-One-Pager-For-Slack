import requests
import re
import pandas as pd
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
