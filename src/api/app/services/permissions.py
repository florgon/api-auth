from enum import Enum


class Permission(Enum):
    # Other.
    noexpire = "noexpire"

    # Profile.
    edit = "edit"
    sessions = "sessions"
    oauth_clients = "oauth_clients"
    email = "email"

    # Private.
    admin = "admin"

    # Services.
    gatey = "gatey"
    notes = "notes"
    habits = "habits"


Permissions = list[Permission]  # Type hint (alias).


def normalize_scope(scope: str) -> str:
    return SCOPE_PERMISSION_SEPARATOR.join(
        [permission.value for permission in parse_permissions_from_scope(scope)]
    )

def permissions_get_ttl(permissions: Permissions, default_ttl: int) -> int:
    if Permission.noexpire in permissions:
        return 0
    return default_ttl

def parse_permissions_from_scope(scope: str) -> Permissions:
    assert isinstance(scope, str)
    return list(
        set(
            [
                Permission(permission)
                for permission in scope.split(SCOPE_PERMISSION_SEPARATOR)
                if (
                    permission
                    and permission in SCOPE_ALLOWED_PERMISSIONS
                )
            ]
        )
    )


SCOPE_PERMISSION_SEPARATOR = ","
SCOPE_ALLOWED_PERMISSIONS = list(
    map(
        lambda p: p.value,
        (
            Permission.oauth_clients,
            Permission.email,
            Permission.noexpire,
            Permission.admin,
            Permission.edit,
            Permission.sessions,
            Permission.gatey,
            Permission.notes,
            Permission.habits,
        ),
    )
)
