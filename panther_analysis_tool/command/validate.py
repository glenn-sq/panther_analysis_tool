import argparse
import io
import logging
import zipfile
from typing import Tuple

from panther_analysis_tool import cli_output
from panther_analysis_tool.backend.client import (
    BulkUploadParams,
    BulkUploadValidateStatusResponse,
)
from panther_analysis_tool.backend.client import Client as BackendClient
from panther_analysis_tool.backend.client import UnsupportedEndpointError
from panther_analysis_tool.json_formatter import JsonOutputFormatter
from panther_analysis_tool.zip_chunker import ZipArgs, analysis_chunks


def run(  # pylint: disable=too-many-return-statements
    backend: BackendClient, args: argparse.Namespace
) -> Tuple[int, str]:
    if backend is None or not backend.supports_bulk_validate():
        return 1, "Invalid backend. `validate` is only supported via API token"

    typed_args = ZipArgs.from_args(args)
    chunks = analysis_chunks(typed_args)
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_out:
        for name in chunks[0].files:
            zip_out.write(name)

    buffer.seek(0, 0)
    params = BulkUploadParams(zip_bytes=buffer.read())

    try:
        result = backend.bulk_validate(params)
        if result.is_valid():
            if hasattr(args, "output_format") and args.output_format == "json":
                return 0, JsonOutputFormatter.format_validation_output(
                    success=True, message="Validation success"
                )
            return 0, f"{cli_output.success('Validation success')}"

        # Handle validation failures
        if hasattr(args, "output_format") and args.output_format == "json":
            errors: list[dict[str, str | None]] = []
            if result.has_error():
                errors.append({"error": result.get_error()})
            for issue in result.get_issues():
                error_info: dict[str, str | None] = {}
                if issue.path:
                    error_info["path"] = issue.path
                if issue.error_message:
                    error_info["message"] = issue.error_message
                if error_info:
                    errors.append(error_info)

            return 1, JsonOutputFormatter.format_validation_output(
                success=False, message="Validation failed", errors=errors
            )

        return 1, cli_output.multipart_error_msg(result, "Validation failed")
    except UnsupportedEndpointError as err:
        logging.debug(err)
        if hasattr(args, "output_format") and args.output_format == "json":
            return 1, JsonOutputFormatter.format_validation_output(
                success=False,
                message="Your Panther instance does not support this feature",
                errors=[{"error": str(err)}],
            )
        return 1, cli_output.warning("Your Panther instance does not support this feature")

    except BaseException as err:  # pylint: disable=broad-except
        if hasattr(args, "output_format") and args.output_format == "json":
            return 1, JsonOutputFormatter.format_validation_output(
                success=False, message="Validation failed", errors=[{"error": str(err)}]
            )
        return 1, cli_output.multipart_error_msg(
            BulkUploadValidateStatusResponse.from_json({"error": str(err)}), "Validation failed"
        )
