from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OIDCIdentity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.CASCADE, related_name='oidc_identity', verbose_name='ユーザー', help_text='このOIDC身元情報に紐づくユーザーアカウント')),
                ('issuer', models.CharField(max_length=255, verbose_name='発行元', help_text='OIDC認証サーバーの識別子。URL形式 https://oidc-portal.com/o まで含む'),),
                ('subject', models.CharField(max_length=255, verbose_name='サブジェクト', help_text='OIDC認証サーバーのユーザー識別子（ID）')),
                ('company_slug', models.CharField(max_length=255, blank=True, default='', verbose_name='会社スラッグ', help_text='OIDC認証サーバーのユーザーの所属会社のスラッグ。')),
                ('last_login_at', models.DateTimeField(blank=True, null=True, verbose_name='最終ログイン日時')),
            ],
            options={'verbose_name': 'OIDC身元情報', 'verbose_name_plural': 'OIDC身元情報'},
        ),
        migrations.AddConstraint(
            model_name='oidcidentity',
            constraint=models.UniqueConstraint(fields=('issuer', 'subject'), name='core_oidcidentity_issuer_subject_uniq'),
        ),
    ]
