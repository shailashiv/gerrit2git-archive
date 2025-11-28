#!/usr/bin/env python3
"""
Helper script to export Gerrit patches organized by owner and topic.

Usage:
    python export_by_owner_topic.py --gerrit-url https://gerrit.example.com \
                                    --owner "Sanyog Kale <skale@habana.ai>" \
                                    --output-dir ./organized-patches
"""

import argparse
import getpass
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.gerrit_api import GerritAPIClient
from src.html_generator import HTMLGenerator


def sanitize_name(name):
    """Convert name/email to safe folder name."""
    # Extract name from "Name <email>" format
    if '<' in name and '>' in name:
        name = name.split('<')[0].strip()
    # Replace special characters (including forward slashes)
    return "".join(c if c.isalnum() or c in ('-', '_', ' ') else '_' for c in name).strip().replace(' ', '_')


def export_by_owner_and_topic(gerrit_url, username, password, owner_query, topics_list, output_dir, 
                              verify_ssl=True, limit=5000):
    """
    Export patches organized by owner and topic.
    
    Args:
        gerrit_url: Gerrit server URL
        username: Gerrit username
        password: Gerrit password
        owner_query: Owner filter (e.g., "Sanyog Kale <skale@habana.ai>")
        topics_list: List of topics to filter (None = all topics)
        output_dir: Base output directory
        verify_ssl: Whether to verify SSL certificates
        limit: Maximum number of changes to fetch
    """
    # Create API client
    api_client = GerritAPIClient(gerrit_url, username, password, verify_ssl)
    
    # Build query: get all changes by owner (open, abandoned, or merged)
    query = f'owner:"{owner_query}"'
    
    # Add topic filter if topics list provided
    if topics_list:
        # Quote topics with special characters to avoid query parsing issues
        topic_query = " OR ".join([f'topic:"{topic}"' for topic in topics_list])
        query += f' AND ({topic_query})'
    
    print(f"Fetching changes from: {gerrit_url}")
    print(f"Owner: {owner_query}")
    if topics_list:
        print(f"Topics filter: {len(topics_list)} topics")
    print(f"Query: {query}")
    print(f"Limit: {limit}\n")
    
    # Fetch changes
    changes = api_client.get_changes(query, limit)
    print(f"Found {len(changes)} changes\n")
    
    if not changes:
        print("No changes found. Exiting.")
        return
    
    # Get owner folder name
    owner_name = sanitize_name(owner_query)
    owner_dir = os.path.join(output_dir, owner_name)
    
    # Organize by topic
    topics = {}
    no_topic = []
    
    for change in changes:
        topic = change.get('topic', None)
        if topic:
            if topic not in topics:
                topics[topic] = []
            topics[topic].append(change)
        else:
            no_topic.append(change)
    
    print(f"Organization:")
    print(f"  Topics found: {len(topics)}")
    print(f"  Changes without topic: {len(no_topic)}\n")
    
    # Export patches by topic
    total_exported = 0
    
    for topic, topic_changes in sorted(topics.items()):
        topic_dir = os.path.join(owner_dir, sanitize_name(topic))
        os.makedirs(topic_dir, exist_ok=True)
        
        print(f"Topic: {topic} ({len(topic_changes)} changes)")
        
        for change in topic_changes:
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
                
                # Get patch content
                patch_content = api_client.get_patch(change_number, current_revision)
                
                # Generate filename
                owner = change.get('owner', {})
                owner_username = owner.get('username', owner.get('name', 'unknown'))
                safe_owner = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in owner_username[:20])
                safe_subject = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in subject[:50])
                base_filename = f"{change_number:06d}-{safe_owner}-{safe_subject}"
                
                # Save patch
                patch_filename = f"{base_filename}.patch"
                patch_path = os.path.join(topic_dir, patch_filename)
                with open(patch_path, 'w', encoding='utf-8') as f:
                    f.write(patch_content)
                
                # Generate HTML
                html_content = HTMLGenerator.generate_change_html(
                    change_detail,
                    comments,
                    files,
                    patch_content
                )
                html_filename = f"{base_filename}.html"
                html_path = os.path.join(topic_dir, html_filename)
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                print(f"  ✓ #{change_number}: {subject[:60]}")
                total_exported += 1
                
            except Exception as e:
                print(f"  ✗ #{change_number}: Error - {e}")
        
        print()
    
    # Export changes without topic
    if no_topic:
        no_topic_dir = os.path.join(owner_dir, "_no_topic")
        os.makedirs(no_topic_dir, exist_ok=True)
        
        print(f"Changes without topic ({len(no_topic)} changes)")
        
        for change in no_topic:
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
                
                # Get patch content
                patch_content = api_client.get_patch(change_number, current_revision)
                
                # Generate filename
                owner = change.get('owner', {})
                owner_username = owner.get('username', owner.get('name', 'unknown'))
                safe_owner = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in owner_username[:20])
                safe_subject = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in subject[:50])
                base_filename = f"{change_number:06d}-{safe_owner}-{safe_subject}"
                
                # Save patch
                patch_filename = f"{base_filename}.patch"
                patch_path = os.path.join(no_topic_dir, patch_filename)
                with open(patch_path, 'w', encoding='utf-8') as f:
                    f.write(patch_content)
                
                # Generate HTML
                html_content = HTMLGenerator.generate_change_html(
                    change_detail,
                    comments,
                    files,
                    patch_content
                )
                html_filename = f"{base_filename}.html"
                html_path = os.path.join(no_topic_dir, html_filename)
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                print(f"  ✓ #{change_number}: {subject[:60]}")
                total_exported += 1
                
            except Exception as e:
                print(f"  ✗ #{change_number}: Error - {e}")
    
    # Generate index.html in owner folder
    print("\nGenerating index.html...")
    index_content = HTMLGenerator.generate_owner_index_html(
        owner_query,
        owner_name,
        changes,
        topics,
        no_topic
    )
    index_path = os.path.join(owner_dir, 'index.html')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_content)
    print(f"✓ Index page created: {index_path}")
    
    print("\n" + "=" * 70)
    print("EXPORT COMPLETE")
    print("=" * 70)
    print(f"Total changes exported: {total_exported}")
    print(f"Output directory: {os.path.abspath(output_dir)}")
    print(f"Owner folder: {owner_name}")
    print(f"Topics: {len(topics)}")
    print(f"Index page: {index_path}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description='Export Gerrit patches organized by owner and topic',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export all patches by owner (all topics)
  python export_by_owner_topic.py --gerrit-url https://gerrit.habana-labs.com \\
      --owner "Sanyog Kale <skale@habana.ai>" \\
      --output-dir ./organized-patches
  
  # Export patches for specific topics only
  python export_by_owner_topic.py --gerrit-url https://gerrit.habana-labs.com \\
      --owner "Sanyog Kale <skale@habana.ai>" \\
      --topics gt_infra eq_event_optz H9_PLDM_BACKDOOR_ICCM_LOAD \\
      --output-dir ./organized-patches
  
  # Export with topics from file
  python export_by_owner_topic.py --gerrit-url https://gerrit.habana-labs.com \\
      --username myuser \\
      --owner "Sanyog Kale <skale@habana.ai>" \\
      --topics-file topics.txt \\
      --output-dir ./organized-patches
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
        '--owner',
        required=True,
        help='Owner name and email (e.g., "John Doe <john@example.com>")'
    )
    parser.add_argument(
        '--topics',
        nargs='*',
        help='List of topics to filter (space-separated). If not provided, fetches all topics.'
    )
    parser.add_argument(
        '--topics-file',
        help='File containing topics (one per line)'
    )
    parser.add_argument(
        '--output-dir',
        default='./organized-patches',
        help='Output directory (default: ./organized-patches)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=5000,
        help='Maximum number of changes to fetch (default: 5000)'
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
    
    # Handle topics
    topics_list = None
    if args.topics:
        topics_list = args.topics
    elif args.topics_file:
        try:
            with open(args.topics_file, 'r') as f:
                topics_list = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"Error reading topics file: {e}", file=sys.stderr)
            sys.exit(1)
    
    try:
        export_by_owner_and_topic(
            gerrit_url=args.gerrit_url,
            username=args.username,
            password=password,
            owner_query=args.owner,
            topics_list=topics_list,
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
