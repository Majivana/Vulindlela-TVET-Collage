"""
Authentication Tests

Unit tests for authentication functionality.
"""

import pytest
from datetime import timedelta
from jose import jwt

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    Role,
    has_permission,
)
from app.core.config import settings


class TestPasswordSecurity:
    """Test password hashing and verification."""
    
    def test_password_hashing(self):
        """Test that passwords are properly hashed."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        # Hash should be different from plain password
        assert hashed != password
        # Hash should be a string
        assert isinstance(hashed, str)
        # Hash should not be empty
        assert len(hashed) > 0
    
    def test_password_verification(self):
        """Test password verification."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        # Correct password should verify
        assert verify_password(password, hashed) is True
        # Incorrect password should not verify
        assert verify_password("wrongpassword", hashed) is False


class TestJWTTokens:
    """Test JWT token creation and validation."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": 1, "email": "test@example.com", "role": "student"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_refresh_token(self):
        """Test refresh token creation."""
        data = {"sub": 1, "email": "test@example.com", "role": "student"}
        token = create_refresh_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_decode_token(self):
        """Test token decoding."""
        data = {"sub": 1, "email": "test@example.com", "role": "student"}
        token = create_access_token(data)
        decoded = decode_token(token)
        
        assert decoded["sub"] == 1
        assert decoded["email"] == "test@example.com"
        assert decoded["role"] == "student"
        assert decoded["type"] == "access"
    
    def test_token_expiration(self):
        """Test that tokens have expiration."""
        data = {"sub": 1}
        token = create_access_token(data, expires_delta=timedelta(minutes=1))
        decoded = decode_token(token)
        
        assert "exp" in decoded
        assert "iat" in decoded


class TestRolePermissions:
    """Test role-based access control."""
    
    def test_student_permissions(self):
        """Test student role permissions."""
        assert has_permission(Role.STUDENT, "view_own_profile") is True
        assert has_permission(Role.STUDENT, "submit_assignment") is True
        assert has_permission(Role.STUDENT, "create_ticket") is True
        assert has_permission(Role.STUDENT, "manage_users") is False
    
    def test_lecturer_permissions(self):
        """Test lecturer role permissions."""
        assert has_permission(Role.LECTURER, "create_assignment") is True
        assert has_permission(Role.LECTURER, "grade_submission") is True
        assert has_permission(Role.LECTURER, "manage_users") is False
    
    def test_admin_permissions(self):
        """Test admin role permissions."""
        assert has_permission(Role.ADMIN, "manage_users") is True
        assert has_permission(Role.ADMIN, "manage_courses") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
