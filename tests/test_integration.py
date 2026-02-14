import unittest
import os
import json
import time
from client import PocketBaseClient
from config import POCKETBASE_URL, POCKETBASE_USER, POCKETBASE_PASSWORD

class TestPocketBaseIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Use config credentials (which should now be valid superuser creds)
        cls.client = PocketBaseClient(POCKETBASE_URL, POCKETBASE_USER, POCKETBASE_PASSWORD)
        print(f"Testing against {POCKETBASE_URL} with user {POCKETBASE_USER}")

    def test_01_authentication(self):
        """Test authentication flow."""
        self.client.authenticate()
        self.assertIsNotNone(self.client.token)
        print("Authentication successful")

    def test_02_list_collections(self):
        """Test listing collections."""
        collections = self.client.list_collections()
        self.assertIsInstance(collections, list)
        self.assertTrue(len(collections) > 0)
        
        # Check if expected collections exist
        names = [c["name"] for c in collections]
        self.assertIn("users", names)
        if "brand_identities" in names:
            print("Found brand_identities collection")

    def test_03_get_schema(self):
        """Test fetching schema for a collection."""
        # Try users collection which always exists
        schema = self.client.get_collection_schema("users")
        self.assertIsInstance(schema, dict)
        self.assertEqual(schema["name"], "users")
        
        # Check for fields (v0.36 uses fields)
        fields = schema.get("fields", schema.get("schema"))
        self.assertIsNotNone(fields)
        self.assertTrue(len(fields) > 0)
        
        # Check specific field
        field_names = [f["name"] for f in fields]
        self.assertIn("email", field_names)

    def test_04_create_record_validation_error(self):
        """Test handling of validation errors (reproduce user reported error)."""
        # brand_identities requires brandName. Try creating without it.
        # If brand_identities doesn't exist, skip or try another.
        try:
            self.client.get_collection_schema("brand_identities")
        except:
            print("Skipping validation test: brand_identities collection not found")
            return

        with self.assertRaises(RuntimeError) as cm:
            self.client.create_record("brand_identities", {
                "slogan": "No brand name"
            })
        
        # Verify error message contains details
        error_msg = str(cm.exception)
        print(f"Caught expected validation error: {error_msg}")
        self.assertIn("PocketBase API Error", error_msg)
        self.assertIn("brandName", error_msg)
        self.assertTrue("cannot be blank" in error_msg.lower())

    def test_05_record_lifecycle(self):
        """Test CRUD operations."""
        # Create a test user (clean up after)
        test_email = f"test_integration_{int(time.time())}@example.com"
        password = "Password123!"
        
        # 1. Create
        print(f"Creating test user {test_email}...")
        try:
            user = self.client.create_record("users", {
                "email": test_email,
                "password": password,
                "passwordConfirm": password,
                "name": "Integration Test User"
            })
            self.assertIsNotNone(user)
            self.assertEqual(user["email"], test_email)
            user_id = user["id"]
        except RuntimeError as e:
            self.fail(f"Failed to create record: {e}")

        # 2. Read
        print(f"Reading user {user_id}...")
        fetched_user = self.client.get_record("users", user_id)
        self.assertEqual(fetched_user["id"], user_id)
        self.assertEqual(fetched_user["email"], test_email)

        # 3. Update
        print(f"Updating user {user_id}...")
        updated_user = self.client.update_record("users", user_id, {
            "name": "Updated Name"
        })
        self.assertEqual(updated_user["name"], "Updated Name")

        # 4. Delete
        print(f"Deleting user {user_id}...")
        result = self.client.delete_record("users", user_id)
        self.assertTrue(result)
        
        # Verify deletion
        with self.assertRaises(RuntimeError):
            self.client.get_record("users", user_id)

if __name__ == "__main__":
    unittest.main()
