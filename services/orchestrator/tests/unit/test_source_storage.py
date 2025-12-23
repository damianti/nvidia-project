"""
Unit tests for source_storage service.
"""
import pytest
import tempfile
import os
import tarfile
import zipfile
from fastapi import HTTPException

from app.services.source_storage import safe_extract_tar, safe_extract_zip, _is_within_directory


@pytest.mark.unit
class TestIsWithinDirectory:
    """Tests for _is_within_directory helper function."""
    
    def test_within_directory_same_path(self):
        """Test that same path is considered within directory."""
        assert _is_within_directory("/tmp/test", "/tmp/test") is True
    
    def test_within_directory_subdirectory(self):
        """Test that subdirectory is considered within directory."""
        assert _is_within_directory("/tmp/test", "/tmp/test/subdir") is True
    
    def test_within_directory_nested(self):
        """Test that nested subdirectory is considered within directory."""
        assert _is_within_directory("/tmp/test", "/tmp/test/subdir/nested") is True
    
    def test_not_within_directory_parent(self):
        """Test that parent directory is not considered within directory."""
        assert _is_within_directory("/tmp/test", "/tmp") is False
    
    def test_not_within_directory_sibling(self):
        """Test that sibling directory is not considered within directory."""
        assert _is_within_directory("/tmp/test", "/tmp/other") is False
    
    def test_not_within_directory_absolute_path_traversal(self):
        """Test that absolute path traversal is detected."""
        assert _is_within_directory("/tmp/test", "/etc/passwd") is False


@pytest.mark.unit
class TestSafeExtractTar:
    """Tests for safe_extract_tar function."""
    
    def test_extract_valid_tar(self):
        """Test extracting a valid tar archive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test tar file
            tar_path = os.path.join(tmpdir, "test.tar")
            dest_dir = os.path.join(tmpdir, "extracted")
            os.makedirs(dest_dir)
            
            # Create tar with a simple file
            with tarfile.open(tar_path, "w") as tar:
                test_file = os.path.join(tmpdir, "test.txt")
                with open(test_file, "w") as f:
                    f.write("test content")
                tar.add(test_file, arcname="test.txt")
            
            # Extract
            safe_extract_tar(tar_path, dest_dir)
            
            # Verify extraction
            extracted_file = os.path.join(dest_dir, "test.txt")
            assert os.path.exists(extracted_file)
            with open(extracted_file, "r") as f:
                assert f.read() == "test content"
    
    def test_extract_tar_with_subdirectory(self):
        """Test extracting tar with subdirectory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tar_path = os.path.join(tmpdir, "test.tar")
            dest_dir = os.path.join(tmpdir, "extracted")
            os.makedirs(dest_dir)
            
            # Create tar with subdirectory
            with tarfile.open(tar_path, "w") as tar:
                test_file = os.path.join(tmpdir, "test.txt")
                with open(test_file, "w") as f:
                    f.write("test")
                tar.add(test_file, arcname="subdir/test.txt")
            
            safe_extract_tar(tar_path, dest_dir)
            
            extracted_file = os.path.join(dest_dir, "subdir", "test.txt")
            assert os.path.exists(extracted_file)
    
    def test_extract_tar_unsafe_path_traversal(self):
        """Test that path traversal attacks are blocked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tar_path = os.path.join(tmpdir, "malicious.tar")
            dest_dir = os.path.join(tmpdir, "extracted")
            os.makedirs(dest_dir)
            
            # Create tar with path traversal
            with tarfile.open(tar_path, "w") as tar:
                test_file = os.path.join(tmpdir, "test.txt")
                with open(test_file, "w") as f:
                    f.write("malicious")
                # Try to extract outside dest_dir
                tar.add(test_file, arcname="../outside.txt")
            
            # Should raise HTTPException
            with pytest.raises(HTTPException) as exc_info:
                safe_extract_tar(tar_path, dest_dir)
            
            assert exc_info.value.status_code == 400
            assert "unsafe path" in str(exc_info.value.detail).lower()


@pytest.mark.unit
class TestSafeExtractZip:
    """Tests for safe_extract_zip function."""
    
    def test_extract_valid_zip(self):
        """Test extracting a valid zip archive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, "test.zip")
            dest_dir = os.path.join(tmpdir, "extracted")
            os.makedirs(dest_dir)
            
            # Create zip with a simple file
            with zipfile.ZipFile(zip_path, "w") as z:
                z.writestr("test.txt", "test content")
            
            # Extract
            safe_extract_zip(zip_path, dest_dir)
            
            # Verify extraction
            extracted_file = os.path.join(dest_dir, "test.txt")
            assert os.path.exists(extracted_file)
            with open(extracted_file, "r") as f:
                assert f.read() == "test content"
    
    def test_extract_zip_with_subdirectory(self):
        """Test extracting zip with subdirectory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, "test.zip")
            dest_dir = os.path.join(tmpdir, "extracted")
            os.makedirs(dest_dir)
            
            # Create zip with subdirectory
            with zipfile.ZipFile(zip_path, "w") as z:
                z.writestr("subdir/test.txt", "test")
            
            safe_extract_zip(zip_path, dest_dir)
            
            extracted_file = os.path.join(dest_dir, "subdir", "test.txt")
            assert os.path.exists(extracted_file)
    
    def test_extract_zip_unsafe_path_traversal(self):
        """Test that path traversal attacks are blocked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, "malicious.zip")
            dest_dir = os.path.join(tmpdir, "extracted")
            os.makedirs(dest_dir)
            
            # Create zip with path traversal
            with zipfile.ZipFile(zip_path, "w") as z:
                z.writestr("../outside.txt", "malicious")
            
            # Should raise HTTPException
            with pytest.raises(HTTPException) as exc_info:
                safe_extract_zip(zip_path, dest_dir)
            
            assert exc_info.value.status_code == 400
            assert "unsafe path" in str(exc_info.value.detail).lower()
