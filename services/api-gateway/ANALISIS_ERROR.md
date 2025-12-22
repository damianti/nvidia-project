# Análisis del Error y Solución

## 🔍 Problema Identificado

El error que estás viendo es:

```
ImportError: email-validator is not installed, run `pip install 'pydantic[email]'`
```

### Cadena de Importación que Causa el Error

1. **`tests/conftest.py` línea 12**: 
   ```python
   from app.main import app
   ```

2. **`app/main.py`** importa los routers:
   ```python
   from app.routes.auth_routes import router as auth_router
   from app.routes.proxy_routes import router as proxy_router
   ```

3. **`app/routes/auth_routes.py`** importa los schemas:
   ```python
   from app.schemas.user import LoginRequest, UserCreate
   ```

4. **`app/schemas/user.py` línea 1 y 7**:
   ```python
   from pydantic import BaseModel, EmailStr, ConfigDict
   ...
   email: EmailStr
   ```

5. **Pydantic intenta validar `EmailStr`** → Requiere `email-validator`
6. **`email-validator` no está instalado** → ❌ Error

## 🎯 Causa Raíz

Aunque `email-validator==2.1.0` está en `requirements.txt`, **NO está instalado en el entorno virtual**. Esto puede pasar porque:

- El entorno virtual se creó antes de agregar `email-validator` al requirements.txt
- Las dependencias no se reinstalaron después de actualizar requirements.txt
- Hubo un error durante la instalación inicial

## ✅ Soluciones (en orden de preferencia)

### Solución 1: Instalar email-validator (RÁPIDA)

```bash
cd services/api-gateway
source venv/bin/activate
pip install email-validator==2.1.0
```

### Solución 2: Reinstalar todas las dependencias (RECOMENDADA)

```bash
cd services/api-gateway
source venv/bin/activate
pip install -r requirements.txt
```

Esto asegura que todas las dependencias estén correctamente instaladas.

### Solución 3: Reinstalar pydantic[email] (ALTERNATIVA)

```bash
cd services/api-gateway
source venv/bin/activate
pip install --force-reinstall 'pydantic[email]==2.5.0'
```

Esto reinstalará pydantic con todas sus dependencias, incluyendo email-validator.

## 🔧 Solución Preventiva (Opcional)

Si quieres evitar este problema en el futuro, puedes hacer la importación de `app` de forma lazy en `conftest.py`:

```python
# En lugar de:
from app.main import app

# Usar:
@pytest.fixture
def test_app():
    from app.main import app
    return app
```

Pero esto requiere cambiar cómo se usa `app` en los tests de integración.

## 📋 Verificación

Después de instalar, verifica:

```bash
pip list | grep email-validator
```

Deberías ver:
```
email-validator    2.1.0
```

## 🚀 Ejecutar Tests Nuevamente

Una vez solucionado:

```bash
pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html
```

## 📝 Resumen

**Problema**: `email-validator` no está instalado aunque está en requirements.txt

**Solución**: Instalar `email-validator` o reinstalar todas las dependencias

**Prevención**: Siempre ejecutar `pip install -r requirements.txt` después de actualizar requirements.txt

