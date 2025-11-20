#!/usr/bin/env python3
"""
Frontend and Django views tests
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AI_Slop.settings')
import django
django.setup()

from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile


class FrontendViewsTest(TestCase):
    """Test frontend views and endpoints"""
    
    def setUp(self):
        """Set up test client"""
        self.client = Client()
    
    def test_index_view(self):
        """Test main index page loads"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AI Job Assistant')
        self.assertContains(response, 'EXECUTE_ANALYSIS')
    
    def test_trace_dashboard_view(self):
        """Test trace dashboard loads"""
        response = self.client.get('/trace/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Trace Dashboard')
        self.assertContains(response, 'Real-time workflow monitoring')
    
    def test_trace_api_view(self):
        """Test trace API returns JSON"""
        response = self.client.get('/trace/api/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Check JSON structure
        import json
        data = json.loads(response.content)
        self.assertIn('traces', data)
        self.assertIn('metrics', data)
    
    @patch('frontend.views.Orchestrator')
    def test_submit_form_missing_data(self, mock_orchestrator):
        """Test form submission with missing data"""
        response = self.client.post('/submit/', {
            'job_position': 'Software Engineer'
            # Missing resume file
        })
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['status'], 'error')
    
    @patch('frontend.views.Orchestrator')
    def test_submit_form_valid_data(self, mock_orchestrator):
        """Test form submission with valid data"""
        
        # Mock the orchestrator response
        mock_orchestrator_instance = MagicMock()
        mock_orchestrator.return_value = mock_orchestrator_instance
        mock_orchestrator_instance.execute_workflow.return_value = {
            'workflow_stages': {
                'job_ranking': 'Mock job ranking results'
            },
            'final_recommendations': {
                'total_jobs_analyzed': 5
            }
        }
        
        # Create a test file
        test_file = SimpleUploadedFile(
            "test_resume.txt", 
            b"Test resume content",
            content_type="text/plain"
        )
        
        response = self.client.post('/submit/', {
            'job_position': 'Software Engineer',
            'job_keywords': 'Python, Django',
            'resume': test_file
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('job_count', data)
        self.assertIn('top_jobs', data)


if __name__ == '__main__':
    unittest.main()