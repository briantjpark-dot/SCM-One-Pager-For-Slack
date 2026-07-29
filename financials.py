import yfinance as yf

key_titles = (
    "chief executive",
    "chief financial",
    "chief operating",
    "chief technology",
    "chairman",
    "founder",
    "cofounder",
    "ceo",
    "cto",
    "cfo",
    "coo"
)

def get_financials(ticker):
    ticker = yf.Ticker(ticker.upper())
    info = ticker.info
    financials = {}
    financials["Management"] = info.get("companyOfficers")
    financials["Share Price"] = info.get("currentPrice")
    financials["Market Cap"] = info.get("marketCap")
    financials["EV"] = info.get("enterpriseValue")
    financials["EV to EBITDA"] = info.get("enterpriseToEbitda")
    financials["Rev. Growth"] = info.get("revenueGrowth")

    income_statement = ticker.income_stmt

#remember .index gives us the row lables of the df, so we are checking if there is a total revenue row in the income statement
    if income_statement.empty or "Total Revenue" not in income_statement.index:
        recent_fy_revenue = None
    else:
        recent_fy_revenue = income_statement.loc["Total Revenue"].iloc[0]
    financials["Revenue"] = recent_fy_revenue
    return financials

#management also comes back as a list of dictionaries, so just take the top 4
#yfinance separately offers a longBusinessSummary so if extraction fails on the 10K, we should use this as a backup --> We can even limit any api costs if we only use yFinance as well

#keyword and officer are loop variables, bit confusing
def priority_management(officer_list):
    roster = []
    for officer in officer_list:
        title = officer.get('title', '').lower()
        if any(keyword in title for keyword in key_titles):
            roster.append({"name": officer.get('name'), "title": officer.get('title')})
    return roster
