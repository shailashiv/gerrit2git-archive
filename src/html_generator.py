#!/usr/bin/env python3
"""
HTML generation module for Gerrit changes.
Generates beautiful HTML pages for changes with review data.
"""

import html
import os
from typing import Dict, List


class HTMLGenerator:
    """Generate HTML documentation for Gerrit changes."""
    
    @staticmethod
    def generate_change_html(change: Dict, comments: Dict, files: Dict, patch_content: str = '') -> str:
        """
        Generate HTML representation of a Gerrit change.
        
        Args:
            change: Change object from Gerrit API
            comments: Comments dictionary
            files: Files dictionary
            patch_content: Patch file content with diffs (optional)
            
        Returns:
            HTML string
        """
        change_number = change['_number']
        subject = html.escape(change['subject'])
        project = html.escape(change['project'])
        branch = html.escape(change.get('branch', 'N/A'))
        status = html.escape(change['status'])
        owner = change.get('owner', {})
        owner_name = html.escape(owner.get('name', 'Unknown'))
        owner_email = html.escape(owner.get('email', 'N/A'))
        
        # Get timestamps
        created = change.get('created', '')
        updated = change.get('updated', '')
        
        # Get current revision info
        current_revision = change.get('current_revision', '')
        revisions = change.get('revisions', {})
        commit_msg = ''
        commit_author = ''
        
        if current_revision and current_revision in revisions:
            commit = revisions[current_revision].get('commit', {})
            commit_msg = html.escape(commit.get('message', ''))
            commit_author_info = commit.get('author', {})
            commit_author = html.escape(commit_author_info.get('name', 'Unknown'))
        
        # Get review labels
        labels_html = HTMLGenerator._generate_labels_html(change.get('labels', {}))
        
        # Get messages/review comments
        messages_html = HTMLGenerator._generate_messages_html(change.get('messages', []))
        
        # Get inline comments
        comments_html = HTMLGenerator._generate_comments_html(comments)
        
        # Get file list
        files_html = HTMLGenerator._generate_files_html(files)
        
        # Get diff HTML from patch content
        diff_html = HTMLGenerator._generate_diff_html(patch_content) if patch_content else ''
        
        # Generate complete HTML
        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Change {change_number}: {subject}</title>
    <style>
        {HTMLGenerator._get_css()}
    </style>
</head>
<body>
    <div class="container">
        <h1>Change {change_number}: {subject}</h1>
        
        <div class="metadata">
            <p><strong>Project:</strong> {project}</p>
            <p><strong>Branch:</strong> {branch}</p>
            <p><strong>Status:</strong> <span class="status {status.lower()}">{status}</span></p>
            <p><strong>Owner:</strong> {owner_name} &lt;{owner_email}&gt;</p>
            <p><strong>Created:</strong> {created}</p>
            <p><strong>Updated:</strong> {updated}</p>
        </div>
        
        <div class="commit-message">
            <h2>Commit Message</h2>
            <pre>{commit_msg}</pre>
        </div>
        
        {labels_html}
        
        {files_html}
        
        {diff_html}
        
        {messages_html}
        
        {comments_html}
    </div>
</body>
</html>'''
        
        return html_content
    
    @staticmethod
    def _generate_labels_html(labels: Dict) -> str:
        """Generate HTML for review labels."""
        if not labels:
            return ''
        
        labels_html = '<div class="labels"><h3>Review Labels</h3><ul>'
        for label_name, label_data in labels.items():
            approved = label_data.get('approved', {})
            rejected = label_data.get('rejected', {})
            
            if approved:
                labels_html += f'<li><strong>{html.escape(label_name)}</strong>: +2 by {html.escape(approved.get("name", "Unknown"))}</li>'
            elif rejected:
                labels_html += f'<li><strong>{html.escape(label_name)}</strong>: -2 by {html.escape(rejected.get("name", "Unknown"))}</li>'
            else:
                all_votes = label_data.get('all', [])
                if all_votes:
                    votes_str = ', '.join([f'{v.get("name", "Unknown")}: {v.get("value", 0):+d}' for v in all_votes])
                    labels_html += f'<li><strong>{html.escape(label_name)}</strong>: {html.escape(votes_str)}</li>'
        labels_html += '</ul></div>'
        
        return labels_html
    
    @staticmethod
    def _generate_messages_html(messages: List[Dict]) -> str:
        """Generate HTML for review messages."""
        if not messages:
            return ''
        
        messages_html = '<div class="messages"><h3>Review Messages</h3>'
        for msg in messages:
            author_info = msg.get('author', {})
            msg_author = html.escape(author_info.get('name', 'Unknown'))
            msg_date = msg.get('date', '')
            msg_text = html.escape(msg.get('message', ''))
            messages_html += f'<div class="message"><strong>{msg_author}</strong> <span class="date">({msg_date})</span><pre>{msg_text}</pre></div>'
        messages_html += '</div>'
        
        return messages_html
    
    @staticmethod
    def _generate_comments_html(comments: Dict) -> str:
        """Generate HTML for inline comments."""
        if not comments:
            return ''
        
        comments_html = '<div class="inline-comments"><h3>Inline Comments</h3>'
        for file_path, file_comments in comments.items():
            if file_comments:
                comments_html += f'<div class="file-comments"><h4>{html.escape(file_path)}</h4><ul>'
                for comment in file_comments:
                    comment_author = html.escape(comment.get('author', {}).get('name', 'Unknown'))
                    comment_msg = html.escape(comment.get('message', ''))
                    comment_line = comment.get('line', 'N/A')
                    comments_html += f'<li><strong>{comment_author}</strong> (Line {comment_line}): {comment_msg}</li>'
                comments_html += '</ul></div>'
        comments_html += '</div>'
        
        return comments_html
    
    @staticmethod
    def _generate_files_html(files: Dict) -> str:
        """Generate HTML for modified files list."""
        files_html = '<div class="files"><h3>Modified Files</h3><ul>'
        for file_path, file_info in files.items():
            if file_path == '/COMMIT_MSG':
                continue
            status_char = file_info.get('status', 'M')
            lines_inserted = file_info.get('lines_inserted', 0)
            lines_deleted = file_info.get('lines_deleted', 0)
            files_html += f'<li><code>{html.escape(file_path)}</code> ({status_char}) +{lines_inserted} -{lines_deleted}</li>'
        files_html += '</ul></div>'
        
        return files_html
    
    @staticmethod
    def _generate_diff_html(patch_content: str) -> str:
        """Generate HTML for diff/patch content."""
        if not patch_content:
            return ''
        
        diff_html = '<div class="diff-section"><h3>Code Changes (Diff)</h3>'
        
        # Split patch into lines
        lines = patch_content.split('\n')
        current_file = None
        in_diff = False
        
        for line in lines:
            # File header
            if line.startswith('diff --git'):
                if current_file:
                    diff_html += '</pre></div>'  # Close previous file
                in_diff = True
                diff_html += '<div class="diff-file">'
            elif line.startswith('---') or line.startswith('+++'):
                if line.startswith('+++'):
                    # Extract filename
                    filename = line[4:].split('\t')[0].strip()
                    if filename != '/dev/null':
                        current_file = filename
                        diff_html += f'<h4 class="diff-filename">{html.escape(filename)}</h4>'
                        diff_html += '<pre class="diff-content">'
            elif line.startswith('@@'):
                # Hunk header
                diff_html += f'<span class="diff-hunk">{html.escape(line)}</span>\n'
            elif line.startswith('+') and not line.startswith('+++'):
                # Added line
                diff_html += f'<span class="diff-add">{html.escape(line)}</span>\n'
            elif line.startswith('-') and not line.startswith('---'):
                # Deleted line
                diff_html += f'<span class="diff-del">{html.escape(line)}</span>\n'
            elif in_diff and current_file and not line.startswith('diff'):
                # Context line
                diff_html += f'<span class="diff-ctx">{html.escape(line)}</span>\n'
        
        # Close last file
        if current_file:
            diff_html += '</pre></div>'
        
        diff_html += '</div>'
        return diff_html
    
    @staticmethod
    def _get_css() -> str:
        """Return CSS styles for HTML pages."""
        return '''body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }
        h2, h3 {
            color: #555;
        }
        .metadata {
            background-color: #f9f9f9;
            padding: 15px;
            border-left: 4px solid #4CAF50;
            margin: 20px 0;
        }
        .metadata p {
            margin: 5px 0;
        }
        .status {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 4px;
            font-weight: bold;
            text-transform: uppercase;
        }
        .status.merged {
            background-color: #4CAF50;
            color: white;
        }
        .status.new, .status.open {
            background-color: #2196F3;
            color: white;
        }
        .status.abandoned {
            background-color: #f44336;
            color: white;
        }
        pre {
            background-color: #f4f4f4;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        code {
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
        .labels, .messages, .inline-comments, .files {
            margin: 30px 0;
        }
        .diff-section {
            margin: 30px 0;
        }
        .diff-file {
            margin: 20px 0;
            border: 1px solid #ddd;
            border-radius: 4px;
            overflow: hidden;
        }
        .diff-filename {
            background-color: #f6f8fa;
            padding: 10px 15px;
            margin: 0;
            border-bottom: 1px solid #ddd;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            color: #24292e;
        }
        .diff-content {
            background-color: #fff;
            padding: 0;
            margin: 0;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.4;
        }
        .diff-content span {
            display: block;
            padding: 0 10px;
            white-space: pre;
        }
        .diff-hunk {
            background-color: #f1f8ff;
            color: #0366d6;
            font-weight: bold;
        }
        .diff-add {
            background-color: #e6ffed;
            color: #22863a;
        }
        .diff-del {
            background-color: #ffeef0;
            color: #cb2431;
        }
        .diff-ctx {
            color: #24292e;
        }
        .message {
            background-color: #f9f9f9;
            padding: 15px;
            margin: 10px 0;
            border-left: 3px solid #2196F3;
        }
        .date {
            color: #888;
            font-size: 0.9em;
        }
        ul {
            padding-left: 20px;
        }
        li {
            margin: 8px 0;
        }
        .file-comments {
            margin: 15px 0;
            padding: 10px;
            background-color: #fff3cd;
            border-radius: 4px;
        }'''
    
    @staticmethod
    def generate_index_html(changes: List[Dict], output_path: str):
        """
        Generate an index.html file listing all changes.
        
        Args:
            changes: List of change objects
            output_path: Full path where index.html should be saved
        """
        index_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gerrit Changes Index</title>
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
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        a {{
            color: #2196F3;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .status {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 0.9em;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .status.merged {{
            background-color: #4CAF50;
            color: white;
        }}
        .status.new, .status.open {{
            background-color: #2196F3;
            color: white;
        }}
        .status.abandoned {{
            background-color: #f44336;
            color: white;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Gerrit Changes Export</h1>
        <p>Total changes: {len(changes)}</p>
        <table>
            <thead>
                <tr>
                    <th>Change #</th>
                    <th>Subject</th>
                    <th>Project</th>
                    <th>Status</th>
                    <th>Owner</th>
                    <th>Updated</th>
                    <th>Patch</th>
                </tr>
            </thead>
            <tbody>'''
        
        for change in changes:
            change_number = change['_number']
            subject = html.escape(change['subject'])
            project = html.escape(change['project'])
            status = html.escape(change['status'])
            owner = change.get('owner', {})
            owner_name = html.escape(owner.get('name', 'Unknown'))
            updated = change.get('updated', '')
            
            # Generate filename with username to match actual file
            owner_username = owner.get('username', owner.get('name', 'unknown'))
            safe_owner = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in owner_username[:20])
            safe_subject = "".join(c if c.isalnum() or c in ('-', '_') else '_' 
                                  for c in change['subject'][:50])
            html_filename = f"{change_number:04d}-{safe_owner}-{safe_subject}.html"
            patch_filename = f"{change_number:04d}-{safe_owner}.patch"
            
            index_html += f'''<tr>
                    <td><a href="{html_filename}">{change_number}</a></td>
                    <td><a href="{html_filename}">{subject}</a></td>
                    <td>{project}</td>
                    <td><span class="status {status.lower()}">{status}</span></td>
                    <td>{owner_name}</td>
                    <td>{updated}</td>
                    <td><a href="../patches/{patch_filename}" download>{change_number}-{safe_owner}.patch</a></td>
                </tr>'''
        
        index_html += '''</tbody>
        </table>
    </div>
</body>
</html>'''
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(index_html)
        
        print(f"\nIndex file created: {output_path}")
    
    @staticmethod
    def generate_readme_md(changes: List[Dict], output_path: str, gerrit_url: str = '', 
                          github_repo: str = '', branch: str = 'gerrit-history'):
        """
        Generate a README.md file with links to all changes.
        
        Args:
            changes: List of change objects
            output_path: Full path where README.md should be saved
            gerrit_url: Original Gerrit server URL
            github_repo: GitHub repository URL (for GitHub Pages links)
            branch: Git branch name
        """
        readme_md = f'''# Gerrit Change History

This repository contains archived Gerrit review history exported as patches and HTML documentation.

'''
        
        if gerrit_url:
            readme_md += f'''**Original Gerrit Server:** {gerrit_url}

'''
        
        readme_md += f'''**Total Changes:** {len(changes)}

## View Changes

📄 **[Browse All Changes (index.html)](html/index.html)**
'''
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(readme_md)
        
        print(f"README.md created: {output_path}")


    @staticmethod
    def generate_owner_index_html(owner_query: str, owner_name: str, changes: List[Dict], 
                                   topics: Dict[str, List[Dict]], no_topic: List[Dict]) -> str:
        """
        Generate index.html for owner's folder organized by topics.
        
        Args:
            owner_query: Owner query string
            owner_name: Sanitized owner folder name
            changes: All changes
            topics: Dictionary of topic -> changes list
            no_topic: List of changes without topics
            
        Returns:
            HTML string
        """
        total_changes = len(changes)
        
        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Patches by {html.escape(owner_query)}</title>
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
        
        .topic-section {{
            margin-bottom: 40px;
        }}
        
        .topic-header {{
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px 20px;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .topic-name {{
            font-size: 1.3em;
            font-weight: bold;
            color: #2196F3;
        }}
        
        .topic-count {{
            background-color: #4CAF50;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
        }}
        
        .changes-list {{
            list-style: none;
            padding: 0;
        }}
        
        .change-item {{
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
            transition: all 0.3s ease;
        }}
        
        .change-item:hover {{
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            transform: translateY(-2px);
        }}
        
        .change-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 10px;
        }}
        
        .change-number {{
            background: #2196F3;
            color: white;
            padding: 5px 12px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 0.9em;
        }}
        
        .change-subject {{
            font-size: 1.1em;
            font-weight: 600;
            color: #333;
            margin: 10px 0;
            flex: 1;
        }}
        
        .change-content {{
            display: flex;
            align-items: center;
            gap: 20px;
            margin-top: 10px;
        }}
        
        .change-links {{
            display: flex;
            gap: 10px;
            flex-shrink: 0;
        }}
        
        .btn {{
            display: inline-block;
            padding: 8px 20px;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 500;
            transition: all 0.3s ease;
            font-size: 0.9em;
        }}
        
        .btn-primary {{
            background: #2196F3;
            color: white;
        }}
        
        .btn-primary:hover {{
            background: #1976D2;
        }}
        
        .btn-secondary {{
            background: #6c757d;
            color: white;
        }}
        
        .btn-secondary:hover {{
            background: #5a6268;
        }}
        
        .status {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        
        .status-merged {{
            background: #4CAF50;
            color: white;
        }}
        
        .status-new, .status-open {{
            background: #2196F3;
            color: white;
        }}
        
        .status-abandoned {{
            background: #6c757d;
            color: white;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>👤 Patches by {html.escape(owner_query)}</h1>
        <p>Organized by Topic</p>
        
        <div class="summary">
            <h2>Summary</h2>
            <div class="summary-stats">
                <div class="summary-stat">
                    <div class="number">{total_changes}</div>
                    <div class="label">Total Changes</div>
                </div>
                <div class="summary-stat">
                    <div class="number">{len(topics)}</div>
                    <div class="label">Topics</div>
                </div>
                <div class="summary-stat">
                    <div class="number">{len(no_topic)}</div>
                    <div class="label">Without Topic</div>
                </div>
            </div>
        </div>
        
        <h2>📁 Topics</h2>
'''
        
        # Add topics
        for topic, topic_changes in sorted(topics.items()):
            topic_folder = HTMLGenerator._sanitize_filename(topic)
            html_content += f'''
            <div class="topic-section">
                <div class="topic-header">
                    <div class="topic-name">📁 {html.escape(topic)}</div>
                    <div class="topic-count">{len(topic_changes)} changes</div>
                </div>
                <ul class="changes-list">
'''
            
            for change in topic_changes:
                change_number = change['_number']
                subject = html.escape(change['subject'])
                status = change.get('status', 'UNKNOWN')
                owner = change.get('owner', {})
                owner_username = owner.get('username', owner.get('name', 'unknown'))
                safe_owner = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in owner_username[:20])
                safe_subject = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in change['subject'][:50])
                base_filename = f"{change_number:06d}-{safe_owner}-{safe_subject}"
                
                status_class = f"status-{status.lower()}"
                
                html_content += f'''
                    <li class="change-item">
                        <div class="change-header">
                            <span class="change-number">#{change_number}</span>
                            <span class="status {status_class}">{status}</span>
                        </div>
                        <div class="change-content">
                            <div class="change-subject">{subject}</div>
                            <div class="change-links">
                                <a href="{topic_folder}/{base_filename}.html" class="btn btn-primary">📄 View Details</a>
                                <a href="{topic_folder}/{base_filename}.patch" class="btn btn-secondary">⬇️ Download Patch</a>
                            </div>
                        </div>
                    </li>
'''
            
            html_content += '''
                </ul>
            </div>
'''
        
        # Add no-topic section
        if no_topic:
            html_content += f'''
            <div class="topic-section">
                <div class="topic-header">
                    <div class="topic-name">📁 _no_topic</div>
                    <div class="topic-count">{len(no_topic)} changes</div>
                </div>
                <ul class="changes-list">
'''
            
            for change in no_topic:
                change_number = change['_number']
                subject = html.escape(change['subject'])
                status = change.get('status', 'UNKNOWN')
                owner = change.get('owner', {})
                owner_username = owner.get('username', owner.get('name', 'unknown'))
                safe_owner = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in owner_username[:20])
                safe_subject = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in change['subject'][:50])
                base_filename = f"{change_number:06d}-{safe_owner}-{safe_subject}"
                
                status_class = f"status-{status.lower()}"
                
                html_content += f'''
                    <li class="change-item">
                        <div class="change-header">
                            <span class="change-number">#{change_number}</span>
                            <span class="status {status_class}">{status}</span>
                        </div>
                        <div class="change-content">
                            <div class="change-subject">{subject}</div>
                            <div class="change-links">
                                <a href="_no_topic/{base_filename}.html" class="btn btn-primary">📄 View Details</a>
                                <a href="_no_topic/{base_filename}.patch" class="btn btn-secondary">⬇️ Download Patch</a>
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
    </div>
</body>
</html>
'''
        
        return html_content
    
    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """Sanitize a string for use as a filename."""
        return "".join(c if c.isalnum() or c in ('-', '_', ' ') else '_' for c in name).strip().replace(' ', '_')


