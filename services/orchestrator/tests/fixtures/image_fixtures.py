from app.schemas.image import ImageCreate

def image_create_factory(**overrides):
    """Factory para crear objetos ImageCreate de prueba."""
    base = dict(
        name="myapp",
        tag="latest",
        app_hostname="example.com",
        container_port=8080,
        min_instances=1,
        max_instances=3,
        cpu_limit="0.5",
        memory_limit="512m",
        user_id=1,
    )
    base.update(overrides)
    return ImageCreate(**base)

def image_model_factory(**overrides):
    """
    Factory para crear objetos Image (SQLAlchemy) de prueba.
    Import lazy para evitar problemas con psycopg2 mock.
    """
    # Import lazy: solo cuando se necesita, después de que el mock esté activo
    from app.database.models import Image
    
    base = dict(
        id=1,
        name="myapp",
        tag="latest",
        app_hostname="example.com",
        container_port=8080,
        min_instances=1,
        max_instances=3,
        cpu_limit="0.5",
        memory_limit="512m",
        status="ready",
        user_id=1,
    )
    base.update(overrides)
    # Image es SQLAlchemy; crea una instancia cruda
    img = Image(**{k: v for k, v in base.items() if hasattr(Image, k)})
    return img

