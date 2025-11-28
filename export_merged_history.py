#!/usr/bin/env python3
"""
Script to export HTML documentation for merged changes across multiple projects.

Usage:
    python export_merged_history.py --gerrit-url https://gerrit.example.com \
                                    --output-dir ./merged-history
"""

import argparse
import getpass
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.gerrit_api import GerritAPIClient
from src.html_generator import HTMLGenerator


def export_merged_changes(gerrit_url, username, password, projects, output_dir, verify_ssl=True, limit=5000):
    """
    Export HTML documentation for merged changes across multiple projects.
    
    Args:
        gerrit_url: Gerrit server URL
        username: Gerrit username
        password: Gerrit password
        projects: List of project names
        output_dir: Base output directory
        verify_ssl: Whether to verify SSL certificates
        limit: Maximum number of changes to fetch per project
    """
    # Create API client
    api_client = GerritAPIClient(gerrit_url, username, password, verify_ssl)
    
    print(f"Fetching merged changes from: {gerrit_url}")
    print(f"Projects: {len(projects)}")
    print(f"Output directory: {output_dir}\n")
    
    # Create base output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Track all changes across projects
    all_changes_by_project = {}
    total_changes = 0
    
    # Fetch merged changes for each project
    for project in projects:
        query = f'project:{project} AND status:merged'
        
        print(f"Fetching: {project}...")
        try:
            changes = api_client.get_changes(query, limit)
            all_changes_by_project[project] = changes
            total_changes += len(changes)
            print(f"  Found {len(changes)} merged changes")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            all_changes_by_project[project] = []
        
    print(f"\nTotal merged changes found: {total_changes}\n")
    
    if total_changes == 0:
        print("No merged changes found. Exiting.")
        return
    
    # Export HTML for each project
    total_exported = 0
    
    for project, changes in all_changes_by_project.items():
        if not changes:
            continue
            
        # Create project directory
        project_safe = project.replace('/', '_')
        project_dir = os.path.join(output_dir, project_safe)
        os.makedirs(project_dir, exist_ok=True)
        
        print(f"\nExporting {project} ({len(changes)} changes)...")
        
        for change in changes:
            change_number = change['_number']
            subject = change['subject']
            current_revision = change.get('current_revision')
            
            if not current_revision:
                print(f"  ⚠ Skipping #{change_number}: No current revision")
                continue
            
            try:
                # Get detailed change info
                change_detail = api_client.get_change_detail(change_number)
                
                # Get comments and files
                comments = api_client.get_change_comments(change_number)
                files = api_client.get_change_files(change_number, current_revision)
                
                # Get patch content for diff display
                patch_content = api_client.get_patch(change_number, current_revision)
                
                # Generate filename
                owner = change.get('owner', {})
                owner_username = owner.get('username', owner.get('name', 'unknown'))
                safe_owner = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in owner_username[:20])
                safe_subject = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in subject[:50])
                base_filename = f"{change_number:06d}-{safe_owner}-{safe_subject}"
                
                # Generate HTML only (no patch file)
                html_content = HTMLGenerator.generate_change_html(
                    change_detail,
                    comments,
                    files,
                    patch_content
                )
                html_filename = f"{base_filename}.html"
                html_path = os.path.join(project_dir, html_filename)
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                print(f"  ✓ #{change_number}: {subject[:60]}")
                total_exported += 1
                
            except Exception as e:
                print(f"  ✗ #{change_number}: Error - {e}")
    
    # Generate master index.html
    print("\nGenerating merged_history.html...")
    index_content = generate_merged_index(gerrit_url, all_changes_by_project, total_changes)
    index_path = os.path.join(output_dir, 'merged_history.html')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_content)
    print(f"✓ Index page created: {index_path}")
    
    print("\n" + "=" * 70)
    print("EXPORT COMPLETE")
    print("=" * 70)
    print(f"Total changes exported: {total_exported}")
    print(f"Output directory: {os.path.abspath(output_dir)}")
    print(f"Projects: {len(all_changes_by_project)}")
    print(f"Index page: {index_path}")
    print("=" * 70)


def generate_merged_index(gerrit_url, all_changes_by_project, total_changes):
    """Generate index.html for merged changes."""
    import html
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Merged Changes History</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        
        h2 {{
            color: #444;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        
        .summary {{
            background-color: #e3f2fd;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        
        .summary-stats {{
            display: flex;
            gap: 30px;
            flex-wrap: wrap;
        }}
        
        .summary-stat {{
            flex: 1;
            min-width: 150px;
        }}
        
        .summary-stat .number {{
            font-size: 2em;
            font-weight: bold;
            color: #4CAF50;
        }}
        
        .summary-stat .label {{
            color: #666;
            font-size: 0.9em;
        }}
        
        .project-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .project-card {{
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            transition: all 0.3s ease;
        }}
        
        .project-card:hover {{
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            transform: translateY(-2px);
        }}
        
        .project-name {{
            font-size: 1.3em;
            font-weight: bold;
            color: #2196F3;
            margin-bottom: 10px;
        }}
        
        .project-stats {{
            color: #666;
            font-size: 0.9em;
            margin-top: 10px;
        }}
        
        .project-section {{
            margin-bottom: 40px;
        }}
        
        .changes-list {{
            list-style: none;
            padding: 0;
        }}
        
        .change-item {{
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
            transition: all 0.3s ease;
        }}
        
        .change-item:hover {{
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            transform: translateY(-2px);
        }}
        
        .change-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        
        .change-number {{
            background: #4CAF50;
            color: white;
            padding: 5px 12px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 0.9em;
        }}
        
        .change-content {{
            display: flex;
            align-items: center;
            gap: 20px;
        }}
        
        .change-subject {{
            font-size: 1.05em;
            font-weight: 600;
            color: #333;
            flex: 1;
        }}
        
        .change-subject a {{
            color: #2196F3;
            text-decoration: none;
        }}
        
        .change-subject a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 Merged Changes History</h1>
        <p>Complete archive of all merged changes across projects</p>
        
        <div class="summary">
            <h2>Summary</h2>
            <div class="summary-stats">
                <div class="summary-stat">
                    <div class="number">{total_changes}</div>
                    <div class="label">Total Merged Changes</div>
                </div>
                <div class="summary-stat">
                    <div class="number">{len([p for p, c in all_changes_by_project.items() if c])}</div>
                    <div class="label">Projects</div>
                </div>
            </div>
        </div>
        
        <h2>📦 Projects</h2>
        <div class="project-grid">
'''
    
    # Add project cards
    for project, changes in sorted(all_changes_by_project.items()):
        if not changes:
            continue
            
        project_safe = project.replace('/', '_')
        
        html_content += f'''
            <div class="project-card">
                <div class="project-name">📦 {html.escape(project)}</div>
                <div class="project-stats">
                    <div><strong>{len(changes)}</strong> merged changes</div>
                </div>
            </div>
'''
    
    html_content += '''
        </div>
        
        <h2>📋 All Changes by Project</h2>
'''
    
    # Add detailed list for each project
    for project, changes in sorted(all_changes_by_project.items()):
        if not changes:
            continue
            
        project_safe = project.replace('/', '_')
        
        html_content += f'''
        <div class="project-section">
            <h3>📦 {html.escape(project)} ({len(changes)} changes)</h3>
            <ul class="changes-list">
'''
        
        for change in changes:
            change_number = change['_number']
            subject = html.escape(change['subject'])
            owner = change.get('owner', {})
            owner_username = owner.get('username', owner.get('name', 'unknown'))
            safe_owner = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in owner_username[:20])
            safe_subject = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in change['subject'][:50])
            base_filename = f"{change_number:06d}-{safe_owner}-{safe_subject}"
            
            html_content += f'''
                <li class="change-item">
                    <div class="change-header">
                        <span class="change-number">#{change_number}</span>
                    </div>
                    <div class="change-content">
                        <div class="change-subject">
                            <a href="{project_safe}/{base_filename}.html">{subject}</a>
                        </div>
                    </div>
                </li>
'''
        
        html_content += '''
            </ul>
        </div>
'''
    
    html_content += '''
    </div>
</body>
</html>
'''
    
    return html_content


def main():
    parser = argparse.ArgumentParser(
        description='Export HTML documentation for merged changes across projects',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export merged changes for all projects
  python export_merged_history.py --gerrit-url https://gerrit.habana-labs.com \\
      --output-dir ./merged-history
  
  # With authentication
  python export_merged_history.py --gerrit-url https://gerrit.habana-labs.com \\
      --username myuser \\
      --output-dir ./merged-history
        """
    )
    
    parser.add_argument(
        '--gerrit-url',
        required=True,
        help='Gerrit server URL (e.g., https://gerrit.example.com)'
    )
    parser.add_argument(
        '--username',
        help='Gerrit username (for authenticated access)'
    )
    parser.add_argument(
        '--password',
        help='Gerrit HTTP password (prompted securely if not provided)'
    )
    parser.add_argument(
        '--output-dir',
        default='./merged-history',
        help='Output directory (default: ./merged-history)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=10000,
        help='Maximum number of changes to fetch per project (default: 10000)'
    )
    parser.add_argument(
        '--no-verify-ssl',
        action='store_true',
        help='Disable SSL certificate verification'
    )
    
    args = parser.parse_args()
    
    # Prompt for password if username provided but password not
    password = args.password
    if args.username and not password:
        password = getpass.getpass(f"Enter password for {args.username}: ")
    
    # List of projects
    projects = [
        'preboot',
        'buildroot-external',
        'fw_loader',
        'eeprom-util',
        'hl-smi',
        'embedded-specs',
        'arcboot',
        'arcpid',
        'arcmgmt',
        'arcevent',
        'zephyr',
        'soc_init',
        'preboot_rtos',
        'zephyr-plugins',
        'mbedtls',
        'eeprom',
        'boot_info',
        'emb-common-mods',
        'mctp',
        'pldm',
        'littlefs',
        'pcie-ss',
        'spdm',
        'libspdm',
        'boot_desc',
        'reset'
    ]
    
    try:
        export_merged_changes(
            gerrit_url=args.gerrit_url,
            username=args.username,
            password=password,
            projects=projects,
            output_dir=args.output_dir,
            verify_ssl=not args.no_verify_ssl,
            limit=args.limit
        )
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
