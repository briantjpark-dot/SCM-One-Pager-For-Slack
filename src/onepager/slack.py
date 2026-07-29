import io
import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from onepager.reporting import run_pipeline, generate_pdf_report

load_dotenv()

app = App(token=os.environ["SLACK_BOT_TOKEN"])


# the following commands are necessary:
# 1. "/invite @OnePagerBot"
# 2. /onepager TICKER HERE

@app.command("/onepager")
def handle_onepager(ack, command, client):
    ack()  # acknowledge within 3 seconds

    ticker = command["text"].strip()
    channel_id = command["channel_id"]

    # Let the user know it's working, since the pipeline takes a while
    client.chat_postMessage(
        channel=channel_id,
        text=f"Generating one-pager for {ticker.upper()}..."
    )
    bundle = run_pipeline(ticker)
    report = generate_pdf_report(bundle)
    pdf_bytes = report.encode("latin-1")

    client.files_upload_v2(
        channel=channel_id,
        filename=f"{ticker.upper()}_onepager.pdf",
        file=io.BytesIO(pdf_bytes),
        initial_comment=f"{ticker.upper()} One-Pager"
    )


if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()

