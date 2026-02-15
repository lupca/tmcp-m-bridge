"""Integration tests for PocketBase MCP Bridge.

Tests authentication, collection listing, schema retrieval,
and full CRUD lifecycle against a running PocketBase instance.
"""
import unittest
import sys
import os
import time
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from client import PocketBaseClient
from config import POCKETBASE_URL, POCKETBASE_USER, POCKETBASE_PASSWORD


class TestPocketBaseIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = PocketBaseClient(POCKETBASE_URL, POCKETBASE_USER, POCKETBASE_PASSWORD)
        print(f"Testing against {POCKETBASE_URL} with user {POCKETBASE_USER}")

    def test_01_authentication(self):
        """Test authentication flow."""
        self.client.authenticate()
        self.assertIsNotNone(self.client.token)

    def test_02_list_collections(self):
        """Test listing collections — verify new schema collections exist."""
        collections = self.client.list_collections()
        self.assertIsInstance(collections, list)
        self.assertTrue(len(collections) > 0)

        names = [c["name"] for c in collections]
        # Verify all 7 new schema collections
        expected = [
            "worksheets",
            "brand_identities",
            "ideal_customer_profiles",
            "marketing_campaigns",
            "campaign_tasks",
            "content_calendar_events",
            "social_posts",
        ]
        for col in expected:
            self.assertIn(col, names, f"Collection '{col}' missing from PocketBase")

    def test_03_get_schema_users(self):
        """Test fetching schema for users collection."""
        schema = self.client.get_collection_schema("users")
        self.assertIsInstance(schema, dict)
        self.assertEqual(schema["name"], "users")

        fields = schema.get("fields", schema.get("schema"))
        self.assertIsNotNone(fields)
        field_names = [f["name"] for f in fields]
        self.assertIn("email", field_names)

    def test_04_get_schema_worksheets(self):
        """Test fetching schema for worksheets collection."""
        schema = self.client.get_collection_schema("worksheets")
        self.assertEqual(schema["name"], "worksheets")
        fields = schema.get("fields", [])
        field_names = [f["name"] for f in fields]
        self.assertIn("title", field_names)
        self.assertIn("content", field_names)
        self.assertIn("ownerId", field_names)
        self.assertIn("members", field_names)

    def test_05_get_schema_campaign_tasks(self):
        """Test schema for campaign_tasks has correct status values."""
        schema = self.client.get_collection_schema("campaign_tasks")
        fields = schema.get("fields", [])
        status_field = next((f for f in fields if f["name"] == "status"), None)
        self.assertIsNotNone(status_field, "status field not found")
        self.assertEqual(status_field["type"], "select")
        values = status_field.get("values", [])
        self.assertIn("To Do", values)
        self.assertIn("In Progress", values)
        self.assertIn("Done", values)
        self.assertIn("Cancelled", values)

    def test_06_create_record_validation_error(self):
        """Test handling of validation error (missing required field)."""
        try:
            self.client.get_collection_schema("brand_identities")
        except Exception:
            self.skipTest("brand_identities collection not found")

        with self.assertRaises(RuntimeError) as cm:
            self.client.create_record("brand_identities", {
                "slogan": "No brand name"
            })

        error_msg = str(cm.exception)
        self.assertIn("PocketBase API Error", error_msg)

    def test_07_worksheet_lifecycle_with_expand(self):
        """Test full CRUD lifecycle for worksheets, including expand on read."""
        # Get a user ID for ownerId
        users = self.client.list_records("users", per_page=1)
        self.assertTrue(len(users["items"]) > 0, "No users found — create one first")
        user_id = users["items"][0]["id"]

        # 1. Create
        ws = self.client.create_record("worksheets", {
            "title": f"Integration test {int(time.time())}",
            "content": {"integ": "test"},
            "ownerId": user_id,
        })
        self.assertIsNotNone(ws)
        self.assertIn("id", ws)
        ws_id = ws["id"]

        try:
            # 2. Read with expand
            fetched = self.client.get_record("worksheets", ws_id, expand="ownerId")
            self.assertEqual(fetched["id"], ws_id)
            self.assertIn("expand", fetched)
            self.assertIn("ownerId", fetched["expand"])

            # 3. Update
            updated = self.client.update_record("worksheets", ws_id, {
                "title": "Updated Title"
            })
            self.assertEqual(updated["title"], "Updated Title")

            # 4. Delete
            result = self.client.delete_record("worksheets", ws_id)
            self.assertTrue(result)

            # Verify deleted
            with self.assertRaises(RuntimeError):
                self.client.get_record("worksheets", ws_id)
        except Exception:
            # Clean up on failure
            try:
                self.client.delete_record("worksheets", ws_id)
            except Exception:
                pass
            raise


if __name__ == "__main__":
    unittest.main()
