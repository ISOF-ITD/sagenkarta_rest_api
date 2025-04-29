import json
import unittest
from datetime import datetime

import requests

import logging
logger = logging.getLogger(__name__)

class APIDescribeViewTestCase(unittest.TestCase):
    """
    API test cases for updating data in the database.
    This test case is independent of Django and can be executed in the shell.

    Run in shell:
    1. Kör API-server
        cd /home/per/dev/server/folkeservice/sagenkarta_rest_api/
        source ../current_venv/bin/activate
        folkeservice runserver
    2. Check transcriptionstatus is "ready to transcribe"
        https://garm-test.isof.se/TradarkAdmin/admin/TradarkAdmin/records/s03684:a_f_128326_a/change/?_changelist_filters=q%3Ds03684:a_f_128326
    3. Start test
    python3 tests/DescribeViewSetTestCase_no_django.py 2> DescribeViewSetTestCase_no_django1.html
    python3 tests/DescribeViewSetTestCase_no_django.py > DescribeViewSetTestCase_no_django_$(date +"%Y-%m-%d:%H%M").txt 2> DescribeViewSetTestCase_no_django_$(date +"%Y-%m-%d:%H%M").html
    4. Validate tests
    Check output files
    Check data in for example TradarkAdmin
        https://garm-test.isof.se/TradarkAdmin/admin/TradarkAdmin/textchanges/
        https://garm-test.isof.se/TradarkAdmin/admin/TradarkAdmin/recordsmediareview
    Check json data for file in concerned record:
        https://garm-test.isof.se/folkeservice/api/records/s03684:a_f_128326_a/

    TODO: Assertions does not work
    """
    # base_url = "https://garm-test.isof.se/folkeservice/api"
    base_url = "http://localhost:8000/api"
    # Real public record:
    # record_id = "s03684:a_f_128326_a"
    # Record only for testing:
    record_id = "s03684:a_f_X_128326_a"
    # Manual tests:
    #file = "Lund/Ljudarkiv/3001-4000/3601-3700/S 3684A Byarum SMÅL.MP3",
    # Automatic tests
    file = "Lund/Ljudarkiv/3001-4000/3601-3700/S 3684B Byarum SMÅL.MP3"
    transcribe_session = "2025-02-28 16:21:33"
    use_slash = "/"
    #use_slash = ""

    @classmethod
    def setUpClass(cls):
        # Start the transcription session
        # response = requests.post(f"{cls.base_url}/transcribestart" + cls.use_slash,
        response=requests.post(f"{cls.base_url}/describe/start" + cls.use_slash,
                                 json={"recordid": cls.record_id})
        # json={"json": {"recordid": cls.record_id}})
        # logger.debug(prefix + " " + str(response))
        cls.log_response(response, "setUpClass /describe/start")

        response_json = response.json()
        success_value = response_json.get('success')
        data = response_json.get('data')
        recordid = data.get('recordid') if data else None

        print(f"Success: {success_value}")
        print(f"Record ID: {recordid}")
        cls.transcribe_session = data.get("transcribesession", None)
        print(f"Transcribe session: {cls.transcribe_session}")
        assert response.status_code in [200, 201], f"Failed to start transcription: {response.text}"
        assert "success" in response.json(), f"Unexpected response: {response.json()}"

    @classmethod
    def log_response(cls, response, prefix):
        if response is None:
            print(prefix + " " + str(response))
        else:
            print(prefix + " " + str(response.status_code))
            print(prefix + " " + str(response.headers))
            print(prefix + " " + str(response.content))
            # print(prefix + " " + str(response.json()))
            # print(prefix + " " + str(response.text))

    @classmethod
    def tearDownClass(cls):
        logid = "tearDownClass transcribecancel"

        data = {
            "transcribesession": cls.transcribe_session,
            "recordid": cls.record_id,
        }
        # headers={"Content-Type": "application/json"}
        # data = {"recordid": cls.record_id, "transcribesession": cls.transcribe_session}
        # data = {"json": {"recordid": cls.record_id, "transcribesession": cls.transcribe_session}}
        # response = requests.post(f"{cls.base_url}/transcribecancel" + cls.use_slash, json=data)

        # USED in client for transcribe: request as file
        headers=None
        files = {
            # "json": (None, data)  # (filename, content)
            # Convert the dictionary to a JSON string
            "json": (None, json.dumps(data))  # (filename, content as JSON string)
        }
        print(logid)
        print(data)
        print(files)
        response=requests.post(f"{cls.base_url}/transcribecancel" + cls.use_slash,
                                 files=files, headers=headers)

        # NOT USED in client for transcribe:
        #response = requests.post(f"{self.base_url}/transcribecancel/", json=data)
        cls.log_response(response, logid)
        cls.assertEqual(response.status_code, 200, f"Unexpected status code: {response.status_code}")
        cls.assertIn("success", response.json(), f"Unexpected response: {response.json()}")
        assert response.status_code == 200, f"Failed to cancel transcription: {response.text}"

    def test_01_delete_description(self):
        # url_path = "/describe/delete/"
        logid = "test_delete_description /describe/delete"
        data = {
            "recordid": self.record_id,
            "file": self.file,
            "transcribesession": self.transcribe_session,
            "from_email": "pertest@isof.se",
            "from_name": "pertest",
            "start": "3:05",
        }
        print(logid)
        print(data)
        response = requests.post(f"{self.base_url}/describe/delete/", json=data)
        self.log_response(response, logid)
        # Check why we get status code 400 and it still works?
        self.assertEqual(response.status_code, 200, f"Unexpected status code: {response.status_code}")
        # self.assertIn("success", response.json(), f"Unexpected response: {response.json()}")

    def test_02_create_description(self):
        logid = "test_create_description /describe/change"
        # Get the current timestamp as a string
        timestamp_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(timestamp_now)
        data = {
            "recordid": self.record_id,
            "file": self.file,
            "transcribesession": self.transcribe_session,
            "from_email": "pertest@isof.se",
            "from_name": "pertest",
            "start": "3:05",
            "change_to": "Jakthistorier på flera björnar to DELETE " + logid + " " + timestamp_now
        }
        print(data)
        response = requests.post(f"{self.base_url}/describe/change/", json=data)
        self.log_response(response, logid)
        self.assertEqual(response.status_code, 200, f"Unexpected status code: {response.status_code}")
        # self.assertIn("success", response.json(), f"Unexpected response: {response.json()}")

    def test_03_create_description(self):
        logid = "test_create_description /describe/change"
        # Get the current timestamp as a string
        timestamp_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(timestamp_now)
        data = {
            "recordid": self.record_id,
            "file": self.file,
            "transcribesession": self.transcribe_session,
            "from_email": "pertest@isof.se",
            "from_name": "pertest",
            "start": "5:05",
            "change_to": "Jakthistorier på flera björnar " + logid + " " + timestamp_now
        }
        print(data)
        response = requests.post(f"{self.base_url}/describe/change/", json=data)
        self.log_response(response, logid)
        self.assertEqual(response.status_code, 200, f"Unexpected status code: {response.status_code}")
        # self.assertIn("success", response.json(), f"Unexpected response: {response.json()}")

    def test_10_update_description(self):
        logid = "test_update_description /describe/change"
        # Get the current timestamp as a string
        timestamp_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(timestamp_now)
        data = {
            "recordid": self.record_id,
            "file": self.file,
            "transcribesession": self.transcribe_session,
            "from_email": "pertest@isof.se",
            "from_name": "pertest",
            "start_from": "5:05",
            "change_from": "Jakthistorier på vilda björnar",
            "change_to": "Jakthistorier på flera björnar " +  logid +  " " + timestamp_now
        }
        print(data)
        response = requests.post(f"{self.base_url}/describe/change/", json=data)
        self.log_response(response, logid)
        self.assertEqual(response.status_code, 200, f"Unexpected status code: {response.status_code}")
        self.assertEqual(response.json().get("message"), "Text updated successfully.",
                         f"Unexpected response: {response.json()}")

    def test_11_update_description_no_user(self):
        logid = "test_update_description_no_user /describe/change"
        # Get the current timestamp as a string
        timestamp_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(timestamp_now)
        data = {
            "recordid": self.record_id,
            "file": self.file,
            "transcribesession": self.transcribe_session,
            "start_from": "5:05",
            "change_from": "Jakthistorier på vilda björnar",
            "change_to": "Jakthistorier på flera björnar " + logid + " " + timestamp_now
        }
        print(data)
        response = requests.post(f"{self.base_url}/describe/change/", json=data)
        self.log_response(response, logid)
        self.assertEqual(response.status_code, 200, f"Unexpected status code: {response.status_code}")
        # self.assertIn("success", response.json(), f"Unexpected response: {response.json()}")

    def test_20_create_description_terms(self):
        logid = "test_create_description /describe/change"
        # Get the current timestamp as a string
        timestamp_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(timestamp_now)
        data = {
            "recordid": self.record_id,
            "file": self.file,
            "transcribesession": self.transcribe_session,
            "from_email": "pertest@isof.se",
            "from_name": "pertest",
            "start": "4:05",
            "change_to": "Starta kolmila " + logid + " " + timestamp_now,
            "terms": [
                {
                    "term": "Kolning",
                    "termid": "B.V.3."
                }
            ]
        }
        print(data)
        response = requests.post(f"{self.base_url}/describe/change/", json=data)
        self.log_response(response, logid)
        self.assertEqual(response.status_code, 200, f"Unexpected status code: {response.status_code}")
        # self.assertIn("success", response.json(), f"Unexpected response: {response.json()}")


    def test_21_update_description_terms(self):
        logid = "test_update_description /describe/change"
        # Get the current timestamp as a string
        timestamp_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(timestamp_now)
        data = {
            "recordid": self.record_id,
            "file": self.file,
            "transcribesession": self.transcribe_session,
            "from_email": "pertest@isof.se",
            "from_name": "pertest",
            "start_from": "4:05",
            "change_from": "Starta kolmila",
            "change_to": "Starta kolmila  " +  logid +  " " + timestamp_now,
            "terms":
                [
                    {
                        "term": "Kolning",
                        "termid": "B.V.3."
                    }
                ]
        }
        print(data)
        response = requests.post(f"{self.base_url}/describe/change/", json=data)
        self.log_response(response, logid)
        self.assertEqual(response.status_code, 200, f"Unexpected status code: {response.status_code}")
        # self.assertIn("success", response.json(), f"Unexpected response: {response.json()}")

if __name__ == "__main__":
    unittest.main()