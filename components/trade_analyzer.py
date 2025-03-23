import streamlit as st
from streamlit_chat import message
import pandas as pd
import openai
import os
from typing import Dict, List, Tuple, Optional
import json
from components.prospects import normalize_name

class TradeAnalyzer:
    def __init__(self, roster_data: pd.DataFrame, projected_rankings: Optional[pd.DataFrame] = None):
        """Initialize the trade analyzer with roster data and projected rankings"""
        self.roster_data = roster_data
        self.projected_rankings = projected_rankings
        self.api_key = os.environ.get("OPENAI_API_KEY")
        
        # Prepare team data for quick access
        self.team_rosters = {}
        self.team_prospects = {}
        self.team_values = {}
        
        # Process team rosters for quick lookups
        for team in roster_data['team'].unique():
            team_df = roster_data[roster_data['team'] == team].copy()
            self.team_rosters[team] = team_df
            
            # Extract prospects
            prospects_df = team_df[team_df['status'].str.upper() == 'MINORS']
            self.team_prospects[team] = prospects_df
            
            # Calculate team value
            if projected_rankings is not None:
                team_value = projected_rankings[projected_rankings['team'] == team]['abl_score'].values
                self.team_values[team] = team_value[0] if len(team_value) > 0 else 0
    
    def get_player_info(self, player_name: str) -> Optional[Dict]:
        """Get detailed player info from the roster data"""
        # Normalize the player name for comparison
        normalized_name = normalize_name(player_name)
        
        # Search for player across all teams
        for team, roster in self.team_rosters.items():
            matches = roster[roster['player_name'].apply(
                lambda x: normalize_name(str(x)) == normalized_name
            )]
            
            if not matches.empty:
                player_data = matches.iloc[0].to_dict()
                player_data['team'] = team
                return player_data
        
        return None
    
    def get_team_players(self, team_name: str) -> pd.DataFrame:
        """Get all players from a specific team"""
        return self.team_rosters.get(team_name, pd.DataFrame())
    
    def analyze_trade(self, team1: str, players1: List[str], team2: str, players2: List[str]) -> Dict[str, any]:
        """Analyze a potential trade between two teams"""
        # Get player details for team 1
        team1_players_data = []
        for player in players1:
            player_data = self.get_player_info(player)
            if player_data:
                team1_players_data.append(player_data)
        
        # Get player details for team 2
        team2_players_data = []
        for player in players2:
            player_data = self.get_player_info(player)
            if player_data:
                team2_players_data.append(player_data)
        
        # If we don't have OpenAI API key or mock mode is enabled, use simplified analysis
        if not self.api_key:
            return self._simplified_trade_analysis(
                team1, team1_players_data, team2, team2_players_data
            )
        
        # Generate context for the AI model
        context = self._generate_trade_context(
            team1, team1_players_data, team2, team2_players_data
        )
        
        # Call the OpenAI API
        return self._call_openai_api(context)
    
    def _simplified_trade_analysis(self, team1: str, players1: List[Dict], 
                                  team2: str, players2: List[Dict]) -> Dict[str, any]:
        """Provide a simplified trade analysis when OpenAI API is not available"""
        # Calculate simple metrics for each side of the trade
        team1_active_count = sum(1 for p in players1 if p.get('status', '').upper() == 'ACTIVE')
        team1_prospect_count = sum(1 for p in players1 if p.get('status', '').upper() == 'MINORS')
        team1_salary = sum(p.get('salary', 0) for p in players1)
        
        team2_active_count = sum(1 for p in players2 if p.get('status', '').upper() == 'ACTIVE')
        team2_prospect_count = sum(1 for p in players2 if p.get('status', '').upper() == 'MINORS')
        team2_salary = sum(p.get('salary', 0) for p in players2)
        
        # Simple trade evaluation
        analysis = {
            "summary": f"Trade proposal between {team1} and {team2}.",
            "team1_analysis": {
                "giving": f"{len(players1)} players (Active: {team1_active_count}, Prospects: {team1_prospect_count}), Total Salary: ${team1_salary:.2f}",
                "evaluation": "Please provide an OpenAI API key for detailed analysis."
            },
            "team2_analysis": {
                "giving": f"{len(players2)} players (Active: {team2_active_count}, Prospects: {team2_prospect_count}), Total Salary: ${team2_salary:.2f}",
                "evaluation": "Please provide an OpenAI API key for detailed analysis."
            },
            "overall_evaluation": "Unable to provide a detailed evaluation without an OpenAI API key."
        }
        
        return analysis
    
    def _generate_trade_context(self, team1: str, players1: List[Dict], 
                               team2: str, players2: List[Dict]) -> str:
        """Generate the context for the OpenAI API with trade details"""
        # Format player information for the prompt
        def format_player_info(player: Dict) -> str:
            status = player.get('status', 'Unknown')
            position = player.get('position', 'Unknown')
            salary = player.get('salary', 0)
            mlb_team = player.get('mlb_team', 'Unknown')
            projected_points = player.get('projected_points', 0)
            
            return (f"Name: {player.get('player_name', 'Unknown')}, "
                   f"Status: {status}, Position: {position}, "
                   f"MLB Team: {mlb_team}, Salary: ${salary:.2f}, "
                   f"Projected Points: {projected_points:.1f}")
        
        # Create team summaries
        team1_players_str = "\n- ".join([""] + [format_player_info(p) for p in players1])
        team2_players_str = "\n- ".join([""] + [format_player_info(p) for p in players2])
        
        # Add team value context if available
        team1_value = f", Team Value (ABL Score): {self.team_values.get(team1, 'Unknown')}" if team1 in self.team_values else ""
        team2_value = f", Team Value (ABL Score): {self.team_values.get(team2, 'Unknown')}" if team2 in self.team_values else ""
        
        context = f"""
        You are a fantasy baseball trade analyzer evaluating a potential trade between two teams in a dynasty fantasy baseball league.
        
        TRADE DETAILS:
        {team1} receives:{team2_players_str}
        
        {team2} receives:{team1_players_str}
        
        TEAM CONTEXT:
        - {team1}{team1_value}
        - {team2}{team2_value}
        
        Please provide a detailed analysis of this trade from both teams' perspectives, considering:
        1. Current player value
        2. Future potential for prospects
        3. Salary considerations
        4. Position needs
        5. Overall team strategy (win-now vs. rebuild)
        
        Format your response as a JSON object with the following structure:
        {{
            "summary": "Brief 1-2 sentence overview of the trade",
            "team1_analysis": {{
                "giving": "Summary of what {team1} is giving up",
                "receiving": "Summary of what {team1} is receiving",
                "evaluation": "Detailed evaluation for {team1}"
            }},
            "team2_analysis": {{
                "giving": "Summary of what {team2} is giving up",
                "receiving": "Summary of what {team2} is receiving",
                "evaluation": "Detailed evaluation for {team2}"
            }},
            "overall_evaluation": "Final thoughts on which team gets the better value in this trade"
        }}
        """
        
        return context
    
    def _call_openai_api(self, prompt: str) -> Dict[str, any]:
        """Call the OpenAI API to analyze the trade"""
        try:
            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model="gpt-4o", 
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You are a fantasy baseball trade analyzer. Respond with JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            # Extract and parse the response
            result = response.choices[0].message.content
            return json.loads(result)
            
        except Exception as e:
            st.error(f"Error calling OpenAI API: {str(e)}")
            # Fallback to simplified analysis
            return {
                "summary": "Error analyzing trade with AI.",
                "team1_analysis": {
                    "giving": "Error in analysis",
                    "receiving": "Error in analysis",
                    "evaluation": f"Error: {str(e)}"
                },
                "team2_analysis": {
                    "giving": "Error in analysis",
                    "receiving": "Error in analysis", 
                    "evaluation": "Please check your OpenAI API key and try again."
                },
                "overall_evaluation": "Unable to complete analysis due to an error."
            }

def render(roster_data: pd.DataFrame, projected_rankings: Optional[pd.DataFrame] = None):
    """Render the chat trade analyzer interface"""
    st.header("Trade Analyzer Chat")
    
    # Initialize session state for chat messages if it doesn't exist
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'trade_analyzer' not in st.session_state:
        st.session_state.trade_analyzer = TradeAnalyzer(roster_data, projected_rankings)
    
    # Check for OpenAI API key
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        st.warning("""
        This feature requires an OpenAI API key to provide detailed trade analysis.
        Please add your OpenAI API key in the app settings or enter it below.
        """)
        
        # Allow user to input API key
        user_api_key = st.text_input("OpenAI API Key", type="password")
        if user_api_key:
            os.environ["OPENAI_API_KEY"] = user_api_key
            st.session_state.trade_analyzer = TradeAnalyzer(roster_data, projected_rankings)
            st.success("API key set successfully! You can now use the trade analyzer.")
            st.rerun()
    
    # Display chat header with instructions
    st.markdown("""
    ### AI Trade Assistant
    
    Ask the AI to analyze potential trades by providing:
    - The teams involved
    - The players each team would receive
    
    **Example questions:**
    - "Analyze a trade: Mariners send Luis Castillo to Yankees for Anthony Volpe"
    - "Who wins a trade where Dodgers give up Mookie Betts and get Yordan Alvarez?"
    - "Is it fair if Angels trade Trout to Braves for Acuña?"
    """)
    
    # Display chat history
    for message_obj in st.session_state.messages:
        message(message_obj["content"], is_user=message_obj["is_user"], key=message_obj["key"])
    
    # Chat input
    prompt = st.chat_input("Ask about a potential trade...")
    
    if prompt:
        # Add user message to chat history
        st.session_state.messages.append({
            "content": prompt,
            "is_user": True,
            "key": f"user_{len(st.session_state.messages)}"
        })
        
        # Process the user message
        try:
            # Very basic parsing for trade details
            response_content = process_trade_query(prompt, st.session_state.trade_analyzer, roster_data)
            
            # Add assistant message to chat history
            st.session_state.messages.append({
                "content": response_content,
                "is_user": False,
                "key": f"assistant_{len(st.session_state.messages)}"
            })
            
            # Rerun to update the UI with the new messages
            st.rerun()
            
        except Exception as e:
            st.error(f"Error processing your request: {str(e)}")

def process_trade_query(query: str, trade_analyzer: TradeAnalyzer, roster_data: pd.DataFrame) -> str:
    """Process a user query about a potential trade"""
    # Get all team names for reference
    all_teams = roster_data['team'].unique().tolist()
    
    # Simple keyword detection for trade analysis
    if any(keyword in query.lower() for keyword in ["trade", "deal", "swap", "exchange"]):
        # Try to extract teams and players from the query
        teams_mentioned = []
        for team in all_teams:
            # Check for team mentions, accounting for partial matches
            team_parts = team.lower().split()
            if team.lower() in query.lower() or any(part in query.lower() for part in team_parts):
                teams_mentioned.append(team)
        
        # If we identified at least two teams, attempt to analyze
        if len(teams_mentioned) >= 2:
            team1 = teams_mentioned[0]
            team2 = teams_mentioned[1]
            
            # Get all players from these teams
            team1_players = trade_analyzer.get_team_players(team1)
            team2_players = trade_analyzer.get_team_players(team2)
            
            # Extract player names mentioned in the query
            team1_players_mentioned = []
            for _, player in team1_players.iterrows():
                player_name = player['player_name']
                if player_name.lower() in query.lower():
                    team1_players_mentioned.append(player_name)
            
            team2_players_mentioned = []
            for _, player in team2_players.iterrows():
                player_name = player['player_name']
                if player_name.lower() in query.lower():
                    team2_players_mentioned.append(player_name)
            
            # If players were identified, analyze the trade
            if team1_players_mentioned and team2_players_mentioned:
                analysis = trade_analyzer.analyze_trade(
                    team1, team1_players_mentioned, team2, team2_players_mentioned
                )
                
                # Format the response
                response = f"""
                ## Trade Analysis: {team1} ⟷ {team2}
                
                **Summary**: {analysis.get('summary', 'No summary available')}
                
                ### {team1} Analysis
                - **Giving**: {analysis.get('team1_analysis', {}).get('giving', 'N/A')}
                - **Receiving**: {analysis.get('team1_analysis', {}).get('receiving', 'N/A')}
                - **Evaluation**: {analysis.get('team1_analysis', {}).get('evaluation', 'No detailed evaluation available')}
                
                ### {team2} Analysis
                - **Giving**: {analysis.get('team2_analysis', {}).get('giving', 'N/A')}
                - **Receiving**: {analysis.get('team2_analysis', {}).get('receiving', 'N/A')}
                - **Evaluation**: {analysis.get('team2_analysis', {}).get('evaluation', 'No detailed evaluation available')}
                
                ### Overall Evaluation
                {analysis.get('overall_evaluation', 'No overall evaluation available')}
                """
                
                return response
            else:
                return ("I couldn't identify specific players in your trade proposal. "
                       f"Please specify which players from {team1} and {team2} are involved in the trade.")
        else:
            return ("I couldn't identify two teams in your trade proposal. "
                   "Please mention the two teams involved in the trade.")
    
    # If not a trade analysis query, provide help
    return """
    I'm your AI Trade Assistant. I can help analyze potential trades between teams.
    
    Please provide details about the trade you want to analyze, including:
    - The teams involved
    - The players each team would send and receive
    
    For example:
    "Analyze a trade where Mariners send Luis Castillo to Yankees for Anthony Volpe"
    """