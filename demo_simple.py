#!/usr/bin/env python3
"""
Simplified demo - tests core functionality without HTTP server
"""

import os
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.html_generator import HTMLGenerator
from src.git_manager import GitManager
from src.metadata_exporter import MetadataExporter


def create_sample_data():
    """Create sample Gerrit data"""
    changes = [
        {
            '_number': 12345,
            'change_id': 'I1234567890abcdef',
            'project': 'my-awesome-project',
            'branch': 'main',
            'subject': 'Add user authentication feature',
            'status': 'MERGED',
            'created': '2025-11-15 10:30:00',
            'updated': '2025-11-16 14:20:00',
            'current_revision': 'abc123',
            'owner': {
                'name': 'John Doe',
                'email': 'john@example.com'
            },
            'revisions': {
                'abc123': {
                    'commit': {
                        'message': 'Add user authentication\n\nImplements login/logout',
                        'author': {'name': 'John Doe', 'email': 'john@example.com'}
                    }
                }
            },
            'labels': {
                'Code-Review': {
                    'approved': {'name': 'Jane Smith'},
                    'all': [{'value': 2, 'name': 'Jane Smith'}]
                }
            },
            'messages': [
                {'author': {'name': 'John Doe'}, 'date': '2025-11-15 10:30:00', 'message': 'Uploaded patch'},
                {'author': {'name': 'Jane Smith'}, 'date': '2025-11-16 14:20:00', 'message': 'LGTM!'}
            ]
        },
        {
            '_number': 12346,
            'change_id': 'I2234567890abcdef',
            'project': 'my-awesome-project',
            'branch': 'develop',
            'subject': 'Fix validation bug',
            'status': 'MERGED',
            'created': '2025-11-17 08:00:00',
            'updated': '2025-11-18 11:30:00',
            'current_revision': 'def456',
            'owner': {
                'name': 'Alice Johnson',
                'email': 'alice@example.com'
            },
            'revisions': {
                'def456': {
                    'commit': {
                        'message': 'Fix validation bug\n\nAdded null checks',
                        'author': {'name': 'Alice Johnson', 'email': 'alice@example.com'}
                    }
                }
            },
            'labels': {
                'Code-Review': {
                    'approved': {'name': 'Bob Wilson'},
                    'all': [{'value': 2, 'name': 'Bob Wilson'}]
                }
            },
            'messages': [
                {'author': {'name': 'Alice Johnson'}, 'date': '2025-11-17 08:00:00', 'message': 'Uploaded patch'},
                {'author': {'name': 'Bob Wilson'}, 'date': '2025-11-18 11:30:00', 'message': 'Nice fix!'}
            ]
        }
    ]
    
    comments = {
        12345: {
            'src/auth.py': [
                {'author': {'name': 'Jane Smith'}, 'line': 42, 'message': 'Good implementation'}
            ]
        },
        12346: {
            'src/validator.py': [
                {'author': {'name': 'Bob Wilson'}, 'line': 15, 'message': 'Great catch!'}
            ]
        }
    }
    
    files = {
        12345: {
            'src/auth.py': {'status': 'A', 'lines_inserted': 150, 'lines_deleted': 0},
            'tests/test_auth.py': {'status': 'A', 'lines_inserted': 80, 'lines_deleted': 0}
        },
        12346: {
            'src/validator.py': {'status': 'M', 'lines_inserted': 25, 'lines_deleted': 10}
        }
    }
    
    return changes, comments, files


def demo_workflow():
    """Demonstrate the complete workflow"""
    print("=" * 70)
    print("GERRIT2GIT-ARCHIVE - SIMPLE DEMO")
    print("=" * 70)
    
    # Get sample data
    changes, comments_map, files_map = create_sample_data()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"\n📁 Working directory: {tmpdir}")
        
        # Setup directories
        repo_path = os.path.join(tmpdir, 'gerrit-history')
        output_dir = os.path.join(tmpdir, 'output')
        patches_dir = os.path.join(output_dir, 'patches')
        html_dir = os.path.join(output_dir, 'html')
        
        os.makedirs(patches_dir, exist_ok=True)
        os.makedirs(html_dir, exist_ok=True)
        
        # Step 1: Initialize Git Repository
        print("\n" + "-" * 70)
        print("STEP 1: Initialize Git Repository")
        print("-" * 70)
        
        git_mgr = GitManager()
        if git_mgr.init_repo(repo_path, 'gerrit-history'):
            print("✓ Git repository initialized")
            print(f"  Location: {repo_path}")
        
        # Step 2: Generate HTML Files
        print("\n" + "-" * 70)
        print("STEP 2: Generate HTML Files")
        print("-" * 70)
        
        html_gen = HTMLGenerator()
        html_files = []
        
        for change in changes:
            change_num = change['_number']
            comments = comments_map.get(change_num, {})
            files = files_map.get(change_num, {})
            
            html_content = html_gen.generate_change_html(change, comments, files)
            
            safe_subject = "".join(c if c.isalnum() or c in ('-', '_') else '_' 
                                  for c in change['subject'][:50])
            html_filename = f"{change_num:04d}-{safe_subject}.html"
            html_path = os.path.join(html_dir, html_filename)
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            html_files.append(html_path)
            print(f"✓ Generated: {html_filename}")
        
        # Generate index
        index_path = os.path.join(html_dir, 'index.html')
        html_gen.generate_index_html(changes, index_path)
        print(f"✓ Generated: index.html")
        
        # Step 3: Create Patch Files
        print("\n" + "-" * 70)
        print("STEP 3: Create Patch Files")
        print("-" * 70)
        
        patch_files = []
        for change in changes:
            change_num = change['_number']
            safe_subject = "".join(c if c.isalnum() or c in ('-', '_') else '_' 
                                  for c in change['subject'][:50])
            patch_filename = f"{change_num:04d}-{safe_subject}.patch"
            patch_path = os.path.join(patches_dir, patch_filename)
            
            # Create sample patch content
            patch_content = f"""From {change['current_revision']} Mon Sep 17 00:00:00 2001
From: {change['owner']['name']} <{change['owner']['email']}>
Date: {change['created']}
Subject: [PATCH] {change['subject']}

{change['revisions'][change['current_revision']]['commit']['message']}
---
"""
            for file_path in files_map[change_num].keys():
                file_info = files_map[change_num][file_path]
                patch_content += f" {file_path} | {file_info['lines_inserted']} ++, {file_info['lines_deleted']} --\n"
            
            with open(patch_path, 'w', encoding='utf-8') as f:
                f.write(patch_content)
            
            patch_files.append(patch_path)
            print(f"✓ Created: {patch_filename}")
        
        # Step 4: Copy to Git Repository
        print("\n" + "-" * 70)
        print("STEP 4: Copy Files to Git Repository")
        print("-" * 70)
        
        import shutil
        
        # Copy patches
        repo_patches_dir = os.path.join(repo_path, 'patches')
        os.makedirs(repo_patches_dir, exist_ok=True)
        for patch_file in patch_files:
            dest = os.path.join(repo_patches_dir, os.path.basename(patch_file))
            shutil.copy2(patch_file, dest)
        print(f"✓ Copied {len(patch_files)} patches to repository")
        
        # Copy HTML
        repo_html_dir = os.path.join(repo_path, 'html')
        os.makedirs(repo_html_dir, exist_ok=True)
        for html_file in html_files:
            dest = os.path.join(repo_html_dir, os.path.basename(html_file))
            shutil.copy2(html_file, dest)
        shutil.copy2(index_path, os.path.join(repo_html_dir, 'index.html'))
        print(f"✓ Copied {len(html_files)} HTML files to repository")
        
        # Step 5: Commit to Git
        print("\n" + "-" * 70)
        print("STEP 5: Commit Files to Git")
        print("-" * 70)
        
        if git_mgr.commit_files(repo_path, '.', f'Add {len(changes)} Gerrit changes'):
            print(f"✓ Committed {len(patch_files)} patches and {len(html_files)} HTML files")
        
        # Step 6: Export Metadata
        print("\n" + "-" * 70)
        print("STEP 6: Export Metadata")
        print("-" * 70)
        
        metadata_exp = MetadataExporter()
        metadata_exp.save_metadata(
            output_dir,
            'https://gerrit.example.com',
            changes,
            comments_map,
            files_map
        )
        
        metadata_file = os.path.join(output_dir, 'metadata', 'gerrit_export_metadata.json')
        if os.path.exists(metadata_file):
            size = os.path.getsize(metadata_file)
            print(f"✓ Metadata exported ({size} bytes)")
        
        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"✓ Changes processed: {len(changes)}")
        print(f"✓ Patches created: {len(patch_files)}")
        print(f"✓ HTML files created: {len(html_files)}")
        print(f"✓ Git repository: {repo_path}")
        print(f"\n📂 Files structure:")
        print(f"   {repo_path}/")
        print(f"   ├── patches/ ({len(list(Path(repo_patches_dir).glob('*.patch')))} files)")
        print(f"   └── html/ ({len(list(Path(repo_html_dir).glob('*.html')))} files)")
        
        # Show sample files
        print(f"\n📄 Sample patch file:")
        sample_patch = patch_files[0]
        with open(sample_patch, 'r') as f:
            lines = f.readlines()[:10]
            for line in lines:
                print(f"   {line.rstrip()}")
        
        print("\n" + "=" * 70)
        print("✓ DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("\nNote: Files created in temp directory (will be cleaned up)")
        print("In production, specify your own output paths.")


if __name__ == '__main__':
    try:
        demo_workflow()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
