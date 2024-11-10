import asyncio

from website import common
import sys

from website.gmail import GmailClient


async def main(argv):
    config = await common.get_config()
    gmail = GmailClient(config)
    await gmail.update_token(interactive=True)

if __name__ == "__main__":
    asyncio.run(main(sys.argv))
