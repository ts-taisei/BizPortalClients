from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings

from .client import BizPortalApiError, BizPortalClient
from .middleware import OIDCSessionCleanupMiddleware
from .settings import get_oidc_identity_model
from .backends import BizPortalOIDCBackend
from .views import safe_next_path


class BizPortalOIDCBackendTests(TestCase):
    def setUp(self):
        self.backend = BizPortalOIDCBackend()
        self.user_model = get_user_model()
        self.OIDCIdentity = get_oidc_identity_model()

    def test_authenticate_associates_existing_identity_and_updates_profile(self):
        user = self.user_model.objects.create_user(
            username='existing-user',
            email='old@example.com',
            first_name='Old',
            last_name='Name',
        )
        identity = self.OIDCIdentity.objects.create(
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
        identity = self.OIDCIdentity.objects.get(user=authenticated_user)
        self.assertEqual(identity.issuer, 'https://idp.example')
        self.assertEqual(identity.subject, 'sub-create')


class OIDCViewUtilityTests(SimpleTestCase):
    def test_safe_next_path_blocks_external_redirects(self):
        self.assertEqual(safe_next_path('https://example.com/a'), '/')
        self.assertEqual(safe_next_path('//example.com/a'), '/')
        self.assertEqual(safe_next_path('/menu/'), '/menu/')


class BizPortalClientTokenRefreshTests(SimpleTestCase):
    def setUp(self):
        self.request = SimpleNamespace(
            session={
                'oidc_access_token': 'expired-token',
                'oidc_refresh_token': 'refresh-token',
                'oidc_access_token_expires_at': 1,
            }
        )

    @patch('django_bizportal_client.client.build_oauth_session')
    @patch('django_bizportal_client.client.oidc_config')
    def test_get_access_token_refreshes_expired_token(self, mock_oidc_config, mock_build_oauth_session):
        mock_oidc_config.return_value = {'token_endpoint': 'https://issuer.example/o/token/'}
        mock_client = Mock()
        mock_client.refresh_token.return_value = {
            'access_token': 'new-access-token',
            'refresh_token': 'new-refresh-token',
            'expires_in': 3600,
        }
        mock_build_oauth_session.return_value = mock_client

        access_token = BizPortalClient(self.request)._get_access_token()

        self.assertEqual(access_token, 'new-access-token')
        self.assertEqual(self.request.session['oidc_access_token'], 'new-access-token')
        self.assertEqual(self.request.session['oidc_refresh_token'], 'new-refresh-token')
        self.assertGreater(self.request.session['oidc_access_token_expires_at'], 1)

    def test_get_access_token_raises_when_refresh_token_missing(self):
        self.request.session.pop('oidc_refresh_token')

        with self.assertRaises(BizPortalApiError) as exc_info:
            BizPortalClient(self.request)._get_access_token()

        self.assertEqual(exc_info.exception.status_code, 401)
        self.assertNotIn('oidc_access_token', self.request.session)
        self.assertNotIn('oidc_access_token_expires_at', self.request.session)


class OIDCSessionCleanupMiddlewareTests(SimpleTestCase):
    def test_cleanup_expired_tokens_preserves_refresh_token(self):
        middleware = OIDCSessionCleanupMiddleware(lambda request: None)
        request = SimpleNamespace(
            session={
                'oidc_access_token': 'expired-token',
                'oidc_refresh_token': 'refresh-token',
                'oidc_access_token_expires_at': 1,
            }
        )

        middleware.cleanup_expired_tokens(request)

        self.assertNotIn('oidc_access_token', request.session)
        self.assertNotIn('oidc_access_token_expires_at', request.session)
        self.assertEqual(request.session['oidc_refresh_token'], 'refresh-token')

