from django.contrib import admin
from .settings import get_oidc_identity_model


@admin.register(get_oidc_identity_model())
class OIDCIdentityAdmin(admin.ModelAdmin):
	list_display = ('user', 'issuer', 'subject', 'company_slug', 'last_login_at')
	search_fields = ('user__username', 'user__email', 'issuer', 'subject', 'company_slug')
	list_filter = ('issuer', 'company_slug')
	raw_id_fields = ('user',)
	readonly_fields = ('last_login_at',)
