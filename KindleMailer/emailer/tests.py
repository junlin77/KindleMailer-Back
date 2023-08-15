from django.test import TestCase
import tempfile
from django.test import TestCase
from django.http import HttpResponse
from unittest.mock import patch, Mock
from django.test import TestCase
from emailer.helpers import *

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

