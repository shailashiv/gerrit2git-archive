#!/usr/bin/env python3
"""
Metadata export module.
Handles exporting Gerrit metadata to JSON files.
"""

import json
import os
from typing import Dict, List
from datetime import datetime


class MetadataExporter:
    """Export Gerrit metadata to JSON format."""
    
    @staticmethod
    def save_metadata(output_dir: str, gerrit_url: str, changes: List[Dict], 
                     comments_map: Dict, files_map: Dict):
        """
        Save complete Gerrit metadata as JSON for future reference.
        
        Args:
            output_dir: Directory to save JSON files
            gerrit_url: Gerrit server URL
            changes: List of change objects
            comments_map: Dictionary mapping change numbers to comments
            files_map: Dictionary mapping change numbers to file lists
        """
        metadata_dir = os.path.join(output_dir, 'metadata')
        os.makedirs(metadata_dir, exist_ok=True)
        
        # Save aggregated metadata
        full_metadata = {
            'export_date': datetime.now().isoformat(),
            'gerrit_url': gerrit_url,
            'total_changes': len(changes),
            'changes': []
        }
        
        for change in changes:
            change_num = change['_number']
            full_metadata['changes'].append({
                'change': change,
                'comments': comments_map.get(change_num, {}),
                'files': files_map.get(change_num, {})
            })
        
        # Save to JSON file
        metadata_path = os.path.join(metadata_dir, 'gerrit_export_metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(full_metadata, f, indent=2, ensure_ascii=False)
        
        print(f"Metadata saved to: {metadata_path}")
        
        # Also save individual change metadata
        for change in changes:
            change_num = change['_number']
            change_metadata = {
                'change': change,
                'comments': comments_map.get(change_num, {}),
                'files': files_map.get(change_num, {})
            }
            
            change_file = os.path.join(metadata_dir, f'change-{change_num:04d}.json')
            with open(change_file, 'w', encoding='utf-8') as f:
                json.dump(change_metadata, f, indent=2, ensure_ascii=False)
