from collections.abc import Iterable


def has_role(user_roles: Iterable[str], required_role: str) -> bool:
    roles_set = {r.upper() for r in user_roles}
    return required_role.upper() in roles_set


def can_manage_user(actor_id: str, target_id: str, actor_roles: Iterable[str]) -> bool:
    roles_set = {r.upper() for r in actor_roles}
    if "ADMIN" in roles_set:
        return True
    return actor_id == target_id
