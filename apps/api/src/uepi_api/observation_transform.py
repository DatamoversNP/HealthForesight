"""Transform observation data to match frontend expectations"""
from typing import Dict, Any, Optional


def transform_observation_for_frontend(observation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform observation data to match frontend field name expectations.
    Maps database field names to frontend-expected field names and computes missing fields.
    """
    if not observation:
        return observation
    
    # Transform comparisons
    comparisons = observation.get('comparisons', {})
    if comparisons:
        # Transform vs_baseline
        vs_baseline = comparisons.get('vs_baseline', {})
        if vs_baseline:
            # Map cost_per_member to cost_pmpm
            if 'baseline_cost_per_member' in vs_baseline and 'baseline_cost_pmpm' not in vs_baseline:
                vs_baseline['baseline_cost_pmpm'] = vs_baseline['baseline_cost_per_member']
            
            # Add observed_cost_pmpm from metrics if available
            metrics = observation.get('metrics', {})
            if 'cost_per_member' in metrics and 'observed_cost_pmpm' not in vs_baseline:
                vs_baseline['observed_cost_pmpm'] = metrics['cost_per_member']
            
            # Compute cost_change / cost_change_pmpm if we have both values
            if 'baseline_cost_pmpm' in vs_baseline and 'observed_cost_pmpm' in vs_baseline:
                baseline_cost = vs_baseline.get('baseline_cost_pmpm', 0) or 0
                observed_cost = vs_baseline.get('observed_cost_pmpm', 0) or 0
                cost_change = observed_cost - baseline_cost
                vs_baseline['cost_change'] = cost_change
                vs_baseline['cost_change_pmpm'] = cost_change  # Same units (PMPM)
                if baseline_cost > 0:
                    cost_change_pct = (cost_change / baseline_cost) * 100
                    vs_baseline['cost_change_pct'] = cost_change_pct
            
            # Ensure observed_utilization_per_1k is present
            if 'observed_utilization_per_1k' not in vs_baseline and 'utilization_per_1k' in metrics:
                vs_baseline['observed_utilization_per_1k'] = metrics['utilization_per_1k']
            
            # Ensure baseline_utilization is present (same as baseline_utilization_per_1k)
            if 'baseline_utilization' not in vs_baseline and 'baseline_utilization_per_1k' in vs_baseline:
                vs_baseline['baseline_utilization'] = vs_baseline['baseline_utilization_per_1k']
            
            # Ensure observed_utilization is present
            if 'observed_utilization' not in vs_baseline and 'observed_utilization_per_1k' in vs_baseline:
                vs_baseline['observed_utilization'] = vs_baseline['observed_utilization_per_1k']
            
            # Compute utilization_change if not present
            if 'utilization_change' not in vs_baseline:
                if 'baseline_utilization_per_1k' in vs_baseline and 'observed_utilization_per_1k' in vs_baseline:
                    baseline_util = vs_baseline.get('baseline_utilization_per_1k', 0) or 0
                    observed_util = vs_baseline.get('observed_utilization_per_1k', 0) or 0
                    vs_baseline['utilization_change'] = observed_util - baseline_util
                    if baseline_util > 0:
                        vs_baseline['utilization_change_pct'] = ((observed_util - baseline_util) / baseline_util) * 100
            
            # Ensure change_from_baseline is present (same as utilization_change)
            if 'change_from_baseline' not in vs_baseline and 'utilization_change' in vs_baseline:
                vs_baseline['change_from_baseline'] = vs_baseline['utilization_change']
        
        # Transform vs_predicted
        vs_predicted = comparisons.get('vs_predicted', {})
        if vs_predicted:
            # Map cost_per_member to cost_pmpm
            if 'predicted_cost_per_member' in vs_predicted and 'predicted_cost_pmpm' not in vs_predicted:
                vs_predicted['predicted_cost_pmpm'] = vs_predicted['predicted_cost_per_member']
            
            # Add observed_cost_pmpm from metrics if available
            metrics = observation.get('metrics', {})
            if 'cost_per_member' in metrics and 'observed_cost_pmpm' not in vs_predicted:
                vs_predicted['observed_cost_pmpm'] = metrics['cost_per_member']
            
            # Ensure observed_utilization_per_1k is present
            if 'observed_utilization_per_1k' not in vs_predicted and 'utilization_per_1k' in metrics:
                vs_predicted['observed_utilization_per_1k'] = metrics['utilization_per_1k']
            
            # Ensure predicted_utilization is present (same as predicted_utilization_per_1k)
            if 'predicted_utilization' not in vs_predicted and 'predicted_utilization_per_1k' in vs_predicted:
                vs_predicted['predicted_utilization'] = vs_predicted['predicted_utilization_per_1k']
            
            # Ensure observed_utilization is present
            if 'observed_utilization' not in vs_predicted and 'observed_utilization_per_1k' in vs_predicted:
                vs_predicted['observed_utilization'] = vs_predicted['observed_utilization_per_1k']
            
            # Compute prediction error if we have both values
            if 'predicted_utilization_per_1k' in vs_predicted and 'observed_utilization_per_1k' in vs_predicted:
                predicted_util = vs_predicted.get('predicted_utilization_per_1k', 0) or 0
                observed_util = vs_predicted.get('observed_utilization_per_1k', 0) or 0
                if predicted_util > 0:
                    prediction_error = abs(observed_util - predicted_util)
                    prediction_error_pct = (prediction_error / predicted_util) * 100
                    vs_predicted['prediction_error'] = prediction_error
                    vs_predicted['prediction_error_pct'] = prediction_error_pct
            
            # Compute predicted change if we have both values
            if 'predicted_cost_pmpm' in vs_predicted and 'observed_cost_pmpm' in vs_predicted:
                predicted_cost = vs_predicted.get('predicted_cost_pmpm', 0) or 0
                observed_cost = vs_predicted.get('observed_cost_pmpm', 0) or 0
                predicted_change = observed_cost - predicted_cost
                vs_predicted['predicted_change_pmpm'] = predicted_change
                if predicted_cost > 0:
                    vs_predicted['predicted_change_pct'] = (predicted_change / predicted_cost) * 100
            
            # Compute predicted utilization change
            if 'predicted_utilization_per_1k' in vs_predicted and 'observed_utilization_per_1k' in vs_predicted:
                predicted_util = vs_predicted.get('predicted_utilization_per_1k', 0) or 0
                observed_util = vs_predicted.get('observed_utilization_per_1k', 0) or 0
                predicted_util_change = observed_util - predicted_util
                vs_predicted['predicted_utilization_change'] = predicted_util_change
                if predicted_util > 0:
                    vs_predicted['predicted_utilization_change_pct'] = (predicted_util_change / predicted_util) * 100
            
            # Add utilization prediction error fields (if not already present)
            if 'prediction_error' not in vs_predicted and 'predicted_utilization_per_1k' in vs_predicted and 'observed_utilization_per_1k' in vs_predicted:
                predicted_util = vs_predicted.get('predicted_utilization_per_1k', 0) or 0
                observed_util = vs_predicted.get('observed_utilization_per_1k', 0) or 0
                if predicted_util > 0:
                    util_error = abs(observed_util - predicted_util)
                    util_error_pct = (util_error / predicted_util) * 100
                    vs_predicted['utilization_prediction_error'] = util_error
                    vs_predicted['utilization_prediction_error_pct'] = util_error_pct
            
            # Add cost prediction error fields (if not already present)
            if 'cost_prediction_error' not in vs_predicted and 'predicted_cost_pmpm' in vs_predicted and 'observed_cost_pmpm' in vs_predicted:
                predicted_cost = vs_predicted.get('predicted_cost_pmpm', 0) or 0
                observed_cost = vs_predicted.get('observed_cost_pmpm', 0) or 0
                if predicted_cost > 0:
                    cost_error = abs(observed_cost - predicted_cost)
                    cost_error_pct = (cost_error / predicted_cost) * 100
                    vs_predicted['cost_prediction_error'] = cost_error
                    vs_predicted['cost_prediction_error_pct'] = cost_error_pct
    
    # Transform metrics to ensure cost_pmpm is present
    metrics = observation.get('metrics', {})
    if metrics:
        if 'cost_per_member' in metrics and 'cost_pmpm' not in metrics:
            metrics['cost_pmpm'] = metrics['cost_per_member']
    
    return observation
