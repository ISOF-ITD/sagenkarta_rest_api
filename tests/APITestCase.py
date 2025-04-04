from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

class APITestCase(TestCase):
    """
    API test cases for updating data in database

    Prepare:
    1. Start the Django server: runserver
    2. Start the Python tests for APITestCase.APITestCase.test_start_transcribe_session

    python manage.py test
    """
    def setUp(self):
        self.client = APIClient()
        self.base_url = "/api"
        # self.base_url = "http://localhost:8000/api"
        self.record_id = "s03684:a_f_128326_0"
        self.transcribe_session = "2025-02-28 16:21:33"

    def tearDown(self):
        self.client.post(f"{self.base_url}/transcribecancel", {"recordid": self.record_id, "transcribesession": self.transcribe_session}, format='json')

    def test_start_transcribe_session(self):
        response = self.client.post(f"{self.base_url}/transcribestart", {"recordid": self.record_id}, format='json')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertIn("success", response.json())

    def test_update_utterance(self):
        self.test_start_transcribe_session()
        data = {
            "recordid": self.record_id,
            "file": "Lund/Ljudarkiv/3001-4000/3601-3700/S 3684A Byarum SMÅL.MP3",
            "transcribesession": self.transcribe_session,
            "from_email": "pertest3@isof.se",
            "from_name": "pertest3",
            "speaker": "A",
            "start_from": "0.3",
            "change_from": "skurit av havren",
            "change_to": "skurit i havren"
        }
        response = self.client.post(f"{self.base_url}/utterances/change/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("success", response.json())

    def test_update_description(self):
        self.test_start_transcribe_session()
        data = {
            "recordid": self.record_id,
            "file": "Lund/Ljudarkiv/3001-4000/3601-3700/S 3684A Byarum SMÅL.MP3",
            "transcribesession": self.transcribe_session,
            "from_email": "pertest@isof.se",
            "from_name": "pertest",
            "start_from": "15:05",
            "change_from": "Jakthistorier på vilda björnar",
            "change_to": "Jakthistorier på flera björnar"
        }
        response = self.client.post(f"{self.base_url}/describe/change/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("success", response.json())

    def test_update_transcribe(self):
        self.test_start_transcribe_session()
        data = {
            "transcribesession": self.transcribe_session,
            "recordid": self.record_id,
            "from_email": "pertest@isof.se",
            "from_name": "pertest",
            "message": "I Kinnekulle berg fanns 2024-11-19.. TESTPER",
            "messageComment": "Svår stil"
        }
        response = self.client.post(f"{self.base_url}/transcribe/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("success", response.json())

    def test_update_transcribe_with_page(self):
        self.test_start_transcribe_session()
        data = {
            "transcribesession": self.transcribe_session,
            "recordid": self.record_id,
            "page": "uppteckningar/liu_00100-00199/liu00198_0029.jpg",
            "from_email": "pertest@isof.se",
            "from_name": "pertest",
            "message": "I Kinnekulle berg fanns 2024-11-19.. TESTPER",
            "messageComment": "Svår stil"
        }
        response = self.client.post(f"{self.base_url}/transcribe/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("success", response.json())
