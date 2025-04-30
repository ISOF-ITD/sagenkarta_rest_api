import unittest
from datetime import datetime

import requests
import json

import logging
logger = logging.getLogger(__name__)

class APIUtteranceViewTestCase(unittest.TestCase):
    """
    API test cases for updating data in the database.
    This test case is independent of Django and can be executed in the shell.

    Run in shell:
    Run in shell:
    1. Kör API-server
        cd /home/per/dev/server/folkeservice/sagenkarta_rest_api/
        source ../current_venv/bin/activate
        folkeservice runserver
    2. Check transcriptionstatus is "ready to transcribe"
        https://garm-test.isof.se/TradarkAdmin/admin/TradarkAdmin/records/liu00198_5F194713_5F1/change/?_changelist_filters=q%3Dliu00198_194713
    3. Start test
    python3 tests/UtteranceViewSetTestCase_no_django.py 2> UtteranceViewSetTestCase_no_django1.html
    python3 tests/UtteranceViewSetTestCase_no_django.py > UtteranceViewSetTestCase_no_django_$(date +"%Y-%m-%d:%H%M")-log.txt 2> UtteranceViewSetTestCase_no_django_$(date +"%Y-%m-%d:%H%M")-results.txt
    4. Validate tests
    Check output files: *-result.txt and if error *-log.txt
    Example *-result.txt:
        Ran 2 tests in 8.493s
        OK (skipped=1)
    Check data in for example TradarkAdmin
        https://garm-test.isof.se/TradarkAdmin/admin/TradarkAdmin/recordsmediareview
    Check text data for file in concerned record:
        https://garm-test.isof.se/folkeservice/api/records/s00247:a_f_127613_a/
        https://garm-test.isof.se/TradarkAdmin/admin/TradarkAdmin/recordsmediareview/?/change/
    """
    base_url = "http://localhost:8000/api"
    record_id = "s00247:a_f_127613_a"
    file = "Lund/Ljudarkiv/1-1000/201-300/S 247A_mp3.MP3"
    transcribe_session = "2025-02-28 16:21:33"
    use_slash = "/"
    #use_slash = ""

    @classmethod
    def setUpClass(cls):
        logid = "setUpClass utterance"
        # Start the transcription session
        response=requests.post(f"{cls.base_url}/description/start" + cls.use_slash,
                                 json={"recordid": cls.record_id})
        # json={"json": {"recordid": cls.record_id}})
        # logger.debug("test Utterance/start" + str(response))
        cls.log_response(response, logid)

        response_json = response.json()
        success_value = response_json.get('success')
        data = response_json.get('data')
        recordid = data.get('recordid') if data else None

        # print(logid + ' ' +f"transcribesession: {str(cls.transcribesession)}")
        print(logid + ' ' +f"Success: {success_value}")
        print(logid + ' ' +f"Record ID: {recordid}")
        cls.transcribe_session = data.get("transcribesession", None)
        print(logid + ' ' +f"Transcribe session: {cls.transcribe_session}")
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

        # USED in client for transcribe: request as file
        headers=None
        files = {
            # "json": (None, data)  # (filename, content)
            # Convert the dictionary to a JSON string
            "json": (None, json.dumps(data))  # (filename, content as JSON string)
        }
        print(logid + ' ' + str(data))
        print(logid + ' ' + str(files))
        # print(logid + ' ' +f"transcribesession: {str(cls.transcribesession)}")
        response=requests.post(f"{cls.base_url}/transcribecancel" + cls.use_slash,
                                 files=files, headers=headers)

        # NOT USED in client for transcribe:
        #response = requests.post(f"{self.base_url}/transcribecancel/", json=data)
        cls.log_response(response, logid)
        # cls.assertEqual(response.status_code, 200, f"Unexpected status code: {response.status_code}")
        cls.assertIn("success", str(response.json()), f"Unexpected response: {response.json()}")
        assert response.status_code == 200, f"Failed to cancel transcription: {response.text}"

    def test_10_update_utterance(self):
        logid = "test_10_update_utterance /describe/change"
        timestamp_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data = {
            "recordid": self.record_id,
            "file": self.file,
            "transcribesession": self.transcribe_session,
            "from_email": "pertest3@isof.se",
            "from_name": "pertest3",
            "speaker": "A",
            "start_from": "0.3",
            "change_from": "skurit av havren",
            "change_to": "skurit i havren" + logid + " " + timestamp_now
        }
        print(logid + ' ' + str(data))
        # print(logid + ' ' + str(files))
        response = requests.post(f"{self.base_url}/utterances/change/", json=data)
        self.log_response(response, logid)
        self.assertEqual(response.status_code, 200, f"Unexpected status code: {response.status_code}")
        # self.assertIn("success", response.json(), f"Unexpected response: {response.json()}")

if __name__ == "__main__":
    unittest.main()