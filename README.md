# Panther Analysis Tool

[Panther Analysis Tool](https://github.com/panther-labs/panther_analysis_tool)
is a Python application for testing, packaging, and deploying Panther
Detections.

For further details, see [Quick Start](https://docs.panther.com/quick-start) and
[Panther Documentation](https://docs.panther.com/).

## Installation

### From PyPi

Use pip to install
[panther_analysis_tool package](https://pypi.org/project/panther-analysis-tool/)
from PyPi:

```shell
pip3 install panther_analysis_tool
```

Or without a virtual environment:

```shell
make deps
pip3 install -e .
```

### From source

```shell
make install
pipenv run -- pip3 install -e .
```

## Usage

### Help

Show available commands and their options:

```bash
$ panther_analysis_tool -h
usage: panther_analysis_tool [-h] [--version] [--debug] [--skip-version-check] {release,test,publish,upload,delete,update-custom-schemas,test-lookup-table,validate,zip,check-connection,benchmark,enrich-test-data} ...

Panther Analysis Tool: A command line tool for managing Panther policies and rules.

positional arguments:
  {release,test,publish,upload,delete,update-custom-schemas,test-lookup-table,validate,zip,check-connection,benchmark,enrich-test-data}
    release             Create release assets for repository containing panther detections. Generates a file called panther-analysis-all.zip and optionally generates panther-analysis-all.sig
    test                Validate analysis specifications and run policy and rule tests.
    publish             Publishes a new release, generates the release assets, and uploads them. Generates a file called panther-analysis-all.zip and optionally generates panther-analysis-all.sig
    upload              Upload specified policies and rules to a Panther deployment.
    delete              Delete policies, rules, or saved queries from a Panther deployment
    update-custom-schemas
                        Update or create custom schemas on a Panther deployment.
    test-lookup-table   Validate a Lookup Table spec file.
    validate            Validate your bulk uploads against your panther instance
    zip                 Create an archive of local policies and rules for uploading to Panther.
    check-connection    Check your Panther API connection
    benchmark           Performance test one rule against one of its log types. The rule must be the only item in the working directory or specified by --path, --ignore-files, and --filter. This feature is an extension
                        of Data Replay and is subject to the same limitations.
    enrich-test-data    Enrich test data with additional enrichments from the Panther API.

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --debug
  --skip-version-check
  --output-format {text,json}
                        Output format for results (default: text)
```

### Test

Run tests for a given path:

```bash
$ panther_analysis_tool test --path tests/fixtures/valid_policies/
[INFO]: Testing analysis packs in tests/fixtures/valid_policies/

AWS.IAM.MFAEnabled
    [PASS] Root MFA not enabled fails compliance
    [PASS] User MFA not enabled fails compliance
```

Run a specific unit test of a rule:

```bash
$ panther_analysis_tool test --filter RuleID=AWS.IAM.AccessKeyCompromised --test-names "An AWS Access Key was Uploaded to Github"
[INFO]: Testing analysis items in .

AWS.IAM.AccessKeyCompromised
        [PASS] An AWS Access Key was Uploaded to Github
```

Run specific unit tests of a rule:

```bash
$ panther_analysis_tool test --filter RuleID=AWS.CloudTrail.Stopped --test-names "CloudTrail Was Stopped" "Error Stopping CloudTrail"
[INFO]: Testing analysis items in .

        [PASS] CloudTrail Was Stopped
        ...
        [PASS] Error Stopping CloudTrail
                [PASS] [rule] false

### Output Formats

The Panther Analysis Tool supports two output formats: text (default) and JSON.

#### Text Output (Default)

Text output provides human-readable results with colored status indicators:

```bash
$ panther_analysis_tool test --path tests/fixtures/valid_policies/
[INFO]: Testing analysis packs in tests/fixtures/valid_policies/

AWS.IAM.MFAEnabled
    [PASS] Root MFA not enabled fails compliance
    [PASS] User MFA not enabled fails compliance
```

#### JSON Output

JSON output provides structured data suitable for programmatic processing and integration with CI/CD pipelines. The `--output-format json` option is supported by the following commands:

- `test` - Test results and validation output
- `validate` - Bulk upload validation results  
- `check-connection` - API connection status
- `benchmark` - Performance test results

```bash
$ panther_analysis_tool --output-format json test --path tests/fixtures/valid_policies/
```

Example JSON output structure for the `test` command:

```json
{
  "summary": {
    "path": "tests/fixtures/valid_policies/",
    "return_code": 0,
    "total_detections": 2,
    "tested_detections": 2,
    "total_tests": 4,
    "passed_tests": 4,
    "failed_tests": 0,
    "invalid_specs": 0,
    "skipped_tests": 0,
    "detections_with_failures": 0
  },
  "detections": [
    {
      "detection_id": "AWS.IAM.MFAEnabled",
      "detection_type": "RULE",
      "test_results": [
        {
          "name": "Root MFA not enabled fails compliance",
          "passed": true,
          "functions": {
            "rule": {
              "matched": true,
              "output": "true"
            },
            "title": {
              "output": "Root MFA not enabled"
            },
            "dedup": {
              "output": "defaultDedupString:AWS.IAM.MFAEnabled"
            },
            "alertContext": {
              "output": {
                "Arn": "arn:aws:iam::123456789012:root",
                "CreateDate": "2019-01-01T00:00:00Z"
              }
            }
          }
        }
      ],
      "failed_tests": []
    }
  ],
  "invalid_specs": [],
  "skipped_tests": []
}
```

Example JSON output for the `validate` command:

```bash
$ panther_analysis_tool --output-format json validate --path tests/fixtures/valid_policies/
```

```json
{
  "success": true,
  "message": "Validation success",
  "errors": [],
  "warnings": []
}
```

Example JSON output for the `check-connection` command:

```bash
$ panther_analysis_tool --output-format json check-connection
```

```json
{
  "success": true,
  "message": "Connection successful",
  "api_host": "https://api.panther.com"
}
```

Example JSON output for the `benchmark` command:

```bash
$ panther_analysis_tool --output-format json benchmark --filter RuleID=AWS.CloudTrail.MFAEnabled
```

```json
{
  "rule_id": "AWS.CloudTrail.MFAEnabled",
  "log_type": "AWS.CloudTrail",
  "iterations": 10,
  "completed_iterations": 10,
  "read_time_nanos": [1000000, 1200000, 1100000],
  "processing_time_nanos": [500000, 600000, 550000],
  "read_time_seconds": [0.001, 0.0012, 0.0011],
  "processing_time_seconds": [0.0005, 0.0006, 0.00055],
  "avg_read_time_seconds": 0.0011,
  "avg_processing_time_seconds": 0.00055,
  "median_read_time_seconds": 0.0011,
  "median_processing_time_seconds": 0.00055,
  "success": true
}
```

The JSON output includes:
- **summary**: Overall statistics about the test run (for `test` command)
- **detections**: Detailed test results for each detection (for `test` command)
- **invalid_specs**: Any specifications that failed validation (for `test` command)
- **skipped_tests**: Tests that were skipped (e.g., disabled detections) (for `test` command)
- **success**: Boolean indicating if the operation succeeded (for all commands)
- **message**: Human-readable status message (for all commands)
- **errors**: Array of error details (for `validate` command)
- **warnings**: Array of warning details (for `validate` command)
- **api_host**: Panther API host URL (for `check-connection` command)
- **performance metrics**: Detailed timing and statistics (for `benchmark` command)

### Upload

Create packages to upload through the Panther UI:

```bash
$ panther_analysis_tool zip --path tests/fixtures/valid_policies/ --out tmp
[INFO]: Testing analysis packs in tests/fixtures/valid_policies/

AWS.IAM.MFAEnabled
    [PASS] Root MFA not enabled fails compliance
    [PASS] User MFA not enabled fails compliance

[INFO]: Zipping analysis packs in tests/fixtures/valid_policies/ to tmp
[INFO]: <current working directory>/tmp/panther-analysis-2020-03-23T12-48-18.zip
```

Or upload packages directly into Panther:

```bash
$ panther_analysis_tool upload --path tests/fixtures/valid_policies/ --out tmp
[INFO]: Testing analysis packs in tests/fixtures/valid_policies/

AWS.IAM.MFAEnabled
    [PASS] Root MFA not enabled fails compliance
    [PASS] User MFA not enabled fails compliance

AWS.IAM.BetaTest
    [PASS] Root MFA not enabled fails compliance
    [PASS] User MFA not enabled fails compliance

AWS.CloudTrail.MFAEnabled
    [PASS] Root MFA not enabled fails compliance
    [PASS] User MFA not enabled fails compliance

[INFO]: Zipping analysis packs in tests/fixtures/valid_policies/ to tmp
[INFO]: Found credentials in environment variables.
[INFO]: Uploading pack to Panther
[INFO]: Upload success.
[INFO]: API Response:
{
  "modifiedPolicies": 0,
  "modifiedRules": 0,
  "newPolicies": 2,
  "newRules": 1,
  "totalPolicies": 2,
  "totalRules": 1
}
```

### Filtering

The `test`, `zip`, and `upload` commands all support filtering. Filtering works
by passing the `--filter` argument with a list of filters specified in the
format `KEY=VALUE1,VALUE2`. The keys can be any valid field in a policy or rule.
When using a filter, only anaylsis that matches each filter specified will be
considered. For example, the following command will test only items with the
AnalysisType as `policy` AND severity as `High`:

```bash
$ panther_analysis_tool test --path tests/fixtures/valid_policies --filter AnalysisType=policy Severity=High
[INFO]: Testing analysis packs in tests/fixtures/valid_policies

AWS.IAM.BetaTest
    [PASS] Root MFA not enabled fails compliance
    [PASS] User MFA not enabled fails compliance
```

Alternately, the following command will test items with the AnalysisType
`policy` OR `rule`, AND the severity `High`:

```bash
$ panther_analysis_tool test --path tests/fixtures/valid_policies --filter AnalysisType=policy,rule Severity=High
[INFO]: Testing analysis packs in tests/fixtures/valid_policies

AWS.IAM.BetaTest
    [PASS] Root MFA not enabled fails compliance
    [PASS] User MFA not enabled fails compliance

AWS.CloudTrail.MFAEnabled
    [PASS] Root MFA not enabled fails compliance
    [PASS] User MFA not enabled fails compliance
```

When writing policies or rules that refer to the global analysis types, include
them in the filter. An empty string as a filter value means the filter applies
only if the field exists. The following command returns an error: the policy
imports a global, but the global lacks a severity and thus is excluded by the
filter.

```bash
$ panther_analysis_tool test --path tests/fixtures/valid_policies --filter AnalysisType=policy,global Severity=Critical
[INFO]: Testing analysis packs in tests/fixtures/valid_policies

AWS.IAM.MFAEnabled
    [ERROR] Error loading module, skipping

Invalid: tests/fixtures/valid_policies/example_policy.yml
    No module named 'panther'

[ERROR]: [('tests/fixtures/valid_policies/example_policy.yml', ModuleNotFoundError("No module named 'panther'"))]
```

For this query to work, allow for the abscence of the severity field:

```bash
$ panther_analysis_tool test --path tests/fixtures/valid_policies --filter AnalysisType=policy,global Severity=Critical,""
[INFO]: Testing analysis packs in tests/fixtures/valid_policies

AWS.IAM.MFAEnabled
    [PASS] Root MFA not enabled fails compliance
    [PASS] User MFA not enabled fails compliance
```

Filters work for the `zip` and `upload` commands in the exact same way they work
for the `test` command.

In addition to filtering, setting a minimum number of unit tests is possible
with the --minimum-tests flag. Detections lacking the minimum number of tests
are considered failing. If `--minimum-tests` is set to 2 or greater, the
requirement becomes that at least one test must return `True` and another must
return `False`.

```
$ panther_analysis_tool test --path tests/fixtures/valid_policies --minimum-tests 2
% panther_analysis_tool test --path okta_rules --minimum-tests 2
[INFO]: Testing analysis packs in okta_rules

Okta.AdminRoleAssigned
    [PASS] Admin Access Assigned

Okta.BruteForceLogins
    [PASS] Failed login

Okta.GeographicallyImprobableAccess
    [PASS] Non Login
    [PASS] Failed Login

--------------------------
Panther CLI Test Summary
    Path: okta_rules
    Passed: 0
    Failed: 3
    Invalid: 0

--------------------------
Failed Tests Summary
    Okta.AdminRoleAssigned
         ['Insufficient test coverage, 2 tests required but only 1 found.', 'Insufficient test coverage: expected at least one passing and one failing test.']

    Okta.BruteForceLogins
        ['Insufficient test coverage, 2 tests required but only 1 found.', 'Insufficient test coverage: expected at least one passing and one failing test]

    Okta.GeographicallyImprobableAccess
        ['Insufficient test coverage: expected at least one passing and one failing test.']
```

In this case, even though the rules passed all their tests, they are still
considered failing because they do not have the correct test coverage.

### Delete Rules, Policies, or Saved Queries

```bash
$ panther_analysis_tool delete

usage: panther_analysis_tool delete [-h] [--no-confirm] [--athena-datalake] [--api-token API_TOKEN] [--api-host API_HOST] [--aws-profile AWS_PROFILE] [--analysis-id ANALYSIS_ID [ANALYSIS_ID ...]]
                                    [--query-id QUERY_ID [QUERY_ID ...]]

Delete policies, rules, or saved queries from a Panther deployment

optional arguments:
  -h, --help            show this help message and exit
  --no-confirm          Skip manual confirmation of deletion (default: False)
  --athena-datalake     Instance DataLake is backed by Athena (default: False)
  --api-token API_TOKEN
                        The Panther API token to use. See: https://docs.panther.com/api-beta (default: None)
  --api-host API_HOST   The Panther API host to use. See: https://docs.panther.com/api-beta (default: None)
  --aws-profile AWS_PROFILE
                        The AWS profile to use when updating the AWS Panther deployment. (default: None)
  --analysis-id ANALYSIS_ID [ANALYSIS_ID ...]
                        Space separated list of Detection IDs (default: [])
  --query-id QUERY_ID [QUERY_ID ...]
                        Space separated list of Saved Queries (default: [])
```

Pass a space-separated list of Analysis IDs (RuleID or PolicyID) or QueryIDs.
Use the --no-confirm flag to bypass confirmation prompts. Rules and their
associated saved queries will be matched and deleted. The default configuration
targets a Snowflake datalake; for an Athena datalake, use the --athena-datalake
flag.

## Configuration File

Panther Analysis Tool will also read options from a configuration file
`.panther_settings.yml` in the current working directory. An example
configuration file is included in this repo,
[example_panther_config.yml](example_panther_config.yml), that contains example
syntax for supported options.

Options in the configuration file take precedence over command-line options. For
instance, if minimum_tests: 2 is set in the configuration file and
--minimum-tests 1 is specified on the command line, the minimum number of tests
will be 2.

## Contributing

All contributions are welcome. Prior to submitting pull requests, consult the
[contributing guidelines](https://github.com/panther-labs/panther-analysis/blob/master/CONTRIBUTING.md).
For steps to open a pull request from a fork, refer to
[GitHub's guide](https://docs.github.com/en/github/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request).

### Local Development

To develop with the panther_analysis_tool locally, prepare two repositories:
this one and another containing the panther analysis content for PAT testing.

From your [panther_analysis](https://github.com/panther-labs/panther-analysis)
content repository, install as editable (and test, for example):

```bash
pipenv install --editable ../relative/path/to/panther_analysis_tool
pipenv run panther_analysis_tool test
```

## License

This repository is licensed under the AGPL-3.0
[license](https://github.com/panther-labs/panther-analysis/blob/master/LICENSE).
