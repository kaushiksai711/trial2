import os
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the backend directory to the path
import sys
sys.path.append(str(Path(__file__).parent.parent / 'backend'))

from ingestion.ingest import PDFIngestor

class TestPDFIngestion(unittest.TestCase):    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory
        self.test_dir = Path(tempfile.mkdtemp())
        
        # Create test data directory structure
        self.raw_dir = self.test_dir / 'data' / 'raw'
        self.processed_dir = self.test_dir / 'data' / 'processed'
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a test PDF file with sample text
        self.test_pdf = self.raw_dir / 'test_document.pdf'
        self._create_sample_pdf()
        
        # Output file
        self.output_file = self.processed_dir / 'chunks.jsonl'
    
    def _create_sample_pdf(self):
        """Create a sample PDF file with test content."""
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        
        # Create a sample PDF with multiple pages
        c = canvas.Canvas(str(self.test_pdf), pagesize=letter)
        
        # Add content that will be split across chunks
        sample_text = " "
        for i in range(5):  # 5 pages of content
            page_text = f"This is page {i+1} of the test document. " * 100
            c.drawString(100, 700, page_text[:100])  # First line
            c.drawString(100, 680, page_text[100:200])  # Second line
            c.showPage()  # End the current page and start a new one
            sample_text += page_text + "\n\n"
        
        c.save()
        self.sample_text = sample_text
    
    def test_pdf_ingestion(self):
        """Test PDF ingestion and chunking."""
        # Initialize ingestor
        ingestor = PDFIngestor(
            input_dir=self.raw_dir,
            output_file=self.output_file,
            chunk_size=500,  # Smaller chunks for testing
            overlap=50
        )
        
        # Process the test PDF
        ingestor.process_all()
        
        # Verify output file was created
        self.assertTrue(self.output_file.exists())
        
        # Read and verify chunks
        chunks = []
        with open(self.output_file, 'r', encoding='utf-8') as f:
            for line in f:
                chunks.append(json.loads(line))
        
        # Should have multiple chunks
        self.assertGreater(len(chunks), 0)
        
        # Verify chunk structure
        for chunk in chunks:
            self.assertIn('source', chunk)
            self.assertIn('text', chunk)
            self.assertIn('start', chunk)
            self.assertIn('end', chunk)
            self.assertIn('length', chunk)
            self.assertIn('chunk_id', chunk)
            self.assertIn('page_count', chunk)
            
            # Verify chunk length is within bounds
            self.assertLessEqual(chunk['length'], 500)  # chunk_size
            
            # Verify chunk content
            self.assertEqual(chunk['source'], 'test_document.pdf')
            self.assertEqual(chunk['page_count'], 5)
    
    def test_chunk_overlap(self):
        """Test that chunks have the correct overlap."""
        chunk_size = 100
        overlap = 20
        
        # Initialize ingestor with small chunk size for testing
        ingestor = PDFIngestor(
            input_dir=self.raw_dir,
            output_file=self.output_file,
            chunk_size=chunk_size,
            overlap=overlap
        )
        
        # Process the test PDF
        ingestor.process_all()
        
        # Read chunks
        chunks = []
        with open(self.output_file, 'r', encoding='utf-8') as f:
            for line in f:
                chunks.append(json.loads(line))
        
        # Check overlap between consecutive chunks
        for i in range(len(chunks) - 1):
            current_chunk = chunks[i]
            next_chunk = chunks[i + 1]
            
            # Calculate expected overlap
            expected_overlap = current_chunk['text'][-(overlap):]
            actual_overlap = next_chunk['text'][:overlap]
            
            # Verify overlap
            self.assertEqual(actual_overlap, expected_overlap)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

if __name__ == '__main__':
    unittest.main()
