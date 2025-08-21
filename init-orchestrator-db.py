#!/usr/bin/env python3
"""
Script para inicializar la base de datos del Team 3 Orchestrator
NVIDIA ScaleUp Hackathon Project
"""

import os
import sys
import time
import psycopg2
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

# Agregar el directorio del proyecto al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'teams/team3-orchestrator'))

def wait_for_database():
    """Esperar a que la base de datos esté disponible"""
    print("🔄 Esperando a que la base de datos esté disponible...")
    
    max_attempts = 30
    attempt = 1
    
    while attempt <= max_attempts:
        try:
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST", "localhost"),
                port=os.getenv("DB_PORT", "5433"),
                database=os.getenv("DB_NAME", "orchestrator"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", "postgres")
            )
            conn.close()
            print("✅ Base de datos disponible")
            return True
        except psycopg2.OperationalError:
            print(f"⏳ Intento {attempt}/{max_attempts} - Base de datos no disponible aún...")
            time.sleep(2)
            attempt += 1
    
    print("❌ No se pudo conectar a la base de datos")
    return False

def create_tables():
    """Crear las tablas del orchestrator"""
    try:
        from app.database.models import Base
        from app.database.config import engine
        
        print("🔨 Creando tablas del orchestrator...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas creadas exitosamente")
        
        # Mostrar tablas creadas
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"📋 Tablas creadas: {tables}")
        
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def insert_sample_data():
    """Insertar datos de muestra"""
    try:
        from app.database.config import SessionLocal
        from app.database.models import User, Image, Container, Billing
        
        print("📝 Insertando datos de muestra...")
        
        db = SessionLocal()
        
        # Crear usuario de prueba
        test_user = User(
            username="testuser",
            email="test@example.com",
            password="hashed_password_123"
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"✅ Usuario creado: {test_user.username}")
        
        # Crear imagen de prueba
        test_image = Image(
            name="nginx",
            tag="alpine",
            min_instances=1,
            max_instances=3,
            cpu_limit="0.5",
            memory_limit="512m",
            status="registered",
            user_id=test_user.id
        )
        db.add(test_image)
        db.commit()
        db.refresh(test_image)
        print(f"✅ Imagen creada: {test_image.name}:{test_image.tag}")
        
        # Crear contenedor de prueba
        test_container = Container(
            container_id="test-container-123",
            name="test-nginx",
            port=8080,
            status="running",
            cpu_usage="0.2",
            memory_usage="256m",
            image_id=test_image.id
        )
        db.add(test_container)
        db.commit()
        db.refresh(test_container)
        print(f"✅ Contenedor creado: {test_container.name}")
        
        # Crear billing de prueba
        test_billing = Billing(
            user_id=test_user.id,
            amount=15.50
        )
        db.add(test_billing)
        db.commit()
        print(f"✅ Billing creado: ${test_billing.amount}")
        
        db.close()
        print("✅ Datos de muestra insertados exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error inserting sample data: {e}")
        return False

def verify_data():
    """Verificar que los datos se insertaron correctamente"""
    try:
        from app.database.config import SessionLocal
        from app.database.models import User, Image, Container, Billing
        
        print("🔍 Verificando datos...")
        
        db = SessionLocal()
        
        # Verificar usuarios
        users = db.query(User).all()
        print(f"👥 Usuarios: {len(users)}")
        for user in users:
            print(f"  - {user.username} ({user.email})")
        
        # Verificar imágenes
        images = db.query(Image).all()
        print(f"🖼️ Imágenes: {len(images)}")
        for image in images:
            print(f"  - {image.name}:{image.tag} (CPU: {image.cpu_limit}, Memory: {image.memory_limit})")
        
        # Verificar contenedores
        containers = db.query(Container).all()
        print(f"📦 Contenedores: {len(containers)}")
        for container in containers:
            print(f"  - {container.name} (Status: {container.status}, Port: {container.port})")
        
        # Verificar billing
        billings = db.query(Billing).all()
        print(f"💰 Billing: {len(billings)}")
        for billing in billings:
            print(f"  - ${billing.amount} (User ID: {billing.user_id})")
        
        db.close()
        print("✅ Verificación completada")
        return True
        
    except Exception as e:
        print(f"❌ Error verifying data: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Inicializando base de datos del Team 3 Orchestrator")
    print("=" * 60)
    
    # Configurar variables de entorno si no están definidas
    os.environ.setdefault("DB_HOST", "localhost")
    os.environ.setdefault("DB_PORT", "5433")
    os.environ.setdefault("DB_NAME", "orchestrator")
    os.environ.setdefault("DB_USER", "postgres")
    os.environ.setdefault("DB_PASSWORD", "postgres")
    
    # Esperar a que la base de datos esté disponible
    if not wait_for_database():
        sys.exit(1)
    
    # Crear tablas
    if not create_tables():
        sys.exit(1)
    
    # Insertar datos de muestra
    if not insert_sample_data():
        sys.exit(1)
    
    # Verificar datos
    if not verify_data():
        sys.exit(1)
    
    print("\n🎉 ¡Base de datos del Orchestrator inicializada exitosamente!")
    print("\n📊 Información de conexión:")
    print(f"   Host: {os.getenv('DB_HOST')}")
    print(f"   Puerto: {os.getenv('DB_PORT')}")
    print(f"   Base de datos: {os.getenv('DB_NAME')}")
    print(f"   Usuario: {os.getenv('DB_USER')}")
    print(f"   Adminer: http://localhost:8083")

if __name__ == "__main__":
    main()
