import requests
import pandas as pd

headers = {'User-Agent': 'TJ research-tool btpx2025@mymail.pomona.edu'}

companyTickers = requests.get(
    "https://www.sec.gov/include/ticker.txt",
    headers=headers
)

#asking user input for ticker --> change ticker to lowercase

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

filteredforms = allFilings[allFilings['form'].isin(["10-K", "10-Q", "DEF 14A"])]

detailedfilteredforms = filteredforms[['filingDate', 'accessionNumber', 'primaryDocument', 'form']]

groupedforms = detailedfilteredforms.groupby('form').head(1)

unpadded_cik = int(cik)

for index, row in groupedforms.iterrows():
    accession = row['accessionNumber'].replace("-","")
    primaryDocument = row['primaryDocument']
    htmlPerForm = requests.get(f"https://www.sec.gov/Archives/edgar/data/{unpadded_cik}/{accession}/{primaryDocument}",
                               headers=headers)
    print(htmlPerForm.status_code)







#unpadded_cik = int(cik)
#accession = accessionNumber.strip("-")
#primarydocument = primaryDocument



#firstEntry = companyTickers.json()['0']

#directCik = companyTickers.json()['0']['cik_str']

#companyData = pd.DataFrame.from_dict(companyTickers.json(),
                                     #orient='index')

#companyData['cik_str'] = companyData['cik_str'].astype(str).str.zfill(10)

#cik = companyData['cik_str'].iloc[0]



#allFilings = pd.DataFrame.from_dict(Metadata.json()['filings']['recent'])

