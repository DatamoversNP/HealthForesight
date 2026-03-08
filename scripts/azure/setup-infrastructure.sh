#!/bin/bash
# Automated Azure Infrastructure Setup Script
# This script helps set up Azure infrastructure using Terraform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}HealthForesight Azure Infrastructure Setup${NC}"
echo "=============================================="
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"
command -v terraform >/dev/null 2>&1 || { 
    echo -e "${RED}❌ Terraform not found. Please install Terraform first.${NC}" >&2
    echo "   Install: https://www.terraform.io/downloads"
    exit 1
}

command -v az >/dev/null 2>&1 || { 
    echo -e "${RED}❌ Azure CLI not found. Please install Azure CLI first.${NC}" >&2
    echo "   Install: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
}

# Check Azure login
echo -e "${YELLOW}Checking Azure login...${NC}"
if ! az account show >/dev/null 2>&1; then
    echo -e "${YELLOW}Not logged in to Azure. Please login...${NC}"
    az login
fi

# Get current subscription
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
echo -e "${GREEN}✅ Using Azure subscription: ${SUBSCRIPTION_NAME} (${SUBSCRIPTION_ID})${NC}"
echo ""

# Change to Terraform directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TERRAFORM_DIR="${PROJECT_ROOT}/infra/terraform/envs/azure"
cd "${TERRAFORM_DIR}"

echo -e "${YELLOW}Working directory: ${TERRAFORM_DIR}${NC}"
echo ""

# Check if terraform.tfvars exists
if [ ! -f "terraform.tfvars" ]; then
    echo -e "${YELLOW}terraform.tfvars not found. Creating from example...${NC}"
    
    if [ -f "terraform.tfvars.example" ]; then
        cp terraform.tfvars.example terraform.tfvars
        echo -e "${GREEN}✅ Created terraform.tfvars from example${NC}"
        echo ""
        echo -e "${YELLOW}⚠️  Please edit terraform.tfvars with your values before continuing!${NC}"
        echo ""
        read -p "Press Enter to edit terraform.tfvars now (or Ctrl+C to cancel)..."
        
        # Open editor (default to nano, fallback to vi)
        if command -v nano >/dev/null 2>&1; then
            nano terraform.tfvars
        elif command -v vi >/dev/null 2>&1; then
            vi terraform.tfvars
        else
            echo -e "${YELLOW}Please edit terraform.tfvars manually${NC}"
            read -p "Press Enter after you've edited terraform.tfvars..."
        fi
    else
        echo -e "${RED}❌ terraform.tfvars.example not found${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ terraform.tfvars found${NC}"
fi

echo ""
echo -e "${BLUE}=============================================="
echo -e "Infrastructure Setup Steps${NC}"
echo -e "${BLUE}=============================================="
echo ""
echo "This will create the following Azure resources:"
echo "  - Resource Group"
echo "  - AKS Cluster (3 nodes)"
echo "  - PostgreSQL Flexible Server"
echo "  - Redis Cache"
echo "  - Storage Account (Blob Storage)"
echo "  - Key Vault"
echo ""
echo -e "${YELLOW}⚠️  This will create real Azure resources that cost money!${NC}"
echo ""
read -p "Do you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo -e "${YELLOW}Cancelled${NC}"
    exit 0
fi

# Initialize Terraform
echo ""
echo -e "${YELLOW}Initializing Terraform...${NC}"
terraform init

# Validate Terraform configuration
echo ""
echo -e "${YELLOW}Validating Terraform configuration...${NC}"
if ! terraform validate; then
    echo -e "${RED}❌ Terraform validation failed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Terraform configuration is valid${NC}"

# Plan
echo ""
echo -e "${YELLOW}Creating Terraform plan...${NC}"
terraform plan -out=tfplan

echo ""
echo -e "${BLUE}=============================================="
echo -e "Review the plan above${NC}"
echo -e "${BLUE}=============================================="
echo ""
read -p "Do you want to apply this plan? (yes/no): " APPLY_CONFIRM

if [ "$APPLY_CONFIRM" != "yes" ]; then
    echo -e "${YELLOW}Plan saved to tfplan. You can apply it later with: terraform apply tfplan${NC}"
    exit 0
fi

# Apply
echo ""
echo -e "${YELLOW}Applying Terraform configuration...${NC}"
echo -e "${YELLOW}This will take 15-30 minutes...${NC}"
terraform apply tfplan

# Clean up plan file
rm -f tfplan

# Show outputs
echo ""
echo -e "${GREEN}=============================================="
echo -e "✅ Infrastructure setup complete!${NC}"
echo -e "${GREEN}=============================================="
echo ""
echo "Outputs:"
terraform output

echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "  1. Configure GitHub Secrets (see NEXT_STEPS.md Step 2)"
echo "  2. Create Kubernetes secrets: ./scripts/azure/setup-secrets.sh"
echo "  3. Deploy application (see NEXT_STEPS.md Step 4)"
echo ""

