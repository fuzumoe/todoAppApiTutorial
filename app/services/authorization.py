"""Authorization code challenge: implement RBAC helpers.

This module contains two functions to implement as part of a coding challenge.
Leave the function signatures intact and implement the described behavior.

Expectations:
- Treat role names case-insensitively.
- Do not mutate inputs.
- Aim for clear, idiomatic Python with O(n) time where n is roles length.
- Prefer readable code over premature optimization.
"""

from collections.abc import Iterable


def has_role(user_roles: Iterable[str], required_role: str) -> bool:
    """Return True if the user has the required role.

    Behavior to implement:
    - Compare role names case-insensitively (e.g., "admin", "Admin", "ADMIN" are equal).
    - Accept any iterable of strings for `user_roles` (list, set, tuple, etc.).
    - Return False if `user_roles` is empty.
    - Ignore duplicates in `user_roles`.

    Edge cases and guidance:
    - If any element in `user_roles` is not a string, you may either cast to str
      or raise a `TypeError`; choose and document your approach.
    - Whitespace-only roles should not match; consider trimming role strings.
    - Treat `required_role` as a single role name; do not accept lists here.

    Examples:
    - has_role(["USER", "ADMIN"], "admin") -> True
    - has_role({"user"}, "ADMIN") -> False
    - has_role([], "USER") -> False
    """
    return False


def can_manage_user(actor_id: str, target_id: str, actor_roles: Iterable[str]) -> bool:
    """Return True if the actor can manage the target user.

    Behavior to implement:
    - Admins (role == "ADMIN", case-insensitive) can manage any user.
    - Non-admins can only manage themselves (i.e., when `actor_id == target_id`).

    Edge cases and guidance:
    - Role comparison is case-insensitive; normalize roles before checking.
    - `actor_id` and `target_id` are opaque identifiers; compare as strings.
    - If `actor_roles` is empty or contains no admin role, only allow self-management.
    - Prefer not to mutate the `actor_roles` iterable; copy or normalize to a new set/list.

    Examples:
    - can_manage_user("u1", "u2", ["ADMIN"]) -> True
    - can_manage_user("u1", "u1", ["USER"]) -> True
    - can_manage_user("u1", "u2", ["user"]) -> False
    """
    return False
