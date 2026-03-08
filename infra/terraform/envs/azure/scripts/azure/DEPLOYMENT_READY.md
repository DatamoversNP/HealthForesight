# 🚀 Ready to Deploy to Azure!

## ✅ Prerequisites Check

- ✅ Azure CLI: Installed and logged in
- ✅ kubectl: Installed  
- ✅ Helm: Installed
- ✅ Terraform: Installed
- ✅ Azure Subscription: Active (Azure subscription 1)

## 🎯 Quick Deployment

Run this command to start the deployment:

```bash
./scripts/azure/start-deployment.sh
```

## ⚠️ Important Notes

1. **Costs**: This will create Azure resources costing ~$500-900/month
2. **Time**: Infrastructure creation takes 15-30 minutes
3. **Images**: You'll need Docker images (script will help)
4. **Confirmation**: Script will ask for confirmation before creating resources

## 📋 What Will Be Created

- AKS Cluster (3 nodes)
- PostgreSQL Database
- Redis Cache
- Storage Account
- Key Vault
- Kubernetes namespace and secrets
- UEPI application deployment

## 🚀 Start Deployment

```bash
./scripts/azure/start-deployment.sh
```

The script will:
1. Ask for confirmation
2. Create Terraform configuration
3. Deploy infrastructure (15-30 min)
4. Configure Kubernetes
5. Deploy UEPI application

## 📝 After Deployment

1. Check status: `kubectl get pods -n uepi-prod`
2. Run migrations: `kubectl exec -it deployment/uepi-api -n uepi-prod -- alembic upgrade head`
3. Get ingress IP: `kubectl get ingress -n uepi-prod`
4. Configure DNS

## 🆘 Need Help?

- See `docs/AZURE_DEPLOYMENT.md` for detailed guide
- See `DEPLOYMENT_CHECKLIST.md` for step-by-step checklist
