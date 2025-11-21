#!/usr/bin/env python3
"""
Demo script to test gerrit2git-archive with mock Gerrit server
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tests'))

from src.history_preserver import GerritHistoryPreserver
from tests.mock_gerrit_server import start_mock_server_background


def run_demo():
    """Run a complete demo of the tool"""
    print("=" * 70)
    print("GERRIT2GIT-ARCHIVE - DEMO")
    print("=" * 70)
    
    # Start mock server
    print("\n1. Starting mock Gerrit server...")
    try:
        start_mock_server_background(port=8765)
    except Exception as e:
        print(f"   Note: {e}")
    
    # Create temporary directories
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = os.path.join(tmpdir, 'output')
        repo_path = os.path.join(tmpdir, 'gerrit-history-repo')
        
        print(f"\n2. Setting up temporary directories...")
        print(f"   Output directory: {output_dir}")
        print(f"   Repository path: {repo_path}")
        
        # Initialize preserver
        print(f"\n3. Initializing Gerrit History Preserver...")
        preserver = GerritHistoryPreserver(
            gerrit_url='http://localhost:8765',
            verify_ssl=False
        )
        
        # Run preservation
        print(f"\n4. Running history preservation workflow...")
        try:
            result = preserver.preserve_history(
                output_dir=output_dir,
                repo_path=repo_path,
                query='status:merged',
                limit=10,
                branch_name='gerrit-history'
            )
            
            print(f"\n5. Exploring results...")
            
            # Check patches
            patches_in_output = list(Path(output_dir).glob('patches/*.patch'))
            patches_in_repo = list(Path(repo_path).glob('patches/*.patch'))
            print(f"   ✓ Patches in output dir: {len(patches_in_output)}")
            print(f"   ✓ Patches in git repo: {len(patches_in_repo)}")
            
            # Check HTML
            html_in_output = list(Path(output_dir).glob('html/*.html'))
            html_in_repo = list(Path(repo_path).glob('html/*.html'))
            print(f"   ✓ HTML files in output dir: {len(html_in_output)}")
            print(f"   ✓ HTML files in git repo: {len(html_in_repo)}")
            
            # Show index.html location
            index_path = os.path.join(output_dir, 'html', 'index.html')
            if os.path.exists(index_path):
                print(f"   ✓ HTML index created: {index_path}")
            
            # Show metadata
            metadata_path = os.path.join(output_dir, 'metadata', 'gerrit_export_metadata.json')
            if os.path.exists(metadata_path):
                file_size = os.path.getsize(metadata_path)
                print(f"   ✓ Metadata JSON created: {file_size} bytes")
            
            # Show sample patch content
            if patches_in_output:
                print(f"\n6. Sample patch file content:")
                print(f"   File: {patches_in_output[0].name}")
                with open(patches_in_output[0], 'r') as f:
                    lines = f.readlines()[:15]
                    for line in lines:
                        print(f"   {line.rstrip()}")
            
            # Show sample HTML snippet
            if html_in_output and len(html_in_output) > 1:
                # Get first non-index HTML file
                html_files = [f for f in html_in_output if f.name != 'index.html']
                if html_files:
                    print(f"\n7. Sample HTML file created:")
                    print(f"   File: {html_files[0].name}")
                    with open(html_files[0], 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'Change' in content and 'Project:' in content:
                            print(f"   ✓ Contains change metadata")
                        if 'Review' in content or 'Code-Review' in content:
                            print(f"   ✓ Contains review information")
            
            print("\n" + "=" * 70)
            print("DEMO COMPLETED SUCCESSFULLY!")
            print("=" * 70)
            print("\nNote: Files were created in temporary directory and have been cleaned up.")
            print("In real usage, files would be persisted to your specified locations.")
            
        except Exception as e:
            print(f"\n✗ Error during demo: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == '__main__':
    run_demo()
