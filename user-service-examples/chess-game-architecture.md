# Arquitectura para Juegos con Estado: Caso Ajedrez

## 🎮 El Problema

Un juego como ajedrez tiene **estado compartido** entre jugadores:
- Tablero actual
- Turno actual (quién juega)
- Historial de movimientos
- Tiempo restante de cada jugador
- Estado de la partida (en curso, finalizada, etc.)

**Con Round Robin sin sticky sessions:**
```
Jugador A hace movimiento → Contenedor 1
Jugador B consulta estado → Contenedor 2 (NO ve el movimiento de A)
```

## ❌ Limitaciones Actuales del Sistema

1. **No hay Sticky Sessions**: Round Robin puro distribuye requests aleatoriamente
2. **No hay WebSockets**: Solo HTTP/HTTPS (no tiempo real bidireccional)
3. **No hay estado compartido**: Cada contenedor es independiente

## ✅ Soluciones Posibles

### Opción 1: Estado Compartido + Polling (Más Simple)

**Arquitectura:**
```
┌─────────────┐
│   Cliente   │
└──────┬──────┘
       │ HTTP (polling cada 1-2 segundos)
       ▼
┌─────────────────┐
│  API Gateway    │
│  (Round Robin)  │
└──────┬──────────┘
       │
       ├─────────┬─────────┐
       ▼         ▼         ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│Container │ │Container │ │Container │
│    A     │ │    B     │ │    C     │
└────┬─────┘ └────┬─────┘ └────┬─────┘
     │           │           │
     └───────────┴───────────┘
                 │
                 ▼
        ┌─────────────────┐
        │  Redis/PostgreSQL│  ← Estado compartido
        │  (Estado del juego)│
        └─────────────────┘
```

**Cómo funciona:**
1. Jugador A hace movimiento → POST `/games/{game_id}/move` → Contenedor A
2. Contenedor A guarda el movimiento en Redis/PostgreSQL
3. Jugador B hace polling → GET `/games/{game_id}/state` → Contenedor B (cualquiera)
4. Contenedor B lee el estado desde Redis/PostgreSQL
5. Jugador B ve el movimiento de A

**Ventajas:**
- ✅ Funciona con la arquitectura actual
- ✅ No requiere cambios en Load Balancer
- ✅ Escalable horizontalmente
- ✅ Simple de implementar

**Desventajas:**
- ❌ Latencia (polling cada 1-2 segundos)
- ❌ No es tiempo real verdadero
- ❌ Más requests HTTP (mayor carga)

**Implementación:**
```python
# Estado en Redis
game_state = {
    "game_id": "abc123",
    "board": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR",
    "current_turn": "white",
    "moves": ["e2e4", "e7e5"],
    "status": "active"
}

# Guardar movimiento
redis.set(f"game:{game_id}", json.dumps(game_state))

# Leer estado (cualquier contenedor)
game_state = json.loads(redis.get(f"game:{game_id}"))
```

---

### Opción 2: Sticky Sessions (Requiere Cambios)

**Arquitectura:**
```
┌─────────────┐
│   Cliente   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  API Gateway    │
│  (Sticky Session│
│   por game_id)  │
└──────┬──────────┘
       │
       │ Mismo contenedor para misma partida
       ▼
┌──────────┐
│Container │  ← Siempre el mismo para game_id="abc123"
│    A     │
└────┬─────┘
     │
     ▼
┌─────────────────┐
│  Redis/PostgreSQL│  ← Backup del estado
└─────────────────┘
```

**Cómo funciona:**
1. Load Balancer usa `game_id` para sticky session
2. Todas las requests de la partida "abc123" van al mismo contenedor
3. Estado se mantiene en memoria del contenedor
4. Redis/PostgreSQL como backup

**Ventajas:**
- ✅ Estado en memoria (muy rápido)
- ✅ No necesita polling
- ✅ Menos carga en base de datos

**Desventajas:**
- ❌ Requiere modificar Load Balancer (agregar sticky sessions)
- ❌ Si el contenedor cae, se pierde el estado en memoria
- ❌ No escala bien (un contenedor por partida activa)

**Implementación necesaria:**
```python
# En Load Balancer - agregar sticky session selector
class StickySessionSelector:
    def select(self, game_id: str, services: List[ServiceInfo]) -> ServiceInfo:
        # Hash del game_id para siempre elegir el mismo contenedor
        index = hash(game_id) % len(services)
        return services[index]
```

---

### Opción 3: WebSockets + Pub/Sub (Más Complejo)

**Arquitectura:**
```
┌─────────────┐
│   Cliente   │
└──────┬──────┘
       │ WebSocket
       ▼
┌─────────────────┐
│  WebSocket      │
│  Gateway        │  ← Nuevo servicio
└──────┬──────────┘
       │
       ├─────────┬─────────┐
       ▼         ▼         ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│Container │ │Container │ │Container │
│    A     │ │    B     │ │    C     │
└────┬─────┘ └────┬─────┘ └────┬─────┘
     │           │           │
     └───────────┴───────────┘
                 │ Pub/Sub
                 ▼
        ┌─────────────────┐
        │  Redis Pub/Sub  │  ← Notificaciones en tiempo real
        └─────────────────┘
                 │
                 ▼
        ┌─────────────────┐
        │  PostgreSQL     │  ← Estado persistente
        └─────────────────┘
```

**Cómo funciona:**
1. Cliente se conecta vía WebSocket
2. Jugador A hace movimiento → Contenedor A
3. Contenedor A publica evento en Redis Pub/Sub: `game:abc123:move`
4. Todos los contenedores suscritos reciben el evento
5. Contenedor B (donde está Jugador B) envía actualización vía WebSocket

**Ventajas:**
- ✅ Tiempo real verdadero
- ✅ Baja latencia
- ✅ Escalable

**Desventajas:**
- ❌ Requiere WebSocket Gateway (no existe actualmente)
- ❌ Más complejo de implementar
- ❌ Requiere Redis Pub/Sub

---

## 🎯 Recomendación

**Para MVP/Desarrollo: Opción 1 (Estado Compartido + Polling)**
- Funciona con la arquitectura actual
- No requiere cambios en el sistema
- Suficiente para la mayoría de juegos por turnos
- Fácil de implementar

**Para Producción: Opción 3 (WebSockets + Pub/Sub)**
- Mejor experiencia de usuario
- Tiempo real verdadero
- Requiere desarrollo adicional

## 📝 Ejemplo de Implementación (Opción 1)

```python
# app.py - Servicio de Ajedrez con estado compartido

from flask import Flask, jsonify, request
import redis
import json

app = Flask(__name__)
redis_client = redis.Redis(host='redis-host', port=6379, db=0)

@app.route("/games/<game_id>/move", methods=["POST"])
def make_move(game_id):
    """Hacer un movimiento"""
    data = request.json
    move = data.get("move")  # "e2e4"
    
    # Leer estado actual
    game_state = json.loads(redis_client.get(f"game:{game_id}") or "{}")
    
    # Validar y aplicar movimiento
    # ... lógica del juego ...
    
    # Guardar nuevo estado
    game_state["moves"].append(move)
    game_state["current_turn"] = "black" if game_state["current_turn"] == "white" else "white"
    redis_client.set(f"game:{game_id}", json.dumps(game_state))
    
    return jsonify({"success": True, "game_state": game_state})

@app.route("/games/<game_id>/state", methods=["GET"])
def get_game_state(game_id):
    """Obtener estado actual (polling)"""
    game_state = json.loads(redis_client.get(f"game:{game_id}") or "{}")
    return jsonify(game_state)
```

## 🔑 Puntos Clave

1. **Estado debe estar fuera de los contenedores**: Redis, PostgreSQL, etc.
2. **Round Robin funciona si el estado es compartido**: Cualquier contenedor puede leer/escribir
3. **Para tiempo real**: Necesitas WebSockets o Server-Sent Events (SSE)
4. **Sticky sessions**: Útil pero no esencial si usas estado compartido

## 🚀 Próximos Pasos

Si quieres implementar un juego:
1. Usa Redis para estado compartido (rápido, en memoria)
2. Implementa polling en el cliente (cada 1-2 segundos)
3. Para mejor UX, considera agregar WebSocket Gateway en el futuro

