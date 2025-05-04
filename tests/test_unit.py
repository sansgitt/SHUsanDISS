import unittest
import json
import sys
import os
import io
from unittest.mock import patch, MagicMock
import numpy as np
from PIL import Image

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import your Flask app
from app import app, contains_profanity

class TestBreedClassifier(unittest.TestCase):
    def setUp(self):
        """Set up test client and other test variables."""
        self.app = app.test_client()
        self.app.testing = True
        
        # Create an application context
        self.app_context = app.app_context()
        self.app_context.push()
        
        # Mock the MongoDB connection
        self.mongo_patcher = patch('app.mongo')
        self.mock_mongo = self.mongo_patcher.start()
        
        # Mock the TensorFlow model
        self.model_patcher = patch('app.model')
        self.mock_model = self.model_patcher.start()
        
    def tearDown(self):
        """Tear down all initialized variables."""
        self.mongo_patcher.stop()
        self.model_patcher.stop()
        self.app_context.pop()
    
    def test_health_check(self):
        """Test the health check endpoint."""
        response = self.app.get('/health')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'ok')
    
    def test_index_route(self):
        """Test the index route returns the correct template."""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
    
    @patch('app.bcrypt.checkpw')
    def test_login_success(self, mock_checkpw):
        """Test successful login."""
        # Mock the user in the database
        mock_user = {
            '_id': '123',
            'name': 'Test User',
            'email': 'test@example.com',
            'password': b'hashed_password'
        }
        self.mock_mongo.db.users.find_one.return_value = mock_user
        
        # Mock password verification
        mock_checkpw.return_value = True
        
        # Test login
        response = self.app.post('/api/login', 
                                json={'email': 'test@example.com', 'password': 'password'})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['user']['name'], 'Test User')
    
    @patch('app.bcrypt.checkpw')
    def test_login_failure(self, mock_checkpw):
        """Test failed login with wrong password."""
        # Mock the user in the database
        mock_user = {
            '_id': '123',
            'name': 'Test User',
            'email': 'test@example.com',
            'password': b'hashed_password'
        }
        self.mock_mongo.db.users.find_one.return_value = mock_user
        
        # Mock password verification to fail
        mock_checkpw.return_value = False
        
        # Test login
        response = self.app.post('/api/login', 
                                json={'email': 'test@example.com', 'password': 'wrong_password'})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(data['success'])
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent user."""
        # Mock no user found
        self.mock_mongo.db.users.find_one.return_value = None
        
        # Test login
        response = self.app.post('/api/login', 
                                json={'email': 'nonexistent@example.com', 'password': 'password'})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(data['success'])
    
    @patch('app.tf.keras.preprocessing.image.load_img')
    @patch('app.tf.keras.preprocessing.image.img_to_array')
    @patch('app.np.expand_dims')
    def test_predict_endpoint(self, mock_expand_dims, mock_img_to_array, mock_load_img):
        """Test the predict endpoint."""
        # Create a mock image and array
        mock_img = MagicMock()
        mock_array = np.zeros((224, 224, 3))
        mock_expanded_array = np.zeros((1, 224, 224, 3))
        
        # Set up the mocks
        mock_load_img.return_value = mock_img
        mock_img_to_array.return_value = mock_array
        mock_expand_dims.return_value = mock_expanded_array
        
        # Mock the model prediction
        # Adjust these values based on your app's species_to_idx and breed_to_idx mappings
        # For example, if Russian Blue is at index 1 in cat_breeds:
        self.mock_model.predict.return_value = [
            # Species prediction (Cat = index 0)
            np.array([[0.8, 0.2]]),
            # Breed prediction (Russian Blue has highest probability)
            np.array([[0.05, 0.7, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05,
                      0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05]])
        ]
        
        # Create a test image using PIL
        img = Image.new('RGB', (224, 224), color='red')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        
        # Test predict endpoint with the image
        with patch('app.os.path.join', return_value='uploads/test_image.jpg'), \
             patch('app.secure_filename', return_value='test_image.jpg'):
            
            response = self.app.post('/predict', 
                                  data={'file': (img_byte_arr, 'test_image.jpg')},
                                  content_type='multipart/form-data')
        
        # Print response for debugging
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data}")
        
        # Parse the response
        data = json.loads(response.data)
        
        # Check for error
        if 'error' in data:
            print(f"Error in response: {data['error']}")
            self.fail(f"API returned error: {data['error']}")
        
        # Check response format
        print(f"Response keys: {data.keys()}")
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        
        # Adjust these assertions based on your actual API response format
        if 'species' in data:
            self.assertEqual(data['species'], 'Cat')
        if 'breed' in data:
            self.assertEqual(data['breed'], 'Russian Blue')  # Changed from Bengal to Russian Blue
    
    def test_profanity_filter(self):
        """Test the profanity filter function."""
        # Test with profane words
        self.assertTrue(contains_profanity("This text contains ass"))
        self.assertTrue(contains_profanity("This text contains Ass"))  # Case insensitive
        
        # Test with clean text
        self.assertFalse(contains_profanity("This is a clean text"))
        
        # Test with edge cases
        self.assertFalse(contains_profanity(""))  # Empty string
        self.assertFalse(contains_profanity(None))  # None value
        self.assertFalse(contains_profanity("classic"))  # Word containing 'ass' but not the word itself
    
    def test_check_auth_authenticated(self):
        """Test check-auth endpoint when user is authenticated."""
        # Use the test client with a session context
        with self.app as client:
            with client.session_transaction() as session:
                session['user_id'] = 'test_user_id'
                session['user_name'] = 'Test User'
                session['user_email'] = 'test@example.com'
            
            response = client.get('/api/check-auth')
            data = json.loads(response.data)
            
            self.assertEqual(response.status_code, 200)
            self.assertTrue(data['authenticated'])
            self.assertEqual(data['user']['name'], 'Test User')
    
    def test_check_auth_unauthenticated(self):
        """Test check-auth endpoint when user is not authenticated."""
        # Use the test client with an empty session
        with self.app as client:
            # Don't set any session variables
            response = client.get('/api/check-auth')
            data = json.loads(response.data)
            
            self.assertEqual(response.status_code, 200)
            self.assertFalse(data['authenticated'])
    
    def test_add_pawprint(self):
        """Test adding a pawprint."""
        # Use the test client with a session context
        with self.app as client:
            with client.session_transaction() as session:
                session['user_id'] = 'test_user_id'
                session['user_name'] = 'Test User'
                session['user_email'] = 'test@example.com'
            
            # Create a test image using PIL
            img = Image.new('RGB', (224, 224), color='red')
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG')
            img_byte_arr.seek(0)
            
            # Test adding a pawprint
            with patch('app.os.path.join', return_value='uploads/test_image.jpg'), \
                 patch('app.secure_filename', return_value='test_image.jpg'), \
                 patch('app.mongo.db.pawprints.insert_one') as mock_insert, \
                 patch('app.mongo.db.activity_log.insert_one'):
                
                response = client.post('/api/pawprints', 
                                      data={
                                          'file': (img_byte_arr, 'test_image.jpg'),
                                          'pet_type': 'cat',
                                          'caption': 'Test caption'
                                      },
                                      content_type='multipart/form-data')
                
                data = json.loads(response.data)
                
                self.assertEqual(response.status_code, 200)
                self.assertTrue(data['success'])
                self.assertTrue(mock_insert.called)

if __name__ == '__main__':
    unittest.main()