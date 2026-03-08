# Azure Deployment Scripts

## deploy.sh

Automated deployment script that:
1. Checks prerequisites (Azure CLI, kubectl, Helm, Terraform)
2. Creates Azure infrastructure with Terraform
3. Configures kubectl for AKS
4. Creates Kubernetes secrets
5. Deploys UEPI with Helm
6. Runs database migrations

**Usage:**
```bash
./scripts/azure/deploy.sh
```

The script will prompt you for:
- Resource group name
- Azure region
- AKS cluster name
- PostgreSQL admin password
- Azure AD OIDC issuer URL

## setup-azure-ad.sh

Sets up Azure AD App Registrations for OIDC authentication.

**Usage:**
```bash
./scripts/azure/setup-azure-ad.sh
```

This creates:
- App Registration for API
- App Registration for Web
- Service Principals
- Provides OIDC configuration

## Manual Steps

If you prefer manual deployment, see [docs/AZURE_DEPLOYMENT.md](../../docs/AZURE_DEPLOYMENT.md)

