from django.conf import settings
from django.db import models


class OIDCIdentity(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='oidc_identity', verbose_name='ユーザー', help_text='このOIDC身元情報に紐づくユーザーアカウント')
	issuer = models.CharField('発行元', max_length=255, help_text='OIDC認証サーバーの識別子。URL形式 https://oidc-portal.com/o まで含む')
	subject = models.CharField('サブジェクト', max_length=255, help_text='OIDC認証サーバーのユーザー識別子（ID）')
	company_slug = models.CharField('会社スラッグ', max_length=255, blank=True, default='', help_text='OIDC認証サーバーのユーザーの所属会社のスラッグ。')
	last_login_at = models.DateTimeField('最終ログイン日時', null=True, blank=True)

	class Meta:
		verbose_name = 'OIDC身元情報'
		verbose_name_plural = 'OIDC身元情報'
		constraints = [
			models.UniqueConstraint(fields=['issuer', 'subject'], name='core_oidcidentity_issuer_subject_uniq'),
		]
