"""
Contrôle de propriété pour les API qui désignent une entreprise (SIRET / DUNS) ou une entité.

Règles, alignées sur l'interface (menus réservés à `membership.is_owner`) :
- accès en lecture : membre de l'entreprise (au niveau de l'entreprise ou d'une de ses entités) ;
- gestion (collaborateurs, descriptions, informations) : propriétaire (`is_owner`) ;
- l'équipe Mixity (`is_staff`) a tous les droits.
"""
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response

from accounts.models import Membership, Structure


def find_structure(data):
    """Structure désignée par `siret`, à défaut par `duns`. None si introuvable."""
    for field in ("siret", "duns"):
        value = data.get(field)
        if value:
            structure = Structure.objects.filter(**{field: value}).first()
            if structure is not None:
                return structure
    return None


def structure_memberships(user, structure):
    return Membership.objects.filter(user=user).filter(
        Q(structure=structure) | Q(entity__entity_level__structure=structure)
    )


def has_structure_access(user, structure):
    return user.is_staff or structure_memberships(user, structure).exists()


def is_structure_owner(user, structure):
    return user.is_staff or structure_memberships(user, structure).filter(is_owner=True).exists()


def owns_entity(user, entity):
    """Propriétaire de l'entreprise (niveau entreprise), de cette entité ou d'une entité parente."""
    if user.is_staff:
        return True
    owner = Membership.objects.filter(user=user, is_owner=True)
    if owner.filter(structure=entity.entity_level.structure, entity__isnull=True).exists():
        return True
    chain = []
    current = entity
    while current is not None and current not in chain:
        chain.append(current)
        current = current.parent_entity
    return owner.filter(entity__in=chain).exists()


def forbidden():
    return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)


def not_found(message="Structure not found"):
    return Response({"detail": message}, status=status.HTTP_404_NOT_FOUND)


def structure_for_member(request):
    """(structure, None) si l'utilisateur a accès à l'entreprise désignée, sinon (None, réponse d'erreur)."""
    structure = find_structure(request.data)
    if structure is None:
        return None, not_found()
    if not has_structure_access(request.user, structure):
        return None, forbidden()
    return structure, None


def structure_for_owner(request):
    """(structure, None) si l'utilisateur est propriétaire de l'entreprise désignée, sinon (None, erreur)."""
    structure = find_structure(request.data)
    if structure is None:
        return None, not_found()
    if not is_structure_owner(request.user, structure):
        return None, forbidden()
    return structure, None
