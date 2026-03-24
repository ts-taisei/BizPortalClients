def oidc_portal_branding(request):
    return {
        "oidc_company_slug": request.session.get("oidc_company_slug", ""),
        "oidc_company_name": request.session.get("oidc_company_name", ""),
        "oidc_installation_name": request.session.get("oidc_installation_name", ""),
    }
