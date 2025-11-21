#!/usr/bin/env python3
"""
Gerrit History Preservation - Main Entry Point
This script preserves Gerrit review history by:
1. Exporting patches and storing them as commits in a git branch
2. Generating HTML files with patch content and review comments
3. Creating an HTML index for browsing the preserved history
"""

import argparse
import getpass
import os
import sys
import traceback

# Handle both package and script execution
try:
    from .history_preserver import GerritHistoryPreserver
except ImportError:
    from history_preserver import GerritHistoryPreserver


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Preserve Gerrit review history by exporting patches to git and generating HTML',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preserve all merged changes
  python main.py --gerrit-url https://gerrit.example.com --query "status:merged" --repo-path ./gerrit-history
  
  # Preserve specific project history
  python main.py --gerrit-url https://gerrit.example.com --query "project:my-project" --repo-path ./my-project-history
  
  # Export without git repository (HTML and patches only)
  python main.py --gerrit-url https://gerrit.example.com --export-only
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
        help='Gerrit HTTP password (for authenticated access). If username is provided but password is not, you will be prompted securely.'
    )
    parser.add_argument(
        '--query',
        default='status:merged OR status:open',
        help='Gerrit query string (default: status:merged OR status:open)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=1000,
        help='Maximum number of changes to fetch (default: 1000)'
    )
    parser.add_argument(
        '--output-dir',
        default='./gerrit-export',
        help='Directory to save HTML and patch files (default: ./gerrit-export)'
    )
    parser.add_argument(
        '--repo-path',
        default='./gerrit-history-repo',
        help='Path to git repository for storing patches as commits (default: ./gerrit-history-repo)'
    )
    parser.add_argument(
        '--branch',
        default='gerrit-history',
        help='Git branch name for storing history (default: gerrit-history)'
    )
    parser.add_argument(
        '--export-only',
        action='store_true',
        help='Export patches and HTML only, do not create git repository'
    )
    parser.add_argument(
        '--no-verify-ssl',
        action='store_true',
        help='Disable SSL certificate verification'
    )
    
    args = parser.parse_args()
    
    # If username is provided but password is not, prompt for it securely
    password = args.password
    if args.username and not password:
        password = getpass.getpass(f"Enter password for {args.username}: ")
    
    # Create preserver instance
    preserver = GerritHistoryPreserver(
        gerrit_url=args.gerrit_url,
        username=args.username,
        password=password,
        verify_ssl=not args.no_verify_ssl
    )
    
    try:
        if args.export_only:
            # Export patches and HTML only (no git repository)
            print(f"Exporting from: {args.gerrit_url}")
            print(f"Export-only mode: No git repository will be created\n")
            
            result = preserver.export_changes_with_html(
                output_dir=args.output_dir,
                query=args.query,
                limit=args.limit
            )
            
            patch_files = result['patches']
            html_files = result['html']
            
            print(f"\nExported {len(patch_files)} patches to: {os.path.join(args.output_dir, 'patches')}")
            print(f"Exported {len(html_files)} HTML files to: {os.path.join(args.output_dir, 'html')}")
            print(f"\nOpen {os.path.join(args.output_dir, 'html', 'index.html')} in a browser to view all changes")
        else:
            # Full history preservation workflow
            result = preserver.preserve_history(
                output_dir=args.output_dir,
                repo_path=args.repo_path,
                query=args.query,
                limit=args.limit,
                branch_name=args.branch
            )
        
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
