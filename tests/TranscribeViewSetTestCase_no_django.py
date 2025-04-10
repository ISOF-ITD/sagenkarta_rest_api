import unittest
import requests
import json
from datetime import datetime

import logging
logger = logging.getLogger(__name__)

class APITranscribeViewTestCase(unittest.TestCase):
    """
    API test cases for updating data in the database.
    This test case is independent of Django and can be executed in the shell.

    Run in shell:
    python3 tests/TranscribeViewSetTestCase_no_django.py 2> TranscribeViewSetTestCase_no_django1.html
    python3 tests/TranscribeViewSetTestCase_no_django.py > TranscribeViewSetTestCase_no_django_$(date +"%Y-%m-%d:%H%M").txt 2> TranscribeViewSetTestCase_no_django_$(date +"%Y-%m-%d:%H%M").html
    """
    base_url = "http://localhost:8000/api"
    record_id = "ifgh00702_195386_1"
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
        #data = '{"recordid":"ifgh00702_195386_1"}'
        data = {"recordid": cls.record_id}
        # headers={"Content-Type": "application/json"}

        # USED in client for transcribe: request as file
        headers=None
        files = {
            # "json": (None, data)  # (filename, content)
            # Convert the dictionary to a JSON string
            "json": (None, json.dumps(data))  # (filename, content as JSON string)
        }
        print(logid)
        print(files)
        print(headers)
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

    def test_transcribe(self):
        """
        https://garm-test.isof.se/folkeservice/api/transcribe/
        ------geckoformboundary1228e4047789406f234bfdd8cc7f20df
        Content-Disposition: form-data; name="json"

        {"transcribesession":"2025-04-11 13:51:07.522","url":"https://sok.folke-test.isof.se/records/ifgh00702_195386_1","recordid":"ifgh00702_195386_1","recordtitle":"Ramsor, påskbrev, gåtor, saga, ordstäv samt öknamn. ","from_email":"pertest@isof.se","from_name":"pertest","subject":"Crowdsource: Transkribering","informantName":"Test Testson","informantBirthDate":"1855","informantBirthPlace":"Trändefors","informantInformation":"Adr. Borekulla","message":"test test testper","messageComment":"per kommentar"}
        ------geckoformboundary1228e4047789406f234bfdd8cc7f20df--
        """
        # Get the current timestamp as a string
        timestamp_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(timestamp_now)
        logid = "test_transcribe /transcribe/"
        data = {
            "transcribesession": self.transcribe_session,
            "recordid": self.record_id,
            "from_email": "pertest@isof.se",
            "from_name": "pertest",
            "message": "I Kinnekulle berg fanns .. " +  logid + " " + timestamp_now,
            "messageComment": "Svår stil"
        }

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
        response=requests.post(f"{self.base_url}/transcribe" + self.use_slash,
                                 files=files, headers=headers)

        # NOT USED in client for transcribe:
        response = requests.post(f"{self.base_url}/transcribe/", json=data)
        self.log_response(response, logid)
        self.assertEqual(response.status_code, 200, f"Unexpected status code: {response.status_code}")
        self.assertIn("success", response.json(), f"Unexpected response: {response.json()}")

    # transcribe cancel only works on status undertranscription
    @unittest.skip("Test not yet implemented")
    def test_transcribe_cancel(self):
        """
        ------geckoformboundaryb8fa1b7e162dc763e9dbc229353ec808
        Content-Disposition: form-data; name="json"

        {"recordid":"ifgh00702_195386_1","transcribesession":"2025-04-11 14:00:50.692"}
        ------geckoformboundaryb8fa1b7e162dc763e9dbc229353ec808--
        """
        logid = "test_transcribe_cancel /transcribecancel/"
        data = {
            "transcribesession": self.transcribe_session,
            "recordid": self.record_id,
        }
        # headers={"Content-Type": "application/json"}

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
        response=requests.post(f"{self.base_url}/transcribecancel" + self.use_slash,
                                 files=files, headers=headers)

        # NOT USED in client for transcribe:
        #response = requests.post(f"{self.base_url}/transcribecancel/", json=data)
        self.log_response(response, logid)
        self.assertEqual(response.status_code, 200, f"Unexpected status code: {response.status_code}")
        self.assertIn("success", response.json(), f"Unexpected response: {response.json()}")

    # @classmethod
    def NOTYETtearDownClass(cls):
        logid = "tearDownClass transcribecancel"
        # Cancel the transcription session
        data = {"recordid": cls.record_id, "transcribesession": cls.transcribe_session}

        # headers={"Content-Type": "application/json"}

        # USED in client for transcribe: request as file
        headers=None
        files = {
            # "json": (None, data)  # (filename, content)
            # Convert the dictionary to a JSON string
            "json": (None, json.dumps(data))  # (filename, content as JSON string)
        }
        response=requests.post(f"{cls.base_url}/transcribecancel" + cls.use_slash,
                                 files=files, headers=headers)

        # NOT USED in client for transcribe:
        #response = requests.post(f"{self.base_url}/transcribecancel/", json=data)
        cls.log_response(response, logid)
        assert response.status_code == 200, f"Failed to cancel transcription: {response.text}"


if __name__ == "__main__":
    unittest.main()