from pathlib import Path
from typing import List, Any
from langchain_core.documents import Document
import json
import os
import re

def normalize_player_name(name: str) -> str:
    """
    Normalize player name for consistent matching:
    - Convert to lowercase
    - Remove all whitespace
    - Remove special characters (dots, dashes, etc.)
    Returns normalized name for matching
    """
    if not name:
        return ""
    # Convert to lowercase, remove all whitespace and special chars
    normalized = re.sub(r'[^\w]', '', name.lower())
    return normalized

def get_name_parts(name: str) -> List[str]:
    """
    Extract name parts from a player name.
    """
    if not name:
        return []
    
    # Split by whitespace and get individual parts
    parts = re.split(r'\s+', name.lower().strip())
    parts = [re.sub(r'[^\w]', '', p) for p in parts if p]  # Remove special chars from each part
    
    # Add normalized full name
    normalized_full = normalize_player_name(name)
    if normalized_full:
        parts.append(normalized_full)
    
    return list(set(parts))  # Remove duplicates

def load_all_documents(data_dir: str = None) -> List[Any]:
    """
    Load IPL Player Stats JSON file and convert to LangChain document structure.
    Structure: {PlayerName: {Season: {Stats}}}
    """
    documents = []
    
    # Load IPL Player Stats JSON
    json_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "All_Player_Stat_Season_wise_2016_to_2025.json")
    json_file = os.path.abspath(json_file)
    
    if not os.path.exists(json_file):
        print(f"[ERROR] IPL player stats file not found: {json_file}")
        return documents
    
    print(f"[INFO] Loading IPL Player Stats from: {json_file}")
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Try to fix common JSON issues (trailing commas)
            content = re.sub(r',(\s*[}\]])', r'\1', content)
            data = json.loads(content)
        
        print(f"[INFO] Found {len(data)} players in JSON file")
        
        # Iterate through each player
        for player_name, seasons_data in data.items():
            if not isinstance(seasons_data, dict):
                continue
            
            # Create a document for each player-season combination
            for season, stats in seasons_data.items():
                if not isinstance(stats, dict):
                    continue
                
                # Normalize player name and get name parts for better search
                normalized_name = normalize_player_name(player_name)
                name_parts = get_name_parts(player_name)
                name_parts_text = " ".join(name_parts)  # Add name parts for search
                
                # Create a comprehensive text representation of player stats
                # Include normalized name and name parts for robust matching
                player_text = f"""Player Name: {player_name}
Player Names: {name_parts_text}
Season: {season}

BATTING STATISTICS:
- Total Batting Runs: {stats.get('Total_Bt_Runs', 0)}
- Total Batting Balls: {stats.get('Total_Bt_Balls', 0)}
- Batting Average: {stats.get('Bt_Avg', 0)}
- Batting Strike Rate: {stats.get('Bt_strike_rate', 0)}
- Total Matches: {stats.get('Total_Matches', 0)}

BOWLING STATISTICS:
- Total Bowling Runs: {stats.get('Total_Bw_Runs', 0)}
- Total Bowling Balls: {stats.get('Total_Bw_Balls', 0)}
- Bowling Economy: {stats.get('Bw_economy', 0)}
- Wickets Per Match: {stats.get('Bw_wicket_per_match', 0)}

MATCH-BY-MATCH DETAILS:
"""
                
                # Add match-by-match batting runs if available
                bt_runs = stats.get('Bt_Runs', [])
                bt_balls = stats.get('Bt_Balls', [])
                bt_fours = stats.get('Bt_four', [])
                bt_sixes = stats.get('Bt_six', [])
                bt_wickets = stats.get('Bt_Wickets', [])
                
                if bt_runs:
                    player_text += f"- Batting Runs (per match): {bt_runs}\n"
                    player_text += f"- Batting Balls (per match): {bt_balls}\n"
                    player_text += f"- Fours (per match): {bt_fours}\n"
                    player_text += f"- Sixes (per match): {bt_sixes}\n"
                    player_text += f"- Batting Wickets (per match): {bt_wickets}\n"
                
                # Add match-by-match bowling data if available
                bw_runs = stats.get('Bw_Runs', [])
                bw_balls = stats.get('Bw_Balls', [])
                bw_wickets = stats.get('Bw_Wickets', [])
                
                if bw_runs and any(bw_runs):  # Only if player bowled
                    player_text += f"- Bowling Runs (per match): {bw_runs}\n"
                    player_text += f"- Bowling Balls (per match): {bw_balls}\n"
                    player_text += f"- Bowling Wickets (per match): {bw_wickets}\n"
                
                # Calculate additional stats
                total_fours = sum(bt_fours) if bt_fours else 0
                total_sixes = sum(bt_sixes) if bt_sixes else 0
                total_batting_wickets = sum(bt_wickets) if bt_wickets else 0
                total_bowling_wickets = sum(bw_wickets) if bw_wickets else 0
                
                player_text += f"""
SUMMARY:
- Total Fours: {total_fours}
- Total Sixes: {total_sixes}
- Total Batting Wickets: {total_batting_wickets}
- Total Bowling Wickets: {total_bowling_wickets}
"""
                
                # Create metadata with normalized name for filtering
                metadata = {
                    "player_name": player_name,
                    "player_name_normalized": normalized_name,
                    "player_name_parts": " ".join(name_parts),  # Store name parts for search
                    "season": season,
                    "total_bt_runs": stats.get('Total_Bt_Runs', 0),
                    "total_bt_balls": stats.get('Total_Bt_Balls', 0),
                    "bt_avg": stats.get('Bt_Avg', 0),
                    "bt_strike_rate": stats.get('Bt_strike_rate', 0),
                    "total_bw_runs": stats.get('Total_Bw_Runs', 0),
                    "total_bw_balls": stats.get('Total_Bw_Balls', 0),
                    "bw_economy": stats.get('Bw_economy', 0),
                    "total_matches": stats.get('Total_Matches', 0),
                    "source": "ipl_player_stats"
                }
                
                doc = Document(page_content=player_text, metadata=metadata)
                documents.append(doc)
            
            # Normalize player name and get name parts for career summary too
            normalized_name = normalize_player_name(player_name)
            name_parts = get_name_parts(player_name)
            name_parts_text = " ".join(name_parts)
            
            # Also create a summary document for each player across all seasons
            all_seasons_text = f"""Player Name: {player_name}
Player Names: {name_parts_text}

CAREER SUMMARY (All Seasons):
"""
            
            # Aggregate stats across all seasons
            total_career_runs = 0
            total_career_balls = 0
            total_career_matches = 0
            seasons_list = []
            
            for season, stats in seasons_data.items():
                if isinstance(stats, dict):
                    seasons_list.append(season)
                    total_career_runs += stats.get('Total_Bt_Runs', 0)
                    total_career_balls += stats.get('Total_Bt_Balls', 0)
                    total_career_matches += stats.get('Total_Matches', 0)
            
            all_seasons_text += f"""
- Seasons Played: {', '.join(sorted(seasons_list))}
- Total Career Batting Runs: {total_career_runs}
- Total Career Batting Balls: {total_career_balls}
- Total Career Matches: {total_career_matches}
- Career Batting Average: {total_career_runs / total_career_matches if total_career_matches > 0 else 0:.2f}
- Career Batting Strike Rate: {(total_career_runs / total_career_balls * 100) if total_career_balls > 0 else 0:.2f}
"""
            
            # Create metadata for career summary with normalized name
            career_metadata = {
                "player_name": player_name,
                "player_name_normalized": normalized_name,
                "player_name_parts": " ".join(name_parts),
                "season": "all_seasons",
                "total_seasons": len(seasons_list),
                "seasons": ", ".join(sorted(seasons_list)),
                "total_career_runs": total_career_runs,
                "total_career_matches": total_career_matches,
                "source": "ipl_player_stats"
            }
            
            career_doc = Document(page_content=all_seasons_text, metadata=career_metadata)
            documents.append(career_doc)
        
        print(f"[INFO] Created {len(documents)} documents from IPL player stats")
        print(f"[INFO] - {len(data)} players")
        print(f"[INFO] - {len([d for d in documents if d.metadata.get('season') != 'all_seasons'])} player-season documents")
        print(f"[INFO] - {len([d for d in documents if d.metadata.get('season') == 'all_seasons'])} career summary documents")
        
    except Exception as e:
        print(f"[ERROR] Failed to load IPL player stats JSON: {e}")
        import traceback
        traceback.print_exc()
        return documents

    return documents

# Example usage
if __name__ == "__main__":
    docs = load_all_documents()
    print(f"\nLoaded {len(docs)} documents.")
    if docs:
        print(f"\nExample document (first 500 chars):\n{docs[0].page_content[:500]}")
        print(f"\nExample metadata:\n{docs[0].metadata}")
