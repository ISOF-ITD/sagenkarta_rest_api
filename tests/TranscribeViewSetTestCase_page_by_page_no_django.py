import unittest
from datetime import datetime

import requests
import json

import logging
logger = logging.getLogger(__name__)

class APITranscribeViewTestCasePageByPage(unittest.TestCase):
    """
    API test cases for updating data in the database.
    This test case is independent of Django and can be executed in the shell.

    Run in shell:
    1. Kör API-server
        cd /home/per/dev/server/folkeservice/sagenkarta_rest_api/
        source ../current_venv/bin/activate
        folkeservice runserver
    2. Check transcriptionstatus is "ready to transcribe"
        https://garm-test.isof.se/TradarkAdmin/admin/TradarkAdmin/records/liu00198_5F194713_5F1/change/?_changelist_filters=q%3Dliu00198_194713
    3. Start test
    python3 tests/TranscribeViewSetTestCase_page_by_page_no_django.py 2> TranscribeViewSetTestCase_no_django1.html
    python3 tests/TranscribeViewSetTestCase_page_by_page_no_django.py > TranscribeViewSetTestCase_page_by_page_no_django_$(date +"%Y-%m-%d:%H%M")-log.txt 2> TranscribeViewSetTestCase_page_by_page_no_django_$(date +"%Y-%m-%d:%H%M")-result.txt
    4. Validate tests
    Check output files: *-result.txt and if error *-log.txt
    Example *-result.txt:
        Ran 2 tests in 8.493s
        OK (skipped=1)
    Check data in for example TradarkAdmin
        https://garm-test.isof.se/TradarkAdmin/admin/TradarkAdmin/recordsmediareview
    Check text data for file in concerned record:
        https://garm-test.isof.se/folkeservice/api/records/10789_X_27860_1/
        (https://garm-test.isof.se/folkeservice/api/records/liu00198_194713_1/)
        https://garm-test.isof.se/TradarkAdmin/admin/TradarkAdmin/recordsmediareview/1553540/change/
    """
    base_url = "http://localhost:8000/api"
    # base_url = "https://garm-test.isof.se/folkeservice/api"
    # base_url = "https://garm.isof.se/folkeservice/api"
    # record_id_page_by_page = "10789_27860_1"
    record_id_page_by_page = "10789_X_27860_1"
    page_file_to_transcribe = "uppteckningar/ulma_10700-10799/10789_0001.jpg"
    # page_file_to_cancel = "uppteckningar/ulma_10700-10799/10789_0002.jpg"
    transcribe_session = "2025-02-28 16:21:33"
    use_slash = "/"
    #use_slash = ""

    @classmethod
    def setUpClass(cls):
        """
        https://garm-test.isof.se/folkeservice/api/transcribestart/
        {
    	"responseHeaders": {
		"headers": [
			{
				"name": "access-control-allow-origin",
				"value": "*"
			},
			{
				"name": "Content-Type",
				"value": "application/json"
			},
			..
        ------geckoformboundarya88288bfeaadd591d31a3cabbaab21e0
        Content-Disposition: form-data; name="json"

        {"recordid":"ifgh00702_195386_1"}
        ------geckoformboundarya88288bfeaadd591d31a3cabbaab21e0--
        """
        logid = "setUpClass /transcribestart"
        # Start the transcription session
        # response = requests.post(f"{cls.base_url}/transcribestart" + cls.use_slash,
        data = {"recordid": cls.record_id_page_by_page}
        # headers={"Content-Type": "application/json"}

        # USED in client for transcribe: request as file
        # USED in client for transcribe: request as file
        headers=None
        files = {
            # "json": (None, data)  # (filename, content)
            # Convert the dictionary to a JSON string
            "json": (None, json.dumps(data))  # (filename, content as JSON string)
        }
        # print(logid + ' ' +f"transcribesession: {str(cls.transcribesession)}")
        print(logid + ' ' + str(data))
        print(logid + ' ' + str(files))
        print(logid + ' ' + str(headers))
        response=requests.post(f"{cls.base_url}/transcribestart" + cls.use_slash,
                                 files=files, headers=headers)

        # NOT USED in client for transcribe: request as json dict
        # response=requests.post(f"{cls.base_url}/transcribestart" + cls.use_slash, json=data, headers=headers)
        # json={"json": {"recordid": cls.record_id}})
        # logger.debug("test Transcribe/start" + str(response))
        cls.log_response(response, logid)

        response_json = response.json()
        success_value = response_json.get('success')
        data = response_json.get('data')
        recordid = data.get('recordid') if data else None

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
        # Cancel the transcription session
        logid = "tearDownClass transcribecancel"
        data = {
            "transcribesession": cls.transcribe_session,
            "recordid": cls.record_id_page_by_page,
        }
        # headers={"Content-Type": "application/json"}

        # USED in client for transcribe: request as file
        headers=None
        files = {
            # "json": (None, data)  # (filename, content)
            # Convert the dictionary to a JSON string
            "json": (None, json.dumps(data))  # (filename, content as JSON string)
        }
        # print(logid + ' ' +f"transcribesession: {str(cls.transcribesession)}")
        print(logid + ' ' + str(data))
        print(logid + ' ' + str(files))
        print(logid + ' ' + str(headers))
        response=requests.post(f"{cls.base_url}/transcribecancel" + cls.use_slash,
                                 files=files, headers=headers)

        # data = {"recordid": cls.record_id_page_by_page, "transcribesession": cls.transcribe_session}
        # response = requests.post(f"{cls.base_url}/transcribecancel" + cls.use_slash, json=data)
        cls.log_response(response, logid)
        assert response.status_code == 200, f"Failed to cancel transcription: {response.text}"
        if response.json():
            # If transcribesession already cancelled as it should:
            assert response.json().get(
                "success") == 'true', f"Expected 'success' to be true, but got: {response.json().get('success')}"
            # If transcribesession not cancelled as it should:
            #assert response.json().get(
            #    "success") == 'true', f"Expected 'success' to be true, but got: {response.json().get('success')}"
        # cls.assertIn("success", response.json(), f"Unexpected response: {response.json()}")

    def test_01_transcribe_page(self):
        logid = "test_01_transcribe_page /transcribe/"
        timestamp_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(logid + " " + timestamp_now)
        data = {
            "transcribesession": self.transcribe_session,
            "recordid": self.record_id_page_by_page,
            "page": self.page_file_to_transcribe,
            "from_email": "pertest@isof.se",
            "from_name": "pertest",
            "message": "Fastlag och påsk. Svar på .. " + logid + " " + timestamp_now,
            "messageComment": "Förfärlig stil"
        }

        # USED in client for transcribe: request as file
        headers=None
        files = {
            # Convert the dictionary to a JSON string
            "json": (None, json.dumps(data))  # (filename, content as JSON string)
        }
        print(logid + ' ' +f"Transcribe session: {self.transcribe_session}")
        print(logid + ' ' + str(data))
        print(logid + ' ' + str(files))
        print(logid + ' ' + str(headers))
        response=requests.post(f"{self.base_url}/transcribe" + self.use_slash,
                                files=files, headers=headers)

        # NOT USED in client for transcribe:
        # response = requests.post(f"{self.base_url}/transcribe/", json=data)
        self.log_response(response, logid)
        self.assertEqual(response.status_code, 200, f"Unexpected status code: {response.status_code}")
        self.assertIn("success", response.json(), f"Unexpected response: {response.json()}")

    # Skip for now as cancel test in tear down class
    @unittest.skip("Test not yet implemented")
    def test_90_transcribe_cancel(self):
        """
        ------geckoformboundaryb8fa1b7e162dc763e9dbc229353ec808
        Content-Disposition: form-data; name="json"

        {"recordid":"ifgh00702_195386_1","transcribesession":"2025-04-11 14:00:50.692"}
        ------geckoformboundaryb8fa1b7e162dc763e9dbc229353ec808--
        """
        logid = "test_transcribe_cancel /transcribecancel/"
        data = {
            "transcribesession": self.transcribe_session,
            "recordid": self.record_id_page_by_page,
        }
        # headers={"Content-Type": "application/json"}

        # USED in client for transcribe: request as file
        headers=None
        files = {
            # Convert the dictionary to a JSON string
            "json": (None, json.dumps(data))  # (filename, content as JSON string)
        }
        print(logid + ' ' + str(data))
        print(logid + ' ' + str(files))
        print(logid + ' ' + str(headers))
        response=requests.post(f"{self.base_url}/transcribecancel" + self.use_slash,
                                 files=files, headers=headers)

        # NOT USED in client for transcribe:
        #response = requests.post(f"{self.base_url}/transcribecancel/", json=data)
        self.log_response(response, logid)
        self.assertEqual(response.status_code, 200, f"Unexpected status code: {response.status_code}")
        self.assertIn("success", response.json(), f"Unexpected response: {response.json()}")

if __name__ == "__main__":
    unittest.main()