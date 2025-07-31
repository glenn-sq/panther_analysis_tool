"""JSON output formatter for Panther Analysis Tool results."""

import json
from dataclasses import asdict, dataclass
from typing import Any, DefaultDict, Dict, List, Optional, Tuple

from panther_core.rule import Detection
from panther_core.testing import TestResult


@dataclass
class JsonTestResult:
    """JSON-serializable test result."""

    name: str
    passed: bool
    functions: Dict[str, Any]


@dataclass
class JsonDetectionResult:
    """JSON-serializable detection test results."""

    detection_id: str
    detection_type: Optional[str]
    test_results: List[JsonTestResult]
    failed_tests: List[str]


@dataclass
class JsonAnalysisOutput:
    """JSON-serializable analysis output."""

    summary: Dict[str, Any]
    detections: List[JsonDetectionResult]
    invalid_specs: List[Dict[str, Any]]
    skipped_tests: List[Dict[str, Any]]


@dataclass
class JsonValidationOutput:
    """JSON-serializable validation output."""

    success: bool
    message: str
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]


@dataclass
class JsonConnectionOutput:
    """JSON-serializable connection check output."""

    success: bool
    message: str
    api_host: str


@dataclass
class JsonBenchmarkOutput:  # pylint: disable=too-many-instance-attributes
    """JSON-serializable benchmark output."""

    rule_id: str
    log_type: str
    iterations: int
    completed_iterations: int
    read_time_nanos: List[int]
    processing_time_nanos: List[int]
    read_time_seconds: List[float]
    processing_time_seconds: List[float]
    avg_read_time_seconds: float
    avg_processing_time_seconds: float
    median_read_time_seconds: float
    median_processing_time_seconds: float
    success: bool
    error_message: Optional[str] = None


class JsonOutputFormatter:
    """Formats analysis results as JSON."""

    def __init__(self) -> None:
        self.detections: List[JsonDetectionResult] = []
        self.invalid_specs: List[Dict[str, Any]] = []
        self.skipped_tests: List[Dict[str, Any]] = []
        self.current_detection: Optional[JsonDetectionResult] = None

    def start_detection(self, detection_id: str, detection_type: Optional[str] = None) -> None:
        """Start formatting results for a new detection."""
        self.current_detection = JsonDetectionResult(
            detection_id=detection_id,
            detection_type=detection_type,
            test_results=[],
            failed_tests=[],
        )

    def add_test_result(
        self,
        detection: Optional[Detection],
        test_result: TestResult,
        failed_tests: DefaultDict[str, list],
    ) -> None:
        """Add a test result to the current detection."""
        if not self.current_detection:
            return

        # Filter and process functions to match text output format exactly
        functions = asdict(test_result.functions)
        filtered_functions = {}

        # Match the exact logic from text output: only include functions that have results
        # and remove "Function" suffix from names
        for function_name, function_result in functions.items():
            # Check if function_result exists and has actual output (not null)
            if function_result and function_result.get("output") is not None:
                # Remove "Function" suffix and handle special case for detection
                printable_name = function_name.replace("Function", "")
                if printable_name == "detection" and detection:
                    # Use the detection's matcher function name
                    printable_name = detection.matcher_function_name

                # Filter out null error fields and parse JSON strings
                cleaned_result = {}
                for key, value in function_result.items():
                    if key == "error" and value is None:
                        continue  # Skip null error fields

                    # If this is the output field and it looks like JSON, try to parse it
                    if key == "output" and isinstance(value, str) and value.strip().startswith("{"):
                        try:
                            cleaned_result[key] = json.loads(value)
                        except (json.JSONDecodeError, ValueError):
                            # If parsing fails, keep the original string
                            cleaned_result[key] = value
                    else:
                        cleaned_result[key] = value

                filtered_functions[printable_name] = cleaned_result

        # Convert test result to JSON-serializable format
        json_test_result = JsonTestResult(
            name=test_result.name,
            passed=test_result.passed,
            functions=filtered_functions,
        )

        self.current_detection.test_results.append(json_test_result)

        # Add failed test information if applicable
        if detection and detection.detection_id in failed_tests:
            self.current_detection.failed_tests.extend(failed_tests[detection.detection_id])

    def finish_detection(self) -> None:
        """Finish the current detection and add it to the results."""
        if self.current_detection:
            self.detections.append(self.current_detection)
            self.current_detection = None

    def add_invalid_spec(self, spec: Tuple[str, Any]) -> None:
        """Add an invalid specification to the results."""
        if isinstance(spec, tuple) and len(spec) == 2:
            filename, error = spec
            self.invalid_specs.append({"filename": filename, "error": str(error)})
        else:
            self.invalid_specs.append({"filename": "", "error": str(spec)})

    def add_skipped_test(self, filename: str, spec: Dict[str, Any]) -> None:
        """Add a skipped test to the results."""
        self.skipped_tests.append(
            {
                "filename": filename,
                "detection_id": spec.get("RuleID") or spec.get("PolicyID", ""),
                "reason": "disabled" if not spec.get("Enabled", False) else "no_matching_tests",
            }
        )

    def get_json_output(
        self,
        path: str,
        total_detections: int,
        failed_tests: DefaultDict[str, list],  # pylint: disable=unused-argument
        return_code: int,
    ) -> str:
        """Generate the final JSON output."""
        # Calculate summary statistics
        total_tests = sum(len(d.test_results) for d in self.detections)
        passed_tests = sum(1 for d in self.detections for t in d.test_results if t.passed)
        failed_test_count = total_tests - passed_tests

        summary = {
            "path": path,
            "return_code": return_code,
            "total_detections": total_detections,
            "tested_detections": len(self.detections),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_test_count,
            "invalid_specs": len(self.invalid_specs),
            "skipped_tests": len(self.skipped_tests),
            "detections_with_failures": len([d for d in self.detections if d.failed_tests]),
        }

        output = JsonAnalysisOutput(
            summary=summary,
            detections=self.detections,
            invalid_specs=self.invalid_specs,
            skipped_tests=self.skipped_tests,
        )

        return json.dumps(asdict(output), indent=2, default=str)

    def print_no_tests_message(self, detection_id: str) -> None:
        """Handle the case where no tests are configured for a detection."""
        if not self.current_detection:
            self.start_detection(detection_id)
        # Add a special marker for no tests
        if self.current_detection:
            self.current_detection.test_results.append(
                JsonTestResult(name="NO_TESTS_CONFIGURED", passed=False, functions={})
            )

    @staticmethod
    def format_validation_output(
        success: bool,
        message: str,
        errors: Optional[List[Dict[str, Any]]] = None,
        warnings: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Format validation results as JSON."""
        output = JsonValidationOutput(
            success=success,
            message=message,
            errors=errors or [],
            warnings=warnings or [],
        )
        return json.dumps(asdict(output), indent=2, default=str)

    @staticmethod
    def format_connection_output(success: bool, message: str, api_host: str) -> str:
        """Format connection check results as JSON."""
        output = JsonConnectionOutput(success=success, message=message, api_host=api_host)
        return json.dumps(asdict(output), indent=2, default=str)

    @staticmethod
    def format_benchmark_output(  # pylint: disable=too-many-arguments,too-many-locals
        rule_id: str,
        log_type: str,
        iterations: int,
        completed_iterations: int,
        read_times: List[int],
        processing_times: List[int],
        success: bool,
        error_message: Optional[str] = None,
    ) -> str:
        """Format benchmark results as JSON."""
        # Convert nanoseconds to seconds
        read_time_seconds = [t / 1_000_000_000 for t in read_times]
        processing_time_seconds = [t / 1_000_000_000 for t in processing_times]

        # Calculate statistics
        avg_read_time = sum(read_time_seconds) / len(read_time_seconds) if read_time_seconds else 0
        avg_processing_time = (
            sum(processing_time_seconds) / len(processing_time_seconds)
            if processing_time_seconds
            else 0
        )

        # Calculate median
        sorted_read_times = sorted(read_time_seconds)
        sorted_processing_times = sorted(processing_time_seconds)
        median_read_time = (
            sorted_read_times[len(sorted_read_times) // 2] if sorted_read_times else 0
        )
        median_processing_time = (
            sorted_processing_times[len(sorted_processing_times) // 2]
            if sorted_processing_times
            else 0
        )

        output = JsonBenchmarkOutput(
            rule_id=rule_id,
            log_type=log_type,
            iterations=iterations,
            completed_iterations=completed_iterations,
            read_time_nanos=read_times,
            processing_time_nanos=processing_times,
            read_time_seconds=read_time_seconds,
            processing_time_seconds=processing_time_seconds,
            avg_read_time_seconds=avg_read_time,
            avg_processing_time_seconds=avg_processing_time,
            median_read_time_seconds=median_read_time,
            median_processing_time_seconds=median_processing_time,
            success=success,
            error_message=error_message,
        )
        return json.dumps(asdict(output), indent=2, default=str)
