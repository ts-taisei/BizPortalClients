from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings

from .models import OIDCIdentity
from .backends import BizPortalOIDCBackend
from .views import safe_next_path


@override_settings(
    OIDC_IDENTITY_MODEL='core.OIDCIdentity',
)
class BizPortalOIDCBackendTests(TestCase):
    def setUp(self):
        self.backend = BizPortalOIDCBackend()
        self.user_model = get_user_model()

    def test_authenticate_associates_existing_identity_and_updates_profile(self):
        user = self.user_model.objects.create_user(
            username='existing-user',
            email='old@example.com',
            first_name='Old',
            last_name='Name',
        )
        identity = OIDCIdentity.objects.create(
            user=user,
            issuer='https://idp.example',
            subject='sub-1',
            company_slug='old-slug',
        )

        authenticated_user = self.backend.authenticate(
            request=None,
            oidc_issuer='https://idp.example',
            oidc_claims={'sub': 'sub-1', 'company_slug': 'new-slug'},
            oidc_userinfo={
                'sub': 'sub-1',
                'email': 'new@example.com',
                'name': 'New Name',
                'company_slug': 'new-slug',
            },
        )

        self.assertEqual(authenticated_user, user)
        user.refresh_from_db()
        identity.refresh_from_db()
        self.assertEqual(user.email, 'new@example.com')
        self.assertEqual(user.first_name, 'New')
        self.assertEqual(user.last_name, 'Name')
        self.assertEqual(identity.company_slug, 'new-slug')
        self.assertIsNotNone(identity.last_login_at)

    @override_settings(OIDC_AUTO_CREATE_USER=True)
    def test_authenticate_creates_local_user_when_enabled(self):
        authenticated_user = self.backend.authenticate(
            request=None,
            oidc_issuer='https://idp.example',
            oidc_claims={'sub': 'sub-create', 'email': 'created@example.com'},
            oidc_userinfo={'sub': 'sub-create', 'email': 'created@example.com', 'name': 'Created User'},
        )

        self.assertIsNotNone(authenticated_user)
        self.assertEqual(authenticated_user.email, 'created@example.com')
        identity = OIDCIdentity.objects.get(user=authenticated_user)
        self.assertEqual(identity.issuer, 'https://idp.example')
        self.assertEqual(identity.subject, 'sub-create')


class OIDCViewUtilityTests(SimpleTestCase):
    def test_safe_next_path_blocks_external_redirects(self):
        self.assertEqual(safe_next_path('https://example.com/a'), '/')
        self.assertEqual(safe_next_path('//example.com/a'), '/')
        self.assertEqual(safe_next_path('/menu/'), '/menu/')

