from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission

class Command(BaseCommand):
    help = 'Crea roles por defecto en la base de datos'

    def handle(self, *args, **kwargs):
        roles = {
            'Admin': ['add_user', 'change_user', 'delete_user', 'view_user'],
            'User': ['view_user']
        }

        for role_name, permissions in roles.items():
            group, created = Group.objects.get_or_create(name=role_name)
            if created:
                for perm_codename in permissions:
                    try:
                        perm = Permission.objects.get(codename=perm_codename)
                        group.permissions.add(perm)
                    except Permission.DoesNotExist:
                        self.stdout.write(f"Permiso {perm_codename} no encontrado.")
            self.stdout.write(f"Rol '{role_name}' creado o actualizado.")
