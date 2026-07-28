from sec import run_sec_pipeline
from financials import get_financials
from dotenv import load_dotenv

load_dotenv()

def run_pipeline(ticker):
    sec_data = run_sec_pipeline(ticker)
    financials_and_management = get_financials(ticker)
    return {"SEC Data": sec_data, "Financials and Management": financials_and_management}


if __name__ == "__main__":
    ticker = input("Please enter a ticker:")
    result = run_pipeline(ticker)
    print(result)

