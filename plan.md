# API Key Detection Feature Implementation Plan

## 1. Create Security Module (`src/gac/security.py`)

- [x] Create file structure and imports
- [x] Define `DetectedSecret` dataclass
  - [x] Add `file_path` field
  - [x] Add `line_number` field
  - [x] Add `secret_type` field
  - [x] Add `matched_text` field
  - [x] Add optional `context` field
- [x] Create `SecretPatterns` class
  - [x] Add AWS Access Key pattern
  - [x] Add AWS Secret Access Key pattern
  - [x] Add AWS Session Token pattern
  - [x] Add Generic API Key pattern
  - [x] Add GitHub Token pattern
  - [x] Add OpenAI API Key pattern
  - [x] Add Anthropic API Key pattern
  - [x] Add Stripe Key pattern
  - [x] Add Private Key (PEM) pattern
  - [x] Add Bearer Token pattern
  - [x] Add JWT Token pattern
  - [x] Add Database URL pattern
  - [x] Add SSH Private Key pattern
  - [x] Add Slack Token pattern
  - [x] Add Google API Key pattern
  - [x] Add Twilio API Key pattern
  - [x] Add Password field pattern
  - [x] Add excluded patterns (false positives)
  - [x] Implement `get_all_patterns()` classmethod
- [x] Implement `is_false_positive()` function
  - [x] Check against excluded patterns
  - [x] Check for all-same characters
- [x] Implement `extract_file_path_from_diff_section()` function
- [x] Implement `extract_line_number_from_hunk()` function
- [x] Implement `scan_diff_section()` function
  - [x] Extract file path
  - [x] Parse diff lines
  - [x] Track hunk headers
  - [x] Scan only added lines ('+' prefix)
  - [x] Match against all patterns
  - [x] Filter false positives
  - [x] Truncate displayed secrets
  - [x] Create DetectedSecret objects
- [x] Implement `scan_staged_diff()` function
  - [x] Split diff into sections
  - [x] Scan each section
  - [x] Aggregate results
- [x] Implement `get_affected_files()` function

## 2. Add Security Error Type (`src/gac/errors.py`)

- [x] Add `SecurityError` class
  - [x] Inherit from `GACError`
  - [x] Set appropriate exit code (6)
  - [x] Add docstring
  - [x] Add to error handling functions
  - [x] Add to remediation steps mapping

## 3. Add Configuration Support

### 3.1 Update `src/gac/constants.py`

- [x] Add to `EnvDefaults` class
  - [x] Add `SKIP_SECRET_SCAN: bool = False` constant

### 3.2 Update `src/gac/config.py`

- [x] Update `load_config()` function
  - [x] Add `skip_secret_scan` to config dict
  - [x] Load from `GAC_SKIP_SECRET_SCAN` env var
  - [x] Use `EnvDefaults.SKIP_SECRET_SCAN` as default
  - [x] Convert to boolean properly

## 4. Add CLI Flag (`src/gac/cli.py`)

- [x] Add `--skip-secret-scan` option
  - [x] Add to CLI decorator
  - [x] Set as flag (is_flag=True)
  - [x] Add help text
  - [x] Place in "Advanced options" section
- [x] Add parameter to `cli()` function signature
  - [x] Add `skip_secret_scan: bool = False` parameter
- [x] Pass to context object
  - [x] Add to `ctx.obj` dict for subcommands
- [x] Pass parameter to `main()` function
  - [x] Combine flag and config values

## 5. Integrate into Main Workflow (`src/gac/main.py`)

- [x] Update `main()` function signature
  - [x] Add `skip_secret_scan: bool = False` parameter
- [x] Add security scan logic
  - [x] Import security module functions
  - [x] Insert after getting diff (line ~91)
  - [x] Insert before preprocessing diff (line ~95)
  - [x] Check if scan should be skipped (flag or config)
  - [x] Run `scan_staged_diff(diff)` on staged diff
  - [x] Handle if secrets detected
- [x] Implement interactive prompt when secrets found
  - [x] Display warning header with Rich
  - [x] List each detected secret with formatting
    - [x] Show file path and line number
    - [x] Show secret type
    - [x] Show truncated matched text
  - [x] Show options menu
    - [x] [A] Abort commit (default)
    - [x] [C] Continue anyway (not recommended)
    - [x] [R] Remove affected file(s) and continue
  - [x] Get user input
  - [x] Handle user choice
    - [x] Abort: Print message and `sys.exit(0)`
    - [x] Continue: Log warning and proceed
    - [x] Remove files: Call `git reset HEAD <files>`, then proceed
- [x] Update CLI invocation in `cli.py`
  - [x] Pass `skip_secret_scan` parameter to `main()`

## 6. Create Tests (`tests/test_security.py`)

### 6.1 Test Secret Pattern Detection

- [x] Test AWS Access Key detection
  - [x] Test valid AWS key format
  - [x] Test invalid AWS key format
- [x] Test AWS Secret Access Key detection
- [x] Test GitHub Token detection
  - [x] Test ghp\_ tokens
  - [x] Test gho\_ tokens
  - [x] Test other GitHub token types
- [x] Test OpenAI API Key detection
- [x] Test Anthropic API Key detection
- [x] Test Stripe Key detection
- [x] Test Private Key detection
- [x] Test Bearer Token detection
- [x] Test JWT Token detection
- [x] Test Database URL detection
- [x] Test SSH Private Key detection
- [x] Test Slack Token detection
- [x] Test Google API Key detection
- [x] Test Twilio API Key detection
- [x] Test Password detection

### 6.2 Test False Positive Filtering

- [x] Test exclusion of "example" keys
- [x] Test exclusion of "placeholder" keys
- [x] Test exclusion of "xxx" patterns
- [x] Test exclusion of all-same-character strings
- [x] Test exclusion of common test passwords

### 6.3 Test Diff Scanning Functions

- [x] Test `extract_file_path_from_diff_section()`
  - [x] Test valid diff section
  - [x] Test invalid diff section
- [x] Test `extract_line_number_from_hunk()`
  - [x] Test valid hunk header
  - [x] Test invalid hunk header
- [x] Test `scan_diff_section()`
  - [x] Test section with secrets
  - [x] Test section without secrets
  - [x] Test section with multiple secrets
  - [x] Test correct line number tracking
- [x] Test `scan_staged_diff()`
  - [x] Test empty diff
  - [x] Test diff with one file
  - [x] Test diff with multiple files
  - [x] Test diff with mixed (secrets and clean files)

### 6.4 Test Helper Functions

- [x] Test `get_affected_files()`
  - [x] Test with no secrets
  - [x] Test with secrets in one file
  - [x] Test with secrets in multiple files
  - [x] Test deduplication
  - [x] Test sorting

### 6.5 Test Integration with Main Workflow

- [x] Test scan is skipped when flag is set
- [x] Test scan is skipped when config is set
- [x] Test scan runs by default
- [x] Test user interaction (mock user input)
  - [x] Test abort choice
  - [x] Test continue choice
  - [x] Test remove files choice
- [x] Test file removal functionality
  - [x] Mock `run_git_command()`
  - [x] Verify correct files are unstaged

## 7. Documentation Updates

- [x] Update `CLAUDE.md`
  - [x] Add security module to architecture section
  - [x] Document secret scanning feature
- [x] Update README (if exists)
  - [x] Document `--skip-secret-scan` flag
  - [x] Document `GAC_SKIP_SECRET_SCAN` config option
  - [x] Add security features section
- [x] Add docstring examples where needed

## 8. Manual Testing

- [x] Test with real repository
  - [x] Stage file with fake API key
  - [x] Run `gac` without flags
  - [x] Verify detection and prompting
  - [x] Test each user choice option
- [x] Test configuration options
  - [x] Test with `--skip-secret-scan` flag
  - [x] Test with `GAC_SKIP_SECRET_SCAN=true` in env
- [x] Test edge cases
  - [x] Very large diffs
  - [x] Binary files in diff
  - [x] Unicode characters
  - [x] Multiple secrets per line
  - [x] Secrets spanning multiple lines

## 9. Code Quality

- [x] Run tests with `make test`
- [x] Ensure all new tests pass
- [x] Check test coverage for new module
- [x] Fix any linting issues (if requested)
- [x] Format code (if requested)

## 10. Final Review

- [x] Review all changed files
- [x] Ensure consistent code style
- [x] Verify error handling is comprehensive
- [x] Check logging is appropriate
- [x] Verify user experience matches design
- [x] Ensure backward compatibility

---

## 11. Post-Review Improvements (Critical Issues)

### 11.1 Fix Line Number Tracking Bug (`src/gac/security.py`)

- [x] **CRITICAL**: Fix `scan_diff_section()` line counter logic
  - [x] Remove incorrect increment after `continue` for added lines
  - [x] Track line numbers for both added lines AND context lines
  - [x] Skip metadata lines (`+++`, `---`) properly
  - [x] Update logic to track line numbers correctly for both added and context lines
  - [x] Add test case for line number accuracy with mixed added/context lines
  - [x] Verify line numbers match actual file line numbers

### 11.2 Improve GENERIC_API_KEY Pattern

- [x] Refine `GENERIC_API_KEY` regex to be more specific
  - [x] Remove bare `key` from pattern (too broad)
  - [x] Add `access[-_]?key` and `secret[-_]?key`
  - [x] Consider minimum length requirements
  - [x] Test against common YAML/JSON key-value pairs
  - [x] Verify no false positives on configuration files

### 11.3 Replace `input()` with `click.prompt()` (`src/gac/main.py`)

- [x] Replace raw `input()` at line 116 with Click's prompt
- [x] Use `click.prompt()` with `type=click.Choice(['A', 'C', 'R'])`
- [x] Set `default='A'` for safety
- [x] Set `case_sensitive=False`
- [x] Maintain existing KeyboardInterrupt handling
- [x] Test that prompt works correctly in all scenarios

### 11.4 Add Status Refresh After File Removal

- [x] In `main.py` line 146-148, also refresh `status`
- [x] After unstaging files, run:

  ```python
  status = run_git_command(["status"])
  diff = run_git_command(["diff", "--staged"])
  diff_stat = " " + run_git_command(["diff", "--stat", "--cached"])
  ```

- [x] Ensure consistency across all git state variables

## 12. Post-Review Improvements (High Priority)

### 12.1 Respect Quiet Mode in Security Scan

- [x] Add `quiet` parameter check before printing warnings
- [x] Modify security scan output in `main.py` to respect quiet mode
- [x] Keep prompt visible even in quiet mode (security is critical)
- [x] Test with `-q` flag

### 12.2 Improve Exception Handling Specificity

- [x] Replace bare `except Exception` at line 136 in `main.py`
- [x] Determine specific exceptions from `run_git_command()`
- [x] Catch `GitError` or `subprocess.CalledProcessError` specifically
- [x] Log appropriate error messages for each exception type

### 12.3 Handle .env File Variants

- [x] Add special handling for `.env.example`, `.env.template`, `.env.sample`
- [x] Add these to false positive exclusions
- [x] Check file name in `is_false_positive()` function and adjust behavior
- [x] Add tests for `.env.example` files with placeholder values

### 12.4 Reconsider PASSWORD Pattern

- [x] Evaluate if `PASSWORD` pattern is too aggressive
- [x] Add more false positive patterns for test passwords
- [x] Include additional common test password patterns like "admin" and "testpass"
- [x] Test against common testing scenarios

## 13. Post-Review Improvements (Medium Priority)

### 13.1 Add Constants for Magic Numbers

- [x] Create constant for secret truncation length
- [x] Add `MAX_DISPLAYED_SECRET_LENGTH = 50` to `constants.py` in the `Utility` class
- [x] Use constant in `scan_diff_section()` instead of hardcoded value

### 13.2 Consider Dry-Run Mode Behavior

- [x] Decide if security scan should run in `--dry-run` mode
- [x] Decision: Always run security scan even in dry-run mode for validation
- [x] Document decision in code comments
- [x] Test both scenarios

### 13.3 Remove or Use `extract_line_number_from_hunk()`

- [x] Remove unused function (DRY principle)
- [x] Function is no longer needed as line number tracking is handled directly in `scan_diff_section()`

### 13.4 Enhance Logging Consistency

- [x] Add debug logging when scan is skipped
- [x] Add debug logging for each file being scanned
- [x] Log statistics (files scanned, patterns checked, etc.)
- [x] Ensure log levels are appropriate (DEBUG vs INFO vs WARNING)

## 14. Additional Test Coverage

### 14.1 Add Missing Test Cases

- [x] Test line number accuracy with mixed added/context lines
  - [x] Create diff with `+`, ``,`+` pattern
  - [x] Verify line numbers match expected values
- [x] Test very long secret truncation (>50 chars)
  - [x] Verify `...` is appended
  - [x] Verify length is exactly 50 + 3
- [x] Test `KeyboardInterrupt` during user prompt
  - [x] Mock interrupt signal
  - [x] Verify graceful exit
- [x] Test `--skip-secret-scan` flag actually skips scan
  - [x] Mock `scan_staged_diff` to track if called
  - [x] Run with flag and verify not called
- [x] Test `GAC_SKIP_SECRET_SCAN=true` config
  - [x] Set environment variable
  - [x] Verify scan is skipped

### 14.2 Add Integration Tests for main.py

- [x] Mock user interaction flow in `main()`
- [x] Test each choice (A, C, R) with mocked input
- [x] Test file unstaging with mocked git commands
- [x] Verify diff refresh after file removal
- [x] Test error handling when unstaging fails

### 14.3 Add Performance Tests

- [x] Test with very large diffs (10,000+ lines)
- [x] Test with 100+ files in single commit
- [x] Measure scan performance
- [x] Ensure scan completes in reasonable time (<5 seconds for typical commits)

## 15. Documentation Enhancements

### 15.1 Add Usage Examples

- [x] Create example in README showing typical workflow:

  ```bash
  # Accidentally staged a secret
  gac  # Detects secret, prompts user

  # Skip scan for this commit (not recommended)
  gac --skip-secret-scan

  # Disable globally in config
  echo "GAC_SKIP_SECRET_SCAN=true" >> ~/.gac.env
  ```

### 15.2 Document Pattern Customization

- [x] Add documentation for extending patterns
- [x] Show how to add custom patterns
- [x] Explain false positive filtering
- [x] Document when to use `--skip-secret-scan`

### 15.3 Add Security Best Practices Guide

- [x] Document what to do if secrets are committed
- [x] Link to GitHub's secret scanning documentation
- [x] Explain git history rewriting (if secret already committed)
- [x] Recommend using tools like `git-secrets` or `trufflehog`

## 16. Future Enhancements (Optional)

### 16.1 Custom Pattern Configuration

- [ ] Allow users to define custom patterns in config
- [ ] Load patterns from `.gac-security.yml` or similar
- [ ] Support per-project pattern overrides

### 16.2 Severity Levels

- [ ] Assign severity levels to different secret types
  - HIGH: AWS keys, production API keys
  - MEDIUM: GitHub tokens, Stripe test keys
  - LOW: Generic API keys
- [ ] Allow filtering by severity
- [ ] Different prompts based on severity

### 16.3 Integration with External Tools

- [ ] Support for `detect-secrets` integration
- [ ] Support for `gitleaks` integration
- [ ] Export findings to SARIF format
- [ ] CI/CD integration examples

### 16.4 Whitelist/Allowlist Support

- [ ] Allow users to whitelist specific files
- [ ] Allow users to whitelist specific patterns/values
- [ ] Store allowlist in `.gac-allowlist` file
- [ ] Add `gac security add-exception` command

---

## Priority Summary

**COMPLETED (Ready for Release):**
All planned improvements for the initial release have been successfully implemented and tested:

1. ✅ Line number tracking bug (11.1)
2. ✅ Replace `input()` with `click.prompt()` (11.3)
3. ✅ Generic API key pattern refinement (11.2)
4. ✅ Status refresh after file removal (11.4)
5. ✅ Respect quiet mode in security scan (12.1)
6. ✅ Improve exception handling specificity (12.2)
7. ✅ Handle .env file variants (12.3)
8. ✅ Password pattern reconsideration (12.4)
9. ✅ Add constants for magic numbers (13.1)
10. ✅ Remove unused `extract_line_number_from_hunk()` function (13.3)
11. ✅ Add missing test cases (14.1)
12. ✅ Consider dry-run mode behavior (13.2)
13. ✅ Enhance logging consistency (13.4)
14. ✅ Add integration tests for main.py (14.2)
15. ✅ Add performance tests (14.3)
16. ✅ Documentation enhancements (15.1-15.3)

**FUTURE (Post-MVP):**

- Custom pattern configuration (16.1)
- Severity levels (16.2)
- External tool integration (16.3)
- Whitelist/Allowlist support (16.4)

## 17. Completed Improvements

All critical, high priority, and medium priority improvements have been successfully implemented and tested:

- ✅ Line number tracking bug fixed
- ✅ Replaced `input()` with `click.prompt()`
- ✅ Improved GENERIC_API_KEY pattern
- ✅ Added status refresh after file removal
- ✅ Respected quiet mode in security scan
- ✅ Improved exception handling specificity
- ✅ Handled .env file variants
- ✅ Reconsidered PASSWORD pattern
- ✅ Added constants for magic numbers
- ✅ Removed unused `extract_line_number_from_hunk()` function
- ✅ Added comprehensive test coverage
- ✅ Updated documentation with usage examples
- ✅ Added security best practices guide
