from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin


class OIDCSessionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        expires_at = request.session.get('oidc_access_token_expires_at')
        if not expires_at:
            return
        try:
            if timezone.now().timestamp() >= float(expires_at):
                request.session.pop('oidc_access_token', None)
                request.session.pop('oidc_refresh_token', None)
                request.session.pop('oidc_access_token_expires_at', None)
        except (TypeError, ValueError):
            request.session.pop('oidc_access_token', None)
            request.session.pop('oidc_refresh_token', None)
            request.session.pop('oidc_access_token_expires_at', None)

