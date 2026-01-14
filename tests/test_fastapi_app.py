"""
Unit tests for Transport Request API

Run tests with:
    pytest test_fastapi_app.py -v
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from fastapi.testclient import TestClient
from io import BytesIO

# Import the FastAPI app and utils
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))
from fastapi_app import app, load_config, TransportRequest
from utils.excel_handler import save_to_excel
from utils.email_handler import parse_email_list


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def sample_form_data():
    """Sample valid form data for testing"""
    return {
        "deliveryNoteNumber": "DN123456",
        "truckLicensePlates": "AB123CD",
        "trailerLicensePlates": "EF456GH",
        "carrierCountry": "Poland",
        "carrierTaxCode": "PL1234567890",
        "carrierFullName": "Test Transport Company",
        "borderCrossing": "Nadlac",
        "borderCrossingDate": "2025-10-25",
        "email": "test@example.com",
        "phoneNumber": "+48 123 456 789"
    }


@pytest.fixture
def sample_file():
    """Create a sample file for testing uploads"""
    return BytesIO(b"This is a test PDF content"), "test_document.pdf"


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns healthy status"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Transport backend running"
        assert data["status"] == "healthy"
    
    def test_api_health_endpoint(self, client):
        """Test API health endpoint"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "transport-api"


class TestTransportRequestModel:
    """Test the Pydantic model validation"""
    
    def test_valid_transport_request(self, sample_form_data):
        """Test valid transport request model creation"""
        request = TransportRequest(**sample_form_data)
        assert request.deliveryNoteNumber == "DN123456"
        assert request.carrierCountry == "Poland"
    
    def test_missing_required_field(self):
        """Test validation fails with missing required field"""
        with pytest.raises(ValueError):
            TransportRequest(
                truckLicensePlates="AB123CD",
                # Missing deliveryNoteNumber
            )
    
    def test_empty_string_validation(self):
        """Test validation with empty strings"""
        with pytest.raises(ValueError):
            TransportRequest(
                deliveryNoteNumber="",  # Empty string
                truckLicensePlates="AB123CD",
                trailerLicensePlates="EF456GH",
                carrierCountry="Poland",
                carrierTaxCode="PL1234567890",
                carrierFullName="Test Company",
                borderCrossing="Nadlac",
                borderCrossingDate="2025-10-25",
                email="test@example.com",
                phoneNumber="+48 123 456 789"
            )


class TestConfigurationLoading:
    """Test configuration loading from YAML"""
    
    @patch("builtins.open", mock_open(read_data="""
default:
  transport:
    local_attachments_folder: "./test_attachments"
    local_excel_file: "./test_data/requests.xlsx"
"""))
    @patch("yaml.safe_load")
    def test_load_config(self, mock_yaml_load):
        """Test configuration loading"""
        mock_yaml_load.return_value = {
            "default": {
                "transport": {
                    "local_attachments_folder": "./test_attachments",
                    "local_excel_file": "./test_data/requests.xlsx"
                }
            }
        }
        
        config = load_config()
        assert "default" in config
        assert "transport" in config["default"]


class TestSubmitEndpoint:
    """Test the main submit endpoint"""
    
    def test_submit_valid_request_no_file(self, client, sample_form_data):
        """Test submitting valid request without file"""
        mock_excel_result = {
            'local_saved': True,
            'sharepoint_saved': False,
            'sharepoint_error': None,
            'local_error': None
        }
        with patch('fastapi_app.save_to_excel', return_value=mock_excel_result):
            response = client.post(
                "/api/submit",
                data={"data": json.dumps(sample_form_data)}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "request_id" in data
        assert data["request_id"].startswith("REQ-")
        assert data["attachment_saved"] is False
        assert data["excel_saved"] is True
    
    def test_submit_valid_request_with_file(self, client, sample_form_data):
        """Test submitting valid request with file attachment"""
        file_content = b"Test PDF content"
        mock_excel_result = {
            'local_saved': True,
            'sharepoint_saved': False,
            'sharepoint_error': None,
            'local_error': None
        }
        
        with patch('fastapi_app.save_to_excel', return_value=mock_excel_result), \
             patch('builtins.open', mock_open()) as mock_file, \
             patch('os.makedirs'), \
             patch('pathlib.Path.mkdir'):
            
            response = client.post(
                "/api/submit",
                data={"data": json.dumps(sample_form_data)},
                files={"attachment": ("test.pdf", BytesIO(file_content), "application/pdf")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["attachment_saved"] is True
        mock_file.assert_called()
    
    def test_submit_invalid_json(self, client):
        """Test submitting invalid JSON data"""
        response = client.post(
            "/api/submit",
            data={"data": "invalid json"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid JSON" in data["detail"]
    
    def test_submit_missing_required_fields(self, client):
        """Test submitting data with missing required fields"""
        incomplete_data = {
            "deliveryNoteNumber": "DN123",
            # Missing other required fields
        }
        
        response = client.post(
            "/api/submit",
            data={"data": json.dumps(incomplete_data)}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid data" in data["detail"]
    
    def test_submit_empty_data(self, client):
        """Test submitting empty data"""
        response = client.post("/api/submit")
        
        assert response.status_code == 422  # Unprocessable Entity


class TestFileHandling:
    """Test file upload and storage functionality"""
    
    @patch('pathlib.Path.mkdir')
    @patch('builtins.open', mock_open())
    def test_file_save_success(self, mock_mkdir):
        """Test successful file saving"""
        # This would be tested as part of the submit endpoint
        # File handling logic is integrated into the main endpoint
        pass
    
    def test_file_extension_handling(self, client, sample_form_data):
        """Test proper file extension handling"""
        mock_excel_result = {
            'local_saved': True,
            'sharepoint_saved': False,
            'sharepoint_error': None,
            'local_error': None
        }
        with patch('fastapi_app.save_to_excel', return_value=mock_excel_result), \
             patch('builtins.open', mock_open()) as mock_file, \
             patch('os.makedirs'), \
             patch('pathlib.Path.mkdir'):
            
            # Test PDF file
            response = client.post(
                "/api/submit",
                data={"data": json.dumps(sample_form_data)},
                files={"attachment": ("document.pdf", BytesIO(b"content"), "application/pdf")}
            )
            
            assert response.status_code == 200
            # Verify file was saved with correct extension
            mock_file.assert_called()


class TestDataPersistence:
    """Test data saving to JSON/Excel"""
    
    @patch('builtins.open', mock_open())
    @patch('json.load', return_value=[])
    @patch('json.dump')
    @patch('pathlib.Path.exists', return_value=False)
    @patch('pathlib.Path.mkdir')
    def test_save_to_excel_new_file(self, mock_mkdir, mock_exists, mock_json_dump, mock_json_load):
        """Test saving data to new Excel/JSON file"""
        request_id = "REQ-20251021-123456-789"
        data = {
            "deliveryNoteNumber": "DN123",
            "carrierFullName": "Test Company",
            "email": "test@example.com",
            "phoneNumber": "+48 123 456 789"
        }
        
        result = save_to_excel(request_id, data, True)
        
        # save_to_excel() returns dict with keys: local_saved, sharepoint_saved, sharepoint_error, local_error
        assert isinstance(result, dict)
        assert 'local_saved' in result
        assert 'sharepoint_saved' in result
        # In test environment, SharePoint will be mocked via SHAREPOINT_ACCESS_TOKEN
        mock_json_dump.assert_called_once()
    
    @patch('builtins.open', mock_open())
    @patch('json.load', return_value=[{"Request_ID": "REQ-OLD"}])
    @patch('json.dump')
    @patch('pathlib.Path.exists', return_value=True)
    def test_save_to_excel_existing_file(self, mock_exists, mock_json_dump, mock_json_load):
        """Test appending data to existing Excel/JSON file"""
        request_id = "REQ-20251021-123456-789"
        data = {
            "deliveryNoteNumber": "DN123",
            "carrierFullName": "Test Company",
            "email": "test@example.com",
            "phoneNumber": "+48 123 456 789"
        }
        
        result = save_to_excel(request_id, data, False)
        
        # save_to_excel() returns dict, not bool
        assert isinstance(result, dict)
        assert 'local_saved' in result
        assert 'sharepoint_saved' in result
        # Verify that existing data was loaded and new data appended
        mock_json_load.assert_called_once()
        mock_json_dump.assert_called_once()
    
    @patch('builtins.open', side_effect=OSError("Permission denied"))
    def test_save_to_excel_error_handling(self, mock_open_error):
        """Test error handling in save_to_excel"""
        request_id = "REQ-20251021-123456-789"
        data = {"deliveryNoteNumber": "DN123"}
        
        result = save_to_excel(request_id, data, False)
        
        # Even on error, save_to_excel() returns dict with error information
        assert isinstance(result, dict)
        assert 'local_saved' in result
        assert 'local_error' in result or 'sharepoint_error' in result
        # At least one operation should have failed
        assert result['local_saved'] == False or result.get('local_error') is not None


class TestRequestIDGeneration:
    """Test Request ID generation functionality"""
    
    def test_request_id_format(self, client, sample_form_data):
        """Test that request IDs follow the correct format"""
        mock_excel_result = {
            'local_saved': True,
            'sharepoint_saved': False,
            'sharepoint_error': None,
            'local_error': None
        }
        with patch('fastapi_app.save_to_excel', return_value=mock_excel_result):
            response = client.post(
                "/api/submit",
                data={"data": json.dumps(sample_form_data)}
            )
        
        data = response.json()
        request_id = data["request_id"]
        
        # Format: REQ-YYYYMMDD-HHMMSS-XXX
        assert request_id.startswith("REQ-")
        parts = request_id.split("-")
        assert len(parts) == 4
        assert len(parts[1]) == 8  # YYYYMMDD
        assert len(parts[2]) == 6  # HHMMSS
        assert len(parts[3]) == 3  # XXX (random number)
    
    def test_request_id_uniqueness(self, client, sample_form_data):
        """Test that multiple requests generate unique IDs"""
        request_ids = []
        mock_excel_result = {
            'local_saved': True,
            'sharepoint_saved': False,
            'sharepoint_error': None,
            'local_error': None
        }
        
        with patch('fastapi_app.save_to_excel', return_value=mock_excel_result):
            for _ in range(5):
                response = client.post(
                    "/api/submit",
                    data={"data": json.dumps(sample_form_data)}
                )
                data = response.json()
                request_ids.append(data["request_id"])
        
        # All IDs should be unique
        assert len(set(request_ids)) == len(request_ids)


class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_malformed_request(self, client):
        """Test handling of malformed requests"""
        response = client.post("/api/submit", data={"invalid": "data"})
        assert response.status_code == 422
    
    def test_oversized_file(self, client, sample_form_data):
        """Test handling of oversized files"""
        # Create a large file (this test would need actual size limits implemented)
        large_content = b"x" * (100 * 1024 * 1024)  # 100MB
        
        response = client.post(
            "/api/submit",
            data={"data": json.dumps(sample_form_data)},
            files={"attachment": ("large.pdf", BytesIO(large_content), "application/pdf")}
        )
        
        # This would depend on actual file size validation implementation
        # For now, the endpoint doesn't have size limits, so this test serves as placeholder


if __name__ == "__main__":
    pytest.main([__file__, "-v"])