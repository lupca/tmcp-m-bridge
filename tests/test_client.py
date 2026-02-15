"""Tests for PocketBaseClient new features: expand, sort, fields, count_records.

Requires a running PocketBase instance with the schema from migrations.
"""
import unittest
import sys
import os
import time
import json

# Add project root to path so we can import client/config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from client import PocketBaseClient
from config import POCKETBASE_URL, POCKETBASE_USER, POCKETBASE_PASSWORD


class TestClientNewFeatures(unittest.TestCase):
    """Integration tests for new client features against live PocketBase."""

    @classmethod
    def setUpClass(cls):
        cls.client = PocketBaseClient(POCKETBASE_URL, POCKETBASE_USER, POCKETBASE_PASSWORD)
        cls.client.authenticate()

        # Create a test worksheet to use as parent for relation tests
        cls.test_worksheet = cls.client.create_record("worksheets", {
            "title": f"Test Worksheet {int(time.time())}",
            "content": {"test": True},
            "ownerId": cls._get_user_id(cls),
        })
        cls.worksheet_id = cls.test_worksheet["id"]

        # Create a test campaign linked to the worksheet
        cls.test_campaign = cls.client.create_record("marketing_campaigns", {
            "worksheetId": cls.worksheet_id,
            "name": f"Test Campaign {int(time.time())}",
            "goal": "Integration test goal",
        })
        cls.campaign_id = cls.test_campaign["id"]

        # Create a couple of tasks for sorting/filtering tests
        cls.task_ids = []
        for i, status in enumerate(["To Do", "Done"]):
            task = cls.client.create_record("campaign_tasks", {
                "campaignId": cls.campaign_id,
                "taskName": f"Test Task {i+1}",
                "status": status,
                "week": i + 1,
            })
            cls.task_ids.append(task["id"])

    def _get_user_id(self):
        """Get the authenticated user ID."""
        users = self.client.list_records("users", per_page=1)
        return users["items"][0]["id"] if users["items"] else None

    @classmethod
    def tearDownClass(cls):
        """Clean up test data in reverse dependency order."""
        for tid in cls.task_ids:
            try:
                cls.client.delete_record("campaign_tasks", tid)
            except Exception:
                pass
        try:
            cls.client.delete_record("marketing_campaigns", cls.campaign_id)
        except Exception:
            pass
        try:
            cls.client.delete_record("worksheets", cls.worksheet_id)
        except Exception:
            pass

    # --- list_records with sort ---

    def test_list_records_sort_asc(self):
        """Sort tasks by week ascending."""
        result = self.client.list_records("campaign_tasks", sort="week",
                                           filter_str=f"campaignId = '{self.campaign_id}'")
        items = result["items"]
        self.assertTrue(len(items) >= 2)
        weeks = [i.get("week", 0) for i in items]
        self.assertEqual(weeks, sorted(weeks))

    def test_list_records_sort_desc(self):
        """Sort tasks by week descending."""
        result = self.client.list_records("campaign_tasks", sort="-week",
                                           filter_str=f"campaignId = '{self.campaign_id}'")
        items = result["items"]
        self.assertTrue(len(items) >= 2)
        weeks = [i.get("week", 0) for i in items]
        self.assertEqual(weeks, sorted(weeks, reverse=True))

    # --- list_records with expand ---

    def test_list_records_expand(self):
        """Expand campaignId relation on tasks."""
        result = self.client.list_records("campaign_tasks", expand="campaignId",
                                           filter_str=f"campaignId = '{self.campaign_id}'")
        items = result["items"]
        self.assertTrue(len(items) >= 1)
        # Check that expand populated the relation
        first = items[0]
        self.assertIn("expand", first)
        self.assertIn("campaignId", first["expand"])
        self.assertEqual(first["expand"]["campaignId"]["name"], self.test_campaign["name"])

    # --- list_records with fields ---

    def test_list_records_fields(self):
        """Request only specific fields."""
        result = self.client.list_records("campaign_tasks", fields="id,taskName",
                                           filter_str=f"campaignId = '{self.campaign_id}'")
        items = result["items"]
        self.assertTrue(len(items) >= 1)
        first = items[0]
        self.assertIn("id", first)
        self.assertIn("taskName", first)
        # Other fields should not be present
        self.assertNotIn("week", first)
        self.assertNotIn("status", first)

    # --- get_record with expand ---

    def test_get_record_expand(self):
        """Get single task with expanded campaignId."""
        record = self.client.get_record("campaign_tasks", self.task_ids[0], expand="campaignId")
        self.assertIn("expand", record)
        self.assertIn("campaignId", record["expand"])
        self.assertEqual(record["expand"]["campaignId"]["id"], self.campaign_id)

    # --- get_record with fields ---

    def test_get_record_fields(self):
        """Get single task with only selected fields."""
        record = self.client.get_record("campaign_tasks", self.task_ids[0], fields="id,taskName")
        self.assertIn("id", record)
        self.assertIn("taskName", record)
        self.assertNotIn("status", record)

    # --- count_records ---

    def test_count_records(self):
        """Count all records in campaign_tasks."""
        count = self.client.count_records("campaign_tasks")
        self.assertIsInstance(count, int)
        self.assertGreaterEqual(count, 2)

    def test_count_records_with_filter(self):
        """Count only 'Done' tasks."""
        count = self.client.count_records("campaign_tasks",
                                           filter_str=f"status = 'Done' && campaignId = '{self.campaign_id}'")
        self.assertIsInstance(count, int)
        self.assertEqual(count, 1)

    def test_count_records_empty(self):
        """Count with filter that matches nothing."""
        count = self.client.count_records("campaign_tasks",
                                           filter_str="status = 'Nonexistent'")
        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
