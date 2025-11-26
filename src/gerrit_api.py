#!/usr/bin/env python3
"""
Gerrit REST API client module.
Handles all interactions with the Gerrit REST API.
"""

import json
import requests
from typing import Dict, List, Optional
from urllib.parse import urljoin


class GerritAPIClient:
    """Client for interacting with Gerrit REST API."""
    
    def __init__(self, gerrit_url: str, username: Optional[str] = None, 
                 password: Optional[str] = None, verify_ssl: bool = True):
        """
        Initialize Gerrit API client.
        
        Args:
            gerrit_url: Base URL of Gerrit instance (e.g., https://gerrit.example.com)
            username: Gerrit username (optional, for authenticated access)
            password: Gerrit HTTP password (optional, for authenticated access)
            verify_ssl: Whether to verify SSL certificates
        """
        self.gerrit_url = gerrit_url.rstrip('/')
        self.auth = (username, password) if username and password else None
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        if not verify_ssl:
            requests.packages.urllib3.disable_warnings()
    
    def _make_request(self, endpoint: str) -> Dict:
        """
        Make a request to Gerrit REST API.
        
        Args:
            endpoint: API endpoint (e.g., '/changes/')
            
        Returns:
            Parsed JSON response
        """
        url = urljoin(self.gerrit_url + '/', endpoint.lstrip('/'))
        response = self.session.get(url, auth=self.auth, verify=self.verify_ssl)
        response.raise_for_status()
        
        # Gerrit prepends ")]}'" to JSON responses for security
        content = response.text
        if content.startswith(")]}'"):
            content = content[4:]
        
        return json.loads(content)
    
    def get_changes(self, query: str = "status:open", limit: int = 100) -> List[Dict]:
        """
        Query Gerrit changes with automatic pagination support.
        
        Args:
            query: Gerrit query string (e.g., "status:open", "project:my-project")
            limit: Maximum number of changes to fetch (will paginate if > 500)
            
        Returns:
            List of change objects
        """
        all_changes = []
        start = 0
        batch_size = 500  # Gerrit's maximum per request
        
        while len(all_changes) < limit:
            # Calculate how many to fetch in this batch
            remaining = limit - len(all_changes)
            current_batch_size = min(batch_size, remaining)
            
            endpoint = f'/a/changes/?q={query}&n={current_batch_size}&S={start}&o=CURRENT_REVISION&o=CURRENT_COMMIT&o=DETAILED_ACCOUNTS&o=MESSAGES&o=DETAILED_LABELS'
            
            try:
                batch = self._make_request(endpoint)
                
                if not batch:
                    # No more results
                    break
                
                all_changes.extend(batch)
                
                # Check if there are more changes
                # Gerrit includes _more_changes: true in the last item if there are more results
                if len(batch) < current_batch_size:
                    # Got fewer results than requested, no more changes available
                    break
                
                # Check the _more_changes flag (it's on the last change object)
                if batch and isinstance(batch[-1], dict) and not batch[-1].get('_more_changes', False):
                    # No more changes available
                    break
                
                # Move to next batch
                start += len(batch)
                
                print(f"  Fetched {len(all_changes)} changes so far...")
                
            except Exception as e:
                print(f"  Warning: Error fetching batch at offset {start}: {e}")
                break
        
        return all_changes[:limit]  # Ensure we don't exceed the requested limit
    
    def get_change_detail(self, change_id: str) -> Dict:
        """
        Get detailed information about a change including reviews and comments.
        
        Args:
            change_id: Change ID or change number
            
        Returns:
            Detailed change object
        """
        endpoint = f'/a/changes/{change_id}/detail?o=CURRENT_REVISION&o=CURRENT_COMMIT&o=MESSAGES&o=DETAILED_LABELS&o=DETAILED_ACCOUNTS&o=REVIEWER_UPDATES'
        return self._make_request(endpoint)
    
    def get_change_comments(self, change_id: str) -> Dict:
        """
        Get all comments for a change.
        
        Args:
            change_id: Change ID or change number
            
        Returns:
            Dictionary of comments organized by file path
        """
        endpoint = f'/a/changes/{change_id}/comments'
        return self._make_request(endpoint)
    
    def get_change_files(self, change_id: str, revision_id: str = 'current') -> Dict:
        """
        Get list of files modified in a change.
        
        Args:
            change_id: Change ID or change number
            revision_id: Revision ID (default: 'current')
            
        Returns:
            Dictionary of files with their metadata
        """
        endpoint = f'/a/changes/{change_id}/revisions/{revision_id}/files/'
        return self._make_request(endpoint)
    
    def get_patch(self, change_id: str, revision_id: str = 'current') -> str:
        """
        Get patch content for a specific change revision.
        
        Args:
            change_id: Change ID or change number
            revision_id: Revision ID (default: 'current')
            
        Returns:
            Patch content as string
        """
        endpoint = f'/a/changes/{change_id}/revisions/{revision_id}/patch'
        url = urljoin(self.gerrit_url + '/', endpoint.lstrip('/'))
        response = self.session.get(url, auth=self.auth, verify=self.verify_ssl)
        response.raise_for_status()
        
        # Gerrit returns base64-encoded patch
        import base64
        return base64.b64decode(response.text).decode('utf-8')
