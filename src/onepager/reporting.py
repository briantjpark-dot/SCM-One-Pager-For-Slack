from onepager.sec import run_sec_pipeline
from onepager.financials import get_financials, priority_management
from dotenv import load_dotenv
from fpdf import FPDF

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
    financials_and_management["Management"] = priority_management(
        financials_and_management["Management"])
    return {"SEC Data": sec_data, "Financials and Management": financials_and_management}

#This is for an .md file. It'll look weird on slack but when separtely opened it looks right
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

# going from formatted data to an md file
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

# Since slack uses a different markdown format I created a duplicate function
# that does the same as generate_report but in a slack-cooperative format

def generate_pdf_report(bundle):
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

    # fpdf's core fonts only support latin-1; the LLM-generated risks/MD&A
    # text uses unicode bullets, smart quotes, and dashes outside that range,
    # so map the common ones to ASCII before falling back to "?" for the rest
    UNICODE_REPLACEMENTS = {
        "•": "-",   # •
        "‘": "'",   # ‘
        "’": "'",   # ’
        "“": '"',   # “
        "”": '"',   # ”
        "–": "-",   # –
        "—": "-",   # —
        "…": "...",  # …
    }

    def clean(text):
        for char, replacement in UNICODE_REPLACEMENTS.items():
            text = text.replace(char, replacement)
        return text.encode("latin-1", "replace").decode("latin-1")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    def add_heading(text):
        pdf.set_font("Arial", "B", 14)
        pdf.multi_cell(0, 10, clean(text))
        pdf.ln(2)

    def add_body(text):
        pdf.set_font("Arial", "", 11)
        pdf.multi_cell(0, 6, clean(text))
        pdf.ln(4)

    add_heading("Business Overview")
    add_body(business)

    add_heading("Key Financials")
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 6, clean(f"Share Price: {sharePrice}"))
    pdf.multi_cell(0, 6, clean(f"Market Cap: {marketCap}"))
    pdf.multi_cell(0, 6, clean(f"Enterprise Value: {ev}"))
    pdf.multi_cell(0, 6, clean(f"EV / EBITDA: {evEBITDA}"))
    pdf.multi_cell(0, 6, clean(f"Revenue (FY): {revenue}"))
    pdf.multi_cell(0, 6, clean(f"Revenue Growth (YoY): {revGrowth}"))
    pdf.ln(4)

    add_heading("Key Risks")
    add_body(risks)

    add_heading("Management's Discussion & Analysis")
    add_body(mda)

    add_heading("Management")
    pdf.set_font("Arial", "", 11)
    if isinstance(management, list):
        for entry in management:
            pdf.multi_cell(0, 6, clean(entry))
    else:
        pdf.multi_cell(0, 6, clean(management))
    pdf.ln(4)

    add_heading("Recent Events")
    pdf.set_font("Arial", "", 11)
    for event in events:
        pdf.multi_cell(0, 6, clean(event))

    report = pdf.output(dest="S")
    return report

if __name__ == "__main__":
    ticker = input("Please enter a ticker:")
    bundle = run_pipeline(ticker)
    report = generate_pdf_report(bundle)
    print(report)

    with open(f"{ticker.upper()}_onepager.pdf", "w", encoding="utf-8") as f:
        f.write(report)
