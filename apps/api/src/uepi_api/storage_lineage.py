"""Lineage storage and tracking - Full data flow from source to dashboards"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from pathlib import Path
import json
import os

from uepi_api.storage_file import BASE_PATH
from uepi_api.storage_ingestions import list_ingestions
from uepi_api.storage_analyses import list_analyses, list_result_indices
from uepi_api.storage_exports import list_exports
from uepi_api.storage_policies import list_policies
from uepi_api.storage_observations import list_observations


def get_full_lineage(tenant_id: UUID) -> Dict[str, Any]:
    """
    Get complete lineage tracking from source to dashboards
    
    Returns:
        {
            "sources": [...],           # Source data files
            "ingestions": [...],        # Data ingestions
            "datasets": [...],          # Processed datasets
            "analyses": [...],          # All analyses (baseline, impact, what-if, etc.)
            "observations": [...],      # Observed impact analyses
            "exports": [...],           # Generated reports/exports
            "dashboards": [...],        # Dashboard views (from observations/exports)
            "relationships": [...],     # Links between entities
        }
    """
    try:
        # Load all entities
        ingestions = list_ingestions(tenant_id)
        analyses = list_analyses(tenant_id)
        observations = list_observations(tenant_id)
        exports = list_exports(tenant_id)
        policies = list_policies(tenant_id)
        
        # Build relationships
        relationships = []
        
        # Map ingestion -> dataset -> analysis -> observation -> export
        for ingestion in ingestions:
            ingestion_id = ingestion.get("id")
            
            # Find analyses that used data from this ingestion
            for analysis in analyses:
                analysis_metadata = analysis.get("metadata", {})
                if ingestion_id in str(analysis_metadata.get("ingestion_ids", [])):
                    relationships.append({
                        "from_type": "ingestion",
                        "from_id": ingestion_id,
                        "to_type": "analysis",
                        "to_id": analysis.get("id"),
                        "relationship_type": "data_source",
                    })
            
            # Find observations linked to ingestions (via data periods)
            for observation in observations:
                obs_data_period = observation.get("data_period_id")
                ingestion_metadata = ingestion.get("metadata", {})
                if obs_data_period and obs_data_period in str(ingestion_metadata.get("data_period_id", "")):
                    relationships.append({
                        "from_type": "ingestion",
                        "from_id": ingestion_id,
                        "to_type": "observation",
                        "to_id": observation.get("observation_id"),
                        "relationship_type": "data_source",
                    })
        
        # Map analysis -> observation
        for analysis in analyses:
            analysis_id = analysis.get("id")
            for observation in observations:
                if observation.get("baseline_version_id") == analysis_id or \
                   observation.get("prediction_id") == analysis_id:
                    relationships.append({
                        "from_type": "analysis",
                        "from_id": analysis_id,
                        "to_type": "observation",
                        "to_id": observation.get("observation_id"),
                        "relationship_type": "baseline_or_prediction",
                    })
        
        # Map observation -> export
        for observation in observations:
            obs_id = observation.get("observation_id")
            for export in exports:
                export_analysis_id = export.get("analysis_id")
                # Link if export was generated from analysis related to this observation
                if export_analysis_id == obs_id or \
                   export_analysis_id in [obs_id, observation.get("baseline_version_id"), observation.get("prediction_id")]:
                    relationships.append({
                        "from_type": "observation",
                        "from_id": obs_id,
                        "to_type": "export",
                        "to_id": export.get("id"),
                        "relationship_type": "report_source",
                    })
        
        # Map analysis -> export
        for analysis in analyses:
            analysis_id = analysis.get("id")
            for export in exports:
                if export.get("analysis_id") == analysis_id:
                    relationships.append({
                        "from_type": "analysis",
                        "from_id": analysis_id,
                        "to_type": "export",
                        "to_id": export.get("id"),
                        "relationship_type": "report_source",
                    })
        
        # Build sources (from ingestion manifest URIs)
        sources = []
        seen_sources = set()
        for ingestion in ingestions:
            manifest_uri = ingestion.get("manifest_uri", "")
            if manifest_uri and manifest_uri not in seen_sources:
                sources.append({
                    "id": f"source-{ingestion.get('id')}",
                    "type": "file",
                    "uri": manifest_uri,
                    "ingestion_id": ingestion.get("id"),
                    "created_at": ingestion.get("created_at"),
                })
                seen_sources.add(manifest_uri)
        
        # Build datasets (from ingestion metadata)
        datasets = []
        for ingestion in ingestions:
            metadata = ingestion.get("metadata", {})
            coverage = metadata.get("coverage", {})
            if coverage:
                datasets.append({
                    "id": f"dataset-{ingestion.get('id')}",
                    "ingestion_id": ingestion.get("id"),
                    "dataset_type": ingestion.get("ingestion_type"),
                    "coverage": coverage,
                    "status": ingestion.get("status"),
                    "created_at": ingestion.get("completed_at") or ingestion.get("created_at"),
                })
        
        # Build dashboards (from observations and exports)
        dashboards = []
        # Dashboard views are essentially what we show - link observations/exports
        for observation in observations:
            dashboards.append({
                "id": f"dashboard-{observation.get('observation_id')}",
                "type": "observation_view",
                "source_id": observation.get("observation_id"),
                "source_type": "observation",
                "created_at": observation.get("computed_at") or observation.get("created_at"),
            })
        
        for export in exports:
            if export.get("status") == "COMPLETED":
                dashboards.append({
                    "id": f"dashboard-{export.get('id')}",
                    "type": "report_view",
                    "source_id": export.get("id"),
                    "source_type": "export",
                    "created_at": export.get("completed_at") or export.get("created_at"),
                })
        
        return {
            "sources": sources,
            "ingestions": ingestions,
            "datasets": datasets,
            "analyses": analyses,
            "observations": observations,
            "exports": exports,
            "dashboards": dashboards,
            "relationships": relationships,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "sources": [],
            "ingestions": [],
            "datasets": [],
            "analyses": [],
            "observations": [],
            "exports": [],
            "dashboards": [],
            "relationships": [],
        }


def compute_coverage_from_data_files(tenant_id: UUID) -> Dict[str, Dict[str, Dict[str, Dict[str, int]]]]:
    """Compute coverage by scanning actual data files"""
    coverage: Dict[str, Dict[str, Dict[str, Dict[str, int]]]] = {}
    
    try:
        # Scan target_data_model directory for parquet files
        target_dir = BASE_PATH / "target_data_model" / str(tenant_id)
        
        if not target_dir.exists():
            return coverage
        
        # Scan for parquet files - they may be directly in dataset_type folder
        all_parquet_files = []
        for item in target_dir.iterdir():
            if not item.is_dir():
                continue
            
            dataset_type = item.name
            
            # Check if there are parquet files directly in dataset_type folder
            parquet_files = list(item.glob("*.parquet"))
            all_parquet_files.extend(parquet_files)
            
            # Also check subdirectories recursively
            for parquet_file in item.rglob("*.parquet"):
                if parquet_file not in all_parquet_files:
                    all_parquet_files.append(parquet_file)
        
        # Try to read metadata from parquet files
        if all_parquet_files:
            # Try polars first (faster), fallback to pandas
            try:
                import polars as pl
                use_polars = True
            except ImportError:
                try:
                    import pandas as pd
                    use_polars = False
                except ImportError:
                    use_polars = None
            
            if use_polars is not None:
                # Sample files to extract date ranges
                sample_files = all_parquet_files[:min(5, len(all_parquet_files))]
                
                for parquet_file in sample_files:
                    try:
                        if use_polars:
                            # Read just head rows with polars
                            df_sample = pl.scan_parquet(str(parquet_file)).head(1000).collect()
                            df_dict = df_sample.to_dict(as_series=False)
                            df_sample = {col: df_dict[col] for col in df_dict.keys()}
                        else:
                            # Read just metadata/head to get date info with pandas
                            df_sample = pd.read_parquet(parquet_file, nrows=1000)
                        
                        # Try to extract year/month from service_date or similar columns
                        columns = list(df_sample.keys()) if use_polars else df_sample.columns
                        date_cols = [col for col in columns if 'date' in col.lower() or 'service' in col.lower()]
                        
                        if date_cols:
                            date_col = date_cols[0]
                            
                            if use_polars:
                                # Extract dates from polars dataframe
                                date_values = df_sample[date_col]
                                # Parse dates
                                dates_parsed = []
                                for date_val in date_values:
                                    if date_val:
                                        try:
                                            if isinstance(date_val, str):
                                                from datetime import datetime
                                                dt = datetime.fromisoformat(date_val.replace('Z', '+00:00'))
                                            else:
                                                dt = date_val
                                            dates_parsed.append(dt)
                                        except:
                                            continue
                                
                                # Get unique year-month combinations
                                year_month_lob_market = {}
                                for dt in dates_parsed:
                                    year = str(dt.year)
                                    month = f"{dt.month:02d}"
                                    
                                    lob = "COMMERCIAL"
                                    market = "NYC"
                                    
                                    # Try to get LOB and market from dataframe
                                    if 'lob' in columns and df_sample.get('lob'):
                                        lob_vals = df_sample['lob']
                                        if lob_vals:
                                            unique_lobs = set([v for v in lob_vals if v])
                                            if unique_lobs:
                                                lob = str(list(unique_lobs)[0]).upper()
                                    
                                    if 'market' in columns and df_sample.get('market'):
                                        market_vals = df_sample['market']
                                        if market_vals:
                                            unique_markets = set([v for v in market_vals if v])
                                            if unique_markets:
                                                market = str(list(unique_markets)[0]).upper()
                                    
                                    key = (year, month, lob, market)
                                    year_month_lob_market[key] = year_month_lob_market.get(key, 0) + 1
                                
                                # Aggregate into coverage structure
                                for (year, month, lob, market), count in year_month_lob_market.items():
                                    if year not in coverage:
                                        coverage[year] = {}
                                    if month not in coverage[year]:
                                        coverage[year][month] = {}
                                    if lob not in coverage[year][month]:
                                        coverage[year][month][lob] = {}
                                    
                                    # Estimate record count
                                    estimated_count = len(all_parquet_files) * 1000
                                    coverage[year][month][lob][market] = coverage[year][month][lob].get(market, 0) + estimated_count
                            else:
                                # Pandas processing
                                df_sample[date_col] = pd.to_datetime(df_sample[date_col], errors='coerce')
                                df_sample = df_sample.dropna(subset=[date_col])
                                
                                for _, row in df_sample.iterrows():
                                    date_val = row[date_col]
                                    if pd.notna(date_val):
                                        year = str(date_val.year)
                                        month = f"{date_val.month:02d}"
                                        
                                        if year not in coverage:
                                            coverage[year] = {}
                                        if month not in coverage[year]:
                                            coverage[year][month] = {}
                                        
                                        # Try to get LOB and market
                                        lob = "COMMERCIAL"  # Default
                                        market = "NYC"  # Default
                                        
                                        if 'lob' in df_sample.columns:
                                            lob_val = row.get('lob', 'COMMERCIAL')
                                            if pd.notna(lob_val):
                                                lob = str(lob_val).upper()
                                        
                                        if 'market' in df_sample.columns:
                                            market_val = row.get('market', 'NYC')
                                            if pd.notna(market_val):
                                                market = str(market_val).upper()
                                        
                                        if lob not in coverage[year][month]:
                                            coverage[year][month][lob] = {}
                                        
                                        # Estimate record count
                                        estimated_count = len(all_parquet_files) * 1000
                                        coverage[year][month][lob][market] = coverage[year][month][lob].get(market, 0) + estimated_count
                        
                        # If no date columns found, infer from file path or use defaults
                        if not date_cols:
                            # Check if dataframe has date info in other columns
                            if use_polars:
                                # Try to infer from other columns
                                pass
                            # Try to extract from file path: .../YYYY/MM/...
                            path_parts = parquet_file.parts
                            year = None
                            month = None
                            
                            for i, part in enumerate(path_parts):
                                if part.isdigit() and len(part) == 4 and 2000 <= int(part) <= 2100:
                                    year = part
                                    # Check next part for month
                                    if i + 1 < len(path_parts) and path_parts[i + 1].isdigit():
                                        month_val = int(path_parts[i + 1])
                                        if 1 <= month_val <= 12:
                                            month = f"{month_val:02d}"
                                    break
                            
                            if year and month:
                                if year not in coverage:
                                    coverage[year] = {}
                                if month not in coverage[year]:
                                    coverage[year][month] = {}
                                
                                lob = "COMMERCIAL"
                                market = "NYC"
                                
                                # Try to extract LOB and market from dataframe if available
                                if use_polars:
                                    if 'lob' in columns and df_sample.get('lob'):
                                        unique_lobs = set([v for v in df_sample['lob'] if v])
                                        if unique_lobs:
                                            lob = str(list(unique_lobs)[0]).upper()
                                    if 'market' in columns and df_sample.get('market'):
                                        unique_markets = set([v for v in df_sample['market'] if v])
                                        if unique_markets:
                                            market = str(list(unique_markets)[0]).upper()
                                else:
                                    if 'lob' in df_sample.columns:
                                        unique_lobs = df_sample['lob'].dropna().unique()
                                        if len(unique_lobs) > 0:
                                            lob = str(unique_lobs[0]).upper()
                                    if 'market' in df_sample.columns:
                                        unique_markets = df_sample['market'].dropna().unique()
                                        if len(unique_markets) > 0:
                                            market = str(unique_markets[0]).upper()
                                
                                if lob not in coverage[year][month]:
                                    coverage[year][month][lob] = {}
                                
                                # Use actual file count
                                file_count = len([f for f in all_parquet_files if year in str(f) and month in str(f)])
                                coverage[year][month][lob][market] = file_count * 1000
                    
                    except Exception as e:
                        print(f"Error reading parquet file {parquet_file}: {e}")
                        continue
                
                # If we still couldn't parse, use current date as default
                if not coverage and all_parquet_files:
                    now = datetime.utcnow()
                    year = str(now.year)
                    month = f"{now.month:02d}"
                    
                    coverage[year] = {
                        month: {
                            "COMMERCIAL": {
                                "NYC": len(all_parquet_files) * 1000,  # Estimate
                            }
                        }
                    }
            else:
                # Neither polars nor pandas available - use file count as estimate
                now = datetime.utcnow()
                year = str(now.year)
                month = f"{now.month:02d}"
                
                coverage[year] = {
                    month: {
                        "COMMERCIAL": {
                            "NYC": len(all_parquet_files) * 1000,  # Estimate
                        }
                    }
                }
    
    except Exception as e:
        print(f"Error computing coverage from data files: {e}")
        import traceback
        traceback.print_exc()
    
    return coverage
