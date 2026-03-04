# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for file operation tools."""

from awslabs.amazon_bedrock_agentcore_code_interpreter_mcp_server.tools import files
from awslabs.amazon_bedrock_agentcore_code_interpreter_mcp_server.tools.files import (
    _validate_sandbox_path,
)
from unittest.mock import MagicMock, patch
import pytest


MODULE_PATH = 'awslabs.amazon_bedrock_agentcore_code_interpreter_mcp_server.tools.files'


class TestValidateSandboxPath:
    """Test cases for _validate_sandbox_path."""

    def test_valid_relative_path(self):
        """Test valid relative paths pass validation."""
        _validate_sandbox_path('data/input.csv')
        _validate_sandbox_path('scripts/run.py')
        _validate_sandbox_path('output.txt')

    def test_rejects_parent_traversal(self):
        """Test rejects paths with .. sequences."""
        with pytest.raises(ValueError, match='Path traversal'):
            _validate_sandbox_path('../../../etc/passwd')

    def test_rejects_mid_path_traversal(self):
        """Test rejects traversal sequences in the middle of a path."""
        with pytest.raises(ValueError, match='Path traversal'):
            _validate_sandbox_path('data/../../etc/passwd')

    def test_rejects_bare_dotdot(self):
        """Test rejects bare .. path."""
        with pytest.raises(ValueError, match='Path traversal'):
            _validate_sandbox_path('..')


class TestUploadFile:
    """Test cases for upload_file."""

    @patch(f'{MODULE_PATH}.get_client')
    async def test_upload_file_happy_path(self, mock_get_client):
        """Test uploading a file returns correct response."""
        # Arrange — SDK requires relative paths
        mock_client = MagicMock()
        mock_client.upload_file.return_value = {}
        mock_get_client.return_value = mock_client

        # Act
        result = await files.upload_file(
            session_id='session-123',
            path='data/input.csv',
            content='col1,col2\n1,2\n3,4',
        )

        # Assert
        assert result['path'] == 'data/input.csv'
        assert result['is_error'] is False
        assert 'successfully' in result['message']
        assert mock_client.session_id == 'session-123'
        mock_client.upload_file.assert_called_once_with(
            path='data/input.csv',
            content='col1,col2\n1,2\n3,4',
        )

    @patch(f'{MODULE_PATH}.get_client')
    async def test_upload_file_with_description(self, mock_get_client):
        """Test uploading a file with description."""
        # Arrange
        mock_client = MagicMock()
        mock_client.upload_file.return_value = {}
        mock_get_client.return_value = mock_client

        # Act
        await files.upload_file(
            session_id='session-123',
            path='scripts/run.py',
            content='print("hello")',
            description='A test script',
        )

        # Assert
        mock_client.upload_file.assert_called_once_with(
            path='scripts/run.py',
            content='print("hello")',
            description='A test script',
        )

    @patch(f'{MODULE_PATH}.get_client')
    async def test_upload_file_absolute_path_rejected(self, mock_get_client):
        """Test SDK raises ValueError for absolute paths."""
        # Arrange — SDK rejects absolute paths with ValueError
        mock_client = MagicMock()
        mock_client.upload_file.side_effect = ValueError('Path must be relative')
        mock_get_client.return_value = mock_client

        # Act
        result = await files.upload_file(
            session_id='session-123',
            path='/tmp/data.csv',
            content='col1,col2\n1,2',
        )

        # Assert
        assert result['is_error'] is True
        assert result['path'] == '/tmp/data.csv'
        assert 'Path must be relative' in result['message']

    @patch(f'{MODULE_PATH}.get_client')
    async def test_upload_file_sdk_exception(self, mock_get_client):
        """Test handles SDK exception gracefully without leaking details."""
        # Arrange
        mock_client = MagicMock()
        mock_client.upload_file.side_effect = Exception('Storage limit exceeded')
        mock_get_client.return_value = mock_client

        # Act
        result = await files.upload_file(
            session_id='session-123',
            path='data/big_file.bin',
            content='x' * 1000,
        )

        # Assert — generic Exception details are sanitized
        assert result['is_error'] is True
        assert result['path'] == 'data/big_file.bin'
        assert 'Storage limit exceeded' not in result['message']
        assert 'internal error' in result['message'].lower()

    async def test_upload_file_path_traversal_rejected(self):
        """Test path traversal attempt is rejected before reaching SDK."""
        result = await files.upload_file(
            session_id='session-123',
            path='../../etc/passwd',
            content='malicious',
        )

        assert result['is_error'] is True
        assert 'Path traversal' in result['message']


class TestDownloadFile:
    """Test cases for download_file."""

    @patch(f'{MODULE_PATH}.get_client')
    async def test_download_file_string_response(self, mock_get_client):
        """Test downloading a file with string response (SDK returns Union[str, bytes])."""
        # Arrange
        mock_client = MagicMock()
        mock_client.download_file.return_value = 'raw file content'
        mock_get_client.return_value = mock_client

        # Act
        result = await files.download_file(
            session_id='session-123',
            path='output/result.txt',
        )

        # Assert
        assert result['path'] == 'output/result.txt'
        assert result['content'] == 'raw file content'
        assert result['is_error'] is False
        assert mock_client.session_id == 'session-123'
        mock_client.download_file.assert_called_once_with(path='output/result.txt')

    @patch(f'{MODULE_PATH}.get_client')
    async def test_download_file_bytes_response(self, mock_get_client):
        """Test downloading a file with bytes response decoded to UTF-8."""
        # Arrange
        mock_client = MagicMock()
        mock_client.download_file.return_value = b'binary content'
        mock_get_client.return_value = mock_client

        # Act
        result = await files.download_file(
            session_id='session-123',
            path='output/data.bin',
        )

        # Assert
        assert result['content'] == 'binary content'
        assert result['is_error'] is False

    @patch(f'{MODULE_PATH}.get_client')
    async def test_download_file_not_found(self, mock_get_client):
        """Test SDK raises FileNotFoundError for missing files."""
        # Arrange
        mock_client = MagicMock()
        mock_client.download_file.side_effect = FileNotFoundError('nonexistent.txt')
        mock_get_client.return_value = mock_client

        # Act
        result = await files.download_file(
            session_id='session-123',
            path='nonexistent.txt',
        )

        # Assert
        assert result['is_error'] is True
        assert result['path'] == 'nonexistent.txt'
        assert 'nonexistent.txt' in result['message']

    @patch(f'{MODULE_PATH}.get_client')
    async def test_download_file_sdk_exception(self, mock_get_client):
        """Test handles generic SDK exception gracefully without leaking details."""
        # Arrange
        mock_client = MagicMock()
        mock_client.download_file.side_effect = Exception('Connection error')
        mock_get_client.return_value = mock_client

        # Act
        result = await files.download_file(
            session_id='session-123',
            path='output/file.txt',
        )

        # Assert — generic Exception details are sanitized
        assert result['is_error'] is True
        assert result['path'] == 'output/file.txt'
        assert 'Connection error' not in result['message']
        assert 'internal error' in result['message'].lower()

    async def test_download_file_path_traversal_rejected(self):
        """Test path traversal attempt is rejected before reaching SDK."""
        result = await files.download_file(
            session_id='session-123',
            path='../../../secrets.txt',
        )

        assert result['is_error'] is True
        assert 'Path traversal' in result['message'] or 'traversal' in result['message'].lower()

    @patch(f'{MODULE_PATH}.get_client')
    async def test_download_file_with_region(self, mock_get_client):
        """Test downloading a file with explicit region."""
        # Arrange — SDK returns str directly
        mock_client = MagicMock()
        mock_client.download_file.return_value = 'regional data'
        mock_get_client.return_value = mock_client

        # Act
        await files.download_file(
            session_id='session-123',
            path='output/file.txt',
            region='ap-northeast-1',
        )

        # Assert
        mock_get_client.assert_called_once_with('ap-northeast-1')
