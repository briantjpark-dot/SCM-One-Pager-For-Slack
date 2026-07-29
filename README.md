# SCM-One-Pager-Agent

A bot that delivers an equity-research one-pager via Slack.

## Disclaimers on Use

This idea was inspired by my time in my own college's student investment fund where, before diving into a full pitch deck on a stock, analysts would draft one-pagers that detailed the initial research and argumentation. These one-pagers would be discussed and analysts were either green-lighted for a full pitch or asked to revise their thesis and research. During my time as a junior analyst I didn't where to gather such information, let alone SEC filings, and wasn't quite sure how to navigate equity research and transition to creating argumentation about strong and weak aspects about companies. 

This tool is intended to make that initial transition easier! A one-pager based on a company's SEC filings and general financial metrics will be produced for junior-level analysts at such student investment funds to read about the materials in SEC filings without having to comb through all the documents themselves. However, these one-pagers are not supposed to support investment theses nor generate them; They provide a skeleton and starting points for further analyst-driven research!

## How it Works

Once a user calls the bot via the command /onepager TICKER, the bot will:
1. Request the most recent 10K via the SEC's EDGAR API. The Business, Risks, and MD&A sections of the 10K will be parsed and then summarized using an LLM call to a Claude Opus 4-6 model.
2. Further request the 8K filings of the past 12 months. The sections of these documents will have their items filtered and labeled based on relevance and materiality.
3. Use the YFinance library to pull various financial statistics such as share price, EV, EV/EBITDA, etc. The bot will also use this library to pull the names and titles of key management.
4. Format this information into a new TICKER_onepager.pdf file.

## Features and Things I've Learned

1. I've separated the gathering and formatting into two different files. This allows future iterations to reconfigure the raw information into different formats. For example, I've kept the function "get_report" in the reporting.py file that writes the information to a .md file for future use.
2. Financials are called through YFinance so they can't really be hallucinated. Missing values will always return as "-"
4. I've tried to keep the code as flexible as possible. Granted this is a basic project so I've hard coded the documents and financial metrics the bot should look for. If analysts find that other SEC filings are more particularly useful or, for example, other multiples than EV/EBITDA are needed, the code can easily adjust to that with simple changes.

## Technical Challenges

1. Requested SEC filings returned as HTML with lots of hidden XBRL financial data in the beginning. This made it difficult to search for specific sections such as "Item 1" or "Item 1a" because the text extraction couldn't just find the nth instance of such words popping up. I found that this XBRL data is consistently hidden through the display:none divs, so I've stripped them before parsing
2. Similarly, I found that the Table of Contents outlines all the items, so I've set up my functions to look for the second instance of each of these items showing up.
3. I also planned on using financial data through the SEC filings as well but found that each company tags specific metrics in different ways such as "Revenue" vs. "RevenueFromContractWithCustomerExcludingAssessedTax" vs "SalesRevenue" so I opted with the standardized yfinance library. Of course there are other data sources that may be more precise.

## Setup and Installation

Copy the code through
```
pip install -e
```

You will also need an Anthropic API Key as well as the Slack Bot Token and a Slack App Token. Please create a .env file and paste

```
ANTHROPIC_API_KEY= Your key here
SLACK_BOT_TOKEN = Your key here
SLACK_APP_TOKEN = Your key here
```

You will also need setup a new app for your desired Slack workspace by yourself. I found this [Youtube Video](https://www.youtube.com/watch?v=KJ5bFv-IRFM&t=586s) by Tech with Tim to be the most helpful for setting up. Here are some key points:

- When first creating your app, please use the "Blank App" template
- Please also set up Socket Mode by making sure you "Enable Socket Mode"
- By 3:53 of the video, Tim discusses the various OAuth Scopes for Slack apps. This app will require the chat:write, commands, and files:write scopes.
- Please also remember to set up the /onepager command. This can be done by navigating to the "Slash Commands" menu on the left and creating a new command and pasting "/onepager" into the command section. The Short Description and Useful Hint are optional

## Usage

Once you have the app settings configured, you will just run "Slack.py" and hopefully see a message in terminal saying
```
⚡️ Bolt app is running!
```
Then proceed to the Slack Workspace you chose during setup and in your desired channel enter "/invite @Name of Your Bot"

To then use the bot, simply enter "/onepager TICKER" where you replace "TICKER" with whatever ticker you would like.

## Future iterations

I plan to keep working on this further with more integrated commands. For example, instead of having the finances be hardcoded, I'm thinking of exploring commands to provide followup financial metrics on command/request.
