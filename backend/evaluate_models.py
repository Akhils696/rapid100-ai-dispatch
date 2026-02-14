"""
Model evaluation script for RAPID-100 emergency call triage system
This script evaluates the accuracy, precision, recall, and F1-score of our AI models
"""
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.preprocessing import LabelEncoder
import json
import logging
from datetime import datetime
import time

from .services.classification_service import ClassificationService
from .services.severity_service import SeverityService
from .services.location_service import LocationService
from .models.call_data import EmergencyType, SeverityLevel

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_sample_data(file_path="data/sample_calls.csv"):
    """
    Load sample emergency call data for evaluation
    """
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} sample calls from {file_path}")
        return df
    except FileNotFoundError:
        logger.warning(f"Sample data file {file_path} not found. Using synthetic data.")
        # Create synthetic data for testing
        synthetic_data = {
            "transcript": [
                "Help! My wife is unconscious and not breathing. She collapsed suddenly.",
                "There's a fire at my house! Smoke is everywhere, flames coming from the kitchen.",
                "Someone is breaking into my house! I hear glass breaking and footsteps.",
                "Car accident on Highway 101 near Exit 15. Multiple cars involved, people injured.",
                "Tornado warning! Severe weather approaching downtown. Taking shelter in basement.",
                "My child has a high fever and is having trouble breathing.",
                "Small fire in my garage, mostly contained. Smoke alarm triggered.",
                "Neighbor's dog is loose and acting aggressively. Bit someone earlier.",
                "Fender-bender on Main Street. Both drivers are ok, just car damage.",
                "Power outage affecting several blocks. Trees down on power lines."
            ],
            "emergency_type": [
                "MEDICAL", "FIRE", "CRIME", "ACCIDENT", "DISASTER",
                "MEDICAL", "FIRE", "CRIME", "ACCIDENT", "DISASTER"
            ],
            "severity": [
                "CRITICAL", "HIGH", "HIGH", "HIGH", "MEDIUM",
                "MEDIUM", "LOW", "LOW", "LOW", "MEDIUM"
            ]
        }
        df = pd.DataFrame(synthetic_data)
        logger.info(f"Created {len(df)} synthetic sample calls")
        return df


def evaluate_classification_model():
    """
    Evaluate the emergency classification model
    """
    logger.info("Starting emergency classification model evaluation...")
    
    df = load_sample_data()
    classification_service = ClassificationService()
    
    # Prepare data
    texts = df['transcript'].tolist()
    true_labels = df['emergency_type'].tolist()
    
    # Predict using our model
    predictions = []
    processing_times = []
    
    for text in texts:
        start_time = time.time()
        pred_enum = classification_service.classify_emergency(text)
        end_time = time.time()
        
        predictions.append(pred_enum.value)
        processing_times.append(end_time - start_time)
    
    # Calculate metrics
    accuracy = accuracy_score(true_labels, predictions)
    
    # For multi-class, we need to use average parameter
    try:
        precision = precision_score(true_labels, predictions, average='weighted', labels=list(EmergencyType.__members__.keys()))
        recall = recall_score(true_labels, predictions, average='weighted', labels=list(EmergencyType.__members__.keys()))
        f1 = f1_score(true_labels, predictions, average='weighted', labels=list(EmergencyType.__members__.keys()))
    except ValueError:
        # Handle case where some classes might be missing in either true or predicted
        precision = precision_score(true_labels, predictions, average='weighted', labels=np.unique(list(true_labels) + predictions))
        recall = recall_score(true_labels, predictions, average='weighted', labels=np.unique(list(true_labels) + predictions))
        f1 = f1_score(true_labels, predictions, average='weighted', labels=np.unique(list(true_labels) + predictions))
    
    # Confusion matrix
    cm = confusion_matrix(true_labels, predictions, labels=list(EmergencyType.__members__.keys()))
    
    avg_processing_time = np.mean(processing_times)
    
    logger.info("Emergency Classification Model Results:")
    logger.info(f"Accuracy: {accuracy:.3f}")
    logger.info(f"Precision: {precision:.3f}")
    logger.info(f"Recall: {recall:.3f}")
    logger.info(f"F1-Score: {f1:.3f}")
    logger.info(f"Avg Processing Time: {avg_processing_time:.4f}s")
    
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "confusion_matrix": cm.tolist(),
        "avg_processing_time": avg_processing_time,
        "predictions": predictions,
        "true_labels": true_labels
    }


def evaluate_severity_model():
    """
    Evaluate the severity scoring model
    """
    logger.info("Starting severity scoring model evaluation...")
    
    df = load_sample_data()
    severity_service = SeverityService()
    
    # Prepare data
    texts = df['transcript'].tolist()
    true_labels = df['severity'].tolist()
    
    # Predict using our model
    predictions = []
    processing_times = []
    
    for text in texts:
        start_time = time.time()
        pred_enum = severity_service.calculate_severity(text)
        end_time = time.time()
        
        predictions.append(pred_enum.value)
        processing_times.append(end_time - start_time)
    
    # Calculate metrics
    accuracy = accuracy_score(true_labels, predictions)
    
    try:
        precision = precision_score(true_labels, predictions, average='weighted', labels=list(SeverityLevel.__members__.keys()))
        recall = recall_score(true_labels, predictions, average='weighted', labels=list(SeverityLevel.__members__.keys()))
        f1 = f1_score(true_labels, predictions, average='weighted', labels=list(SeverityLevel.__members__.keys()))
    except ValueError:
        # Handle case where some classes might be missing
        precision = precision_score(true_labels, predictions, average='weighted', labels=np.unique(list(true_labels) + predictions))
        recall = recall_score(true_labels, predictions, average='weighted', labels=np.unique(list(true_labels) + predictions))
        f1 = f1_score(true_labels, predictions, average='weighted', labels=np.unique(list(true_labels) + predictions))
    
    # Confusion matrix
    cm = confusion_matrix(true_labels, predictions, labels=list(SeverityLevel.__members__.keys()))
    
    avg_processing_time = np.mean(processing_times)
    
    logger.info("Severity Scoring Model Results:")
    logger.info(f"Accuracy: {accuracy:.3f}")
    logger.info(f"Precision: {precision:.3f}")
    logger.info(f"Recall: {recall:.3f}")
    logger.info(f"F1-Score: {f1:.3f}")
    logger.info(f"Avg Processing Time: {avg_processing_time:.4f}s")
    
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "confusion_matrix": cm.tolist(),
        "avg_processing_time": avg_processing_time,
        "predictions": predictions,
        "true_labels": true_labels
    }


def evaluate_end_to_end_pipeline():
    """
    Evaluate the complete end-to-end pipeline
    """
    logger.info("Starting end-to-end pipeline evaluation...")
    
    df = load_sample_data()
    
    # Initialize all services
    classification_service = ClassificationService()
    severity_service = SeverityService()
    location_service = LocationService()
    
    total_processing_times = []
    
    for idx, row in df.iterrows():
        start_time = time.time()
        
        # Run through entire pipeline
        text = row['transcript']
        
        # Classification
        emergency_type = classification_service.classify_emergency(text)
        
        # Severity
        severity = severity_service.calculate_severity(text)
        
        # Location
        location = location_service.extract_location(text)
        
        end_time = time.time()
        total_processing_times.append(end_time - start_time)
    
    avg_total_time = np.mean(total_processing_times)
    std_total_time = np.std(total_processing_times)
    
    logger.info("End-to-End Pipeline Results:")
    logger.info(f"Avg Total Processing Time: {avg_total_time:.4f}s")
    logger.info(f"Std Dev Processing Time: {std_total_time:.4f}s")
    logger.info(f"Total Calls Processed: {len(df)}")
    
    # Check if we meet the 2-3 second requirement
    meets_requirement = avg_total_time <= 3.0
    logger.info(f"Meets 2-3s requirement: {'YES' if meets_requirement else 'NO'}")
    
    return {
        "avg_total_processing_time": avg_total_time,
        "std_total_processing_time": std_total_time,
        "total_calls_processed": len(df),
        "meets_performance_requirement": meets_requirement
    }


def main():
    """
    Main evaluation function
    """
    logger.info("Starting RAPID-100 Model Evaluation")
    
    # Create results dictionary
    results = {
        "evaluation_timestamp": datetime.now().isoformat(),
        "classification_results": None,
        "severity_results": None,
        "pipeline_results": None
    }
    
    try:
        # Evaluate classification model
        results["classification_results"] = evaluate_classification_model()
    except Exception as e:
        logger.error(f"Error evaluating classification model: {e}")
        results["classification_results"] = {"error": str(e)}
    
    try:
        # Evaluate severity model
        results["severity_results"] = evaluate_severity_model()
    except Exception as e:
        logger.error(f"Error evaluating severity model: {e}")
        results["severity_results"] = {"error": str(e)}
    
    try:
        # Evaluate end-to-end pipeline
        results["pipeline_results"] = evaluate_end_to_end_pipeline()
    except Exception as e:
        logger.error(f"Error evaluating pipeline: {e}")
        results["pipeline_results"] = {"error": str(e)}
    
    # Save results to file
    output_file = f"evaluation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Evaluation results saved to {output_file}")
    
    # Print summary
    print("\n" + "="*60)
    print("RAPID-100 MODEL EVALUATION SUMMARY")
    print("="*60)
    
    if results["classification_results"] and "error" not in results["classification_results"]:
        cls_res = results["classification_results"]
        print(f"Classification Model:")
        print(f"  Accuracy:  {cls_res['accuracy']:.3f}")
        print(f"  Precision: {cls_res['precision']:.3f}")
        print(f"  Recall:    {cls_res['recall']:.3f}")
        print(f"  F1-Score:  {cls_res['f1_score']:.3f}")
        print(f"  Avg Time:  {cls_res['avg_processing_time']:.4f}s")
    
    if results["severity_results"] and "error" not in results["severity_results"]:
        sev_res = results["severity_results"]
        print(f"\nSeverity Model:")
        print(f"  Accuracy:  {sev_res['accuracy']:.3f}")
        print(f"  Precision: {sev_res['precision']:.3f}")
        print(f"  Recall:    {sev_res['recall']:.3f}")
        print(f"  F1-Score:  {sev_res['f1_score']:.3f}")
        print(f"  Avg Time:  {sev_res['avg_processing_time']:.4f}s")
    
    if results["pipeline_results"] and "error" not in results["pipeline_results"]:
        pipe_res = results["pipeline_results"]
        print(f"\nPipeline Performance:")
        print(f"  Avg Time:  {pipe_res['avg_total_processing_time']:.4f}s")
        print(f"  Std Dev:   {pipe_res['std_total_processing_time']:.4f}s")
        print(f"  Requirement Met: {'YES' if pipe_res['meets_performance_requirement'] else 'NO'}")
    
    print("="*60)


if __name__ == "__main__":
    main()