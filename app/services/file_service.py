# app/services/file_service.py - Created by setup script
"""
CorePath Impact File Service
Local file upload and management service
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional, Tuple
from fastapi import UploadFile, HTTPException, status
from PIL import Image
import uuid
from datetime import datetime

from app.core.config import settings
from app.utils.helpers import generate_filename, get_file_hash, ensure_directory


class FileService:
    """Service for handling file uploads and management"""
    
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.max_file_size = settings.MAX_FILE_SIZE
        self.allowed_image_types = settings.allowed_image_extensions
        
        # Ensure upload directories exist
        self._ensure_upload_directories()
    
    def _ensure_upload_directories(self):
        """Create upload directories if they don't exist"""
        subdirs = ['products', 'users', 'courses', 'categories', 'temp']
        for subdir in subdirs:
            ensure_directory(self.upload_dir / subdir)
    
    def _validate_file(self, file: UploadFile, allowed_types: List[str] = None) -> None:
        """Validate uploaded file"""
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        # Check file size
        if file.size and file.size > self.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed size of {self.max_file_size / (1024*1024):.1f}MB"
            )
        
        # Check file extension
        file_ext = file.filename.split('.')[-1].lower()
        allowed = allowed_types or self.allowed_image_types
        
        if file_ext not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type '{file_ext}' not allowed. Allowed types: {', '.join(allowed)}"
            )
    
    def _generate_unique_filename(self, original_filename: str, directory: str) -> str:
        """Generate unique filename to avoid conflicts"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        name, ext = os.path.splitext(original_filename)
        
        # Clean filename
        clean_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
        clean_name = clean_name.replace(' ', '_')
        
        return f"{timestamp}_{unique_id}_{clean_name}{ext}"
    
    def _optimize_image(self, file_path: Path, max_width: int = 1200, quality: int = 85) -> None:
        """Optimize image size and quality"""
        try:
            with Image.open(file_path) as img:
                # Convert RGBA to RGB if necessary
                if img.mode == 'RGBA':
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    rgb_img.paste(img, mask=img.split()[-1])
                    img = rgb_img
                
                # Resize if too large
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                
                # Save optimized image
                img.save(file_path, optimize=True, quality=quality)
                
        except Exception as e:
            print(f"Warning: Could not optimize image {file_path}: {e}")
    
    async def upload_image(
        self, 
        file: UploadFile, 
        directory: str = "products",
        user_id: Optional[int] = None,
        optimize: bool = True
    ) -> dict:
        """
        Upload and process an image file
        
        Args:
            file: FastAPI UploadFile object
            directory: Upload subdirectory (products, users, etc.)
            user_id: Optional user ID for naming
            optimize: Whether to optimize the image
            
        Returns:
            dict: File information including URL and metadata
        """
        # Validate file
        self._validate_file(file, self.allowed_image_types)
        
        # Generate unique filename
        filename = self._generate_unique_filename(file.filename, directory)
        
        # Create full file path
        upload_subdir = self.upload_dir / directory
        file_path = upload_subdir / filename
        
        try:
            # Save file
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            # Optimize image if requested
            if optimize and file.content_type and file.content_type.startswith('image/'):
                self._optimize_image(file_path)
            
            # Get file info
            file_info = self._get_file_info(file_path, filename, directory)
            
            return file_info
            
        except Exception as e:
            # Clean up file if something went wrong
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {str(e)}"
            )
    
    async def upload_multiple_images(
        self,
        files: List[UploadFile],
        directory: str = "products",
        user_id: Optional[int] = None,
        max_files: int = 10
    ) -> List[dict]:
        """
        Upload multiple image files
        
        Args:
            files: List of FastAPI UploadFile objects
            directory: Upload subdirectory
            user_id: Optional user ID
            max_files: Maximum number of files allowed
            
        Returns:
            List[dict]: List of file information
        """
        if len(files) > max_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Too many files. Maximum {max_files} files allowed"
            )
        
        uploaded_files = []
        errors = []
        
        for i, file in enumerate(files):
            try:
                file_info = await self.upload_image(file, directory, user_id)
                uploaded_files.append(file_info)
            except HTTPException as e:
                errors.append(f"File {i+1} ({file.filename}): {e.detail}")
                continue
        
        if errors and not uploaded_files:
            # All files failed
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"All file uploads failed: {'; '.join(errors)}"
            )
        
        return uploaded_files
    
    def _get_file_info(self, file_path: Path, filename: str, directory: str) -> dict:
        """Get file information and metadata"""
        file_stat = file_path.stat()
        
        # Generate URL (relative to upload directory)
        file_url = f"/uploads/{directory}/{filename}"
        
        # Get image dimensions if it's an image
        dimensions = None
        try:
            if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                with Image.open(file_path) as img:
                    dimensions = {"width": img.width, "height": img.height}
        except:
            pass
        
        return {
            "filename": filename,
            "original_filename": filename.split('_', 2)[-1] if '_' in filename else filename,
            "file_url": file_url,
            "file_path": str(file_path),
            "file_size": file_stat.st_size,
            "mime_type": self._get_mime_type(file_path),
            "dimensions": dimensions,
            "created_at": datetime.fromtimestamp(file_stat.st_ctime).isoformat()
        }
    
    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type based on file extension"""
        ext = file_path.suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain'
        }
        return mime_types.get(ext, 'application/octet-stream')
    
    def delete_file(self, file_url: str) -> bool:
        """
        Delete a file by URL
        
        Args:
            file_url: File URL (e.g., '/uploads/products/image.jpg')
            
        Returns:
            bool: True if file was deleted, False if not found
        """
        try:
            # Convert URL to file path
            if file_url.startswith('/uploads/'):
                relative_path = file_url[9:]  # Remove '/uploads/'
                file_path = self.upload_dir / relative_path
                
                if file_path.exists() and file_path.is_file():
                    file_path.unlink()
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error deleting file {file_url}: {e}")
            return False
    
    def delete_multiple_files(self, file_urls: List[str]) -> dict:
        """
        Delete multiple files
        
        Args:
            file_urls: List of file URLs
            
        Returns:
            dict: Summary of deletion results
        """
        deleted = []
        failed = []
        
        for url in file_urls:
            if self.delete_file(url):
                deleted.append(url)
            else:
                failed.append(url)
        
        return {
            "deleted": deleted,
            "failed": failed,
            "deleted_count": len(deleted),
            "failed_count": len(failed)
        }
    
    def get_file_info(self, file_url: str) -> Optional[dict]:
        """
        Get file information by URL
        
        Args:
            file_url: File URL
            
        Returns:
            dict: File information or None if not found
        """
        try:
            if file_url.startswith('/uploads/'):
                relative_path = file_url[9:]
                file_path = self.upload_dir / relative_path
                
                if file_path.exists() and file_path.is_file():
                    directory = file_path.parent.name
                    return self._get_file_info(file_path, file_path.name, directory)
            
            return None
            
        except Exception:
            return None
    
    def create_thumbnail(
        self, 
        source_url: str, 
        size: Tuple[int, int] = (300, 300),
        quality: int = 80
    ) -> Optional[str]:
        """
        Create a thumbnail from an existing image
        
        Args:
            source_url: Source image URL
            size: Thumbnail size (width, height)
            quality: JPEG quality
            
        Returns:
            str: Thumbnail URL or None if failed
        """
        try:
            if not source_url.startswith('/uploads/'):
                return None
            
            # Get source file path
            relative_path = source_url[9:]
            source_path = self.upload_dir / relative_path
            
            if not source_path.exists():
                return None
            
            # Generate thumbnail filename
            thumb_name = f"thumb_{size[0]}x{size[1]}_{source_path.name}"
            thumb_path = source_path.parent / thumb_name
            
            # Skip if thumbnail already exists
            if thumb_path.exists():
                return f"/uploads/{relative_path.split('/')[0]}/{thumb_name}"
            
            # Create thumbnail
            with Image.open(source_path) as img:
                # Convert RGBA to RGB if necessary
                if img.mode == 'RGBA':
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    rgb_img.paste(img, mask=img.split()[-1])
                    img = rgb_img
                
                # Create thumbnail
                img.thumbnail(size, Image.Resampling.LANCZOS)
                img.save(thumb_path, optimize=True, quality=quality)
            
            return f"/uploads/{relative_path.split('/')[0]}/{thumb_name}"
            
        except Exception as e:
            print(f"Error creating thumbnail for {source_url}: {e}")
            return None
    
    def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """
        Clean up temporary files older than specified age
        
        Args:
            max_age_hours: Maximum age in hours
            
        Returns:
            int: Number of files deleted
        """
        temp_dir = self.upload_dir / "temp"
        if not temp_dir.exists():
            return 0
        
        deleted_count = 0
        max_age_seconds = max_age_hours * 3600
        current_time = datetime.now().timestamp()
        
        try:
            for file_path in temp_dir.iterdir():
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_ctime
                    if file_age > max_age_seconds:
                        file_path.unlink()
                        deleted_count += 1
        except Exception as e:
            print(f"Error during temp file cleanup: {e}")
        
        return deleted_count
    
    def get_storage_stats(self) -> dict:
        """Get storage statistics"""
        stats = {
            "total_files": 0,
            "total_size": 0,
            "directories": {}
        }
        
        try:
            for subdir in ['products', 'users', 'courses', 'categories']:
                dir_path = self.upload_dir / subdir
                if dir_path.exists():
                    files = list(dir_path.iterdir())
                    file_count = len([f for f in files if f.is_file()])
                    total_size = sum(f.stat().st_size for f in files if f.is_file())
                    
                    stats["directories"][subdir] = {
                        "file_count": file_count,
                        "total_size": total_size,
                        "total_size_mb": round(total_size / (1024 * 1024), 2)
                    }
                    
                    stats["total_files"] += file_count
                    stats["total_size"] += total_size
            
            stats["total_size_mb"] = round(stats["total_size"] / (1024 * 1024), 2)
            
        except Exception as e:
            print(f"Error getting storage stats: {e}")
        
        return stats