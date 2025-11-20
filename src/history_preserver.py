#!/usr/bin/env python3
"""
Main history preservation orchestrator.
Coordinates all modules to preserve Gerrit history.
"""

import os
import shutil
from typing import Dict, Optional

from .gerrit_api import GerritAPIClient
from .html_generator import HTMLGenerator
from .git_manager import GitManager
from .metadata_exporter import MetadataExporter


class GerritHistoryPreserver:
    """Orchestrate Gerrit history preservation workflow."""
    
    def __init__(self, gerrit_url: str, username: Optional[str] = None, 
                 password: Optional[str] = None, verify_ssl: bool = True):
        """
        Initialize history preserver.
        
        Args:
            gerrit_url: Base URL of Gerrit instance
            username: Gerrit username (optional)
            password: Gerrit HTTP password (optional)
            verify_ssl: Whether to verify SSL certificates
        """
        self.api_client = GerritAPIClient(gerrit_url, username, password, verify_ssl)
        self.html_generator = HTMLGenerator()
        self.git_manager = GitManager()
        self.metadata_exporter = MetadataExporter()
        self.gerrit_url = gerrit_url
    
    def export_changes_with_html(self, output_dir: str, query: str = "status:open",
                                 limit: int = 100) -> Dict:
        """
        Export patches and HTML representations of changes (no git repository).
        
        Args:
            output_dir: Directory to save files
            query: Gerrit query string
            limit: Maximum number of changes to fetch
            
        Returns:
            Dictionary with 'patches' and 'html' lists of file paths
        """
        patches_dir = os.path.join(output_dir, 'patches')
        html_dir = os.path.join(output_dir, 'html')
        os.makedirs(patches_dir, exist_ok=True)
        os.makedirs(html_dir, exist_ok=True)
        
        changes = self.api_client.get_changes(query, limit)
        patch_files = []
        html_files = []
        
        print(f"Found {len(changes)} changes matching query: {query}")
        
        for change in changes:
            change_number = change['_number']
            subject = change['subject']
            
            # Get current revision
            current_revision = change.get('current_revision')
            if not current_revision:
                print(f"Skipping change {change_number}: No current revision")
                continue
            
            print(f"\nExporting change {change_number}: {subject}")
            
            # Get detailed information
            try:
                change_detail = self.api_client.get_change_detail(change_number)
                comments = self.api_client.get_change_comments(change_number)
                files = self.api_client.get_change_files(change_number, current_revision)
            except Exception as e:
                print(f"  Error getting change details: {e}")
                continue
            
            # Export patch
            try:
                patch_content = self.api_client.get_patch(change_number, current_revision)
                safe_subject = "".join(c if c.isalnum() or c in ('-', '_') else '_' 
                                      for c in subject[:50])
                patch_filename = f"{change_number:04d}-{safe_subject}.patch"
                patch_path = os.path.join(patches_dir, patch_filename)
                
                with open(patch_path, 'w', encoding='utf-8') as f:
                    f.write(patch_content)
                
                patch_files.append(patch_path)
                print(f"  Patch saved to: {patch_path}")
            except Exception as e:
                print(f"  Error exporting patch: {e}")
            
            # Export HTML
            try:
                html_content = self.html_generator.generate_change_html(change_detail, comments, files)
                html_filename = f"{change_number:04d}-{safe_subject}.html"
                html_path = os.path.join(html_dir, html_filename)
                
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                html_files.append(html_path)
                print(f"  HTML saved to: {html_path}")
            except Exception as e:
                print(f"  Error generating HTML: {e}")
        
        # Generate index HTML
        index_path = os.path.join(html_dir, 'index.html')
        self.html_generator.generate_index_html(changes, index_path)
        
        return {'patches': patch_files, 'html': html_files}
    
    def preserve_history(self, output_dir: str, repo_path: str, 
                        query: str = "status:merged", limit: int = 100,
                        branch_name: str = 'gerrit-history') -> Dict:
        """
        Complete Gerrit history preservation workflow.
        Stores patches as files (does not apply them as commits).
        
        Args:
            output_dir: Directory for HTML and metadata exports
            repo_path: Path to git repository for storing patches and HTML files
            query: Gerrit query string
            limit: Maximum number of changes to fetch
            branch_name: Git branch name for storing history
            
        Returns:
            Dictionary with statistics and file paths
        """
        print("=" * 70)
        print("GERRIT HISTORY PRESERVATION")
        print("=" * 70)
        
        # Initialize git repository
        if not self.git_manager.init_repo(repo_path, branch_name):
            raise Exception("Failed to initialize git repository")
        
        # Create output directories
        patches_dir = os.path.join(output_dir, 'patches')
        html_dir = os.path.join(output_dir, 'html')
        os.makedirs(patches_dir, exist_ok=True)
        os.makedirs(html_dir, exist_ok=True)
        
        # Fetch changes from Gerrit
        print(f"\nFetching changes from Gerrit...")
        print(f"Query: {query}")
        print(f"Limit: {limit}")
        changes = self.api_client.get_changes(query, limit)
        print(f"Found {len(changes)} changes")
        
        # Sort changes by creation date to preserve chronological order
        changes.sort(key=lambda x: x.get('created', ''))
        
        patch_files = []
        html_files = []
        comments_map = {}
        files_map = {}
        
        print(f"\nProcessing changes...")
        for idx, change in enumerate(changes, 1):
            change_number = change['_number']
            subject = change['subject']
            
            print(f"\n[{idx}/{len(changes)}] Change #{change_number}: {subject[:60]}...")
            
            # Get current revision
            current_revision = change.get('current_revision')
            if not current_revision:
                print(f"  ⚠ Skipping: No current revision")
                continue
            
            # Get detailed information
            try:
                change_detail = self.api_client.get_change_detail(change_number)
                comments = self.api_client.get_change_comments(change_number)
                files = self.api_client.get_change_files(change_number, current_revision)
                
                comments_map[change_number] = comments
                files_map[change_number] = files
            except Exception as e:
                print(f"  ⚠ Error getting details: {e}")
                continue
            
            # Export patch
            safe_subject = "".join(c if c.isalnum() or c in ('-', '_') else '_' 
                                  for c in subject[:50])
            patch_filename = f"{change_number:04d}-{safe_subject}.patch"
            patch_path = os.path.join(patches_dir, patch_filename)
            
            try:
                patch_content = self.api_client.get_patch(change_number, current_revision)
                with open(patch_path, 'w', encoding='utf-8') as f:
                    f.write(patch_content)
                patch_files.append(patch_path)
                print(f"  ✓ Patch saved")
            except Exception as e:
                print(f"  ⚠ Error exporting patch: {e}")
                continue
            
            # Generate HTML
            try:
                html_content = self.html_generator.generate_change_html(change_detail, comments, files)
                html_filename = f"{change_number:04d}-{safe_subject}.html"
                html_path = os.path.join(html_dir, html_filename)
                
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                html_files.append(html_path)
                print(f"  ✓ HTML generated")
            except Exception as e:
                print(f"  ⚠ Error generating HTML: {e}")
        
        # Generate index HTML
        print(f"\nGenerating HTML index...")
        index_path = os.path.join(html_dir, 'index.html')
        self.html_generator.generate_index_html(changes, index_path)
        
        # Save metadata JSON
        print(f"\nSaving metadata...")
        self.metadata_exporter.save_metadata(output_dir, self.gerrit_url, changes, 
                                            comments_map, files_map)
        
        # Copy patches and HTML files to git repository for preservation
        print(f"\nAdding files to git repository...")
        
        # Copy patches
        patches_repo_dir = os.path.join(repo_path, 'patches')
        os.makedirs(patches_repo_dir, exist_ok=True)
        for patch_file in patch_files:
            dest = os.path.join(patches_repo_dir, os.path.basename(patch_file))
            shutil.copy2(patch_file, dest)
        
        # Copy HTML files
        html_repo_dir = os.path.join(repo_path, 'html')
        os.makedirs(html_repo_dir, exist_ok=True)
        for html_file in html_files:
            dest = os.path.join(html_repo_dir, os.path.basename(html_file))
            shutil.copy2(html_file, dest)
        
        # Copy index.html
        index_src = os.path.join(html_dir, 'index.html')
        if os.path.exists(index_src):
            shutil.copy2(index_src, os.path.join(html_repo_dir, 'index.html'))
        
        # Commit all files
        print(f"\nCommitting files to repository...")
        if self.git_manager.commit_files(repo_path, '.', 
                                         f'Add {len(patch_files)} patches and {len(html_files)} HTML files'):
            print(f"  ✓ Patches and HTML files committed to repository")
        else:
            print(f"  ℹ No changes to commit (files may already exist)")
        
        # Print summary
        print("\n" + "=" * 70)
        print("PRESERVATION COMPLETE")
        print("=" * 70)
        print(f"Total changes processed: {len(changes)}")
        print(f"Patches stored: {len(patch_files)}")
        print(f"HTML files generated: {len(html_files)}")
        print(f"\nGit repository: {repo_path}")
        print(f"Git branch: {branch_name}")
        print(f"Patches directory: {os.path.join(repo_path, 'patches')}")
        print(f"HTML directory: {os.path.join(repo_path, 'html')}")
        print(f"HTML index: {os.path.join(html_dir, 'index.html')}")
        print("=" * 70)
        
        return {
            'total_changes': len(changes),
            'patches_stored': len(patch_files),
            'html_files': len(html_files),
            'repo_path': repo_path,
            'branch_name': branch_name,
            'html_index': os.path.join(html_dir, 'index.html')
        }
