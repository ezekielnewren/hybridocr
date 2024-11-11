import unittest

from starlette.testclient import TestClient
from website.server import app


class TestWebsite(unittest.TestCase):
    def __init__(self, other):
        super().__init__(other)
        self.client = TestClient(app)

    def __del__(self):
        self.client.close()

    def test_landing_page(self):
        resp = self.client.get("/")

        self.assertIsNotNone(resp)
