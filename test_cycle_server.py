import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest

import cycle_server as app


class PortalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = app.ROOT
        app.ROOT = Path(self.tmp.name)
        app.SESSIONS.clear()
        app.LOGIN_ATTEMPTS.clear()
        self.server = app.ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.cookie = None
        self.bike = dict(brand="Fixture", model="Test only", specs="Steel single speed",
                         size="M", replacement=6999, age=2, condition="good", demand="standard",
                         repairs=300, overhead=200, quote=1800, target=300,
                         inspected=False, ownership=False, damage=False)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        app.ROOT = self.root
        self.tmp.cleanup()

    def request(self, method, path, data=None, auth=False, origin=True):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port)
        headers = {"Content-Type": "application/json"}
        if origin:
            headers["Origin"] = app.URL
        if auth and self.cookie:
            headers["Cookie"] = self.cookie
        connection.request(method, path, json.dumps(data) if data is not None else None, headers)
        response = connection.getresponse()
        cookie = response.getheader("Set-Cookie")
        if cookie:
            self.cookie = cookie.split(";")[0]
        result = response.status, json.loads(response.read())
        connection.close()
        return result

    def test_private_inspection_flow(self):
        fixture = {**self.bike, "contact_name": "Test fixture", "phone": "+91 90000 00000",
                   "preference": "Test meeting preference", "consent": True}
        status, saved = self.request("POST", "/inspection", fixture)
        self.assertEqual(status, 201)
        self.assertEqual(self.request("GET", "/admin/requests")[0], 401)
        self.assertEqual(self.request("GET", "/listings")[1], [])
        password = "test-only-owner-password"
        self.assertEqual(self.request("POST", "/admin/setup", {"password": password})[0], 200)
        status, requests = self.request("GET", "/admin/requests", auth=True)
        self.assertEqual(status, 200)
        self.assertEqual(requests[0]["phone"], "+919000000000")
        self.assertEqual(requests[0]["status"], "New")
        self.assertEqual(self.request("POST", "/admin/update", {"id": requests[0]["id"], "status": "Contacted", "notes": "Test note"}, auth=True)[0], 200)
        self.assertEqual(self.request("GET", "/admin/requests", auth=True)[1][0]["status"], "Contacted")
        self.assertEqual(self.request("POST", "/admin/setup", {"password": password})[0], 400)
        self.request("POST", "/admin/logout", {}, auth=True)
        self.assertEqual(self.request("GET", "/admin/requests", auth=True)[0], 401)
        self.assertEqual(self.request("POST", "/admin/login", {"password": "wrong-password"})[0], 401)
        self.assertEqual(self.request("POST", "/admin/login", {"password": password})[0], 200)

    def test_offer_thresholds_are_enforced_by_server(self):
        for quote, accepted in ((2309, True), (2310, False), (3000, False)):
            status, result = self.request("POST", "/seller-offer", {**self.bike, "quote": quote})
            self.assertEqual(status, 200)
            self.assertEqual(result["price_ok"], accepted)
        for amount, accepted in ((3079, False), (3080, True), (4000, True)):
            status, result = self.request("POST", "/buyer-offer", {"listing_id": "demo", "offer": amount, "value": 1})
            self.assertEqual(status, 200)
            self.assertEqual(result["price_ok"], accepted)
            self.assertNotIn("price", result)
            self.assertNotIn("3080", result["message"])
            self.assertNotIn("3,080", result["message"])
        self.assertEqual(self.request("POST", "/value", self.bike)[0], 401)
        listing = app.public_listing({"id": "test", "data": json.dumps(self.bike), "value": 3850})
        self.assertNotIn("price", listing)
        self.assertNotIn("value", listing)
        self.assertEqual(self.request("POST", "/listings", self.bike)[0], 401)
        self.assertEqual(self.request("POST", "/inspection", self.bike, origin=False)[0], 403)

    def test_bad_contact_and_no_consent_are_not_saved(self):
        status, result = self.request("POST", "/inspection", {**self.bike, "contact_name": "Test", "phone": "123", "consent": True})
        self.assertEqual(status, 400)
        with app.database() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM requests").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
