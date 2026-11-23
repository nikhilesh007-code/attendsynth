import unittest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal
from backend.models import DatasetModel, StudentModel

class TestAIQueryFlow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_ai_query_defensive_dataset_resolution(self):
        # 1. Normal query with active dataset
        active = self.db.query(DatasetModel).filter(DatasetModel.is_active == True).first()
        if not active:
            active = self.db.query(DatasetModel).first()
        self.assertIsNotNone(active, "At least one dataset must exist in DB")

        res = self.client.post(
            f"/api/ai/query?dataset_id={active.id}",
            json={"query": "Analyze attendance trend"}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("status", data)
        self.assertIn("response", data)

    def test_ai_query_short_message(self):
        # Verify that short queries like 'hi' are accepted and do NOT return 422
        res = self.client.post(
            "/api/ai/query",
            json={"query": "hi"}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success") or data.get("is_fallback"))

if __name__ == "__main__":
    unittest.main()
