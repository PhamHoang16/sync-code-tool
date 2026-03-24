# GitHub to Bitbucket Sync Tool

An automated Python script designed to seamlessly synchronize branches from a GitHub repository to an internal Bitbucket repository.

## Features
- **Flexible Branch Mapping**: Support for 1-to-1 branch mapping or an automated "Sync All" mode.
- **Secure Authentication**: Supports SSH, Config mapping, and Environment Variables. Explicit URL encoding prevents malformed URL errors when special characters exist in tokens or usernames.
- **CI/CD Ready**: Built-in credential scrubbing in stdout ensures logs remain clean. Properly handles system exit codes (`sys.exit(1)`) on synchronization failures for accurate CI/CD reporting.
- **Jenkins Integration**: Natively integrates with `Jenkinsfile` and `withCredentials` plugins.

## Prerequisites
- Server/Agent with `git` and `python3` installed.

## Usage

### Method 1: Environment Variables (Recommended for CI/CD & Jenkins)
This method is highly recommended for automated pipelines (Jenkins, GitHub Actions, GitLab CI). It utilizes Personal Access Tokens (PAT) and App Passwords injected via environment variables.

```bash
export SYNC_SRC_TOKEN="ghp_xxxx"
export SYNC_DEST_TOKEN="BBDC-xxxx"

python3 src/github_to_bitbucket_sync.py \
  --auth-method env \
  --sync-all \
  --src-url "https://github.com/my-org/repo.git" \
  --dest-url "http://bitbucket.company.com/scm/proj/repo.git" \
  --src-user "github_user" \
  --dest-user "bitbucket_user"
```

### Method 2: SSH Connection (Recommended for Dedicated Servers)
Relies on SSH keys configured on the host machine for both GitHub and Bitbucket.

**1. Explicit Branch Mapping**
Sync specific branches from source to destination (e.g., `main` to `prod`):
```bash
python3 src/github_to_bitbucket_sync.py \
  --auth-method ssh \
  --src-url "git@github.com:my-org/repo.git" \
  --dest-url "ssh://git@bitbucket.company.com:7999/proj/repo.git" \
  --src-branches "main" "dev" \
  --dest-branches "prod" "stag"
```

**2. Sync All Branches**
Automatically fetches and pushes all branches (`--sync-all`):
```bash
python3 src/github_to_bitbucket_sync.py \
  --auth-method ssh \
  --sync-all \
  --src-url "git@github.com:my-org/repo.git" \
  --dest-url "ssh://git@bitbucket.company.com:7999/proj/repo.git"
```

### Method 3: Configuration File
Instead of passing long CLI arguments, you can define configurations in a `config.example.json` file.

**Sample `config.example.json` (SSH Authentication):**
```json
{
    "src_url": "git@github.com:my-org/repo.git",
    "dest_url": "ssh://git@bitbucket.company.com:7999/proj/repo.git",
    "auth_method": "ssh",
    "sync_all": true
}
```

Execute the tool using the configuration file:
```bash
python3 src/github_to_bitbucket_sync.py --config config.example.json
```
