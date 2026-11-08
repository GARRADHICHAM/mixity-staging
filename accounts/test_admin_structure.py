from accounts.admin import StructureAdmin
from accounts.models import Membership
from mixity.testing import TestCase


class AdminStructureMainEntityTest(TestCase):
    """Une structure créée dans l'administration reçoit son entité principale, comme côté client."""

    def setUp(self):
        business_line = self.make_business_line("bl", "Secteur", "Sector")
        self.structure = self.make_structure("Société Admin", "societe-admin", 300, "Diversity", business_line)
        self.owner = self.make_user("owner@example.com", "pw", username="owner@example.com")
        Membership.objects.create(user=self.owner, structure=self.structure, is_owner=True)

    def test_main_entity_created_and_owner_attached(self):
        StructureAdmin.ensure_main_entity(self.structure)
        entity = self.structure.get_main_entity
        self.assertIsNotNone(entity)
        self.assertEqual(entity.entity_level.level, 0)
        self.assertEqual(entity.workforce, 300)
        self.assertEqual(Membership.objects.get(user=self.owner).entity, entity)

    def test_existing_main_entity_kept(self):
        StructureAdmin.ensure_main_entity(self.structure)
        entity = self.structure.get_main_entity
        StructureAdmin.ensure_main_entity(self.structure)
        self.assertEqual(self.structure.get_main_entity, entity)
        self.assertEqual(self.structure.entity_level.get().entities.count(), 1)
