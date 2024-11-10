import asyncio

from website import common
import sys

async def main(argv):
    config = await common.get_config()
    await common.update_token_gmail(config, interactive=True)

if __name__ == "__main__":
    asyncio.run(main(sys.argv))
