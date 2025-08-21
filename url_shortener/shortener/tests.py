from django.test import TestCase, Client
from django.urls import reverse


class ShortenerAPITests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_shorten_and_resolve(self):
        resp = self.client.post(reverse("shorten"), data={"target_url": "https://example.com", "ttl": 60})
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        code = data["short_id"]
        self.assertTrue(code)
        # Resolve
        r2 = self.client.get(reverse("resolve", kwargs={"code": code}))
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()["url"], "https://example.com")

    def test_redirect_and_stats(self):
        resp = self.client.post(reverse("shorten"), data={"target_url": "https://example.com"})
        code = resp.json()["short_id"]
        # redirect
        r = self.client.get(reverse("redirect", kwargs={"code": code}))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r["Location"], "https://example.com")
        # stats
        s = self.client.get(reverse("stats", kwargs={"code": code}))
        self.assertEqual(s.status_code, 200)
        body = s.json()
        self.assertEqual(body["hit_count"], 1)
        self.assertFalse(body["expired"])

    def test_expired(self):
        # ttl=0 makes it immediately expired
        resp = self.client.post(reverse("shorten"), data={"target_url": "https://example.com", "ttl": 0})
        code = resp.json()["short_id"]
        r = self.client.get(reverse("redirect", kwargs={"code": code}))
        self.assertEqual(r.status_code, 410)
        r2 = self.client.get(reverse("resolve", kwargs={"code": code}))
        self.assertEqual(r2.status_code, 410)

    def test_invalid_url(self):
        resp = self.client.post(reverse("shorten"), data={"target_url": "not a url"})
        self.assertEqual(resp.status_code, 400)
        body = resp.json()
        self.assertIn("error", body)
