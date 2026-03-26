# Git Repository Sync Tool

An automated Python script to synchronize branches between any Git-compatible SCM platforms (GitHub, GitLab, Bitbucket, etc.).

## Features
- **SCM-Agnostic**: Works with any Git remote — GitHub ↔ Bitbucket, GitLab ↔ GitHub, GitLab ↔ Bitbucket, etc.
- **Flexible Branch Mapping**: Support for 1-to-1 branch mapping or an automated "Sync All" mode.
- **Secure Authentication**: Supports SSH, Config file, and Environment Variables. URL encoding prevents malformed URL errors with special characters in tokens.
- **CI/CD Ready**: Credential scrubbing in logs, proper exit codes (`sys.exit(1)`) on failures for accurate pipeline reporting.
- **Jenkins Integration**: Natively integrates with `Jenkinsfile` and `withCredentials` plugins.

## Prerequisites
- Server/Agent with `git` and `python3` (3.6+) installed.

## Usage

### Method 1: Environment Variables (Recommended for CI/CD & Jenkins)

```bash
export SYNC_SRC_TOKEN="ghp_xxxx"
export SYNC_DEST_TOKEN="BBDC-xxxx"

# Sync all but ignore some protected branches
python3 src/git_repo_sync.py \
  --auth-method env \
  --sync-all \
  --ignore-branches "master, production, release" \
  --src-url "https://github.com/my-org/repo.git" \
  --dest-url "http://bitbucket.company.com/scm/proj/repo.git" \
  --src_user "github_user" \
  --dest_user "bitbucket_user"
```

### Method 2: SSH Connection

```bash
# Explicit branch mapping (main → prod, dev → stag)
# Use comma-separated list or multiple arguments
python3 src/git_repo_sync.py \
  --auth-method ssh \
  --src-url "git@github.com:my-org/repo.git" \
  --dest-url "ssh://git@bitbucket.company.com:7999/proj/repo.git" \
  --src-branches "main, dev, feature/abc" \
  --dest-branches "prod, stag, feature/abc"
```

### Method 3: Configuration File

```bash
python3 src/git_repo_sync.py --config config.example.json
```

## SCM Compatibility Matrix

| Source | Destination | Auth Method |
|--------|------------|-------------|
| GitHub | Bitbucket | PAT + App Password / HTTP Token |
| GitHub | GitLab | PAT + Personal Access Token |
| GitLab | Bitbucket | Personal Access Token + App Password |
| GitLab | GitHub | Personal Access Token + PAT |
| Bitbucket | GitHub | HTTP Token + PAT |

## Jenkins Integration

The included `Jenkinsfile` provides a parameterized pipeline. Users select pre-configured credentials from a dropdown — no token handling required.

### Setup
1. Create `usernamePassword` credentials in Jenkins for source and destination SCMs
2. Configure the pipeline job to use the `Jenkinsfile` from this repository
3. Build with Parameters: select URLs, credentials, and branch options
