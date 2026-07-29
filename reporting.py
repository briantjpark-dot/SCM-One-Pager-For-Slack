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

def format_management(roster):
     entries = []
     if roster is None or len(roster) == 0:
          return "--"
     for officer in roster:
          name = officer.get("name")
          title = officer.get("title")
          entry = f"{name}: {title}"
          entries.append(entry)
     return entries

def format_financial_numbers(number):
     if number is None:
          return "--"
     abs_number = abs(number)
     sign = "-" if number < 0 else ""
     if abs_number >= 1_000_000_000_000:
          return sign + f"${abs_number / 1_000_000_000_000:.2f}T"
     elif abs_number >= 1_000_000_000:
          return sign + f"${abs_number / 1_000_000_000:.2f}B"
     elif abs_number >= 1_000_000:
          return sign + f"${abs_number / 1_000_000:.2f}M"
     elif abs_number >= 1_000:
          return sign + f"${abs_number / 1_000:.2f}K"   
     else:
          return sign + f"${abs_number:.2f}"  

def format_rev_growth(growth):
     if growth is None:
          return "--"
     growth = growth*100
     return f"{growth:.2f}%"

def format_multiples(multiple):
     if multiple is None:
          return "--"
     return f"{multiple:.2f}"

def run_pipeline(ticker):
    sec_data = run_sec_pipeline(ticker)
    financials_and_management = get_financials(ticker)
    financials_and_management["Management"] = priority_management(financials_and_management["Management"])
    return {"SEC Data": sec_data, "Financials and Management": financials_and_management}

def generate_report(bundle):
     sec = bundle["SEC Data"]
     finances = bundle["Financials and Management"]

     business = sec["business"]
     risks = sec["risks"]
     mda = sec["mda"]
     events = format_eightk_events(sec["events"])

     management = format_management(finances["Management"])
     revenue = format_financial_numbers(finances["Revenue"])
     sharePrice = format_financial_numbers(finances["Share Price"])
     marketCap = format_financial_numbers(finances["Market Cap"])
     ev = format_financial_numbers(finances["EV"])
     evEBITDA = format_multiples(finances["EV to EBITDA"])
     revGrowth = format_rev_growth(finances["Rev. Growth"])

#going from formatted data to an md file
     lines = []
     lines.append("## Business Overview")
     lines.append("")
     lines.append(business)
     lines.append("")

     lines.append("## Key Financials")
     lines.append("")
     lines.append(f"**Share Price:** {sharePrice}")
     lines.append(f"**Market Cap:** {marketCap}")
     lines.append(f"**Enterprise Value:** {ev}")
     lines.append(f"**EV / EBITDA:** {evEBITDA}")
     lines.append(f"**Revenue (FY):** {revenue}")
     lines.append(f"**Revenue Growth (YoY):** {revGrowth}")
     lines.append("")

     lines.append("## Key Risks")
     lines.append("")
     lines.append(risks)
     lines.append("")

     lines.append("## Management's Discussion & Analysis")
     lines.append("")
     lines.append(mda)
     lines.append("")

     lines.append("## Management")
     lines.append("")
     lines.extend(management)
     lines.append("")

     lines.append("## Recent Events")
     lines.append("")
     lines.extend(events)

     report = "\n".join(lines)
     return report



if __name__ == "__main__":
    ticker = input("Please enter a ticker:")
    bundle = run_pipeline(ticker)
    report = generate_report(bundle)
    print(report)