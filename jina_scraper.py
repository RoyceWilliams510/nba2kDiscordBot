#!/usr/bin/env python3
"""
NBA 2K Ratings Jina.ai Scraper
A web scraper using Jina.ai's service to extract player data from 2kratings.com
"""

import requests
import os
import json
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional
from dotenv import load_dotenv
import time


class JinaNBA2KScraper:
    """Web scraper using Jina.ai for 2kratings.com"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        self.jina_api_key = os.getenv('JINA_API_KEY')
        if not self.jina_api_key:
            raise ValueError("JINA_API_KEY not found in environment variables")
        
        self.base_url = "https://www.2kratings.com"
        self.jina_base_url = "https://r.jina.ai"
        
        # Session for making requests
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.jina_api_key}',
            'Content-Type': 'application/json'
        })
    
    def scrape_url(self, url: str) -> Optional[str]:
        """
        Scrape a URL using Jina.ai
        
        Args:
            url: URL to scrape
            
        Returns:
            HTML content as string or None if failed
        """
        try:
            jina_url = f"{self.jina_base_url}/{url}"
            print(f"Scraping via Jina.ai: {jina_url}")
            
            response = self.session.get(jina_url, timeout=30)
            
            if response.status_code == 200:
                print(f"Successfully scraped {url}")
                return response.text
            else:
                print(f"Failed to scrape {url}. Status: {response.status_code}")
                print(f"Response: {response.text[:500]}...")
                return None
                
        except requests.RequestException as e:
            print(f"Error scraping {url}: {e}")
            return None
    
    def read_local_file(self, file_path: str) -> Optional[str]:
        """
        Read content from a local file (for testing)
        
        Args:
            file_path: Path to the local file
            
        Returns:
            File content as string or None if failed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"Successfully read local file: {file_path}")
            return content
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None
    
    def search_player(self, player_name: str) -> List[Dict]:
        """
        Search for a player on 2kratings.com using Jina.ai
        
        Args:
            player_name: Name of the player to search for
            
        Returns:
            List of player data dictionaries
        """
        try:
            # Convert player name to URL format
            url_name = player_name.lower().replace(' ', '-')
            
            # Try different URL patterns
            url_patterns = [
                f"{self.base_url}/{url_name}",
                f"{self.base_url}/player/{url_name}",
                f"{self.base_url}/players/{url_name}"
            ]
            
            print(f"Searching for: {player_name}")
            
            for url_pattern in url_patterns:
                print(f"Trying URL: {url_pattern}")
                
                # Scrape the page using Jina.ai
                html_content = self.scrape_url(url_pattern)
                
                if html_content:
                    # Parse the HTML content
                    player_data = self.parse_player_page(html_content, url_pattern)
                    if player_data:
                        return [player_data]
                    else:
                        print(f"No player data found at: {url_pattern}")
                else:
                    print(f"Failed to scrape: {url_pattern}")
                
                # Add delay between attempts
                time.sleep(1)
            
            print("All URL patterns failed")
            return []
            
        except Exception as e:
            print(f"Error searching for player: {e}")
            return []
    
    def test_with_local_file(self, file_path: str, player_name: str = "Nikola Jokic") -> List[Dict]:
        """
        Test the parser with a local file instead of making API calls
        
        Args:
            file_path: Path to the local HTML file
            player_name: Name of the player for display purposes
            
        Returns:
            List of player data dictionaries
        """
        try:
            print(f"Testing parser with local file: {file_path}")
            print(f"Player: {player_name}")
            print("=" * 50)
            
            # Read the local file
            html_content = self.read_local_file(file_path)
            
            if html_content:
                # Parse the content
                player_data = self.parse_player_page(html_content, f"file://{file_path}")
                if player_data:
                    return [player_data]
                else:
                    print("No player data found in file")
                    return []
            else:
                print("Failed to read file")
                return []
                
        except Exception as e:
            print(f"Error testing with local file: {e}")
            return []
    
    def parse_player_page(self, html_content: str, url: str) -> Optional[Dict]:
        """
        Parse player data from Jina.ai markdown content
        
        Args:
            html_content: Markdown content as string from Jina.ai
            url: Original URL that was scraped
            
        Returns:
            Dictionary containing player data or None if error
        """
        try:
            # Extract player name from the title
            player_name = "Unknown Player"
            if "Title:" in html_content:
                title_line = html_content.split("Title:")[1].split("\n")[0].strip()
                player_name = title_line.replace(" NBA 2K25 Rating (Current", "").replace(")", "").strip()
            
            # Extract overall rating
            overall_rating = None
            if "Overall 2K Rating of" in html_content:
                rating_match = re.search(r'Overall 2K Rating of (\d+)', html_content)
                if rating_match:
                    overall_rating = int(rating_match.group(1))
            
            # Extract badge information
            badge_info = self.extract_badge_info_from_markdown(html_content)
            
            # Extract attributes
            attributes = self.extract_attributes_from_markdown(html_content)
            
            # Extract additional player details
            player_details = self.extract_player_details_from_markdown(html_content)
            
            player_data = {
                'name': player_name,
                'url': url,
                'overall_rating': overall_rating,
                'badge_info': badge_info,
                'attributes': attributes,
                'player_details': player_details,
                'raw_content': html_content[:1000] + "..." if len(html_content) > 1000 else html_content
            }
            
            return player_data
            
        except Exception as e:
            print(f"Error parsing player page: {e}")
            return None
    
    def extract_attributes_from_markdown(self, content: str) -> Dict:
        """
        Extract attributes from markdown content
        
        Args:
            content: Markdown content from Jina.ai
            
        Returns:
            Dictionary of attributes with main categories and detailed sub-attributes
        """
        attributes = {}
        
        # Look for the main attribute categories in the markdown format
        # Pattern: "#### 91-1 Outside Scoring" or "#### 78 Athleticism"
        attribute_sections = [
            'Outside Scoring',
            'Inside Scoring',
            'Defense',
            'Athleticism',
            'Playmaking',
            'Rebounding'
        ]
        
        for section in attribute_sections:
            # Look for the section header with rating
            pattern = rf'#### (\d+)(?:[+-]\d+)? {re.escape(section)}'
            match = re.search(pattern, content)
            if match:
                rating = int(match.group(1))
                
                # Create section with main rating and sub-attributes
                attributes[section] = {
                    'rating': rating,
                    'sub_attributes': self.extract_sub_attributes(content, section)
                }
        
        return attributes
    
    def extract_sub_attributes(self, content: str, section_name: str) -> Dict:
        """
        Extract sub-attributes for a specific section
        
        Args:
            content: Markdown content from Jina.ai
            section_name: Name of the main attribute section
            
        Returns:
            Dictionary of sub-attributes with their values
        """
        sub_attributes = {}
        
        # Find the section in the content
        section_pattern = rf'#### \d+(?:[+-]\d+)? {re.escape(section_name)}'
        section_match = re.search(section_pattern, content)
        
        if section_match:
            # Get the content after this section until the next section or end
            start_pos = section_match.end()
            
            # Find the next section or end of content
            next_section_pattern = r'#### \d+(?:[+-]\d+)? [A-Za-z\s]+'
            next_section_match = re.search(next_section_pattern, content[start_pos:])
            
            if next_section_match:
                section_content = content[start_pos:start_pos + next_section_match.start()]
            else:
                section_content = content[start_pos:]
            
            # Extract sub-attributes from this section
            # Pattern: "*   99 Close Shot" or "*   98+1 Mid-Range Shot"
            sub_attr_pattern = r'\*\s*(\d+(?:[+-]\d+)?)\s+([^\n\r]+)'
            matches = re.findall(sub_attr_pattern, section_content)
            
            for match in matches:
                value_str = match[0]
                attr_name = match[1].strip()
                
                # Extract the base value (remove +/- modifiers)
                base_value = int(re.search(r'(\d+)', value_str).group(1))
                
                sub_attributes[attr_name] = {
                    'value': base_value,
                    'raw_value': value_str
                }
        
        return sub_attributes
    
    def extract_badge_info_from_markdown(self, content: str) -> Dict:
        """
        Extract badge information from markdown content
        
        Args:
            content: Markdown content from Jina.ai
            
        Returns:
            Dictionary with badge information
        """
        badge_info = {
            'total_badges': 0,
            'hof_badges': 0,
            'gold_badges': 0,
            'silver_badges': 0,
            'bronze_badges': 0,
            'legendary_badges': 0,
            'badge_breakdown': {},
            'individual_badges': []
        }
        
        # Extract badge counts from image URLs
        # Pattern: ![Image X: Badge Type](https://www.2kratings.com/wp-content/uploads/badge-type-sum.png)number
        legendary_match = re.search(r'legendary-sum\.png\)\s*(\d+)', content)
        hof_match = re.search(r'hof-sum\.png\)\s*(\d+)', content)
        gold_match = re.search(r'gold-sum\.png\)\s*(\d+)', content)
        silver_match = re.search(r'silver-sum\.png\)\s*(\d+)', content)
        bronze_match = re.search(r'bronze-sum\.png\)\s*(\d+)', content)
        
        if legendary_match:
            badge_info['legendary_badges'] = int(legendary_match.group(1))
        if hof_match:
            badge_info['hof_badges'] = int(hof_match.group(1))
        if gold_match:
            badge_info['gold_badges'] = int(gold_match.group(1))
        if silver_match:
            badge_info['silver_badges'] = int(silver_match.group(1))
        if bronze_match:
            badge_info['bronze_badges'] = int(bronze_match.group(1))
        
        # Set total badges as the sum of all badge types
        badge_info['total_badges'] = (
            badge_info['legendary_badges'] +
            badge_info['hof_badges'] +
            badge_info['gold_badges'] +
            badge_info['silver_badges'] +
            badge_info['bronze_badges']
        )
        
        # Look for badge breakdown by category
        badge_categories = [
            'Outside Scoring',
            'Inside Scoring',
            'Playmaking',
            'Defense',
            'Rebounding',
            'General Offense',
            'All Around'
        ]
        
        for category in badge_categories:
            # Look for patterns like "Outside Scoring (4)" or "Inside Scoring (9)"
            cat_pattern = rf'{re.escape(category)} \((\d+)\)'
            cat_match = re.search(cat_pattern, content)
            if cat_match:
                badge_info['badge_breakdown'][category] = int(cat_match.group(1))
        
        # Extract individual badges with quality levels
        badge_info['individual_badges'] = self.extract_individual_badges(content, badge_info)
        
        return badge_info
    
    def extract_individual_badges(self, content: str, badge_info: Dict) -> List[Dict]:
        """
        Extract individual badges with their quality levels and categories
        
        Args:
            content: Markdown content from Jina.ai
            badge_info: Dictionary with badge counts for quality assignment
            
        Returns:
            List of badge dictionaries with name, quality, category, and description
        """
        individual_badges = []
        
        # Find the badges section (look for the NBA 2K25 Badges section)
        badge_section_start = content.find("[NBA 2K25 Badges]")
        if badge_section_start == -1:
            return individual_badges
        
        # Extract the badges section
        badge_section = content[badge_section_start:]
        
        # Find the end of the badges section (look for "NBA 2K25 Hot Zones" or similar)
        view_all_end = badge_section.find("NBA 2K25 Hot Zones")
        if view_all_end != -1:
            badge_section = badge_section[:view_all_end]
        
        # Extract all badges using regex
        # Pattern: #### BadgeName\n\nCategory\nDescription\n\n![Image
        badge_pattern = r'#### ([^\n]+)\n\n([^\n]+)\n([^\n]+(?:\n[^\n]+)*?)(?=\n\n#### |\n\n\[View All Badges\]|$)'
        badge_matches = re.findall(badge_pattern, badge_section, re.DOTALL)
        
        # Alternative pattern that looks for badges ending with image tags
        badge_pattern_v2 = r'#### ([^\n]+)\n\n([^\n]+)\n([^\n]+(?:\n[^\n]+)*?)(?=\n\n#### |\n\n\[View All Badges\]|\n\n!\[Image|$)'
        badge_matches = re.findall(badge_pattern_v2, badge_section, re.DOTALL)
        
        # Assign quality levels based on position and actual counts
        legendary_count = badge_info.get('legendary_badges', 0)
        hof_count = badge_info.get('hof_badges', 0)
        gold_count = badge_info.get('gold_badges', 0)
        silver_count = badge_info.get('silver_badges', 0)
        bronze_count = badge_info.get('bronze_badges', 0)
        
        for i, (badge_name, category, description) in enumerate(badge_matches):
            # Stop if we've reached the total badge count
            if i >= badge_info.get('total_badges', 0):
                break
                
            # Determine quality based on position and actual counts
            if i < legendary_count:
                quality = "Legendary"
            elif i < legendary_count + hof_count:
                quality = "Hall of Fame"
            elif i < legendary_count + hof_count + gold_count:
                quality = "Gold"
            elif i < legendary_count + hof_count + gold_count + silver_count:
                quality = "Silver"
            elif i < legendary_count + hof_count + gold_count + silver_count + bronze_count:
                quality = "Bronze"
            else:
                quality = "Unknown"
            
            # Clean up description (remove extra whitespace and newlines)
            description = re.sub(r'\n+', ' ', description).strip()
            
            individual_badges.append({
                'name': badge_name.strip(),
                'quality': quality,
                'category': category.strip(),
                'description': description
            })
        
        return individual_badges
    
    def extract_player_details_from_markdown(self, content: str) -> Dict:
        """
        Extract additional player details from markdown content
        
        Args:
            content: Markdown content from Jina.ai
            
        Returns:
            Dictionary with player details
        """
        details = {}
        
        # Extract position
        position_match = re.search(r'Position:\s*\[([^\]]+)\]', content)
        if position_match:
            details['position'] = position_match.group(1).strip()
        
        # Extract team
        team_match = re.search(r'Team:\s*\[([^\]]+)\]', content)
        if team_match:
            details['team'] = team_match.group(1).strip()
        
        # Extract height
        height_match = re.search(r'Height:\s*([^\n\r]+)', content)
        if height_match:
            details['height'] = height_match.group(1).strip()
        
        # Extract weight
        weight_match = re.search(r'Weight:\s*([^\n\r]+)', content)
        if weight_match:
            details['weight'] = weight_match.group(1).strip()
        
        # Extract wingspan
        wingspan_match = re.search(r'Wingspan:\s*([^\n\r]+)', content)
        if wingspan_match:
            details['wingspan'] = wingspan_match.group(1).strip()
        
        # Extract archetype
        archetype_match = re.search(r'Archetype:\s*([^\n\r]+)', content)
        if archetype_match:
            details['archetype'] = archetype_match.group(1).strip()
        
        return details


def main():
    """Main function to test the Jina scraper with API call"""
    try:
        scraper = JinaNBA2KScraper()
        
        # Test with a real API call
        test_player = "Stephen Curry"
        print(f"Testing Jina scraper with API call: {test_player}")
        print("=" * 50)
        
        players = scraper.search_player(test_player)
        
        if players:
            print(f"Found {len(players)} players:")
            for i, player in enumerate(players, 1):
                print(f"\n{i}. {player['name']}")
                print(f"   URL: {player['url']}")
                print(f"   Overall Rating: {player['overall_rating']}")
                
                # Display player details
                if player['player_details']:
                    print(f"   Position: {player['player_details'].get('position', 'N/A')}")
                    print(f"   Team: {player['player_details'].get('team', 'N/A')}")
                    print(f"   Height: {player['player_details'].get('height', 'N/A')}")
                    print(f"   Weight: {player['player_details'].get('weight', 'N/A')}")
                    print(f"   Wingspan: {player['player_details'].get('wingspan', 'N/A')}")
                    print(f"   Archetype: {player['player_details'].get('archetype', 'N/A')}")
                
                # Display attributes
                if player['attributes']:
                    print(f"   Attributes:")
                    for attr, attr_data in player['attributes'].items():
                        print(f"     {attr}: {attr_data['rating']}")
                        if attr_data['sub_attributes']:
                            for sub_attr, sub_value in attr_data['sub_attributes'].items():
                                print(f"       {sub_attr}: {sub_value['value']} ({sub_value['raw_value']})")
                
                # Display badge information
                if player['badge_info']:
                    badge_info = player['badge_info']
                    print(f"   Badges: {badge_info['total_badges']} total")
                    print(f"     Legendary: {badge_info['legendary_badges']}, HOF: {badge_info['hof_badges']}, Gold: {badge_info['gold_badges']}, Silver: {badge_info['silver_badges']}, Bronze: {badge_info['bronze_badges']}")
                    
                    if badge_info.get('badge_breakdown'):
                        print(f"     Breakdown by category:")
                        for category, count in badge_info['badge_breakdown'].items():
                            print(f"       {category}: {count}")
                    
                    # Display individual badges
                    if badge_info.get('individual_badges'):
                        print(f"     Individual Badges:")
                        for badge in badge_info['individual_badges']:
                            print(f"       {badge['quality']} {badge['name']} ({badge['category']})")
                            print(f"         {badge['description']}")
                
                # Save to JSON file for inspection
                output_filename = f"player_data_{player['name'].lower().replace(' ', '_')}.json"
                
                # Ensure output directory exists
                os.makedirs('output', exist_ok=True)
                output_path = os.path.join('output', output_filename)
                
                with open(output_path, 'w') as f:
                    json.dump(player, f, indent=2)
                print(f"   Data saved to: {output_path}")
        else:
            print("No players found")
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main() 