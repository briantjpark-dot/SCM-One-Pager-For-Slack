import yfinance as yf

#obv once we connect to main file we should remove this
stock = input("Please put in a valid stock ticker:")
stock = stock.upper()

ticker = yf.Ticker(stock)

def get_financials(ticker):
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
    return financials, recent_fy_revenue

result = get_financials(ticker)

print(result)

#management also comes back as a list of dictionaries, so just take the top 4
#yfinance separately offers a longBusinessSummary so if extraction fails on the 10K, we should use this as a backup --> We can even limit any api costs if we only use yFinance as well
