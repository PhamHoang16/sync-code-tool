import argparse
import json
import subprocess
import sys
import tempfile
import os
import re
import urllib.parse

def scrub_url(text):
    """Hide credentials in URLs from logs."""
    if not isinstance(text, str):
        return text
    # Mask credentials in http/https URLs to prevent leaks
    return re.sub(r'(https?://)[^@]+@', r'\1***:***@', text)

def run_cmd(cmd, cwd=None, hide_output=False):
    """Run a shell command and handle errors safely."""
    try:
        result = subprocess.run(
            cmd, 
            cwd=cwd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            universal_newlines=True,
            check=True
        )
        if not hide_output and result.stdout:
            print(scrub_url(result.stdout))
        return result.stdout
    except subprocess.CalledProcessError as e:
        scrubbed_cmd = [scrub_url(c) for c in cmd]
        print(f"[-] Command failed: {' '.join(scrubbed_cmd)}")
        if e.stderr:
            print(f"Error output:\n{scrub_url(e.stderr.strip())}")
        raise e

def construct_auth_url(url, user, token):
    """Construct an authenticated HTTPS URL if credentials are provided."""
    if not token:
        return url
    
    # Avoid accidentally adding auth twice if user already provided it in URL
    if "@" in url and ("https://" in url or "http://" in url):
        return url
        
    safe_token = urllib.parse.quote(token, safe="")
    
    auth_prefix = ""
    if user:
        safe_user = urllib.parse.quote(user, safe="")
        auth_prefix = f"{safe_user}:{safe_token}@"
    else:
        auth_prefix = f"{safe_token}@"
        
    if url.startswith("https://"):
        return url.replace("https://", f"https://{auth_prefix}")
    elif url.startswith("http://"):
        return url.replace("http://", f"http://{auth_prefix}")
        
    return url

def sync_branches(src_url, dest_url, src_branches, dest_branches, sync_all, ignore_branches=None):
    with tempfile.TemporaryDirectory() as tmpdir:
        print("[*] Created temporary workspace...")
        print("[*] Cloning source repository...")
        
        try:
            # Bare clone is efficient for sync, but we'll use a standard no-checkout 
            # clone to keep the process standard and robust for fetching specific branches.
            run_cmd(["git", "clone", "--no-checkout", src_url, "repo"], cwd=tmpdir, hide_output=True)
        except subprocess.CalledProcessError:
            print("[-] Exiting due to clone failure. Please check URLs and credentials.")
            sys.exit(1)

        repo_dir = os.path.join(tmpdir, "repo")

        try:
            run_cmd(["git", "remote", "add", "destination", dest_url], cwd=repo_dir, hide_output=True)
        except subprocess.CalledProcessError:
            print("[-] Failed to add destination remote.")
            sys.exit(1)

        if sync_all:
            print("[*] Sync All mode enabled. Fetching all branches from source...")
            try:
                run_cmd(["git", "fetch", "origin"], cwd=repo_dir, hide_output=True)
            except subprocess.CalledProcessError:
                print("[-] Failed to fetch from origin.")
                sys.exit(1)
                
            output = run_cmd(["git", "branch", "-r"], cwd=repo_dir, hide_output=True)
            branches = []
            for line in output.split("\n"):
                line = line.strip()
                # Exclude HEAD pointer and only target remote origin branches
                if line and "->" not in line and line.startswith("origin/"):
                    branch_name = line.replace("origin/", "", 1)
                    branches.append(branch_name)
                    
            if ignore_branches:
                print(f"[*] Filtering out ignored branches: {', '.join(ignore_branches)}")
                branches = [b for b in branches if b not in ignore_branches]
                    
            print(f"[*] Found {len(branches)} branch(es) to sync.")
            failed_branches = []
            for branch in branches:
                print(f"[*] Pushing '{branch}'...")
                try:
                    run_cmd(["git", "push", "destination", f"refs/remotes/origin/{branch}:refs/heads/{branch}", "--force"], cwd=repo_dir, hide_output=True)
                    print(f"[+] Successfully synced '{branch}' [OK]")
                except subprocess.CalledProcessError:
                    print(f"[-] Failed to sync '{branch}' [ER]")
                    failed_branches.append(branch)
            if failed_branches:
                print(f"[-] Synchronization completed with errors. Failed branches: {', '.join(failed_branches)}")
                sys.exit(1)
        else:
            if not src_branches or not dest_branches:
                print("[-] In mapping mode, 'source_branches' and 'dest_branches' lists must be provided and non-empty.")
                sys.exit(1)
                
            if len(src_branches) != len(dest_branches):
                print(f"[-] Parameter mismatch: {len(src_branches)} source branches vs {len(dest_branches)} destination branches.")
                sys.exit(1)
                
            print(f"[*] Mapping mode enabled: Syncing {len(src_branches)} mapped mapped branches.")
            failed_mappings = []
            for src_b, dest_b in zip(src_branches, dest_branches):
                print(f"[*] Analyzing mapping '{src_b}' -> '{dest_b}'...")
                
                try:
                    # Fetch only the specific branch needed for mapping
                    run_cmd(["git", "fetch", "origin", src_b], cwd=repo_dir, hide_output=True)
                except subprocess.CalledProcessError:
                    print(f"[-] Source branch '{src_b}' does not exist on source. Skipping mapping. [ER]")
                    failed_mappings.append(f"{src_b}->{dest_b}")
                    continue
                    
                print(f"[*] Pushing '{src_b}' to destination as '{dest_b}'...")
                try:
                    # FETCH_HEAD evaluates to the branch we just explicitly fetched above
                    run_cmd(["git", "push", "destination", f"FETCH_HEAD:refs/heads/{dest_b}", "--force"], cwd=repo_dir, hide_output=True)
                    print(f"[+] Successfully synced '{src_b}' -> '{dest_b}' [OK]")
                except subprocess.CalledProcessError:
                    print(f"[-] Failed to sync '{src_b}' -> '{dest_b}' [ER]")
                    failed_mappings.append(f"{src_b}->{dest_b}")
            if failed_mappings:
                print(f"[-] Synchronization completed with errors. Failed mappings: {', '.join(failed_mappings)}")
                sys.exit(1)

def parse_list(input_list):
    """Parse a list of strings that might contain comma-separated values."""
    if not input_list:
        return []
    result = []
    for item in input_list:
        # Split by comma and strip whitespace
        parts = [p.strip() for p in item.split(',')]
        for p in parts:
            if p:
                # Further split by space just in case
                subparts = [sp.strip() for sp in p.split()]
                result.extend([sp for sp in subparts if sp])
    return result

def generate_sample_config():
    """Outputs a sample JSON configuration."""
    sample = {
        "src_url": "https://github.com/your-org/source-repo.git",
        "src_user": "github_username",
        "src_token": "ghp_your_github_token",
        "dest_url": "https://bitbucket.internal.company.com/scm/proj/dest-repo.git",
        "dest_user": "bitbucket_service_account",
        "dest_token": "your_app_password_or_token",
        "auth_method": "env",
        "sync_all": False,
        "src_branches": ["main", "dev", "feature-1"],
        "dest_branches": ["prod", "stag", "feature-1"]
    }
    print("Sample config.json format:")
    print(json.dumps(sample, indent=4))

def main():
    parser = argparse.ArgumentParser(description="Automated Git repository synchronization tool. Supports any Git-compatible SCM (GitHub, GitLab, Bitbucket, etc.).")
    
    # Config file
    parser.add_argument("-c", "--config", help="Path to config.json file. Options inside override or complement CLI args.")
    parser.add_argument("--generate-config", action="store_true", help="Print a sample config.json and exit.")
    parser.add_argument("--auth-method", choices=["token", "ssh", "config", "env"], help="Force an authentication method (token, ssh, config, env) to ensure safety.")
    
    # Source
    src_group = parser.add_argument_group('Source Repository')
    src_group.add_argument("--src-url", help="Source repository URL (HTTPS or SSH)")
    src_group.add_argument("--src-user", help="Source username or token owner")
    src_group.add_argument("--src-token", help="Source access token (PAT, App Password, etc.)")
    
    # Destination
    dest_group = parser.add_argument_group('Destination Repository')
    dest_group.add_argument("--dest-url", help="Destination repository URL (HTTPS or SSH)")
    dest_group.add_argument("--dest-user", help="Destination username (service account)")
    dest_group.add_argument("--dest-token", help="Destination access token (App Password, HTTP Token, etc.)")
    
    # Branching
    branch_group = parser.add_argument_group('Branch Configurations')
    branch_group.add_argument("--sync-all", action="store_true", help="Automatically fetch and push all branches (name mapping 1:1).")
    branch_group.add_argument("--src-branches", nargs="*", help="List of source branches (e.g. main dev)")
    branch_group.add_argument("--dest-branches", nargs="*", help="List of destination branches (e.g. prod stag)")
    branch_group.add_argument("--ignore-branches", nargs="*", help="List of branches to ignore during sync-all (e.g. master production)")

    args = parser.parse_args()
    
    if args.generate_config:
        generate_sample_config()
        sys.exit(0)
    
    config = {}
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            print(f"[-] Config file '{args.config}' not found.")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"[-] Invalid JSON in config file: {e}")
            sys.exit(1)

    # Resolution (CLI args > Config File > Environment Variables)
    src_url = args.src_url or config.get("src_url") or os.environ.get("SYNC_SRC_URL")
    src_user = args.src_user or config.get("src_user") or os.environ.get("SYNC_SRC_USER")
    src_token = args.src_token or config.get("src_token") or os.environ.get("SYNC_SRC_TOKEN")
    
    dest_url = args.dest_url or config.get("dest_url") or os.environ.get("SYNC_DEST_URL")
    dest_user = args.dest_user or config.get("dest_user") or os.environ.get("SYNC_DEST_USER")
    dest_token = args.dest_token or config.get("dest_token") or os.environ.get("SYNC_DEST_TOKEN")
    
    sync_all = args.sync_all if getattr(args, 'sync_all', False) else config.get("sync_all", False)
    
    src_branches = parse_list(args.src_branches or config.get("src_branches", []))
    dest_branches = parse_list(args.dest_branches or config.get("dest_branches", []))
    ignore_branches = parse_list(args.ignore_branches or config.get("ignore_branches", []))

    if not src_url or not dest_url:
        print("[-] Error: Both source (--src-url) and destination (--dest-url) URLs must be defined.")
        parser.print_help()
        sys.exit(1)

    auth_method = getattr(args, "auth_method", None) or config.get("auth_method", "config")
    
    if auth_method == "ssh":
        if "http://" in src_url or "https://" in src_url or "http://" in dest_url or "https://" in dest_url:
            print("[-] Validation Error: 'ssh' auth method selected but one of the URLs is HTTP/HTTPS.")
            sys.exit(1)
        # Clear out credentials so they are never embedded
        src_user = src_token = dest_user = dest_token = None
    elif auth_method == "env":
        # Override tokens explicitly from env to ignore config file completely
        src_token = os.environ.get("SYNC_SRC_TOKEN")
        dest_token = os.environ.get("SYNC_DEST_TOKEN")
        if not src_token or not dest_token:
            print("[-] Error: 'env' auth method selected but SYNC_SRC_TOKEN / SYNC_DEST_TOKEN are missing.")
            sys.exit(1)

    print("========================================")
    print("       Git Repository Sync Tool")
    print("========================================")
    print(f"Source      : {scrub_url(src_url)}")
    print(f"Destination : {scrub_url(dest_url)}")
    print(f"Sync All    : {sync_all}")
    if not sync_all:
        print(f"Src branches: {src_branches}")
        print(f"Dst branches: {dest_branches}")
    else:
        if ignore_branches:
            print(f"Ignore list : {ignore_branches}")
    print("----------------------------------------")

    auth_src_url = construct_auth_url(src_url, src_user, src_token)
    auth_dest_url = construct_auth_url(dest_url, dest_user, dest_token)

    try:
        sync_branches(auth_src_url, auth_dest_url, src_branches, dest_branches, sync_all, ignore_branches)
    except KeyboardInterrupt:
        print("\n[-] Sync canceled by user.")
        sys.exit(1)

if __name__ == "__main__":
    main()
