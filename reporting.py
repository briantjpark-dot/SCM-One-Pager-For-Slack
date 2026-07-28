from sec import run_sec_pipeline
from financials import get_financials, priority_management
from dotenv import load_dotenv

load_dotenv()

def format_eightk_events(events_df):
    events = []
    if events_df is None or events_df.empty:
            return ["- No significant events"]
    for index, row in events_df.iterrows():
        filingDate = row["filingDate"].strftime("%Y-%m-%d")
        event = str(row["items"])
        bullet = f"- {filingDate}: {event}"
        events.append(bullet)
    return events

def normalize_financial_numbers(number):
     abs_number = abs(number)

     if abs_number >= 1_000_000_000_000:
          return f"${abs_number / 1_000_000_000_000:.2f}T"
     elif abs_number >= 1_000_000_000:
          return f"${abs_number / 1_000_000_000:.2f}B"
     elif abs_number >= 1_000_000:
          return f"${abs_number / 1_000_000:.2f}M"
     elif abs_number >= 1_000:
          return f"${abs_number / 1_000:.2f}K"   
     else:
          return f"${abs_number:.2f}"  

#make sure for rev growth you just stick percent at the end


def run_pipeline(ticker):
    sec_data = run_sec_pipeline(ticker)
    financials_and_management = get_financials(ticker)
    financials_and_management["Management"] = priority_management(financials_and_management["Management"])
    return {"SEC Data": sec_data, "Financials and Management": financials_and_management}

if __name__ == "__main__":
    ticker = input("Please enter a ticker:")
    result = run_pipeline(ticker)
    print(result)