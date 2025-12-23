"""
Unit tests for build_context service.
"""
import pytest
import tempfile
import os
import tarfile
import zipfile
from pathlib import Path
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException, UploadFile

from app.services.build_context import (
    build_context_root,
    save_upload_to_disk,
    extract_archive,
    validate_context,
    cleanup_context,
    prepare_context,
)


@pytest.mark.unit
class TestBuildContextRoot:
    """Tests for build_context_root function."""
    
    @patch("app.services.build_context.DEFAULT_BUILD_CONTEXT_BASE_DIR", "/var/lib/orchestrator/build-contexts")
    def test_build_context_root(self):
        """Test that build_context_root returns correct path."""
        result = build_context_root(user_id=1, image_id=42)
        
        expected = "/var/lib/orchestrator/build-contexts/1/42"
        assert result == expected
    
    @patch("app.services.build_context.DEFAULT_BUILD_CONTEXT_BASE_DIR", "/tmp/build")
    def test_build_context_root_different_base(self):
        """Test with different base directory."""
        result = build_context_root(user_id=100, image_id=200)
        
        assert result == "/tmp/build/100/200"


@pytest.mark.unit
class TestSaveUploadToDisk:
    """Tests for save_upload_to_disk function."""
    
    @pytest.mark.asyncio
    async def test_save_upload_to_disk_success(self):
        """Test successfully saving uploaded file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dest_path = os.path.join(tmpdir, "uploaded_file.zip")
            
            # Create mock UploadFile
            mock_file = AsyncMock(spec=UploadFile)
            mock_file.filename = "test.zip"
            mock_file.content_type = "application/zip"
            mock_file.read = AsyncMock(return_value=b"test file content")
            
            await save_upload_to_disk(mock_file, dest_path)
            
            # Verify file was saved
            assert os.path.exists(dest_path)
            with open(dest_path, "rb") as f:
                assert f.read() == b"test file content"
            
            # Verify file.read was called
            mock_file.read.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_upload_to_disk_error(self):
        """Test error handling when saving file fails."""
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.filename = "test.zip"
        mock_file.content_type = "application/zip"
        mock_file.read = AsyncMock(side_effect=IOError("Disk full"))
        
        with pytest.raises(HTTPException) as exc_info:
            await save_upload_to_disk(mock_file, "/invalid/path/file.zip")
        
        assert exc_info.value.status_code == 500
        assert "Failed to save uploaded file" in str(exc_info.value.detail)


@pytest.mark.unit
class TestExtractArchive:
    """Tests for extract_archive function."""
    
    def test_extract_tar_archive(self):
        """Test extracting tar archive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create tar archive
            tar_path = os.path.join(tmpdir, "test.tar")
            context_dir = os.path.join(tmpdir, "context")
            os.makedirs(context_dir)
            
            with tarfile.open(tar_path, "w") as tar:
                test_file = os.path.join(tmpdir, "test.txt")
                with open(test_file, "w") as f:
                    f.write("test content")
                tar.add(test_file, arcname="test.txt")
            
            extract_archive("test.tar", tar_path, context_dir)
            
            # Verify extraction
            extracted_file = os.path.join(context_dir, "test.txt")
            assert os.path.exists(extracted_file)
    
    def test_extract_tar_gz_archive(self):
        """Test extracting tar.gz archive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tar_path = os.path.join(tmpdir, "test.tar.gz")
            context_dir = os.path.join(tmpdir, "context")
            os.makedirs(context_dir)
            
            with tarfile.open(tar_path, "w:gz") as tar:
                test_file = os.path.join(tmpdir, "test.txt")
                with open(test_file, "w") as f:
                    f.write("test")
                tar.add(test_file, arcname="test.txt")
            
            extract_archive("test.tar.gz", tar_path, context_dir)
            
            assert os.path.exists(os.path.join(context_dir, "test.txt"))
    
    def test_extract_zip_archive(self):
        """Test extracting zip archive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, "test.zip")
            context_dir = os.path.join(tmpdir, "context")
            os.makedirs(context_dir)
            
            with zipfile.ZipFile(zip_path, "w") as z:
                z.writestr("test.txt", "test content")
            
            extract_archive("test.zip", zip_path, context_dir)
            
            extracted_file = os.path.join(context_dir, "test.txt")
            assert os.path.exists(extracted_file)
            with open(extracted_file, "r") as f:
                assert f.read() == "test content"
    
    def test_extract_unsupported_format(self):
        """Test that unsupported formats raise HTTPException."""
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = os.path.join(tmpdir, "test.rar")
            context_dir = os.path.join(tmpdir, "context")
            os.makedirs(context_dir)
            
            with pytest.raises(HTTPException) as exc_info:
                extract_archive("test.rar", archive_path, context_dir)
            
            assert exc_info.value.status_code == 400
            assert "Unsupported file type" in str(exc_info.value.detail)
    
    def test_extract_archive_extraction_error(self):
        """Test error handling when extraction fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = os.path.join(tmpdir, "corrupted.tar")
            context_dir = os.path.join(tmpdir, "context")
            os.makedirs(context_dir)
            
            # Create invalid tar file
            with open(archive_path, "w") as f:
                f.write("not a tar file")
            
            with pytest.raises(HTTPException) as exc_info:
                extract_archive("test.tar", archive_path, context_dir)
            
            assert exc_info.value.status_code == 500
            assert "Failed to extract archive" in str(exc_info.value.detail)


@pytest.mark.unit
class TestValidateContext:
    """Tests for validate_context function."""
    
    def test_validate_context_with_dockerfile(self):
        """Test validation succeeds when Dockerfile exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dockerfile_path = Path(tmpdir) / "Dockerfile"
            dockerfile_path.write_text("FROM python:3.11")
            
            # Should not raise
            validate_context(tmpdir)
    
    def test_validate_context_no_dockerfile(self):
        """Test validation fails when Dockerfile is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(HTTPException) as exc_info:
                validate_context(tmpdir)
            
            assert exc_info.value.status_code == 400
            assert "Dockerfile not found" in str(exc_info.value.detail)
    
    def test_validate_context_dockerfile_is_directory(self):
        """Test validation fails when Dockerfile is a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dockerfile_path = Path(tmpdir) / "Dockerfile"
            dockerfile_path.mkdir()
            
            with pytest.raises(HTTPException) as exc_info:
                validate_context(tmpdir)
            
            assert exc_info.value.status_code == 400


@pytest.mark.unit
class TestCleanupContext:
    """Tests for cleanup_context function."""
    
    def test_cleanup_context_success(self):
        """Test successful cleanup of context directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = os.path.join(tmpdir, "test_context")
            os.makedirs(test_dir)
            
            # Create some files
            test_file = os.path.join(test_dir, "test.txt")
            with open(test_file, "w") as f:
                f.write("test")
            
            assert os.path.exists(test_dir)
            
            cleanup_context(test_dir)
            
            assert not os.path.exists(test_dir)
    
    def test_cleanup_context_not_exists(self):
        """Test cleanup when directory doesn't exist."""
        # Should not raise
        cleanup_context("/nonexistent/path")
    
    def test_cleanup_context_empty_string(self):
        """Test cleanup with empty string."""
        # Should not raise
        cleanup_context("")
    
    def test_cleanup_context_none(self):
        """Test cleanup with None (should handle gracefully)."""
        # Should not raise (though function expects str, not None)
        cleanup_context("")


@pytest.mark.unit
class TestPrepareContext:
    """Tests for prepare_context function."""
    
    @pytest.mark.asyncio
    @patch("app.services.build_context.DEFAULT_BUILD_CONTEXT_BASE_DIR", "/tmp/test-build-contexts")
    async def test_prepare_context_success(self):
        """Test successful preparation of build context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a zip file with Dockerfile
            zip_path = os.path.join(tmpdir, "test.zip")
            with zipfile.ZipFile(zip_path, "w") as z:
                z.writestr("Dockerfile", "FROM python:3.11")
                z.writestr("app.py", "print('hello')")
            
            # Read zip content
            with open(zip_path, "rb") as f:
                zip_content = f.read()
            
            # Create mock UploadFile
            mock_file = AsyncMock(spec=UploadFile)
            mock_file.filename = "test.zip"
            mock_file.content_type = "application/zip"
            mock_file.read = AsyncMock(return_value=zip_content)
            
            # Call prepare_context
            root_dir, context_dir = await prepare_context(user_id=1, image_id=42, file=mock_file)
            
            # Verify directories were created
            assert os.path.exists(root_dir)
            assert os.path.exists(context_dir)
            
            # Verify Dockerfile exists
            dockerfile_path = os.path.join(context_dir, "Dockerfile")
            assert os.path.exists(dockerfile_path)
            
            # Verify app.py was extracted
            app_path = os.path.join(context_dir, "app.py")
            assert os.path.exists(app_path)
            
            # Verify archive was cleaned up
            # Archive files have UUID in name, so we check that no .zip files remain
            root_path = Path(root_dir)
            zip_files = list(root_path.glob("upload-*.zip"))
            assert len(zip_files) == 0  # Archive should be deleted
    
    @pytest.mark.asyncio
    @patch("app.services.build_context.DEFAULT_BUILD_CONTEXT_BASE_DIR", "/tmp/test-build-contexts")
    async def test_prepare_context_with_tar_gz(self):
        """Test preparation with tar.gz archive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a tar.gz file with Dockerfile
            tar_path = os.path.join(tmpdir, "test.tar.gz")
            with tarfile.open(tar_path, "w:gz") as tar:
                # Create a temporary file with Dockerfile content
                dockerfile_temp = os.path.join(tmpdir, "Dockerfile")
                with open(dockerfile_temp, "w") as f:
                    f.write("FROM python:3.11")
                tar.add(dockerfile_temp, arcname="Dockerfile")
            
            # Read tar.gz content
            with open(tar_path, "rb") as f:
                tar_content = f.read()
            
            # Create mock UploadFile
            mock_file = AsyncMock(spec=UploadFile)
            mock_file.filename = "test.tar.gz"
            mock_file.content_type = "application/gzip"
            mock_file.read = AsyncMock(return_value=tar_content)
            
            # Call prepare_context
            root_dir, context_dir = await prepare_context(user_id=2, image_id=100, file=mock_file)
            
            # Verify Dockerfile exists
            dockerfile_path = os.path.join(context_dir, "Dockerfile")
            assert os.path.exists(dockerfile_path)
    
    @pytest.mark.asyncio
    @patch("app.services.build_context.DEFAULT_BUILD_CONTEXT_BASE_DIR", "/tmp/test-build-contexts")
    async def test_prepare_context_no_dockerfile(self):
        """Test preparation fails when Dockerfile is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a zip file without Dockerfile
            zip_path = os.path.join(tmpdir, "test.zip")
            with zipfile.ZipFile(zip_path, "w") as z:
                z.writestr("app.py", "print('hello')")
            
            with open(zip_path, "rb") as f:
                zip_content = f.read()
            
            mock_file = AsyncMock(spec=UploadFile)
            mock_file.filename = "test.zip"
            mock_file.content_type = "application/zip"
            mock_file.read = AsyncMock(return_value=zip_content)
            
            # Should raise HTTPException
            with pytest.raises(HTTPException) as exc_info:
                await prepare_context(user_id=1, image_id=42, file=mock_file)
            
            assert exc_info.value.status_code == 400
            assert "Dockerfile not found" in str(exc_info.value.detail)
