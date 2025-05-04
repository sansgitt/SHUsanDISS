import pytest
import os
import sys
import tempfile
from unittest.mock import patch

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app as flask_app

@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    # Create a temporary file to use as a test image
    test_image = tempfile.NamedTemporaryFile(suffix='.jpg')
    with open(test_image.name, 'wb') as f:
        f.write(b'dummy image content')
    
    # Set up application config for testing
    flask_app.config.update({
        'TESTING': True,
        'MONGO_URI': 'mongodb://localhost:27017/breedclassify_test',
        'UPLOAD_FOLDER': tempfile.mkdtemp(),
        'PROCESSED_FOLDER': tempfile.mkdtemp(),
    })
    
    # Create necessary directories
    os.makedirs(flask_app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(flask_app.config['PROCESSED_FOLDER'], exist_ok=True)
    os.makedirs('static/game_images', exist_ok=True)
    
    # Mock the MongoDB connection
    with patch('app.mongo') as mock_mongo:
        # Mock the TensorFlow model
        with patch('app.model') as mock_model:
            yield flask_app
    
    # Clean up
    test_image.close()
    os.rmdir(flask_app.config['UPLOAD_FOLDER'])
    os.rmdir(flask_app.config['PROCESSED_FOLDER'])

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test CLI runner for the app."""
    return app.test_cli_runner()

@pytest.fixture
def auth_client(client):
    """A test client with an authenticated session."""
    with client.session_transaction() as session:
        session['user_id'] = 'test_user_id'
        session['user_name'] = 'Test User'
        session['user_email'] = 'test@example.com'
    return client

@pytest.fixture
def mock_db():
    """Mock database functions."""
    with patch('app.mongo.db') as mock_db:
        yield mock_db

@pytest.fixture
def mock_model():
    """Mock the TensorFlow model."""
    with patch('app.model') as mock_model:
        # Set up default prediction behavior
        mock_model.predict.return_value = [
            # Species prediction (Cat)
            [[0.8, 0.2]],
            # Breed prediction
            [[0.05, 0.1, 0.2, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05,
              0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05]]
        ]
        yield mock_model
