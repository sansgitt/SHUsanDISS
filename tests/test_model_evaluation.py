import unittest
import numpy as np
import tensorflow as tf
import sys
import os
from unittest.mock import patch, MagicMock

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import your app
from app import app, model, idx_to_breed, idx_to_species

class TestModelEvaluation(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.app = app.test_client()
        self.app.testing = True
    
    def test_model_prediction_format(self):
        """Test that the model returns predictions in the expected format."""
        # Create a small random image array (3 channels RGB)
        test_image = np.random.rand(1, 224, 224, 3).astype(np.float32)
        
        # Get predictions
        predictions = model.predict(test_image)
        
        # Check that we get two prediction arrays (species and breed)
        self.assertEqual(len(predictions), 2)
        
        # Check species predictions shape (should be [1, 2] for Cat/Dog)
        self.assertEqual(predictions[0].shape[1], 2)
        
        # Check breed predictions shape (should be [1, 24] for all breeds)
        self.assertEqual(predictions[1].shape[1], 24)
        
        # Check that probabilities sum to approximately 1
        self.assertAlmostEqual(np.sum(predictions[0][0]), 1.0, places=5)
        self.assertAlmostEqual(np.sum(predictions[1][0]), 1.0, places=5)
    
    def test_calculate_mae(self):
        """Test calculating MAE for model predictions."""
        # Create mock ground truth and predictions
        y_true = np.array([0, 1, 0, 0])  # One-hot encoded true label (e.g., Bengal)
        y_pred = np.array([0.1, 0.7, 0.1, 0.1])  # Predicted probabilities
        
        # Calculate MAE
        mae = np.mean(np.abs(y_true - y_pred))
        
        # Expected MAE: (0.1 + 0.3 + 0.1 + 0.1) / 4 = 0.15
        self.assertAlmostEqual(mae, 0.15)
        
        # Calculate RMAE (Root MAE)
        rmae = np.sqrt(mae)
        self.assertAlmostEqual(rmae, np.sqrt(0.15))
    
    def test_calculate_rmae_batch(self):
        """Test calculating RMAE for a batch of predictions."""
        # Create mock batch of ground truth and predictions
        y_true_batch = np.array([
            [1, 0, 0, 0],  # First sample, class 0
            [0, 1, 0, 0],  # Second sample, class 1
            [0, 0, 1, 0]   # Third sample, class 2
        ])
        
        y_pred_batch = np.array([
            [0.8, 0.1, 0.05, 0.05],  # Predictions for first sample
            [0.2, 0.6, 0.1, 0.1],    # Predictions for second sample
            [0.1, 0.2, 0.6, 0.1]     # Predictions for third sample
        ])
        
        # Calculate MAE for each sample
        sample_maes = np.mean(np.abs(y_true_batch - y_pred_batch), axis=1)
        
        # Expected MAEs:
        # Sample 1: (0.2 + 0.1 + 0.05 + 0.05) / 4 = 0.1
        # Sample 2: (0.2 + 0.4 + 0.1 + 0.1) / 4 = 0.2
        # Sample 3: (0.1 + 0.2 + 0.4 + 0.1) / 4 = 0.2
        expected_maes = np.array([0.1, 0.2, 0.2])
        np.testing.assert_almost_equal(sample_maes, expected_maes)
        
        # Calculate overall MAE
        overall_mae = np.mean(sample_maes)
        self.assertAlmostEqual(overall_mae, 0.16666666666666666)
        
        # Calculate overall RMAE
        overall_rmae = np.sqrt(overall_mae)
        self.assertAlmostEqual(overall_rmae, np.sqrt(0.16666666666666666))
    
    def test_rmae_vs_accuracy(self):
        """Test relationship between RMAE and accuracy."""
        # Create mock data with different levels of accuracy
        num_classes = 10
        num_samples = 100
        
        # Generate random true labels
        y_true_indices = np.random.randint(0, num_classes, num_samples)
        y_true = np.zeros((num_samples, num_classes))
        y_true[np.arange(num_samples), y_true_indices] = 1
        
        # Generate predictions with varying accuracy levels
        accuracy_levels = [0.3, 0.5, 0.7, 0.9]
        rmae_values = []
        
        for acc in accuracy_levels:
            # Create predictions with specified accuracy
            y_pred = np.random.random((num_samples, num_classes))
            # Normalize to sum to 1
            y_pred = y_pred / np.sum(y_pred, axis=1, keepdims=True)
            
            # Adjust to achieve target accuracy
            for i in range(num_samples):
                if np.random.random() < acc:
                    # Make the correct class have the highest probability
                    correct_class = np.argmax(y_true[i])
                    y_pred[i] = np.random.random(num_classes) * 0.1  # Small random values
                    y_pred[i, correct_class] = np.random.random() * 0.5 + 0.5  # Between 0.5 and 1.0
                    y_pred[i] = y_pred[i] / np.sum(y_pred[i])  # Normalize again
            
            # Calculate MAE and RMAE
            mae = np.mean(np.abs(y_true - y_pred))
            rmae = np.sqrt(mae)
            rmae_values.append(rmae)
            
            # Calculate actual accuracy
            pred_classes = np.argmax(y_pred, axis=1)
            true_classes = np.argmax(y_true, axis=1)
            actual_acc = np.mean(pred_classes == true_classes)
            
            print(f"Target accuracy: {acc}, Actual accuracy: {actual_acc}, RMAE: {rmae}")
            
            # RMAE should decrease as accuracy increases
            if len(rmae_values) > 1:
                self.assertLess(rmae, rmae_values[-2])

if __name__ == '__main__':
    unittest.main()