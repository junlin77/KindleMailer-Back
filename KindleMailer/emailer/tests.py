import tempfile
from django.test import TestCase, Client, RequestFactory
from django.http import HttpResponse
from unittest.mock import patch, Mock
from django.test import TestCase
from emailer.helpers import *
from django.http import HttpRequest
from .views import search_api, send_to_kindle_api, login_api, KindleEmailAPI
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIRequestFactory
from requests_mock import Mocker
from emailer.models import UserProfile 


class EmailValidationTestCase(TestCase):

    def test_valid_email(self):
        # Test case for a valid email address
        email = 'test@example.com'
        result = validate_email(email)
        self.assertTrue(result)

    def test_invalid_email(self):
        # Test case for an invalid email address
        email = 'invalid-email'
        result = validate_email(email)
        self.assertFalse(result)

    def test_empty_email(self):
        # Test case for an empty email address
        email = ''
        result = validate_email(email)
        self.assertFalse(result)

class IterateDownloadLinksCase(TestCase):

    @patch('urllib.request.urlopen')
    def test_failed_iterate_download(self, mock_urlopen):
        # Mock the urlopen function to raise an exception for all URLs
        mock_urlopen.side_effect = Exception('Failed to download from all URLs.')

        # Create a mock URL dictionary
        url = {
            "key1": "http://example.com/url1",
            "key2": "http://example.com/url2"
        }

        # Call the function under test
        response = iterate_download_links(url)

        # Assert that the function returns an HttpResponse with the expected message
        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Failed to download from all URLs.")

        # Assert that urlopen was called with the correct URLs
        mock_urlopen.assert_any_call("http://example.com/url1")
        mock_urlopen.assert_any_call("http://example.com/url2")

class SaveFileAndDeleteFileCase(TestCase):

    @patch('builtins.open', create=True)
    def test_save_file_success(self, mock_open):
        # Create a mock response object
        mock_response = Mock()
        mock_response.read.return_value = b"Mock File Content"

        # Set up the mock file path and media root directory
        file_path = '/path/to/file.ext'

        # Mock the os.path.exists function to return True
        with patch('os.path.exists', return_value=True):
            # Call the function under test
            result = save_file_in_media_root(mock_response, file_path)

        # Assert that the file was opened and written correctly
        mock_open.assert_called_once_with(file_path, 'wb')
        mock_open.return_value.__enter__.return_value.write.assert_called_once_with(b"Mock File Content")

        # Assert that the function returns True
        self.assertTrue(result)

    @patch('builtins.open', create=True)
    def test_save_file_failure(self, mock_open):
        # Create a mock response object
        mock_response = Mock()
        mock_response.read.return_value = b"Mock File Content"

        # Set up the mock file path and media root directory
        file_path = '/path/to/file.ext'

        # Mock the os.path.exists function to return False
        with patch('os.path.exists', return_value=False):
            # Call the function under test
            result = save_file_in_media_root(mock_response, file_path)

        # Assert that the file was opened and written correctly
        mock_open.assert_called_once_with(file_path, 'wb')
        mock_open.return_value.__enter__.return_value.write.assert_called_once_with(b"Mock File Content")

        # Assert that the function returns False
        self.assertFalse(result)

class SendEmailTestCase(TestCase):

    @patch('django.core.mail.EmailMessage.send')
    def test_send_email_with_attachment_success(self, mock_send):
        # Mock the email sending
        mock_send.return_value = None

        # Define the test data
        email_address = 'test@example.com'

        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b'Test content')

        try:
            # Call the function being tested
            result = send_email_with_attachment(email_address, temp_file.name)

            # Assertions
            self.assertTrue(result)
            mock_send.assert_called_once()
        finally:
            # Clean up the temporary file
            os.remove(temp_file.name)

    @patch('django.core.mail.EmailMessage.send')
    def test_send_email_with_attachment_failure(self, mock_send):
        # Mock the email sending
        mock_send.side_effect = Exception('Failed to send email')

        # Define the test data
        email_address = 'test@example.com'

        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b'Test content')

        try:
            # Call the function being tested
            result = send_email_with_attachment(email_address, temp_file.name)

            # Assertions
            self.assertFalse(result)
            mock_send.assert_called_once()
        finally:
            # Clean up the temporary file
            os.remove(temp_file.name)

class DeleteFileTestCase(TestCase):

    @patch('os.path.exists')
    @patch('os.remove')
    def test_delete_file(self, mock_remove, mock_exists):
        # Mock the necessary dependencies
        file_path = "path/to/file"
        mock_exists.return_value = True

        # Call the function
        delete_file(file_path)

        # Assert the function behavior
        mock_exists.assert_called_once_with(file_path)
        mock_remove.assert_called_once_with(file_path)

class SearchAPITestCase(TestCase):
    @patch("emailer.views.LibgenSearch")
    def test_search_api(self, mock_libgen_search):
        mock_libgen_search_instance = mock_libgen_search.return_value
        mock_libgen_search_instance.search_title.return_value = [
            {"Title": "Book 1", "Author": "Author 1", "Publisher": "Publisher 1", "Year": "2020", "Language": "English",
              "Pages": "100", "Extension": "pdf", "Size": "100MB", "Mirror_1": "http://example.com/url1", "Mirror_2": "http://example.com/url2", "Mirror_3": "http://example.com/url3"},
            {"Title": "Book 2", "Author": "Author 2", "Publisher": "Publisher 2", "Year": "2020", "Language": "English", 
             "Pages": "100", "Extension": "pdf", "Size": "100MB", "Mirror_1": "http://example.com/url1", "Mirror_2": "http://example.com/url2", "Mirror_3": "http://example.com/url3"},
        ]

        # Test case for title search
        mock_request = HttpRequest()
        mock_request.method = "GET"
        mock_request.GET = {
            "title": "Title",
            "author": None,
            "extension": None,
            "publisher": None,
            "year": None,
            "language": None
        }
        response = search_api(mock_request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        print(response.data)

        # Test case for author search
        mock_request.GET = {
            "title": None,
            "author": "Author 2",
            "extension": None,
            "publisher": None,
            "year": None,
            "language": None
        }
        response = search_api(mock_request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

class SendToKindleTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()

    @patch("emailer.helpers.validate_email", return_value=True)
    @patch("emailer.views.LibgenSearch")
    @patch("emailer.helpers.iterate_download_links", return_value="sample_response")
    @patch("emailer.helpers.send_email_with_attachment", return_value=True)
    @patch("emailer.helpers.delete_file")
    @patch("emailer.helpers.save_file_in_media_root", return_value=True)
    def test_valid_email_address(self, mock_save_file, mock_delete_file,
                                 mock_send_email, mock_iterate_links,
                                 mock_libgen_search, mock_validate_email):
        mock_request = self.factory.post(reverse('send_to_kindle_api'), {
            'book_to_download': '{"ID": "123", "Title": "Book Title", "Extension": "pdf"}',
            'kindle_email': 'test@example.com'
        })

        mock_libgen_search_instance = mock_libgen_search.return_value
        mock_libgen_search_instance.resolve_download_links.return_value = "sample_url"

        response = send_to_kindle_api(mock_request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"success": True})
        self.assertTrue(mock_validate_email.called)
        self.assertTrue(mock_iterate_links.called)
        self.assertTrue(mock_send_email.called)
        self.assertTrue(mock_delete_file.called)
        self.assertTrue(mock_save_file.called)

    @patch("emailer.views.validate_email", return_value=False)
    def test_invalid_email_address(self, mock_validate_email):
        response = self.client.post(reverse('send_to_kindle_api'), {
            'book_to_download': '{"ID": "123", "Title": "Book Title", "Extension": "pdf"}',
            'kindle_email': 'invalid_email'
        })
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Invalid email address.")
        self.assertTrue(mock_validate_email.called)

    @patch("emailer.views.validate_email", return_value=True)
    def test_no_email_address(self, mock_validate_email):
        response = self.client.post(reverse('send_to_kindle_api'), {
            'book_to_download': '{"ID": "123", "Title": "Book Title", "Extension": "pdf"}',
            'kindle_email': ''
        })
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "No email address provided.")
        self.assertTrue(mock_validate_email.called)

class LoginAPITestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_login_new_user(self):
        # Mock the Google OAuth2 userinfo response
        with Mocker() as m:
            access_token = "test_access_token"
            userinfo_data = {
                "id": "test_user_id",
                "picture": "https://example.com/profile_picture.jpg"
            }
            m.get(
                f"https://www.googleapis.com/oauth2/v1/userinfo?access_token={access_token}",
                json=userinfo_data,
                status_code=200
            )

            url = reverse("login_api")
            data = {"access_token": access_token}
            request = self.factory.post(url, data)
            response = login_api(request)

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data["message"], "New user profile created")
            self.assertEqual(response.data["profile_picture"], userinfo_data["picture"])
            self.assertEqual(response.data["user_id"], userinfo_data["id"])
            self.assertEqual(response.data["kindle_email"], "")

    def test_login_existing_user(self):
        # Create a test user profile
        UserProfile.objects.create(google_user_id="test_user_id")

        # Mock the Google OAuth2 userinfo response
        with Mocker() as m:
            access_token = "test_access_token"
            userinfo_data = {
                "id": "test_user_id",
                "picture": "https://example.com/profile_picture.jpg"
            }
            m.get(
                f"https://www.googleapis.com/oauth2/v1/userinfo?access_token={access_token}",
                json=userinfo_data,
                status_code=200
            )

            url = reverse("login_api")
            data = {"access_token": access_token}
            request = self.factory.post(url, data)
            response = login_api(request)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["message"], "User already exists")
            self.assertEqual(response.data["profile_picture"], userinfo_data["picture"])
            self.assertEqual(response.data["user_id"], userinfo_data["id"])
            self.assertEqual(response.data["kindle_email"], "")

class KindleEmailAPITestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_get_kindle_email_existing_profile(self):
        # Create a test user profile
        user_profile = UserProfile.objects.create(google_user_id="test_user_id", kindle_email="test@example.com")

        url = reverse("get_kindle_email_api") 
        request = self.factory.get(url, {"user_id": "test_user_id"})
        response = KindleEmailAPI.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"kindle_email": "test@example.com"})

    def test_get_kindle_email_nonexistent_profile(self):
        url = reverse("get_kindle_email_api")  
        request = self.factory.get(url, {"user_id": "nonexistent_user"})
        response = KindleEmailAPI.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"error": "User profile not found"})

    def test_set_kindle_email_success(self):
        # Create a test user profile
        UserProfile.objects.create(google_user_id="test_user_id")

        url = reverse("set_kindle_email_api")  
        data = {
            "user_id": "test_user_id",
            "kindle_email": "new_email@example.com"
        }
        request = self.factory.post(url, data)
        response = KindleEmailAPI.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"message": "Kindle email set successfully"})
        user_profile = UserProfile.objects.get(google_user_id="test_user_id")
        self.assertEqual(user_profile.kindle_email, "new_email@example.com")

    def test_set_kindle_email_invalid_email(self):
        # Create a test user profile
        UserProfile.objects.create(google_user_id="test_user_id")

        url = reverse("set_kindle_email_api")
        data = {
            "user_id": "test_user_id",
            "kindle_email": ""  # Empty email
        }
        request = self.factory.post(url, data)
        response = KindleEmailAPI.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "Kindle email is required"})
        user_profile = UserProfile.objects.get(google_user_id="test_user_id")
        self.assertEqual(user_profile.kindle_email, "")

    def test_set_kindle_email_profile_not_found(self):
        url = reverse("set_kindle_email_api")  
        data = {
            "user_id": "nonexistent_user",
            "kindle_email": "new_email@example.com"
        }
        request = self.factory.post(url, data)
        response = KindleEmailAPI.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"error": "User profile not found"})

    
