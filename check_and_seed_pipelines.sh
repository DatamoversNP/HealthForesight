#!/bin/bash
# Check if pipelines exist and seed them if needed
cd "$(dirname "$0")"

export PYTHONPATH="${PWD}/apps/api/src:${PWD}/packages/common/src:${PYTHONPATH}"
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/uepi_db"

echo "Checking pipelines in database..."
python3 -c "
from uepi_api.storage_pipelines import list_pipelines
pipelines = list_pipelines('00000000-0000-0000-0000-000000000001')
print(f'Found {len(pipelines)} pipelines')
if len(pipelines) == 0:
    print('No pipelines found. Seeding...')
    import subprocess
    subprocess.run(['python3', 'apps/api/scripts/04_seed_pipelines.py'])
else:
    print('Pipelines already exist:')
    for p in pipelines[:5]:
        print(f'  - {p.get(\"pipeline_name\", \"Unknown\")}')
" 2>&1

