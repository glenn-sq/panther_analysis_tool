import argparse
import logging
from typing import Tuple

from panther_analysis_tool.backend.client import Client as BackendClient
from panther_analysis_tool.json_formatter import JsonOutputFormatter


def run(backend: BackendClient, args: argparse.Namespace) -> Tuple[int, str]:
    logging.info("checking connection to %s...", args.api_host)
    result = backend.check()

    if not result.success:
        logging.info("connection failed")
        if hasattr(args, "output_format") and args.output_format == "json":
            return 1, JsonOutputFormatter.format_connection_output(
                success=False, message=result.message, api_host=args.api_host
            )
        return 1, result.message

    logging.info("connection successful: %s", result.message)
    if hasattr(args, "output_format") and args.output_format == "json":
        return 0, JsonOutputFormatter.format_connection_output(
            success=True, message=result.message, api_host=args.api_host
        )
    return 0, ""
