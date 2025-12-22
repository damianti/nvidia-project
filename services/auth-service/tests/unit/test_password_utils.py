"""
Unit tests for password hashing utilities.
"""
import pytest
from unittest.mock import patch, MagicMock
from app.utils import passwords


class TestPasswordHashing:
    """Tests for password hash generation and verification."""
    
    @patch('app.utils.passwords.pwd_context')
    def test_get_password_hash_generates_different_hashes(
        self,
        mock_pwd_context: MagicMock
    ) -> None:
        """
        Test that verifies que cada hash generado es único (diferentes salts).
        Arrange: Mock de pwd_context que retorna hashes diferentes
        Act: Generar dos hashes para la misma contraseña
        Assert: Los hashes deben ser diferentes
        """
        # Simular que cada llamada retorna un hash diferente (diferentes salts)
        mock_pwd_context.hash.side_effect = [
            "$2b$12$hash1diferente1234567890123456789012345678901234567890123456789012",
            "$2b$12$hash2diferente1234567890123456789012345678901234567890123456789012"
        ]
        
        password = "testpassword123"
        
        hash1 = passwords.get_password_hash(password)
        hash2 = passwords.get_password_hash(password)
        
        assert hash1 != hash2
        assert len(hash1) > 0
        assert len(hash2) > 0
        assert mock_pwd_context.hash.call_count == 2
    
    @patch('app.utils.passwords.pwd_context')
    def test_verify_password_correct_password(
        self,
        mock_pwd_context: MagicMock
    ) -> None:
        """
        Test that verifies que una contraseña correcta pasa la verificación.
        Arrange: Mock de pwd_context que retorna True para verificación
        Act: Verificar la contraseña contra el hash
        Assert: La verificación debe ser exitosa
        """
        password = "testpassword123"
        hashed = "$2b$12$hashedpassword1234567890123456789012345678901234567890123456789012"
        mock_pwd_context.verify.return_value = True
        
        result = passwords.verify_password(password, hashed)
        
        assert result is True
        mock_pwd_context.verify.assert_called_once_with(password, hashed)
    
    @patch('app.utils.passwords.pwd_context')
    def test_verify_password_incorrect_password(
        self,
        mock_pwd_context: MagicMock
    ) -> None:
        """
        Test that verifies que una contraseña incorrecta falla la verificación.
        Arrange: Mock de pwd_context que retorna False para verificación
        Act: Verificar la contraseña incorrecta
        Assert: La verificación debe fallar
        """
        wrong_password = "wrongpassword456"
        hashed = "$2b$12$hashedpassword1234567890123456789012345678901234567890123456789012"
        mock_pwd_context.verify.return_value = False
        
        result = passwords.verify_password(wrong_password, hashed)
        
        assert result is False
        mock_pwd_context.verify.assert_called_once_with(wrong_password, hashed)
    
    @patch('app.utils.passwords.pwd_context')
    def test_verify_password_empty_password(
        self,
        mock_pwd_context: MagicMock
    ) -> None:
        """
        Test that verifies el comportamiento con contraseña vacía.
        Arrange: Mock de pwd_context que retorna False para contraseña vacía
        Act: Verificar contraseña vacía
        Assert: La verificación debe fallar
        """
        hashed = "$2b$12$hashedpassword1234567890123456789012345678901234567890123456789012"
        mock_pwd_context.verify.return_value = False
        
        result = passwords.verify_password("", hashed)
        
        assert result is False
        mock_pwd_context.verify.assert_called_once_with("", hashed)
    
    @patch('app.utils.passwords.pwd_context')
    def test_get_password_hash_empty_string(
        self,
        mock_pwd_context: MagicMock
    ) -> None:
        """
        Test that verifies que se puede generar hash de string vacío.
        Arrange: Mock de pwd_context que retorna un hash
        Act: Generar hash
        Assert: Se genera un hash válido
        """
        password = ""
        mock_hash = "$2b$12$hashedpassword1234567890123456789012345678901234567890123456789012"
        mock_pwd_context.hash.return_value = mock_hash
        mock_pwd_context.verify.return_value = True
        
        hashed = passwords.get_password_hash(password)
        
        assert len(hashed) > 0
        assert hashed == mock_hash
        mock_pwd_context.hash.assert_called_once_with(password)
    
    @patch('app.utils.passwords.pwd_context')
    def test_verify_password_unicode_password(
        self,
        mock_pwd_context: MagicMock
    ) -> None:
        """
        Test that verifies el manejo de contraseñas con caracteres Unicode.
        Arrange: Mock de pwd_context que retorna True para verificación
        Act: Generar hash y verificar
        Assert: La verificación debe ser exitosa
        """
        password = "test密码🔒123"
        mock_hash = "$2b$12$hashedpassword1234567890123456789012345678901234567890123456789012"
        mock_pwd_context.hash.return_value = mock_hash
        mock_pwd_context.verify.return_value = True
        
        hashed = passwords.get_password_hash(password)
        result = passwords.verify_password(password, hashed)
        
        assert result is True
        assert hashed == mock_hash
    
    @patch('app.utils.passwords.pwd_context')
    def test_verify_password_long_password(
        self,
        mock_pwd_context: MagicMock
    ) -> None:
        """
        Test that verifies el manejo de contraseñas largas (dentro del límite de bcrypt).
        Arrange: Mock de pwd_context que retorna True para verificación
        Act: Generar hash y verificar
        Assert: La verificación debe ser exitosa
        """
        # bcrypt has a 72-byte limit, we use 70 to be safe
        password = "a" * 70
        mock_hash = "$2b$12$hashedpassword1234567890123456789012345678901234567890123456789012"
        mock_pwd_context.hash.return_value = mock_hash
        mock_pwd_context.verify.return_value = True
        
        hashed = passwords.get_password_hash(password)
        result = passwords.verify_password(password, hashed)
        
        assert result is True
        assert hashed == mock_hash
    
    @patch('app.utils.passwords.pwd_context')
    def test_password_hash_format(
        self,
        mock_pwd_context: MagicMock
    ) -> None:
        """
        Test that verifies el formato del hash generado (bcrypt).
        Arrange: Mock de pwd_context que retorna hash con formato bcrypt
        Act: Generar hash
        Assert: El hash debe comenzar con $2b$ (formato bcrypt)
        """
        password = "testpassword123"
        mock_hash = "$2b$12$hashedpassword1234567890123456789012345678901234567890123456789012"
        mock_pwd_context.hash.return_value = mock_hash
        
        hashed = passwords.get_password_hash(password)
        
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
        assert hashed == mock_hash

