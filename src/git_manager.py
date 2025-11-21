#!/usr/bin/env python3
"""
Git repository management module.
Handles git operations for storing patches as files.
"""

import os
import subprocess
from typing import Dict, Optional


class GitManager:
    """Manage git repository operations for Gerrit history preservation."""
    
    @staticmethod
    def init_repo(repo_path: str, branch_name: str = 'gerrit-history') -> bool:
        """
        Initialize a git repository for storing patches and HTML files.
        
        Args:
            repo_path: Path where git repository should be created/used
            branch_name: Name of the branch to store history
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if repo_path is an existing git repository
            git_dir = os.path.join(repo_path, '.git')
            is_existing_repo = os.path.exists(git_dir)
            
            if is_existing_repo:
                # Existing repo - create output folder inside it
                output_path = os.path.join(repo_path, 'gerrit-archive')
                os.makedirs(output_path, exist_ok=True)
                print(f"Using existing git repository at: {repo_path}")
                print(f"Creating output folder: gerrit-archive/")
                return output_path
            
            # Create directory if it doesn't exist
            os.makedirs(repo_path, exist_ok=True)
            
            # Initialize new git repo
            print(f"Initializing git repository at: {repo_path}")
            subprocess.run(['git', 'init'], cwd=repo_path, check=True, capture_output=True)
            
            # Create initial commit
            readme_path = os.path.join(repo_path, 'README.md')
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(f"# Gerrit History Preservation\n\n")
                f.write(f"This repository preserves Gerrit review history.\n\n")
                f.write(f"- Branch `{branch_name}`: Contains patch files and HTML review data\n")
                f.write(f"- `patches/` directory: Patch files for each change\n")
                f.write(f"- `html/` directory: Browsable HTML review data\n")
            
            subprocess.run(['git', 'add', 'README.md'], cwd=repo_path, check=True, capture_output=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit: Gerrit history preservation'], 
                         cwd=repo_path, check=True, capture_output=True)
            print(f"  Repository initialized successfully")
            
            # Create or checkout the history branch
            result = subprocess.run(['git', 'rev-parse', '--verify', branch_name], 
                                  cwd=repo_path, capture_output=True, text=True)
            
            if result.returncode != 0:
                # Branch doesn't exist, create it
                print(f"Creating branch: {branch_name}")
                subprocess.run(['git', 'checkout', '-b', branch_name], 
                             cwd=repo_path, check=True, capture_output=True)
            else:
                # Branch exists, checkout
                print(f"Checking out existing branch: {branch_name}")
                subprocess.run(['git', 'checkout', branch_name], 
                             cwd=repo_path, check=True, capture_output=True)
            
            return True
            
        except Exception as e:
            print(f"Error initializing git repository: {e}")
            return False
    
    @staticmethod
    def commit_files(repo_path: str, file_pattern: str, message: str) -> bool:
        """
        Add and commit files to the repository.
        
        Args:
            repo_path: Path to git repository
            file_pattern: File pattern to add (e.g., 'html/')
            message: Commit message
            
        Returns:
            True if successful, False otherwise
        """
        try:
            subprocess.run(['git', 'add', file_pattern], cwd=repo_path, check=True, capture_output=True)
            subprocess.run(['git', 'commit', '-m', message], cwd=repo_path, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    @staticmethod
    def push_to_remote(repo_path: str, remote_url: str, branch_name: str = 'gerrit-history') -> bool:
        """
        Push the repository to a remote URL.
        
        Args:
            repo_path: Path to git repository
            remote_url: Remote repository URL (e.g., https://github.com/user/repo.git)
            branch_name: Branch to push
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if remote 'origin' already exists
            result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                                  cwd=repo_path, capture_output=True, text=True)
            
            if result.returncode != 0:
                # Add remote origin
                print(f"Adding remote origin: {remote_url}")
                subprocess.run(['git', 'remote', 'add', 'origin', remote_url], 
                             cwd=repo_path, check=True, capture_output=True)
            else:
                existing_url = result.stdout.strip()
                if existing_url != remote_url:
                    print(f"Updating remote origin from {existing_url} to {remote_url}")
                    subprocess.run(['git', 'remote', 'set-url', 'origin', remote_url], 
                                 cwd=repo_path, check=True, capture_output=True)
            
            # Push to remote
            print(f"Pushing branch '{branch_name}' to remote...")
            subprocess.run(['git', 'push', '-u', 'origin', branch_name], 
                         cwd=repo_path, check=True, capture_output=True)
            print(f"✓ Successfully pushed to {remote_url}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error pushing to remote: {e}")
            print(f"  You may need to authenticate or check remote URL")
            return False
