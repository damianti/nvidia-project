from app.schemas.container import ContainerCreate


def container_create_factory(**overrides):
    """Factory para crear objetos ContainerCreate de prueba."""
    base = dict(
        name="test-container",
        image_id=1,
        count=1,
    )
    base.update(overrides)
    return ContainerCreate(**base)


def container_model_factory(**overrides):
    """
    Factory para crear objetos Container (SQLAlchemy) de prueba.
    Import lazy para evitar problemas con psycopg2 mock.
    """
    # Import lazy: solo cuando se necesita, después de que el mock esté activo
    from app.database.models import Container, ContainerStatus

    base = dict(
        id=1,
        container_id="docker-id-123",
        container_ip="172.17.0.2",
        name="test-container",
        internal_port=8080,
        external_port=8081,
        status=ContainerStatus.RUNNING,
        cpu_usage="0.0",
        memory_usage="0m",
        user_id=1,
        image_id=1,
    )
    base.update(overrides)
    c = Container(**{k: v for k, v in base.items() if hasattr(Container, k)})
    return c
