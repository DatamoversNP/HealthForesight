#!/bin/bash
# Reorganize data directory structure with proper naming
# synthetic -> source_data
# curated -> target_data_model

set -e

DATA_DIR="data"
SOURCE_DIR="${DATA_DIR}/source_data"
TARGET_DIR="${DATA_DIR}/target_data_model"

echo "📁 Reorganizing Data Directory Structure"
echo "========================================"

# Create new directory structure
echo "Creating new directory structure..."
mkdir -p "${SOURCE_DIR}"
mkdir -p "${TARGET_DIR}"

# Move synthetic to source_data if it exists
if [ -d "${DATA_DIR}/synthetic" ]; then
    echo "Moving synthetic/ -> source_data/"
    if [ -d "${SOURCE_DIR}/synthetic" ]; then
        echo "  Warning: ${SOURCE_DIR}/synthetic already exists, merging..."
        cp -r "${DATA_DIR}/synthetic"/* "${SOURCE_DIR}/" 2>/dev/null || true
        rm -rf "${DATA_DIR}/synthetic"
    else
        mv "${DATA_DIR}/synthetic" "${SOURCE_DIR}/"
    fi
    echo "  ✅ Moved synthetic to source_data"
fi

# Move curated to target_data_model if it exists
if [ -d "${DATA_DIR}/curated" ]; then
    echo "Moving curated/ -> target_data_model/"
    if [ -d "${TARGET_DIR}/curated" ]; then
        echo "  Warning: ${TARGET_DIR}/curated already exists, merging..."
        cp -r "${DATA_DIR}/curated"/* "${TARGET_DIR}/" 2>/dev/null || true
        rm -rf "${DATA_DIR}/curated"
    else
        mv "${DATA_DIR}/curated" "${TARGET_DIR}/"
    fi
    echo "  ✅ Moved curated to target_data_model"
fi

# Move raw to source_data/raw if it exists
if [ -d "${DATA_DIR}/raw" ]; then
    echo "Moving raw/ -> source_data/raw/"
    if [ -d "${SOURCE_DIR}/raw" ]; then
        echo "  Warning: ${SOURCE_DIR}/raw already exists, merging..."
        cp -r "${DATA_DIR}/raw"/* "${SOURCE_DIR}/raw/" 2>/dev/null || true
        rm -rf "${DATA_DIR}/raw"
    else
        mv "${DATA_DIR}/raw" "${SOURCE_DIR}/"
    fi
    echo "  ✅ Moved raw to source_data/raw"
fi

# Move uploads to source_data/uploads if it exists
if [ -d "${DATA_DIR}/uploads" ]; then
    echo "Moving uploads/ -> source_data/uploads/"
    if [ -d "${SOURCE_DIR}/uploads" ]; then
        echo "  Warning: ${SOURCE_DIR}/uploads already exists, merging..."
        cp -r "${DATA_DIR}/uploads"/* "${SOURCE_DIR}/uploads/" 2>/dev/null || true
        rm -rf "${DATA_DIR}/uploads"
    else
        mv "${DATA_DIR}/uploads" "${SOURCE_DIR}/"
    fi
    echo "  ✅ Moved uploads to source_data/uploads"
fi

echo ""
echo "✅ Data reorganization complete!"
echo ""
echo "New structure:"
echo "  ${SOURCE_DIR}/     - Source data files (formerly synthetic/)"
echo "  ${TARGET_DIR}/     - Target/curated data model files (formerly curated/)"
echo ""
echo "Next steps:"
echo "  1. Update code references from 'synthetic' to 'source_data'"
echo "  2. Update code references from 'curated' to 'target_data_model'"
echo "  3. Restart API server"

