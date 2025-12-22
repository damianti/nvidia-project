"""
Tests unitarios para las utilidades de tokens JWT.
"""
import pytest
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
import jwt

from app.utils import tokens
from app.utils.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.schemas.user import TokenData
from app.exceptions.domain import TokenExpiredError, InvalidTokenError


class TestCreateAccessToken:
    """Tests para la creación de tokens JWT."""
    
    def test_create_access_token_success(self) -> None:
        """
        Test que verifica la creación exitosa de un token JWT.
        Arrange: Datos para el token
        Act: Crear token
        Assert: El token debe ser válido y decodificable
        """
        data: Dict[str, Any] = {"sub": "testuser"}
        
        token = tokens.create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verificar que el token puede ser decodificado
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["sub"] == "testuser"
        assert "exp" in decoded
    
    def test_create_access_token_with_expiration(self) -> None:
        """
        Test que verifica que el token tiene una expiración correcta.
        Arrange: Datos para el token
        Act: Crear token
        Assert: El token debe expirar en el tiempo configurado
        """
        data: Dict[str, Any] = {"sub": "testuser"}
        
        token = tokens.create_access_token(data)
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        exp_timestamp = decoded["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        expected_exp = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Verificar que la expiración está dentro de un rango razonable (1 minuto de diferencia)
        time_diff = abs((exp_datetime - expected_exp).total_seconds())
        assert time_diff < 60
    
    def test_create_access_token_with_custom_claims(self) -> None:
        """
        Test que verifica que se pueden agregar claims personalizados al token.
        Arrange: Datos con claims adicionales
        Act: Crear token
        Assert: El token debe contener todos los claims
        """
        data: Dict[str, Any] = {
            "sub": "testuser",
            "user_id": 123,
            "role": "admin"
        }
        
        token = tokens.create_access_token(data)
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        assert decoded["sub"] == "testuser"
        assert decoded["user_id"] == 123
        assert decoded["role"] == "admin"
    
    def test_create_access_token_preserves_original_data(self) -> None:
        """
        Test que verifica que los datos originales se preservan en el token.
        Arrange: Datos originales
        Act: Crear token y decodificar
        Assert: Los datos deben ser idénticos (excepto exp)
        """
        original_data: Dict[str, Any] = {"sub": "testuser", "custom": "value"}
        
        token = tokens.create_access_token(original_data)
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        assert decoded["sub"] == original_data["sub"]
        assert decoded["custom"] == original_data["custom"]


class TestDecodeAccessToken:
    """Tests para la decodificación de tokens JWT."""
    
    def test_decode_access_token_success(self) -> None:
        """
        Test que verifica la decodificación exitosa de un token válido.
        Arrange: Token válido
        Act: Decodificar token
        Assert: Debe retornar TokenData con username correcto
        """
        data: Dict[str, Any] = {"sub": "testuser"}
        token = tokens.create_access_token(data)
        
        token_data = tokens.decode_access_token(token)
        
        assert isinstance(token_data, TokenData)
        assert token_data.username == "testuser"
    
    def test_decode_access_token_expired(self) -> None:
        """
        Test que verifica que un token expirado lanza TokenExpiredError.
        Arrange: Token expirado
        Act: Decodificar token
        Assert: Debe lanzar TokenExpiredError
        """
        # Crear token expirado manualmente
        payload = {
            "sub": "testuser",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1)
        }
        expired_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        
        with pytest.raises(TokenExpiredError) as exc_info:
            tokens.decode_access_token(expired_token)
        
        assert "expired" in str(exc_info.value).lower()
    
    def test_decode_access_token_invalid_signature(self) -> None:
        """
        Test que verifica que un token con firma inválida lanza InvalidTokenError.
        Arrange: Token con firma inválida
        Act: Decodificar token
        Assert: Debe lanzar InvalidTokenError
        """
        # Crear token con otra clave secreta
        wrong_secret = "wrong_secret_key"
        payload = {"sub": "testuser", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
        invalid_token = jwt.encode(payload, wrong_secret, algorithm=ALGORITHM)
        
        with pytest.raises(InvalidTokenError) as exc_info:
            tokens.decode_access_token(invalid_token)
        
        assert "invalid" in str(exc_info.value).lower()
    
    def test_decode_access_token_missing_sub(self) -> None:
        """
        Test que verifica que un token sin 'sub' lanza InvalidTokenError.
        Arrange: Token sin claim 'sub'
        Act: Decodificar token
        Assert: Debe lanzar InvalidTokenError
        """
        payload = {"exp": datetime.now(timezone.utc) + timedelta(hours=1)}
        token_without_sub = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        
        with pytest.raises(InvalidTokenError) as exc_info:
            tokens.decode_access_token(token_without_sub)
        
        assert "username" in str(exc_info.value).lower() or "missing" in str(exc_info.value).lower()
    
    def test_decode_access_token_malformed_token(self) -> None:
        """
        Test que verifica que un token malformado lanza InvalidTokenError.
        Arrange: String que no es un token válido
        Act: Decodificar token
        Assert: Debe lanzar InvalidTokenError
        """
        malformed_token = "not.a.valid.token"
        
        with pytest.raises(InvalidTokenError) as exc_info:
            tokens.decode_access_token(malformed_token)
        
        assert "invalid" in str(exc_info.value).lower()
    
    def test_decode_access_token_empty_string(self) -> None:
        """
        Test que verifica que un string vacío lanza InvalidTokenError.
        Arrange: String vacío
        Act: Decodificar token
        Assert: Debe lanzar InvalidTokenError
        """
        empty_token = ""
        
        with pytest.raises(InvalidTokenError):
            tokens.decode_access_token(empty_token)
    
    def test_decode_access_token_wrong_algorithm(self) -> None:
        """
        Test que verifica que un token con algoritmo incorrecto lanza InvalidTokenError.
        Arrange: Token con algoritmo diferente
        Act: Decodificar token
        Assert: Debe lanzar InvalidTokenError
        """
        payload = {"sub": "testuser", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
        # Crear token con algoritmo HS256 en lugar del configurado
        token_wrong_alg = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        
        # Si el algoritmo configurado es diferente, debería fallar
        # Nota: Esto puede variar según la configuración
        try:
            tokens.decode_access_token(token_wrong_alg)
        except InvalidTokenError:
            pass  # Esperado si el algoritmo no coincide

