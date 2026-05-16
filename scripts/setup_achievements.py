import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "homie.settings")
django.setup()

from accounts.models import Achievement

Achievement.objects.all().delete()

achievements_data = [
    # Casas (houses)
    ("Primer Hogar", "Únete a 1 casa", "🏠", "houses", 1, 10),
    ("Compañerismo", "Participa en 2 casas diferentes", "🤝", "houses", 2, 10),
    ("Agente Inmobiliario", "Llega a estar en 5 casas", "🌆", "houses", 5, 20),
    
    # Tareas (tasks)
    ("Manos a la obra", "Completa tu primera tarea", "🧹", "tasks", 1, 10),
    ("Ayudante", "Completa 5 tareas", "🧽", "tasks", 5, 10),
    ("Comprometido", "Completa 20 tareas", "✨", "tasks", 20, 20),
    ("Trabajador Estrella", "Completa 50 tareas", "🌟", "tasks", 50, 30),
    ("Leyenda del Hogar", "Completa 100 tareas", "👑", "tasks", 100, 50),
    
    # Compras (shopping)
    ("Primera Compra", "Tacha 1 objeto de la lista de compra", "🛒", "shopping", 1, 10),
    ("Comprador Frecuente", "Compra 10 objetos", "🛍️", "shopping", 10, 10),
    ("Repartidor", "Compra 25 objetos", "🚚", "shopping", 25, 20),
    ("Amo del Supermercado", "Compra 50 objetos", "🏪", "shopping", 50, 30),
    ("El que paga manda", "Compra 100 objetos", "💳", "shopping", 100, 50),
    
    # Puntos ganados (points)
    ("Ahorrador", "Consigue 100 puntos en total", "🪙", "points", 100, 10),
    ("Riqueza", "Acumula 500 puntos", "💰", "points", 500, 20),
    ("Caudaloso", "Consigue 1,000 puntos", "💸", "points", 1000, 30),
    ("Magnate", "Alcanza los 5,000 puntos", "🏦", "points", 5000, 50),
    
    # Mensajes (messages)
    ("Participante", "Envía 1 mensaje por el chat", "💬", "messages", 1, 10),
    ("Conversador", "Envía 50 mensajes por el chat", "🗣️", "messages", 50, 20),
    ("Charlatán", "Envía 200 mensajes al chat", "📱", "messages", 200, 50),
]

for name, desc, icon, ctype, target, reward in achievements_data:
    Achievement.objects.create(
        name=name,
        description=desc,
        icon=icon,
        condition_type=ctype,
        target_value=target,
        reward_saldo=reward
    )

print("20 achievements created successfully!")
