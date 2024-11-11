import base64
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from website import common
from website.hcvault import VaultClient


class GmailClient:
    SCOPES = ["https://mail.google.com/"]

    def __init__(self, _config):
        self.__init = False
        self.config = _config
        self.token = None
        self.service = None

    async def init(self, interactive=False):
        if not self.__init or (self.token is not None and not self.token.valid):
            self.__init = True
            await self.update_token(interactive)
            from googleapiclient.discovery import build
            self.service = build("gmail", "v1", credentials=self.token)

    async def update_token(self, interactive=False):
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow



        vault = VaultClient.from_config(self.config)

        cred_gmail = await vault.kv_get(Path("kv/oauth_cred/gmail"))

        saveit = lambda v: vault.kv_put(Path("kv/oauth_token/gmail"), json.loads(v.to_json()))
        try:
            t = await vault.kv_get(Path("kv/oauth_token/gmail"))
            self.token = Credentials.from_authorized_user_info(t, GmailClient.SCOPES)
            if not self.token.valid:
                self.token.refresh(Request())
                await saveit(self.token)
        except KeyError:
            if not interactive:
                raise IOError("unable to update gmail token")
            flow = InstalledAppFlow.from_client_config(cred_gmail, GmailClient.SCOPES)
            self.token = flow.run_local_server(port=6324)
            await saveit(self.token)

    async def list_email(self, inbox):
        await self.init()

        return self.service.users().messages().list(userId=inbox + "@"+common.DOMAIN).execute()

    async def send_email(self, sender, recipient, subject, body):
        await self.init()

        message = MIMEMultipart()
        message['to'] = recipient
        message['from'] = f"{sender}@{common.DOMAIN}"
        message['subject'] = subject
        message.attach(MIMEText(body, 'plain'))

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        try:
            send_request = self.service.users().messages().send(
                userId="me",
                body={'raw': raw_message}
            )
            send_request.execute()
        except Exception as e:
            raise e
