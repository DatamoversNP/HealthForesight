"""
Baseline Utilization + Baseline Behavior Profiling
Stage 3 of platform execution - establishes what "normal" looks like
"""
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, date
from uuid import UUID, uuid4
from pathlib import Path
import pandas as pd
import numpy as np
import json
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class BaselineTimeSeriesResult(BaseModel):
    """Baseline time-series decomposition result"""
    date: date
    observed: float
    trend: float
    seasonal: float
    residual: float
    lower_bound: float
    upper_bound: float
    confidence_level: float = Field(0.95, description="Confidence level for bounds")


class BaselineBenchmark(BaseModel):
    """Baseline utilization/cost benchmark"""
    metric_name: str
    metric_value: float
    unit: str  # e.g., "per_1k", "PMPM", "percentage"
    segment: Optional[str] = None  # e.g., "LOB", "market", "age_group"
    segment_value: Optional[str] = None
    confidence_interval_lower: Optional[float] = None
    confidence_interval_upper: Optional[float] = None
    sample_size: int


class ProviderArchetype(BaseModel):
    """Provider archetype from clustering"""
    archetype_id: int
    archetype_name: str
    provider_count: int
    characteristics: Dict[str, Any]  # e.g., ordering_intensity, site_preference, etc.
    representative_providers: List[str]  # Sample provider IDs


class PatientSensitivitySegment(BaseModel):
    """Patient sensitivity segment"""
    segment_id: int
    segment_name: str
    member_count: int
    characteristics: Dict[str, Any]  # e.g., risk_band, cost_share_exposure, access_friction
    utilization_profile: Dict[str, float]  # Baseline utilization metrics for this segment


class BaselineConfounderEvent(BaseModel):
    """Baseline confounder calendar event"""
    event_date: date
    event_type: str  # e.g., "SEASONALITY", "MARKET_EVENT", "REGULATORY_CHANGE"
    event_description: str
    impact_magnitude: Optional[float] = None  # Estimated impact on utilization
    affected_segments: List[str] = Field(default_factory=list)


class BaselineAnalysisResult(BaseModel):
    """Complete baseline analysis result"""
    analysis_id: str
    tenant_id: str
    generated_at: datetime
    
    # Time-series baseline
    time_series: List[BaselineTimeSeriesResult] = Field(default_factory=list)
    
    # Benchmarks
    benchmarks: List[BaselineBenchmark] = Field(default_factory=list)
    
    # Provider archetypes
    provider_archetypes: List[ProviderArchetype] = Field(default_factory=list)
    
    # Patient sensitivity segments
    patient_segments: List[PatientSensitivitySegment] = Field(default_factory=list)
    
    # Confounder calendar
    confounder_events: List[BaselineConfounderEvent] = Field(default_factory=list)
    
    # Metadata
    data_coverage: Dict[str, Any] = Field(default_factory=dict)
    model_parameters: Dict[str, Any] = Field(default_factory=dict)


class BaselineTimeSeriesModel:
    """Baseline time-series model using STL decomposition or GAM"""
    
    def __init__(self, seasonal_period: int = 12):
        """
        Initialize baseline time-series model
        
        Args:
            seasonal_period: Seasonal period (12 for monthly, 4 for quarterly)
        """
        # Ensure seasonal_period is an int (not float)
        self.seasonal_period = int(seasonal_period) if seasonal_period is not None else 12
    
    def fit_predict(
        self,
        df: pd.DataFrame,
        date_column: str,
        value_column: str,
        group_by: Optional[List[str]] = None,
    ) -> List[BaselineTimeSeriesResult]:
        """
        Fit time-series model and generate baseline predictions
        
        Args:
            df: DataFrame with time-series data
            date_column: Name of date column
            value_column: Name of value column to model
            group_by: Optional columns to group by (e.g., ['lob', 'market'])
            
        Returns:
            List of BaselineTimeSeriesResult
        """
        try:
            # Convert date column to datetime
            df = df.copy()
            original_length = len(df)
            
            # Check if date column is empty or all null
            non_null_count = df[date_column].notna().sum()
            non_empty_count = (df[date_column].astype(str).str.strip() != '').sum() if non_null_count > 0 else 0
            
            if non_null_count == 0 or non_empty_count == 0:
                logger.warning(f"Date column '{date_column}' is empty or all null ({non_null_count} non-null, {non_empty_count} non-empty out of {len(df)} rows). Cannot generate time series.")
                return []
            
            # Convert dates, handling errors - try multiple formats
            # First, check what format the dates are in
            sample_date = df[date_column].iloc[0] if len(df) > 0 else None
            logger.info(f"Date column '{date_column}' sample value: {repr(sample_date)} (type: {type(sample_date).__name__})")
            
            # Try parsing with different formats
            if sample_date is not None:
                # Try common date formats
                date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y%m%d', '%m-%d-%Y', '%d-%m-%Y']
                parsed_successfully = False
                
                for fmt in date_formats:
                    try:
                        test_date = pd.to_datetime(df[date_column].iloc[0], format=fmt, errors='raise')
                        logger.info(f"Successfully parsed date with format '{fmt}'")
                        # Parse all dates with this format
                        df[date_column] = pd.to_datetime(df[date_column], format=fmt, errors='coerce')
                        parsed_successfully = True
                        break
                    except:
                        continue
                
                if not parsed_successfully:
                    # Fallback to infer format
                    logger.warning(f"Could not parse date with common formats, trying infer_datetime_format")
                    df[date_column] = pd.to_datetime(df[date_column], infer_datetime_format=True, errors='coerce')
            else:
                # No sample, just try standard conversion
                df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
            
            df = df.sort_values(date_column)
            
            # Check for NaT dates
            nat_count = df[date_column].isna().sum()
            if nat_count > 0:
                logger.warning(f"Found {nat_count} NaT dates out of {original_length} rows after conversion")
                if nat_count == original_length:
                    # Show sample of what we're trying to parse
                    sample_values = df[date_column].iloc[:5].tolist() if len(df) > 0 else []
                    logger.error(f"ALL dates are NaT! Sample raw values: {sample_values}")
            
            # Drop NaT dates before processing
            df = df.dropna(subset=[date_column])
            
            if len(df) == 0:
                logger.error(f"All {original_length} rows had invalid dates after conversion. Cannot generate time series.")
                return []
            
            logger.info(f"Processing {len(df)} valid rows (dropped {original_length - len(df)} rows with invalid dates)")
            
            results = []
            
            if group_by:
                # Group by segments
                for group_key, group_df in df.groupby(group_by):
                    group_results = self._fit_group(group_df, date_column, value_column, group_key)
                    results.extend(group_results)
            else:
                # Single time-series
                results = self._fit_group(df, date_column, value_column, None)
            
            logger.info(f"Generated {len(results)} time series results from {len(df)} rows")
            if len(results) == 0:
                logger.warning(f"No time series results generated. DataFrame shape: {df.shape}, date_column: {date_column}, value_column: {value_column}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in baseline time-series model: {e}", exc_info=True)
            raise
    
    def _fit_group(
        self,
        df: pd.DataFrame,
        date_column: str,
        value_column: str,
        group_key: Optional[Tuple],
    ) -> List[BaselineTimeSeriesResult]:
        """Fit model for a single group"""
        try:
            # Use STL decomposition if statsmodels available, otherwise use simple moving average
            try:
                from statsmodels.tsa.seasonal import STL
                
                # Prepare data for STL
                # Use 'ME' (Month End) instead of deprecated 'M'
                ts = df.set_index(date_column)[value_column].resample('ME').sum()
                ts = ts.ffill().fillna(0)
                
                # STL requires seasonal_period to be an odd integer >= 3
                # If even, convert to next odd number (e.g., 12 -> 13)
                seasonal_period_stl = int(self.seasonal_period)
                if seasonal_period_stl < 3:
                    seasonal_period_stl = 3
                elif seasonal_period_stl % 2 == 0:
                    seasonal_period_stl = seasonal_period_stl + 1  # Make odd
                
                if len(ts) < 2 * seasonal_period_stl:
                    # Not enough data for STL, use simple trend
                    return self._simple_trend(df, date_column, value_column, group_key)
                
                # Fit STL with odd seasonal period
                stl = STL(ts, seasonal=seasonal_period_stl, robust=True)
                result = stl.fit()
                
                # Generate results
                results = []
                for idx, (date_val, observed) in enumerate(ts.items()):
                    trend = result.trend.loc[date_val] if date_val in result.trend.index else observed
                    seasonal = result.seasonal.loc[date_val] if date_val in result.seasonal.index else 0
                    residual = result.resid.loc[date_val] if date_val in result.resid.index else 0
                    
                    # Calculate confidence bounds (simple: trend ± 2*std(residual))
                    residual_std = result.resid.std()
                    lower_bound = trend + seasonal - 2 * residual_std
                    upper_bound = trend + seasonal + 2 * residual_std
                    
                    results.append(BaselineTimeSeriesResult(
                        date=date_val.date() if isinstance(date_val, pd.Timestamp) else date_val,
                        observed=float(observed),
                        trend=float(trend),
                        seasonal=float(seasonal),
                        residual=float(residual),
                        lower_bound=float(lower_bound),
                        upper_bound=float(upper_bound),
                    ))
                
                return results
                
            except ImportError:
                # Fallback to simple trend if statsmodels not available
                return self._simple_trend(df, date_column, value_column, group_key)
                
        except Exception as e:
            logger.warning(f"Error in STL decomposition, using simple trend: {e}")
            return self._simple_trend(df, date_column, value_column, group_key)
    
    def _simple_trend(
        self,
        df: pd.DataFrame,
        date_column: str,
        value_column: str,
        group_key: Optional[Tuple],
    ) -> List[BaselineTimeSeriesResult]:
        """Simple trend model using moving average"""
        df = df.copy()
        df = df.sort_values(date_column)
        
        # Calculate moving average for trend
        # Ensure window is an int - pandas rolling() requires int, not float
        seasonal_period_int = int(self.seasonal_period) if hasattr(self, 'seasonal_period') else 12
        df_len = len(df)
        window = int(min(seasonal_period_int, df_len // 2)) if df_len > 4 else int(df_len)
        df['trend'] = df[value_column].rolling(window=window, center=True).mean()
        # Use modern pandas fillna syntax
        df['trend'] = df['trend'].bfill().ffill()
        
        # Simple seasonal adjustment (mean by month)
        df['month'] = pd.to_datetime(df[date_column]).dt.month
        seasonal_means = df.groupby('month')[value_column].mean()
        df['seasonal'] = df['month'].map(seasonal_means) - df[value_column].mean()
        
        # Residual
        df['residual'] = df[value_column] - df['trend'] - df['seasonal']
        
        # Confidence bounds
        residual_std = df['residual'].std()
        df['lower_bound'] = df['trend'] + df['seasonal'] - 2 * residual_std
        df['upper_bound'] = df['trend'] + df['seasonal'] + 2 * residual_std
        
        results = []
        skipped_count = 0
        for _, row in df.iterrows():
            date_val = row[date_column]
            
            # Skip rows with NaT (Not a Time) or null dates
            if pd.isna(date_val) or date_val is pd.NaT or date_val is None:
                skipped_count += 1
                continue
            
            if isinstance(date_val, pd.Timestamp):
                date_val = date_val.date()
            elif isinstance(date_val, str):
                date_val = pd.to_datetime(date_val).date()
            elif isinstance(date_val, datetime):
                date_val = date_val.date()
            elif not isinstance(date_val, date):
                # Fallback: try to convert
                try:
                    date_val = pd.to_datetime(date_val).date()
                    # Double-check after conversion - NaT will still be NaT after to_datetime
                    if pd.isna(date_val) or date_val is pd.NaT:
                        logger.debug(f"Skipping row - date conversion resulted in NaT: {date_val}")
                        continue
                except Exception as e:
                    logger.warning(f"Could not convert date value: {date_val}, error: {e}")
                    continue
            
            # Ensure all numeric values are properly converted to native Python types
            # Pydantic v2 requires native Python types, not numpy/pandas types
            try:
                # Convert numpy/pandas types to native Python types explicitly
                def to_native_float(val):
                    """Convert to native Python float, handling numpy/pandas types"""
                    if pd.isna(val) or val is None:
                        return 0.0
                    # Handle numpy scalar types - use .item() to get native Python type
                    if hasattr(val, 'item'):
                        try:
                            val = val.item()  # This returns native Python type
                        except (ValueError, AttributeError):
                            pass
                    # Handle pandas Series/DataFrame values
                    if hasattr(val, 'iloc'):
                        val = val.iloc[0] if len(val) > 0 else 0.0
                        if hasattr(val, 'item'):
                            val = val.item()
                    # Convert to native Python float explicitly - double conversion to ensure purity
                    try:
                        # First convert to Python float
                        result = float(val)
                        # Then convert again to ensure it's not a numpy float64
                        result = float(result)
                        # Verify it's actually a Python float, not numpy
                        import numpy as np
                        if isinstance(result, np.floating):
                            result = float(result.item())
                        return result
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Could not convert value to float: {val}, type: {type(val)}, error: {e}")
                        return 0.0
                
                # Ensure date is a proper date object (not datetime or Timestamp)
                # Handle all possible date input types
                if isinstance(date_val, date):
                    # Already a date, keep it
                    final_date = date_val
                elif isinstance(date_val, pd.Timestamp):
                    final_date = date_val.date()
                elif isinstance(date_val, datetime):
                    final_date = date_val.date()
                elif isinstance(date_val, str):
                    final_date = pd.to_datetime(date_val).date()
                else:
                    # Try to convert anything else
                    try:
                        final_date = pd.to_datetime(date_val).date()
                    except Exception:
                        logger.warning(f"Could not convert date value: {date_val} (type: {type(date_val)})")
                        continue
                
                # Create the result object with all native Python types
                # Extract and convert all values explicitly before passing to Pydantic
                observed_val = to_native_float(row[value_column])
                trend_val = to_native_float(row['trend'])
                seasonal_val = to_native_float(row['seasonal'])
                residual_val = to_native_float(row['residual'])
                lower_bound_val = to_native_float(row['lower_bound'])
                upper_bound_val = to_native_float(row['upper_bound'])
                
                # Double-check all values are native Python types
                assert isinstance(observed_val, float), f"observed_val is {type(observed_val)}, not float"
                assert isinstance(trend_val, float), f"trend_val is {type(trend_val)}, not float"
                assert isinstance(seasonal_val, float), f"seasonal_val is {type(seasonal_val)}, not float"
                assert isinstance(residual_val, float), f"residual_val is {type(residual_val)}, not float"
                assert isinstance(lower_bound_val, float), f"lower_bound_val is {type(lower_bound_val)}, not float"
                assert isinstance(upper_bound_val, float), f"upper_bound_val is {type(upper_bound_val)}, not float"
                assert isinstance(final_date, date), f"final_date is {type(final_date)}, not date"
                
                # Explicitly set confidence_level to ensure it's a native Python float
                confidence_level_val = float(0.95)
                
                # Force all values to be JSON-serializable (truly native Python types)
                # This ensures Pydantic v2 receives only native types
                try:
                    # Create a dict with all values
                    data_dict = {
                        'date': final_date.isoformat(),
                        'observed': observed_val,
                        'trend': trend_val,
                        'seasonal': seasonal_val,
                        'residual': residual_val,
                        'lower_bound': lower_bound_val,
                        'upper_bound': upper_bound_val,
                        'confidence_level': confidence_level_val,
                    }
                    # Serialize and deserialize to force native types
                    json_str = json.dumps(data_dict, default=str)
                    data_dict = json.loads(json_str)
                    # Convert date back from ISO string
                    data_dict['date'] = date.fromisoformat(data_dict['date'])
                    
                    result_obj = BaselineTimeSeriesResult(**data_dict)
                except Exception as e:
                    # Fallback to direct constructor if JSON approach fails
                    logger.warning(f"JSON serialization approach failed, using direct constructor: {e}")
                    result_obj = BaselineTimeSeriesResult(
                        date=final_date,
                        observed=observed_val,
                        trend=trend_val,
                        seasonal=seasonal_val,
                        residual=residual_val,
                        lower_bound=lower_bound_val,
                        upper_bound=upper_bound_val,
                        confidence_level=confidence_level_val,
                    )
                results.append(result_obj)
            except Exception as e:
                logger.error(f"Error creating BaselineTimeSeriesResult: {e}, date_val={date_val}, type={type(date_val)}")
                logger.error(f"Row data types: date={type(row[date_column])}, observed={type(row[value_column])}")
                # Don't raise - skip this row and continue
                continue
        
        if skipped_count > 0:
            logger.warning(f"Skipped {skipped_count} rows with invalid dates out of {len(df)} total rows")
        if len(results) == 0 and len(df) > 0:
            logger.warning(f"No time series results created. All rows may have invalid dates or conversion errors.")
        
        return results


class BaselineBenchmarkCalculator:
    """Calculate baseline utilization/cost benchmarks"""
    
    def calculate_benchmarks(
        self,
        claims_df: pd.DataFrame,
        enrollment_df: Optional[pd.DataFrame] = None,
        group_by: Optional[List[str]] = None,
    ) -> List[BaselineBenchmark]:
        """
        Calculate baseline benchmarks
        
        Args:
            claims_df: Claims data
            enrollment_df: Optional enrollment data for PMPM calculations
            group_by: Optional columns to group by
            
        Returns:
            List of BaselineBenchmark
        """
        benchmarks = []
        
        # Calculate per-1k metrics
        per_1k_benchmarks = self._calculate_per_1k(claims_df, group_by)
        benchmarks.extend(per_1k_benchmarks)
        
        # Calculate PMPM if enrollment data available
        if enrollment_df is not None:
            pmpm_benchmarks = self._calculate_pmpm(claims_df, enrollment_df, group_by)
            benchmarks.extend(pmpm_benchmarks)
        
        # Calculate site-of-care mix
        site_mix = self._calculate_site_of_care_mix(claims_df, group_by)
        benchmarks.extend(site_mix)
        
        # Calculate service mix
        service_mix = self._calculate_service_mix(claims_df, group_by)
        benchmarks.extend(service_mix)
        
        return benchmarks
    
    def _calculate_per_1k(
        self,
        claims_df: pd.DataFrame,
        group_by: Optional[List[str]],
    ) -> List[BaselineBenchmark]:
        """Calculate per-1k utilization metrics"""
        benchmarks = []
        
        # Get member months (approximate from claims)
        if 'member_id' in claims_df.columns:
            member_months = len(claims_df['member_id'].unique()) * 12  # Approximate
        else:
            member_months = len(claims_df) * 12  # Rough estimate
        
        # Calculate metrics per 1,000 members
        if group_by:
            for group_key, group_df in claims_df.groupby(group_by):
                group_member_months = len(group_df['member_id'].unique()) * 12 if 'member_id' in group_df.columns else len(group_df) * 12
                
                # Utilization rate per 1,000 member-months (metric dictionary: util_rate_total_per_1000_mm)
                total_claims = len(group_df)
                per_1k = (total_claims / group_member_months) * 1000 if group_member_months > 0 else 0
                
                benchmarks.append(BaselineBenchmark(
                    metric_name="util_rate_total_per_1000_mm",
                    metric_value=float(per_1k),
                    unit="claim_lines per 1,000 member-months",
                    segment="_".join(group_by),
                    segment_value=str(group_key),
                    sample_size=int(len(group_df)),  # Ensure int
                ))
                
                # Allowed cost PMPM (metric dictionary: allowed_pmpm_total)
                if 'allowed_amount' in group_df.columns or 'paid_amount' in group_df.columns:
                    total_cost = group_df.get('allowed_amount', group_df.get('paid_amount')).sum()
                    pmpm = (total_cost / group_member_months) if group_member_months > 0 else 0
                    
                    benchmarks.append(BaselineBenchmark(
                        metric_name="allowed_pmpm_total",
                        metric_value=float(pmpm),
                        unit="dollars PMPM",
                        segment="_".join(group_by),
                        segment_value=str(group_key),
                        sample_size=int(len(group_df)),  # Ensure int
                    ))
                
                # Backward compatibility: also include total_cost_per_1k (for legacy code)
                if 'paid_amount' in group_df.columns:
                    total_cost = group_df['paid_amount'].sum()
                    cost_per_1k = (total_cost / group_member_months) * 1000 if group_member_months > 0 else 0
                    
                    benchmarks.append(BaselineBenchmark(
                        metric_name="total_cost_per_1k",
                        metric_value=float(cost_per_1k),
                        unit="per_1k",
                        segment="_".join(group_by),
                        segment_value=str(group_key),
                        sample_size=int(len(group_df)),  # Ensure int
                    ))
        else:
            # Overall metrics
            # Utilization rate per 1,000 member-months (metric dictionary: util_rate_total_per_1000_mm)
            total_claims = len(claims_df)
            per_1k = (total_claims / member_months) * 1000 if member_months > 0 else 0
            
            benchmarks.append(BaselineBenchmark(
                metric_name="util_rate_total_per_1000_mm",
                metric_value=float(per_1k),
                unit="claim_lines per 1,000 member-months",
                sample_size=int(len(claims_df)),  # Ensure int
            ))
            
            # Allowed cost PMPM (metric dictionary: allowed_pmpm_total)
            if 'allowed_amount' in claims_df.columns or 'paid_amount' in claims_df.columns:
                total_cost = claims_df.get('allowed_amount', claims_df.get('paid_amount')).sum()
                pmpm = (total_cost / member_months) if member_months > 0 else 0
                
                benchmarks.append(BaselineBenchmark(
                    metric_name="allowed_pmpm_total",
                    metric_value=float(pmpm),
                    unit="dollars PMPM",
                    sample_size=int(len(claims_df)),  # Ensure int
                ))
            
            # Backward compatibility: also include total_cost_per_1k (for legacy code)
            if 'paid_amount' in claims_df.columns:
                total_cost = claims_df['paid_amount'].sum()
                cost_per_1k = (total_cost / member_months) * 1000 if member_months > 0 else 0
                
                benchmarks.append(BaselineBenchmark(
                    metric_name="total_cost_per_1k",
                    metric_value=float(cost_per_1k),
                    unit="per_1k",
                    sample_size=int(len(claims_df)),  # Ensure int
                ))
        
        return benchmarks
    
    def _calculate_pmpm(
        self,
        claims_df: pd.DataFrame,
        enrollment_df: pd.DataFrame,
        group_by: Optional[List[str]],
    ) -> List[BaselineBenchmark]:
        """Calculate PMPM (Per Member Per Month) metrics"""
        benchmarks = []
        
        # Merge claims with enrollment to get member months
        if 'member_id' in claims_df.columns and 'member_id' in enrollment_df.columns:
            # Calculate member months from enrollment
            enrollment_df['coverage_month'] = pd.to_datetime(enrollment_df.get('coverage_month', enrollment_df.get('month', '2024-01')))
            member_months = len(enrollment_df.groupby(['member_id', enrollment_df['coverage_month'].dt.to_period('M')]))
            
            if group_by:
                for group_key, group_df in claims_df.groupby(group_by):
                    # Filter enrollment for this group
                    group_member_ids = set(group_df['member_id'].unique())
                    group_enrollment = enrollment_df[enrollment_df['member_id'].isin(group_member_ids)]
                    group_member_months = len(group_enrollment.groupby(['member_id', group_enrollment['coverage_month'].dt.to_period('M')]))
                    
                    # Use allowed_amount if available, otherwise paid_amount
                    cost_col = group_df.get('allowed_amount') if 'allowed_amount' in group_df.columns else group_df.get('paid_amount')
                    if cost_col is not None and group_member_months > 0:
                        total_cost = cost_col.sum()
                        pmpm = total_cost / group_member_months
                        
                        benchmarks.append(BaselineBenchmark(
                            metric_name="allowed_pmpm_total",
                            metric_value=float(pmpm),
                            unit="dollars PMPM",
                            segment="_".join(group_by),
                            segment_value=str(group_key),
                            sample_size=int(len(group_df)),  # Ensure int
                        ))
                        
                        # Backward compatibility: also include cost_pmpm
                        benchmarks.append(BaselineBenchmark(
                            metric_name="cost_pmpm",
                            metric_value=float(pmpm),
                            unit="PMPM",
                            segment="_".join(group_by),
                            segment_value=str(group_key),
                            sample_size=int(len(group_df)),  # Ensure int
                        ))
            else:
                # Use allowed_amount if available, otherwise paid_amount
                cost_col = claims_df.get('allowed_amount') if 'allowed_amount' in claims_df.columns else claims_df.get('paid_amount')
                if cost_col is not None and member_months > 0:
                    total_cost = cost_col.sum()
                    pmpm = total_cost / member_months
                    
                    benchmarks.append(BaselineBenchmark(
                        metric_name="allowed_pmpm_total",
                        metric_value=float(pmpm),
                        unit="dollars PMPM",
                        sample_size=int(len(claims_df)),  # Ensure int
                    ))
                    
                    # Backward compatibility: also include cost_pmpm
                    benchmarks.append(BaselineBenchmark(
                        metric_name="cost_pmpm",
                        metric_value=float(pmpm),
                        unit="PMPM",
                        sample_size=int(len(claims_df)),  # Ensure int
                    ))
        
        return benchmarks
    
    def _calculate_site_of_care_mix(
        self,
        claims_df: pd.DataFrame,
        group_by: Optional[List[str]],
    ) -> List[BaselineBenchmark]:
        """Calculate site-of-care mix percentages"""
        benchmarks = []
        
        if 'place_of_service' in claims_df.columns:
            if group_by:
                for group_key, group_df in claims_df.groupby(group_by):
                    pos_counts = group_df['place_of_service'].value_counts()
                    total = len(group_df)
                    
                    for pos, count in pos_counts.items():
                        percentage = (count / total) * 100 if total > 0 else 0
                        
                        benchmarks.append(BaselineBenchmark(
                            metric_name=f"site_of_care_{pos}_percentage",
                            metric_value=float(percentage),
                            unit="percentage",
                            segment="_".join(group_by),
                            segment_value=str(group_key),
                            sample_size=int(count),  # Ensure int (value_counts returns numpy int64)
                        ))
            else:
                pos_counts = claims_df['place_of_service'].value_counts()
                total = len(claims_df)
                
                for pos, count in pos_counts.items():
                    percentage = (count / total) * 100 if total > 0 else 0
                    
                    benchmarks.append(BaselineBenchmark(
                        metric_name=f"site_of_care_{pos}_percentage",
                        metric_value=float(percentage),
                        unit="percentage",
                        sample_size=int(count),  # Ensure int (value_counts returns numpy int64)
                    ))
        
        return benchmarks
    
    def _calculate_service_mix(
        self,
        claims_df: pd.DataFrame,
        group_by: Optional[List[str]],
    ) -> List[BaselineBenchmark]:
        """Calculate service mix percentages"""
        benchmarks = []
        
        # Use CPT/HCPCS codes or service category
        service_column = None
        if 'cpt_hcpcs' in claims_df.columns:
            service_column = 'cpt_hcpcs'
        elif 'service_category' in claims_df.columns:
            service_column = 'service_category'
        
        if service_column:
            if group_by:
                for group_key, group_df in claims_df.groupby(group_by):
                    service_counts = group_df[service_column].value_counts().head(20)  # Top 20
                    total = len(group_df)
                    
                    for service, count in service_counts.items():
                        percentage = (count / total) * 100 if total > 0 else 0
                        
                        benchmarks.append(BaselineBenchmark(
                            metric_name=f"service_{service}_percentage",
                            metric_value=float(percentage),
                            unit="percentage",
                            segment="_".join(group_by),
                            segment_value=str(group_key),
                            sample_size=int(count),  # Ensure int (value_counts returns numpy int64)
                        ))
            else:
                service_counts = claims_df[service_column].value_counts().head(20)
                total = len(claims_df)
                
                for service, count in service_counts.items():
                    percentage = (count / total) * 100 if total > 0 else 0
                    
                    benchmarks.append(BaselineBenchmark(
                        metric_name=f"service_{service}_percentage",
                        metric_value=float(percentage),
                        unit="percentage",
                        sample_size=int(count),  # Ensure int (value_counts returns numpy int64)
                    ))
        
        return benchmarks



class ProviderPracticePatternProfiler:
    """Profile provider practice patterns using clustering"""
    
    def __init__(self, n_clusters: int = 5):
        self.n_clusters = int(n_clusters)  # Ensure it's an integer
    
    def profile_providers(
        self,
        claims_df: pd.DataFrame,
        provider_df: Optional[pd.DataFrame] = None,
    ) -> List[ProviderArchetype]:
        """Profile providers and create archetypes"""
        # Check for provider ID column upfront - return empty list if missing
        provider_id_col = None
        for col in ['rendering_npi', 'provider_id', 'npi']:
            if col in claims_df.columns:
                provider_id_col = col
                break
        if not provider_id_col:
            available_cols = list(claims_df.columns)
            logger.warning(
                f"Provider profiling skipped: No provider ID column found. "
                f"Looking for: ['rendering_npi', 'provider_id', 'npi']. "
                f"Available columns: {available_cols[:10]}"
            )
            return []
        
        try:
            provider_features = self._extract_provider_features(claims_df, provider_df)
            n_clusters_int = int(self.n_clusters)  # Ensure integer
            if len(provider_features) < n_clusters_int:
                logger.warning(f"Not enough providers ({len(provider_features)}) for {n_clusters_int} clusters")
                return []
            archetypes = self._cluster_providers(provider_features)
            return archetypes
        except ValueError as e:
            # If it's a "No provider ID column" error, return empty list instead of failing
            if "No provider ID column" in str(e):
                logger.warning(f"Provider profiling skipped: {e}")
                return []
            # Re-raise other ValueErrors
            logger.error(f"Error in provider practice pattern profiling: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Error in provider practice pattern profiling: {e}", exc_info=True)
            # Don't fail the entire baseline analysis if provider profiling fails
            logger.warning("Continuing baseline analysis without provider archetypes")
            return []
    
    def _extract_provider_features(
        self,
        claims_df: pd.DataFrame,
        provider_df: Optional[pd.DataFrame],
    ) -> pd.DataFrame:
        """Extract features for provider clustering"""
        provider_id_col = None
        for col in ['rendering_npi', 'provider_id', 'npi']:
            if col in claims_df.columns:
                provider_id_col = col
                break
        if not provider_id_col:
            # Log available columns for debugging
            available_cols = list(claims_df.columns)
            logger.warning(
                f"No provider ID column found in claims data. "
                f"Looking for: ['rendering_npi', 'provider_id', 'npi']. "
                f"Available columns: {available_cols[:20]}"  # Show first 20 columns
            )
            raise ValueError(
                f"No provider ID column found in claims data. "
                f"Looking for: ['rendering_npi', 'provider_id', 'npi']. "
                f"Available columns: {available_cols[:10]}"
            )
        
        provider_metrics = []
        
        # Find amount column
        amount_col = None
        for col in ['paid_amount', 'allowed_amount', 'total_charge', 'charge_amount']:
            if col in claims_df.columns:
                amount_col = col
                break
        
        if not amount_col:
            logger.warning("No amount column found for provider profiling, using 0")
            amount_col = 'amount'
            claims_df = claims_df.copy()
            claims_df[amount_col] = 0
        
        for provider_id, provider_claims in claims_df.groupby(provider_id_col):
            total_cost = float(provider_claims[amount_col].sum()) if amount_col in provider_claims.columns else 0.0
            avg_cost = float(provider_claims[amount_col].mean()) if amount_col in provider_claims.columns and len(provider_claims) > 0 else 0.0
            
            metrics = {
                'provider_id': provider_id,
                'total_claims': len(provider_claims),
                'total_cost': total_cost,
                'avg_cost_per_claim': avg_cost,
            }
            
            # Find member_id column
            member_id_col = None
            for col in ['member_id', 'member', 'patient_id', 'subscriber_id']:
                if col in provider_claims.columns:
                    member_id_col = col
                    break
            
            if member_id_col:
                unique_members = provider_claims[member_id_col].nunique()
                metrics['claims_per_member'] = len(provider_claims) / unique_members if unique_members > 0 else 0
            else:
                metrics['claims_per_member'] = 0
            provider_metrics.append(metrics)
        return pd.DataFrame(provider_metrics)
    
    def _cluster_providers(self, provider_features: pd.DataFrame) -> List[ProviderArchetype]:
        """Cluster providers into archetypes"""
        try:
            try:
                from sklearn.cluster import KMeans
                from sklearn.preprocessing import StandardScaler
            except ImportError:
                # sklearn not available - skip clustering
                KMeans = None
                StandardScaler = None
            feature_cols = [col for col in provider_features.columns if col != 'provider_id']
            X = provider_features[feature_cols].fillna(0)
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            n_clusters_int = int(self.n_clusters)  # Ensure integer
            kmeans = KMeans(n_clusters=n_clusters_int, random_state=42, n_init=10)
            provider_features['cluster'] = kmeans.fit_predict(X_scaled)
            archetypes = []
            for cluster_id in range(n_clusters_int):
                cluster_providers = provider_features[provider_features['cluster'] == cluster_id]
                if len(cluster_providers) == 0:
                    continue
                characteristics = {col: float(cluster_providers[col].mean()) for col in feature_cols}
                # Ensure cluster_id is int for array indexing
                cluster_id_int = int(cluster_id)
                cluster_center = kmeans.cluster_centers_[cluster_id_int]
                distances = np.linalg.norm(X_scaled[provider_features['cluster'] == cluster_id] - cluster_center, axis=1)
                # Ensure slice upper bound is int
                max_reps = int(min(5, len(cluster_providers)))
                closest_indices = distances.argsort()[:int(max_reps)]  # Ensure int for slice
                # Ensure indices are native Python ints (not numpy int64)
                closest_indices_list = [int(idx) for idx in closest_indices] if hasattr(closest_indices, '__iter__') else [int(closest_indices)]
                # Convert provider IDs to strings (Pydantic expects List[str])
                provider_ids = cluster_providers.iloc[closest_indices_list]['provider_id'].tolist()
                representative_providers = [str(pid) for pid in provider_ids]
                archetype_name = f"Archetype {cluster_id + 1}"
                archetypes.append(ProviderArchetype(
                    archetype_id=int(cluster_id),  # Ensure int for Pydantic
                    archetype_name=archetype_name,
                    provider_count=int(len(cluster_providers)),  # Ensure int
                    characteristics=characteristics,
                    representative_providers=representative_providers,
                ))
            return archetypes
        except ImportError:
            logger.warning("sklearn not available, using simple grouping")
            if 'total_claims' in provider_features.columns:
                n_clusters_int = int(self.n_clusters)  # Ensure integer
                provider_features['group'] = pd.qcut(provider_features['total_claims'], q=n_clusters_int, labels=False, duplicates='drop')
            else:
                provider_features['group'] = 0
            archetypes = []
            for group_id_raw in provider_features['group'].unique():
                # pd.qcut can return float64, ensure it's converted to int
                group_id = int(float(group_id_raw)) if pd.notna(group_id_raw) else 0
                group_providers = provider_features[provider_features['group'] == group_id_raw]  # Use raw for filtering
                characteristics = {col: float(group_providers[col].mean()) for col in provider_features.columns if col not in ['provider_id', 'group']}
                archetypes.append(ProviderArchetype(
                    archetype_id=group_id,  # Use converted int
                    archetype_name=f"Group {int(group_id) + 1}",
                    provider_count=int(len(group_providers)),  # Ensure int
                    characteristics=characteristics,
                    representative_providers=[str(pid) for pid in group_providers['provider_id'].head(5).tolist()],
                ))
            return archetypes


class ProviderNetworkAnalyzer:
    """Analyze provider network and market position features"""
    
    def analyze_network_features(
        self,
        claims_df: pd.DataFrame,
        provider_df: Optional[pd.DataFrame] = None,
        network_df: Optional[pd.DataFrame] = None,
    ) -> Dict[str, Any]:
        """Analyze provider network and market position"""
        features = {}
        features['provider_concentration'] = self._calculate_provider_concentration(claims_df)
        if provider_df is not None and 'system_affiliation' in provider_df.columns:
            features['system_affiliation_distribution'] = self._calculate_system_affiliation(claims_df, provider_df)
        if 'in_network_flag' in claims_df.columns:
            features['steerage_metrics'] = self._calculate_steerage_metrics(claims_df)
        if 'market' in claims_df.columns:
            features['market_concentration'] = self._calculate_market_concentration(claims_df)
        return features
    
    def _calculate_provider_concentration(self, claims_df: pd.DataFrame) -> Dict[str, float]:
        """Calculate provider concentration (HHI)"""
        provider_id_col = None
        for col in ['rendering_npi', 'provider_id', 'npi']:
            if col in claims_df.columns:
                provider_id_col = col
                break
        if not provider_id_col:
            return {}
        provider_shares = claims_df[provider_id_col].value_counts(normalize=True)
        hhi = (provider_shares ** 2).sum() * 10000
        return {
            'hhi': float(hhi),
            'top_10_provider_share': float(provider_shares.head(10).sum() * 100),
            'provider_count': len(provider_shares),
        }
    
    def _calculate_system_affiliation(self, claims_df: pd.DataFrame, provider_df: pd.DataFrame) -> Dict[str, float]:
        """Calculate system affiliation distribution"""
        # Find provider ID column in claims
        claims_provider_id_col = None
        for col in ['rendering_npi', 'provider_id', 'npi']:
            if col in claims_df.columns:
                claims_provider_id_col = col
                break
        if not claims_provider_id_col:
            return {}
        
        # Find matching provider ID column in provider_df
        provider_id_col = None
        if claims_provider_id_col in provider_df.columns:
            provider_id_col = claims_provider_id_col
        elif 'provider_id' in provider_df.columns:
            provider_id_col = 'provider_id'
        elif 'npi' in provider_df.columns:
            provider_id_col = 'npi'
        else:
            # No matching column found, return empty
            return {}
        
        # Ensure system_affiliation exists in provider_df
        if 'system_affiliation' not in provider_df.columns:
            return {}
        
        try:
            # Merge on the matching provider ID column
            if claims_provider_id_col == provider_id_col:
                merged = claims_df.merge(
                    provider_df[[provider_id_col, 'system_affiliation']], 
                    on=provider_id_col, 
                    how='left'
                )
            else:
                # Different column names, need to map
                provider_map = provider_df[[provider_id_col, 'system_affiliation']].set_index(provider_id_col)
                merged = claims_df.copy()
                merged['system_affiliation'] = merged[claims_provider_id_col].map(
                    provider_map['system_affiliation'].to_dict()
                )
            
            # Filter out None/NaN values before counting
            affiliation_series = merged['system_affiliation'].dropna()
            if len(affiliation_series) == 0:
                return {}
            
            affiliation_dist = affiliation_series.value_counts(normalize=True).to_dict()
            return {k: float(v * 100) for k, v in affiliation_dist.items()}
        except Exception as e:
            logger.warning(f"Error calculating system affiliation distribution: {e}")
            return {}
    
    def _calculate_steerage_metrics(self, claims_df: pd.DataFrame) -> Dict[str, float]:
        """Calculate steerage metrics"""
        in_network_pct = (claims_df['in_network_flag'].sum() / len(claims_df) * 100) if len(claims_df) > 0 else 0
        return {
            'in_network_percentage': float(in_network_pct),
            'out_of_network_percentage': float(100 - in_network_pct),
        }
    
    def _calculate_market_concentration(self, claims_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate market concentration"""
        market_shares = claims_df['market'].value_counts(normalize=True)
        return {
            'top_market_share': float(market_shares.iloc[0] * 100) if len(market_shares) > 0 else 0,
            'market_count': len(market_shares),
            'market_distribution': {k: float(v * 100) for k, v in market_shares.head(int(10)).items()},
        }


class PatientSensitivityStratifier:
    """Stratify patients by sensitivity (risk, cost-share, access friction)"""
    
    def stratify_patients(
        self,
        claims_df: pd.DataFrame,
        enrollment_df: Optional[pd.DataFrame] = None,
        member_df: Optional[pd.DataFrame] = None,
    ) -> List[PatientSensitivitySegment]:
        """Stratify patients into sensitivity segments"""
        try:
            patient_features = self._extract_patient_features(claims_df, enrollment_df, member_df)
            segments = self._create_segments(patient_features)
            return segments
        except Exception as e:
            logger.error(f"Error in patient sensitivity stratification: {e}", exc_info=True)
            raise
    
    def _extract_patient_features(
        self,
        claims_df: pd.DataFrame,
        enrollment_df: Optional[pd.DataFrame],
        member_df: Optional[pd.DataFrame],
    ) -> pd.DataFrame:
        """Extract patient-level features"""
        member_features = []
        
        # Find member_id column
        member_id_col = None
        for col in ['member_id', 'member', 'patient_id', 'subscriber_id']:
            if col in claims_df.columns:
                member_id_col = col
                break
        
        if not member_id_col:
            logger.warning("No member_id column found, using index as member_id")
            member_id_col = 'member_id'
            claims_df = claims_df.copy()
            claims_df['member_id'] = claims_df.index
        
        # Find amount column
        amount_col = None
        for col in ['paid_amount', 'allowed_amount', 'total_charge', 'charge_amount']:
            if col in claims_df.columns:
                amount_col = col
                break
        
        if not amount_col:
            logger.warning("No amount column found, using 0 as default")
            amount_col = 'amount'
            claims_df = claims_df.copy()
            claims_df['amount'] = 0
        
        for member_id, member_claims in claims_df.groupby(member_id_col):
            total_cost = float(member_claims[amount_col].sum()) if amount_col in member_claims.columns else 0.0
            avg_cost = float(member_claims[amount_col].mean()) if amount_col in member_claims.columns and len(member_claims) > 0 else 0.0
            
            features = {
                'member_id': member_id,
                'total_claims': len(member_claims),
                'total_cost': total_cost,
                'avg_cost_per_claim': avg_cost,
            }
            # risk_band assigned later in _create_segments using percentiles for balanced segments
            features['risk_band'] = None
            
            # Find cost share column
            cost_share_col = None
            for col in ['member_cost_share', 'cost_share', 'copay', 'coinsurance']:
                if col in member_claims.columns:
                    cost_share_col = col
                    break
            
            features['cost_share_exposure'] = float(member_claims[cost_share_col].sum()) if cost_share_col else 0.0
            features['access_friction'] = 0.0
            member_features.append(features)
        
        return pd.DataFrame(member_features)
    
    def _create_segments(self, patient_features: pd.DataFrame) -> List[PatientSensitivitySegment]:
        """Create patient sensitivity segments (LOW / MEDIUM / HIGH) using percentile-based bands so we get multiple segments when data has variation."""
        segments = []
        if patient_features is None or len(patient_features) == 0:
            return segments

        # Assign risk_band by cost percentiles so we get a balanced split (avoids "everyone in one segment")
        costs = patient_features['total_cost']
        p33 = float(costs.quantile(0.33)) if len(costs) > 0 else 0.0
        p67 = float(costs.quantile(0.67)) if len(costs) > 0 else 0.0
        if p33 == p67 and len(costs) > 0:
            # All same or two values: split by median
            p50 = float(costs.quantile(0.5))
            p33, p67 = p50 * 0.5, p50 * 1.5
        if p33 >= p67:
            p67 = p33 + 1.0  # ensure distinct bands

        def assign_band(total_cost: float) -> str:
            if total_cost <= p33:
                return 'LOW'
            if total_cost <= p67:
                return 'MEDIUM'
            return 'HIGH'

        patient_features = patient_features.copy()
        patient_features['risk_band'] = patient_features['total_cost'].apply(assign_band)

        # Always emit three segments (LOW, MEDIUM, HIGH) so the UI shows the full picture
        for risk_band in ['LOW', 'MEDIUM', 'HIGH']:
            band_members = patient_features[patient_features['risk_band'] == risk_band]
            if len(band_members) == 0:
                utilization_profile = {
                    'avg_claims_per_member': 0.0,
                    'avg_cost_per_member': 0.0,
                    'avg_cost_per_claim': 0.0,
                }
                characteristics = {'risk_band': risk_band, 'avg_cost_share_exposure': 0.0, 'avg_access_friction': 0.0}
            else:
                utilization_profile = {
                    'avg_claims_per_member': float(band_members['total_claims'].mean()),
                    'avg_cost_per_member': float(band_members['total_cost'].mean()),
                    'avg_cost_per_claim': float(band_members['avg_cost_per_claim'].mean()),
                }
                characteristics = {
                    'risk_band': risk_band,
                    'avg_cost_share_exposure': float(band_members['cost_share_exposure'].mean()),
                    'avg_access_friction': float(band_members['access_friction'].mean()),
                }
            segments.append(PatientSensitivitySegment(
                segment_id=len(segments),
                segment_name=f"{risk_band} Risk",
                member_count=int(len(band_members)),
                characteristics=characteristics,
                utilization_profile=utilization_profile,
            ))
        return segments


class BaselineConfounderCalendar:
    """Generate baseline confounder calendar (events/seasonality)"""
    
    def generate_calendar(
        self,
        start_date: date,
        end_date: date,
        market_events_df: Optional[pd.DataFrame] = None,
    ) -> List[BaselineConfounderEvent]:
        """Generate confounder calendar"""
        events = []
        seasonality_events = self._generate_seasonality_events(start_date, end_date)
        events.extend(seasonality_events)
        if market_events_df is not None:
            market_events = self._extract_market_events(market_events_df, start_date, end_date)
            events.extend(market_events)
        return events
    
    def _generate_seasonality_events(self, start_date: date, end_date: date) -> List[BaselineConfounderEvent]:
        """Generate seasonality events"""
        events = []
        current_date = start_date
        while current_date <= end_date:
            if current_date.month in [1, 2, 3]:
                events.append(BaselineConfounderEvent(
                    event_date=current_date,
                    event_type="SEASONALITY",
                    event_description="Q1: Post-holiday period, flu season",
                    impact_magnitude=1.1,
                    affected_segments=["ALL"],
                ))
            elif current_date.month in [4, 5, 6]:
                events.append(BaselineConfounderEvent(
                    event_date=current_date,
                    event_type="SEASONALITY",
                    event_description="Q2: Spring, routine care period",
                    impact_magnitude=1.0,
                    affected_segments=["ALL"],
                ))
            elif current_date.month in [7, 8, 9]:
                events.append(BaselineConfounderEvent(
                    event_date=current_date,
                    event_type="SEASONALITY",
                    event_description="Q3: Summer, typically lower utilization",
                    impact_magnitude=0.9,
                    affected_segments=["ALL"],
                ))
            elif current_date.month in [10, 11, 12]:
                events.append(BaselineConfounderEvent(
                    event_date=current_date,
                    event_type="SEASONALITY",
                    event_description="Q4: Year-end, deductible reset period",
                    impact_magnitude=1.15,
                    affected_segments=["ALL"],
                ))
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        return events
    
    def _extract_market_events(
        self,
        market_events_df: pd.DataFrame,
        start_date: date,
        end_date: date,
    ) -> List[BaselineConfounderEvent]:
        """Extract market events from data"""
        events = []
        if 'event_date' in market_events_df.columns:
            market_events_df['event_date'] = pd.to_datetime(market_events_df['event_date'])
            filtered = market_events_df[
                (market_events_df['event_date'].dt.date >= start_date) &
                (market_events_df['event_date'].dt.date <= end_date)
            ]
            for _, row in filtered.iterrows():
                events.append(BaselineConfounderEvent(
                    event_date=row['event_date'].date(),
                    event_type=row.get('event_type', 'MARKET_EVENT'),
                    event_description=row.get('event_description', 'Market event'),
                    impact_magnitude=row.get('impact_magnitude'),
                    affected_segments=row.get('affected_segments', []).split(',') if isinstance(row.get('affected_segments'), str) else [],
                ))
        return events


class BaselineAnalysisEngine:
    """Main engine for baseline utilization and behavior profiling"""
    
    def __init__(self, n_clusters: int = 5):
        """
        Initialize baseline analysis engine
        
        Args:
            n_clusters: Number of provider archetype clusters (default: 5)
        """
        self.time_series_model = BaselineTimeSeriesModel()
        self.benchmark_calculator = BaselineBenchmarkCalculator()
        self.provider_profiler = ProviderPracticePatternProfiler(n_clusters=int(n_clusters))  # Ensure it's an integer
        self.network_analyzer = ProviderNetworkAnalyzer()
        self.patient_stratifier = PatientSensitivityStratifier()
        self.confounder_calendar = BaselineConfounderCalendar()
    
    def run_baseline_analysis(
        self,
        tenant_id: UUID,
        claims_data_path: str,
        enrollment_data_path: Optional[str] = None,
        provider_data_path: Optional[str] = None,
        member_data_path: Optional[str] = None,
        network_data_path: Optional[str] = None,
        market_events_path: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> BaselineAnalysisResult:
        """Run complete baseline analysis"""
        try:
            claims_df = self._load_data(claims_data_path)
            enrollment_df = self._load_data(enrollment_data_path) if enrollment_data_path else None
            provider_df = self._load_data(provider_data_path) if provider_data_path else None
            member_df = self._load_data(member_data_path) if member_data_path else None
            network_df = self._load_data(network_data_path) if network_data_path else None
            market_events_df = self._load_data(market_events_path) if market_events_path else None
            
            # Determine date and value columns
            date_col = None
            for col in ['service_date_from', 'service_date', 'service_from_date', 'date_of_service', 'service_dt', 'service_date_to']:
                if col in claims_df.columns:
                    date_col = col
                    break
            
            if not date_col:
                # Try to find any date-like column
                for col in claims_df.columns:
                    if 'date' in col.lower() or 'dt' in col.lower():
                        date_col = col
                        break
            
            if not date_col:
                raise ValueError("No date column found in claims data. Expected columns: service_date, service_date_from, service_from_date")
            
            value_col = None
            for col in ['paid_amount', 'allowed_amount', 'total_charge', 'charge_amount', 'amount']:
                if col in claims_df.columns:
                    value_col = col
                    break
            
            if not value_col:
                raise ValueError("No amount column found in claims data. Expected columns: paid_amount, allowed_amount")
            
            # Set default dates if not provided
            if not start_date or not end_date:
                if date_col in claims_df.columns:
                    try:
                        dates = pd.to_datetime(claims_df[date_col], errors='coerce')
                        dates = dates.dropna()
                        if len(dates) > 0:
                            start_date = start_date or dates.min().date()
                            end_date = end_date or dates.max().date()
                        else:
                            start_date = start_date or date(2023, 1, 1)
                            end_date = end_date or date(2025, 12, 31)
                    except Exception as e:
                        logger.warning(f"Error parsing dates: {e}")
                        start_date = start_date or date(2023, 1, 1)
                        end_date = end_date or date(2025, 12, 31)
                else:
                    start_date = start_date or date(2023, 1, 1)
                    end_date = end_date or date(2025, 12, 31)
            time_series = self.time_series_model.fit_predict(
                claims_df,
                date_column=date_col,
                value_column=value_col,
                group_by=['lob', 'market'] if 'lob' in claims_df.columns and 'market' in claims_df.columns else None,
            )
            
            benchmarks = self.benchmark_calculator.calculate_benchmarks(
                claims_df,
                enrollment_df,
                group_by=['lob', 'market'] if 'lob' in claims_df.columns and 'market' in claims_df.columns else None,
            )
            
            provider_archetypes = self.provider_profiler.profile_providers(claims_df, provider_df)
            network_features = self.network_analyzer.analyze_network_features(claims_df, provider_df, network_df)
            patient_segments = self.patient_stratifier.stratify_patients(claims_df, enrollment_df, member_df)
            confounder_events = self.confounder_calendar.generate_calendar(start_date, end_date, market_events_df)
            
            result = BaselineAnalysisResult(
                analysis_id=str(uuid4()),
                tenant_id=str(tenant_id),
                generated_at=datetime.utcnow(),
                time_series=time_series,
                benchmarks=benchmarks,
                provider_archetypes=provider_archetypes,
                patient_segments=patient_segments,
                confounder_events=confounder_events,
                data_coverage={
                    'claims_records': len(claims_df),
                    'date_range': {'start': str(start_date), 'end': str(end_date)},
                },
                model_parameters={
                    'seasonal_period': self.time_series_model.seasonal_period,
                    'n_clusters': self.provider_profiler.n_clusters,
                },
            )
            return result
        except Exception as e:
            logger.error(f"Error in baseline analysis: {e}", exc_info=True)
            raise
    
    def _load_data(self, data_path: str) -> pd.DataFrame:
        """Load data from file"""
        try:
            path = Path(data_path)
            if not path.exists():
                raise FileNotFoundError(f"Data file not found: {data_path}")
            
            if path.suffix == '.parquet':
                return pd.read_parquet(path)
            elif path.suffix == '.csv':
                # Try to read with common encodings
                try:
                    return pd.read_csv(path, low_memory=False)
                except UnicodeDecodeError:
                    # Try with different encoding
                    return pd.read_csv(path, encoding='latin-1', low_memory=False)
            else:
                raise ValueError(f"Unsupported file format: {path.suffix}. Supported formats: .csv, .parquet")
        except Exception as e:
            logger.error(f"Error loading data from {data_path}: {e}", exc_info=True)
            raise
