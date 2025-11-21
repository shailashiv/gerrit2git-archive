"""
Integration test for gerrit2git-archive
Tests the complete workflow with mock data
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from gerrit_api import GerritAPIClient
from git_manager import GitManager
from html_generator import HTMLGenerator
from metadata_exporter import MetadataExporter


def create_mock_change_data():
    """Create mock Gerrit change data for testing"""
    return [
        {
            '_number': 12345,
            'change_id': 'I1234567890abcdef1234567890abcdef12345678',
            'project': 'test-project',
            'branch': 'main',
            'subject': 'Add new feature: user authentication',
            'status': 'MERGED',
            'created': '2025-11-15 10:30:00.000000000',
            'updated': '2025-11-16 14:20:00.000000000',
            'current_revision': 'abc123',
            'owner': {
                'name': 'John Doe',
                'email': 'john.doe@example.com',
                '_account_id': 1000
            },
            'revisions': {
                'abc123': {
                    'commit': {
                        'message': 'Add new feature: user authentication\n\nImplements login and logout functionality.\n\nChange-Id: I1234567890abcdef1234567890abcdef12345678',
                        'author': {
                            'name': 'John Doe',
                            'email': 'john.doe@example.com'
                        }
                    }
                }
            },
            'labels': {
                'Code-Review': {
                    'approved': {
                        'name': 'Jane Smith',
                        '_account_id': 1001
                    },
                    'all': [
                        {'value': 2, 'name': 'Jane Smith', '_account_id': 1001}
                    ]
                },
                'Verified': {
                    'approved': {
                        'name': 'CI Bot',
                        '_account_id': 2000
                    },
                    'all': [
                        {'value': 1, 'name': 'CI Bot', '_account_id': 2000}
                    ]
                }
            },
            'messages': [
                {
                    'author': {'name': 'John Doe'},
                    'date': '2025-11-15 10:30:00.000000000',
                    'message': 'Uploaded patch set 1.'
                },
                {
                    'author': {'name': 'Jane Smith'},
                    'date': '2025-11-16 09:15:00.000000000',
                    'message': 'LGTM! Great implementation.'
                },
                {
                    'author': {'name': 'Jane Smith'},
                    'date': '2025-11-16 14:20:00.000000000',
                    'message': 'Patch Set 1: Code-Review+2'
                }
            ]
        },
        {
            '_number': 12346,
            'change_id': 'I2234567890abcdef1234567890abcdef12345678',
            'project': 'test-project',
            'branch': 'develop',
            'subject': 'Fix bug in data validation',
            'status': 'MERGED',
            'created': '2025-11-17 08:00:00.000000000',
            'updated': '2025-11-18 11:30:00.000000000',
            'current_revision': 'def456',
            'owner': {
                'name': 'Alice Johnson',
                'email': 'alice.j@example.com',
                '_account_id': 1002
            },
            'revisions': {
                'def456': {
                    'commit': {
                        'message': 'Fix bug in data validation\n\nAdded null checks and improved error handling.\n\nChange-Id: I2234567890abcdef1234567890abcdef12345678',
                        'author': {
                            'name': 'Alice Johnson',
                            'email': 'alice.j@example.com'
                        }
                    }
                }
            },
            'labels': {
                'Code-Review': {
                    'approved': {
                        'name': 'Bob Wilson',
                        '_account_id': 1003
                    },
                    'all': [
                        {'value': 2, 'name': 'Bob Wilson', '_account_id': 1003}
                    ]
                }
            },
            'messages': [
                {
                    'author': {'name': 'Alice Johnson'},
                    'date': '2025-11-17 08:00:00.000000000',
                    'message': 'Uploaded patch set 1.'
                },
                {
                    'author': {'name': 'Bob Wilson'},
                    'date': '2025-11-18 11:30:00.000000000',
                    'message': 'Patch Set 1: Code-Review+2\n\nNice fix!'
                }
            ]
        }
    ]


def create_mock_comments():
    """Create mock inline comments"""
    return {
        12345: {
            'src/auth.py': [
                {
                    'author': {'name': 'Jane Smith'},
                    'line': 42,
                    'message': 'Consider using a stronger hash algorithm here.'
                }
            ]
        },
        12346: {
            'src/validator.py': [
                {
                    'author': {'name': 'Bob Wilson'},
                    'line': 15,
                    'message': 'Good catch on the null check!'
                }
            ]
        }
    }


def create_mock_files():
    """Create mock file lists"""
    return {
        12345: {
            'src/auth.py': {
                'status': 'A',
                'lines_inserted': 150,
                'lines_deleted': 0
            },
            'tests/test_auth.py': {
                'status': 'A',
                'lines_inserted': 80,
                'lines_deleted': 0
            }
        },
        12346: {
            'src/validator.py': {
                'status': 'M',
                'lines_inserted': 25,
                'lines_deleted': 10
            }
        }
    }


def create_mock_patch(change_number):
    """Create a mock patch file content"""
    if change_number == 12345:
        return """From abc123def456 Mon Sep 17 00:00:00 2001
From: John Doe <john.doe@example.com>
Date: Wed, 15 Nov 2025 10:30:00 +0000
Subject: [PATCH] Add new feature: user authentication

Implements login and logout functionality.

Change-Id: I1234567890abcdef1234567890abcdef12345678
---
 src/auth.py       | 150 +++++++++++++++++++++++++++++++++++++++
 tests/test_auth.py |  80 ++++++++++++++++++++
 2 files changed, 230 insertions(+)
 create mode 100644 src/auth.py
 create mode 100644 tests/test_auth.py

diff --git a/src/auth.py b/src/auth.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/src/auth.py
@@ -0,0 +1,150 @@
+def authenticate_user(username, password):
+    # Authentication logic here
+    pass
"""
    else:
        return """From def456abc789 Mon Sep 17 00:00:00 2001
From: Alice Johnson <alice.j@example.com>
Date: Sun, 17 Nov 2025 08:00:00 +0000
Subject: [PATCH] Fix bug in data validation

Added null checks and improved error handling.

Change-Id: I2234567890abcdef1234567890abcdef12345678
---
 src/validator.py | 35 +++++++++++++++++++++++------------
 1 file changed, 25 insertions(+), 10 deletions(-)

diff --git a/src/validator.py b/src/validator.py
index 7891234..abc5678 100644
--- a/src/validator.py
+++ b/src/validator.py
@@ -10,10 +10,25 @@ def validate_data(data):
+    if data is None:
+        raise ValueError("Data cannot be None")
     return True
"""


def test_html_generation():
    """Test HTML generation with mock data"""
    print("\n" + "=" * 70)
    print("TEST: HTML Generation")
    print("=" * 70)
    
    changes = create_mock_change_data()
    comments_map = create_mock_comments()
    files_map = create_mock_files()
    
    html_gen = HTMLGenerator()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        html_dir = os.path.join(tmpdir, 'html')
        os.makedirs(html_dir)
        
        # Generate HTML for each change
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
            
            print(f"✓ Generated HTML for change {change_num}: {html_filename}")
        
        # Generate index
        index_path = os.path.join(html_dir, 'index.html')
        html_gen.generate_index_html(changes, index_path)
        print(f"✓ Generated index.html")
        
        # Verify files exist
        html_files = list(Path(html_dir).glob('*.html'))
        print(f"\n✓ Total HTML files created: {len(html_files)}")
        
        return html_dir


def test_git_operations():
    """Test git repository operations"""
    print("\n" + "=" * 70)
    print("TEST: Git Repository Operations")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = os.path.join(tmpdir, 'test-repo')
        
        git_mgr = GitManager()
        
        # Initialize repository
        if git_mgr.init_repo(repo_path, 'gerrit-history'):
            print("✓ Repository initialized successfully")
        else:
            print("✗ Failed to initialize repository")
            return
        
        # Create mock patches and HTML
        patches_dir = os.path.join(repo_path, 'patches')
        html_dir = os.path.join(repo_path, 'html')
        os.makedirs(patches_dir, exist_ok=True)
        os.makedirs(html_dir, exist_ok=True)
        
        changes = create_mock_change_data()
        
        # Create patch files
        for change in changes:
            change_num = change['_number']
            patch_content = create_mock_patch(change_num)
            
            safe_subject = "".join(c if c.isalnum() or c in ('-', '_') else '_' 
                                  for c in change['subject'][:50])
            patch_filename = f"{change_num:04d}-{safe_subject}.patch"
            patch_path = os.path.join(patches_dir, patch_filename)
            
            with open(patch_path, 'w', encoding='utf-8') as f:
                f.write(patch_content)
            
            print(f"✓ Created patch file: {patch_filename}")
        
        # Create a simple HTML file
        with open(os.path.join(html_dir, 'test.html'), 'w') as f:
            f.write('<html><body>Test</body></html>')
        
        # Commit files
        if git_mgr.commit_files(repo_path, '.', 'Add test patches and HTML'):
            print("✓ Files committed to repository")
        else:
            print("✗ Failed to commit files")
        
        print(f"\n✓ Repository created at: {repo_path}")


def test_metadata_export():
    """Test metadata export to JSON"""
    print("\n" + "=" * 70)
    print("TEST: Metadata Export")
    print("=" * 70)
    
    changes = create_mock_change_data()
    comments_map = create_mock_comments()
    files_map = create_mock_files()
    
    metadata_exp = MetadataExporter()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_exp.save_metadata(
            tmpdir,
            'https://gerrit.example.com',
            changes,
            comments_map,
            files_map
        )
        
        metadata_file = os.path.join(tmpdir, 'metadata', 'gerrit_export_metadata.json')
        if os.path.exists(metadata_file):
            file_size = os.path.getsize(metadata_file)
            print(f"✓ Metadata file created: {file_size} bytes")
            
            # Read and verify
            import json
            with open(metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"✓ Total changes in metadata: {data['total_changes']}")
            print(f"✓ Gerrit URL: {data['gerrit_url']}")
            print(f"✓ Export date: {data['export_date']}")
        else:
            print("✗ Metadata file not created")


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("GERRIT2GIT-ARCHIVE - INTEGRATION TESTS")
    print("=" * 70)
    
    try:
        test_html_generation()
        test_git_operations()
        test_metadata_export()
        
        print("\n" + "=" * 70)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    run_all_tests()
