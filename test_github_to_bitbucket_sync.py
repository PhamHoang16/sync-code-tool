import unittest
from unittest.mock import patch, MagicMock
import subprocess
import sys
import os

# Add the directory to sys.path so we can import the script directly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import github_to_bitbucket_sync as sync_tool

class TestSyncTool(unittest.TestCase):

    def test_scrub_url(self):
        # Test HTTP/HTTPS scrubbing
        self.assertEqual(
            sync_tool.scrub_url("https://user:password@github.com/repo.git"),
            "https://***:***@github.com/repo.git"
        )
        self.assertEqual(
            sync_tool.scrub_url("http://user:password@bitbucket.digital.vn/repo.git"),
            "http://***:***@bitbucket.digital.vn/repo.git"
        )
        # Test normal URLs are unaffected
        self.assertEqual(
            sync_tool.scrub_url("https://github.com/repo.git"),
            "https://github.com/repo.git"
        )
        # Test SSH URLs are unaffected
        self.assertEqual(
            sync_tool.scrub_url("git@github.com:user/repo.git"),
            "git@github.com:user/repo.git"
        )
        # Test text logging containing URL
        self.assertEqual(
            sync_tool.scrub_url("Cloning from https://abc:xyz@github.com !"),
            "Cloning from https://***:***@github.com !"
        )

    def test_construct_auth_url(self):
        # Base case
        url = "https://github.com/repo.git"
        self.assertEqual(
            sync_tool.construct_auth_url(url, "myuser", "mytoken"),
            "https://myuser:mytoken@github.com/repo.git"
        )
        
        # Missing credentials
        self.assertEqual(
            sync_tool.construct_auth_url(url, None, "mytoken"),
            url
        )
        
        # Already has auth, should not append again
        url_with_auth = "https://user:pass@github.com/repo.git"
        self.assertEqual(
            sync_tool.construct_auth_url(url_with_auth, "newuser", "newtoken"),
            url_with_auth
        )
        
        # Ignore SSH (git@...)
        ssh_url = "git@github.com:user/repo.git"
        self.assertEqual(
            sync_tool.construct_auth_url(ssh_url, "user", "token"),
            ssh_url
        )

    @patch('subprocess.run')
    def test_run_cmd_success(self, mock_run):
        mock_result = MagicMock()
        mock_result.stdout = "hello world\n"
        mock_run.return_value = mock_result
        
        result = sync_tool.run_cmd(["echo", "hello world"])
        self.assertEqual(result, "hello world\n")
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_run_cmd_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, cmd=["false"], stderr="error output")
        
        with self.assertRaises(subprocess.CalledProcessError):
            with patch('sys.stdout', new=MagicMock()): # suppress print
                sync_tool.run_cmd(["false"])

    @patch('github_to_bitbucket_sync.run_cmd')
    def test_sync_branches_mapping_success(self, mock_run_cmd):
        # We don't want the actual git commands to run
        mock_run_cmd.return_value = "mocked output"
        
        try:
            with patch('sys.stdout', new=MagicMock()): 
                sync_tool.sync_branches("src_url", "dest_url", ["main"], ["prod"], False)
        except SystemExit:
            self.fail("sync_branches exited unexpectedly")
            
        # Verify run_cmd was called with correct git commands structure
        commands = [call.args[0][0:2] for call in mock_run_cmd.call_args_list]
        self.assertIn(['git', 'clone'], commands)
        self.assertIn(['git', 'remote'], commands)
        self.assertIn(['git', 'fetch'], commands)
        self.assertIn(['git', 'push'], commands)

    @patch('github_to_bitbucket_sync.run_cmd')
    def test_sync_branches_sync_all_success(self, mock_run_cmd):
        # Mock the git branch -r output to return two branches
        def side_effect(cmd, **kwargs):
            if cmd[:2] == ['git', 'branch']:
                return "  origin/main\n  origin/feature\n"
            return ""
            
        mock_run_cmd.side_effect = side_effect
        
        try:
            with patch('sys.stdout', new=MagicMock()):
                sync_tool.sync_branches("src_url", "dest_url", [], [], True)
        except SystemExit:
            self.fail("sync_branches exited unexpectedly")
            
        # Check that it pushed main and feature
        push_calls = [call for call in mock_run_cmd.call_args_list if call.args[0][:2] == ['git', 'push']]
        self.assertEqual(len(push_calls), 2)
        
        # Verify branches being pushed
        pushed_branches = [call.args[0][3] for call in push_calls]
        self.assertTrue(any('refs/remotes/origin/main:refs/heads/main' in b for b in pushed_branches))
        self.assertTrue(any('refs/remotes/origin/feature:refs/heads/feature' in b for b in pushed_branches))

    @patch('github_to_bitbucket_sync.run_cmd')
    def test_sync_branches_mapping_mismatch(self, mock_run_cmd):
        # Testing list size mismatch in mapping mode (e.g. 2 src branches but only 1 dest branch)
        with patch('sys.stdout', new=MagicMock()): 
            with self.assertRaises(SystemExit) as cm:
                sync_tool.sync_branches("src", "dest", ["main", "dev"], ["prod"], False)
            self.assertEqual(cm.exception.code, 1)

    @patch('github_to_bitbucket_sync.run_cmd')
    def test_sync_branches_missing_source_branch(self, mock_run_cmd):
        # If fetch fails on a mapped branch, it should skip it and continue to the next
        def side_effect(cmd, **kwargs):
            if cmd == ['git', 'fetch', 'origin', 'missing']:
                raise subprocess.CalledProcessError(1, cmd)
            return ""
            
        mock_run_cmd.side_effect = side_effect
        
        with patch('sys.stdout', new=MagicMock()):
            with self.assertRaises(SystemExit) as cm:
                sync_tool.sync_branches("src", "dest", ["missing", "main"], ["prod", "stag"], False)
            self.assertEqual(cm.exception.code, 1)
            
        # It should still push the second branch (main) to (stag)
        push_calls = [call for call in mock_run_cmd.call_args_list if call.args[0][:2] == ['git', 'push']]
        self.assertEqual(len(push_calls), 1)
        self.assertIn('refs/heads/stag', push_calls[0].args[0][3])

    @patch('github_to_bitbucket_sync.run_cmd')
    def test_sync_branches_sync_all_push_failure(self, mock_run_cmd):
        def side_effect(cmd, **kwargs):
            if cmd[:2] == ['git', 'branch']:
                return "  origin/main\n"
            if cmd[:2] == ['git', 'push']:
                raise subprocess.CalledProcessError(1, cmd)
            return ""
            
        mock_run_cmd.side_effect = side_effect
        
        with patch('sys.stdout', new=MagicMock()):
            with self.assertRaises(SystemExit) as cm:
                sync_tool.sync_branches("src", "dest", [], [], True)
            self.assertEqual(cm.exception.code, 1)

    @patch('github_to_bitbucket_sync.run_cmd')
    def test_sync_branches_mapping_push_failure(self, mock_run_cmd):
        def side_effect(cmd, **kwargs):
            if cmd[:2] == ['git', 'push']:
                raise subprocess.CalledProcessError(1, cmd)
            return ""
            
        mock_run_cmd.side_effect = side_effect
        
        with patch('sys.stdout', new=MagicMock()):
            with self.assertRaises(SystemExit) as cm:
                sync_tool.sync_branches("src", "dest", ["main"], ["prod"], False)
            self.assertEqual(cm.exception.code, 1)

if __name__ == '__main__':
    unittest.main()
