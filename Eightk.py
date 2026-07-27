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


