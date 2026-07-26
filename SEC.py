import requests
import re
import pandas as pd
from bs4 import BeautifulSoup

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
    ["10-K", "10-Q", "DEF 14A"])]

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
# print(documents.keys())


#print(documents['10-K'][:4000])

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

print(business, risks, mda)

#This is where we use our Claude API & prompts to summarize

