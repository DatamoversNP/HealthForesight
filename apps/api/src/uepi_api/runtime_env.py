"""Runtime environment hints (Azure App Service, etc.)"""
import os


def is_azure_app_service() -> bool:
    """True when running on Azure App Service (including Linux custom containers).

    Do not use WEBSITE_INSTANCE_ID alone — it is often unset in Web App for Containers.
    """
    return bool(
        os.environ.get("WEBSITE_SITE_NAME")
        or os.environ.get("WEBSITE_HOSTNAME")
        or os.environ.get("WEBSITE_RESOURCE_GROUP")
    )
