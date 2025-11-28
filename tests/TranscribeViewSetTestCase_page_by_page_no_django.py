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
    I. Setup
    1. Kör API-server
        cd /home/per/dev/server/folkeservice/sagenkarta_rest_api/
        source ../current_venv/bin/activate
        folkeservice runserver
    2. Check transcriptionstatus is "ready to transcribe"
        https://garm-test.isof.se/TradarkAdmin/admin/TradarkAdmin/records/liu00198_5F194713/change/?_changelist_filters=q%3Dliu00198_194713
	3. Setup testdata
	Setup by SQL UNTIL setup in testcase
	record:
	select id, changedate, left(transcriptiondate, 16) as transcr_date, left(user_session_date, 16) as session_date, left(title,10), left(text,10), transcribedby, transcriptionstatus, transcriptiontype FROM svenska_sagor.records r
	-- update svenska_sagor.records r
	set transcriptionstatus = 'readytotranscribe'
	where type = 'arkiv'
	and record_type = 'one_accession_row'
	-- Omregistrering inför nytt test:
	-- and transcriptionstatus in ('undertranscription', 'transcribed')
	and r.id in ('10789_X_27860', 'ifgh00702_X_195386')

	records_media:
    select record, transcriptionstatus, replace(rm.source,'uppteckningar/','') as filepath, changedate, left(transcriptiondate, 16) as transcr_date, title, right(text,30), pagenumber, fonetic_signs, unreadable, transcription_comment, comment, transcribedby, transcriptiontype FROM svenska_sagor.records_media rm
    -- select * FROM svenska_sagor.records_media rm
    -- update svenska_sagor.records_media rm
    -- set transcriptionstatus = 'readytotranscribe'
    where type = 'image'
    and right(source,4) = '.jpg'
    -- Omregistrering inför nytt test:
    -- and transcriptionstatus in ('undertranscription', 'transcribed', 'published', 'autopublished')
    -- and transcriptionstatus in ('transcribed')
    and rm.source in ("uppteckningar/ulma_10700-10799/10789_0001.jpg", "uppteckningar/ifgh_00700-00799/ifgh00702_0002.jpg", "uppteckningar/ifgh_00700-00799/ifgh00702_0003.jpg")
    and record in ('10789_X_27860', 'ifgh00702_X_195386')

    II. Test
    0. Set up environment
    cd /home/per/dev/server/folkeservice/sagenkarta_rest_api/
    source ../current_venv/bin/activate
    1. Start test
    # python3 tests/TranscribeViewSetTestCase_page_by_page_no_django.py 2> TranscribeViewSetTestCase_no_django1.html
    python3 tests/TranscribeViewSetTestCase_page_by_page_no_django.py > TranscribeViewSetTestCase_page_by_page_no_django_$(date +"%Y-%m-%d:%H%M")-log.txt 2> TranscribeViewSetTestCase_page_by_page_no_django_$(date +"%Y-%m-%d:%H%M")-result.txt
    2. Validate tests
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
    # OLD: Transcribe is done in one_record
    # record_id_page_by_page = "10789_27860_1"
    # record_id_page_by_page = "10789_X_27860_1"
    # From 2025-11-XX: Transcribe is done in one_accession_row
    record_id_page_by_page_1 = "10789_X_27860"
    transcribe_session_1 = "2025-02-28 16:21:33"
    page_file_to_transcribe_1 = "uppteckningar/ulma_10700-10799/10789_0001.jpg"
    message_1 = "Fastlag och påsk. Svar på .. "
    messageComment_1 = "Förfärlig stil"

    record_id_page_by_page_2 = "ifgh00702_X_195386"
    transcribe_session_2 = "2025-02-28 16:21:33"
    page_file_to_transcribe_2a = "uppteckningar/ifgh_00700-00799/ifgh00702_0002.jpg"
    message_2a = "Nu är påsken den glada tid .. "
    messageComment_2a = "Fritext Svår stil"
    page_file_to_transcribe_2b = "uppteckningar/ifgh_00700-00799/ifgh00702_0003.jpg"
    title_2b = "Fastlag och påsk"
    message_2b = "Nu är påsken den glada tid .. "
    messageComment_2b = "Uppteckningsblankett Svår stil"
    # page_file_to_cancel = "uppteckningar/ulma_10700-10799/10789_0002.jpg"
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
        # ----------------------------------------------
        # Start 1
        # Start the transcription session
        # response = requests.post(f"{cls.base_url}/transcribestart" + cls.use_slash,
        data = {"recordid": cls.record_id_page_by_page_1}
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
        cls.transcribe_session_1 = data.get("transcribesession", None)
        print(logid + ' ' +f"Transcribe session: {cls.transcribe_session_1}")
        assert response.status_code in [200, 201], f"Failed to start transcription: {response.text}"
        assert "success" in response.json(), f"Unexpected response: {response.json()}"

    @classmethod
    def test_02_transcribe_start(self):
        logid = "test_02_transcribe_start /transcribestart"
        # ----------------------------------------------
        # Start 2
        # Start the transcription session
        # response = requests.post(f"{cls.base_url}/transcribestart" + cls.use_slash,
        data = {"recordid": self.record_id_page_by_page_2}
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
        response=requests.post(f"{self.base_url}/transcribestart" + self.use_slash,
                                 files=files, headers=headers)

        # NOT USED in client for transcribe: request as json dict
        # response=requests.post(f"{cls.base_url}/transcribestart" + cls.use_slash, json=data, headers=headers)
        # json={"json": {"recordid": cls.record_id}})
        # logger.debug("test Transcribe/start" + str(response))
        self.log_response(response, logid)

        response_json = response.json()
        success_value = response_json.get('success')
        data = response_json.get('data')
        recordid = data.get('recordid') if data else None

        print(logid + ' ' +f"Success: {success_value}")
        print(logid + ' ' +f"Record ID: {recordid}")
        self.transcribe_session_2 = data.get("transcribesession", None)
        print(logid + ' ' +f"Transcribe session: {self.transcribe_session_2}")
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
            "transcribesession": cls.transcribe_session_1,
            "recordid": cls.record_id_page_by_page_1,
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

		# ----------------------------------
        # Cancel the transcription session 2
        logid = "tearDownClass transcribecancel"
        data = {
            "transcribesession": cls.transcribe_session_2,
            "recordid": cls.record_id_page_by_page_2,
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

    def test_11_transcribe_page(self):
        logid = "test_11_transcribe_page /transcribe/"
        timestamp_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(logid + " " + timestamp_now)
        message = str(self.message_1) + logid + " " + timestamp_now
        data = {
            "transcribesession": self.transcribe_session_1,
            "recordid": self.record_id_page_by_page_1,
            "page": self.page_file_to_transcribe_1,
            "from_email": "testuser1@isof.se",
            "from_name": "Test User",
            "message": message,
            "pagenumber": "1",
            "fonetic_signs": "Y",
            "unreadable": True,
            "messageComment": str(self.messageComment_1)
        }

        # USED in client for transcribe: request as file
        headers=None
        files = {
            # Convert the dictionary to a JSON string
            "json": (None, json.dumps(data))  # (filename, content as JSON string)
        }
        print(logid + ' ' +f"Transcribe session: {self.transcribe_session_1}")
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

    def test_12_transcribe_page(self):
        logid = "test_12_transcribe_page /transcribe/"
        timestamp_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(logid + " " + timestamp_now)
        message = str(self.message_2a) + logid + " " + timestamp_now
        data = {
            "transcribesession": self.transcribe_session_2,
            "recordid": self.record_id_page_by_page_2,
            "page": self.page_file_to_transcribe_2a,
            "from_email": "testuser1@isof.se",
            "from_name": "Test User",
            "pagenumber": "2A",
            "fonetic_signs": "N",
            "unreadable": False,
            "message": message,
            "messageComment": str(self.messageComment_2a)
        }

        # USED in client for transcribe: request as file
        headers=None
        files = {
            # Convert the dictionary to a JSON string
            "json": (None, json.dumps(data))  # (filename, content as JSON string)
        }
        print(logid + ' ' +f"Transcribe session: {self.transcribe_session_2}")
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

    def test_03_transcribe_page(self):
        logid = "test_03_2b_transcribe_page /transcribe/"
        timestamp_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(logid + " " + timestamp_now)
        message = str(self.message_2b) + logid + " " + timestamp_now
        data = {
            "transcribesession": self.transcribe_session_2,
            "recordid": self.record_id_page_by_page_2,
            "page": self.page_file_to_transcribe_2b,
            "from_email": "testuser2@isof.se",
            "from_name": "Test User Ny",
            "message": message,
            "messageComment": str(self.messageComment_2b)
        }

        # USED in client for transcribe: request as file
        headers=None
        files = {
            # Convert the dictionary to a JSON string
            "json": (None, json.dumps(data))  # (filename, content as JSON string)
        }
        print(logid + ' ' +f"Transcribe session: {self.transcribe_session_2}")
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
            "transcribesession": self.transcribe_session_1,
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