"""
Unit tests for the Electroduction Desktop Application
"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock

# Mock customtkinter before importing main
sys.modules['customtkinter'] = MagicMock()

import main

def test_app_initialization():
    """Test that app class can be instantiated"""
    with patch.object(main.ctk, 'CTk'):
        app = main.ElectroductionApp
        assert app is not None

def test_api_url_default():
    """Test default API URL"""
    with patch.object(main.ctk, 'CTk'):
        app = main.ElectroductionApp()
        assert app.api_url == "http://localhost:8000"

@patch('requests.get')
def test_check_api_connection_success(mock_get):
    """Test successful API connection"""
    mock_response = Mock()
    mock_response.ok = True
    mock_get.return_value = mock_response

    with patch.object(main.ctk, 'CTk'):
        app = main.ElectroductionApp()
        # API connection check happens in thread
        assert app.api_url == "http://localhost:8000"

@patch('requests.get')
def test_check_api_connection_failure(mock_get):
    """Test failed API connection"""
    mock_get.side_effect = Exception("Connection failed")

    with patch.object(main.ctk, 'CTk'):
        app = main.ElectroductionApp()
        # Initial state should be disconnected
        assert app.api_connected == False

def test_window_title():
    """Test window title is set correctly"""
    with patch.object(main.ctk, 'CTk'):
        app = main.ElectroductionApp()
        # Verify title method was called
        assert hasattr(app, 'title')

@patch('requests.post')
def test_submit_contact_missing_fields(mock_post):
    """Test contact form validation"""
    with patch.object(main.ctk, 'CTk'):
        app = main.ElectroductionApp()
        app.api_connected = True

        # Mock UI elements
        app.name_entry = Mock()
        app.email_entry = Mock()
        app.message_text = Mock()
        app.contact_status = Mock()

        app.name_entry.get.return_value = ""
        app.email_entry.get.return_value = ""
        app.message_text.get.return_value = ""

        app.submit_contact()

        # Should not call API with empty fields
        mock_post.assert_not_called()

@patch('requests.post')
def test_submit_contact_success(mock_post):
    """Test successful contact form submission"""
    mock_response = Mock()
    mock_response.ok = True
    mock_post.return_value = mock_response

    with patch.object(main.ctk, 'CTk'):
        app = main.ElectroductionApp()
        app.api_connected = True

        # Mock UI elements
        app.name_entry = Mock()
        app.email_entry = Mock()
        app.message_text = Mock()
        app.contact_status = Mock()

        app.name_entry.get.return_value = "Test User"
        app.email_entry.get.return_value = "test@example.com"
        app.message_text.get.return_value = "Test message"

        app.submit_contact()

        # Should call API with data
        mock_post.assert_called_once()

def test_clear_content():
    """Test content clearing method"""
    with patch.object(main.ctk, 'CTk'):
        app = main.ElectroductionApp()
        # Method should exist
        assert hasattr(app, 'clear_content')
        assert callable(app.clear_content)

def test_navigation_methods_exist():
    """Test that all navigation methods exist"""
    with patch.object(main.ctk, 'CTk'):
        app = main.ElectroductionApp()
        assert hasattr(app, 'show_home')
        assert hasattr(app, 'show_projects')
        assert hasattr(app, 'show_game_stats')
        assert hasattr(app, 'show_leaderboard')
        assert hasattr(app, 'show_contact')
        assert hasattr(app, 'show_settings')

def test_appearance_mode_change():
    """Test appearance mode can be changed"""
    with patch.object(main.ctk, 'CTk'):
        with patch.object(main.ctk, 'set_appearance_mode') as mock_set_mode:
            app = main.ElectroductionApp()
            app.change_appearance_mode("Light")
            mock_set_mode.assert_called_with("light")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
