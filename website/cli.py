import asyncio
import argparse

from website.hcvault import get_config
import sys

from website.gmail import GmailClient


async def main(argv):
    parser = argparse.ArgumentParser(description="Run updates for: Gmail")
    parser.add_argument('--update', action='store_true', help="Runs updates for: Gmail")
    args = parser.parse_args(argv[1:])
    config = await get_config()

    if args.update:
        gmail = GmailClient(config)
        await gmail.update_token(interactive=True)
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main(sys.argv))
