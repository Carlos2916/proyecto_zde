from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType

@receiver(post_migrate)
def crear_roles(sender, **kwargs):
    roles = ['Administrador', 'Recursos Humanos', 'Supervisor']

    for rol in roles:
        grupo, creado = Group.objects.get_or_create(name=rol)

        if creado:
            print(f"Grupo creado: {rol}")
            # Aquí puedes añadir permisos si quieres, por ejemplo:
            # permiso = Permission.objects.get(codename='add_user')
            # grupo.permissions.add(permiso)
