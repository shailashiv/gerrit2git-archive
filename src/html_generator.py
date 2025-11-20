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
    def generate_change_html(change: Dict, comments: Dict, files: Dict) -> str:
        """
        Generate HTML representation of a Gerrit change.
        
        Args:
            change: Change object from Gerrit API
            comments: Comments dictionary
            files: Files dictionary
            
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
            
            safe_subject = "".join(c if c.isalnum() or c in ('-', '_') else '_' 
                                  for c in change['subject'][:50])
            html_filename = f"{change_number:04d}-{safe_subject}.html"
            
            index_html += f'''<tr>
                    <td><a href="{html_filename}">{change_number}</a></td>
                    <td><a href="{html_filename}">{subject}</a></td>
                    <td>{project}</td>
                    <td><span class="status {status.lower()}">{status}</span></td>
                    <td>{owner_name}</td>
                    <td>{updated}</td>
                </tr>'''
        
        index_html += '''</tbody>
        </table>
    </div>
</body>
</html>'''
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(index_html)
        
        print(f"\nIndex file created: {output_path}")
