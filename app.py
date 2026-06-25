import streamlit as st
import pandas as pd

# Page setup
st.set_page_config(page_title="Women's WC Dashboard", layout="wide", page_icon="🏏")
st.title("🏏 Women's T20 WC Points Dashboard")

# The unique ID of your Google Sheet
SPREADSHEET_ID = "1Ln5OEyO_-aJo8FXJBbVLibhvgfe0_IUONtRBWJOZtEU"

# Standard Google Sheet export URL format with safe space encoding
def get_sheet_url(sheet_name):
    safe_sheet_name = sheet_name.replace(" ", "%20")
    return f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={safe_sheet_name}"

# Directly load using Pandas over the network
@st.cache_data(ttl=300)
def load_data(sheet_name):
    url = get_sheet_url(sheet_name)
    return pd.read_csv(url)

try:
    # 1. Load the required datasets directly via Pandas
    df_draft = load_data("Draft")
    df_points_detail = load_data("Points2026")
    df_purse = load_data("Purse details")
    
    # Clean up empty rows/columns from Draft tab
    df_draft = df_draft.dropna(subset=["Player Name"]) if "Player Name" in df_draft.columns else df_draft
    
    # Define the 5 explicit managers allowed on the dashboard
    VALID_MANAGERS = ["Ahaan", "Ninad", "Anant", "Rishabh", "Suryansh"]
    
    if not df_purse.empty and "Team" in df_purse.columns:
        # Clean up names from the "Purse details" tab
        df_purse = df_purse.dropna(subset=["Team"])
        df_purse["Team"] = df_purse["Team"].astype(str).str.strip()
        
        # Keep ONLY the rows matching our 5 main players
        df_purse = df_purse[df_purse["Team"].isin(VALID_MANAGERS)]

    # --- SIDEBAR: SCORING RULES ---
    with st.sidebar:
        st.header("🎯 Scoring System")
        with st.expander("View Point Matrix"):
            scoring_rules = {
                "Event": ["Wicket", "Six", "Four", "Caught", "Stumping", "Dot", "Run out"],
                "Points": [3.5, 3.5, 2.5, 2.5, 2.5, 1.0, "1.5/3.0"]
            }
            st.table(pd.DataFrame(scoring_rules))

    # --- MAIN TABS ---
    tab1, tab2, tab3 = st.tabs(["🏆 Leaderboard", "👥 Squad Displays", "📊 Detailed Player Stats"])
    
    # ----------------------------------------------------
    # TAB 1: LEADERBOARD
    # ----------------------------------------------------
    with tab1:
        st.header("Global Standings")
        
        points_col = "Points" if "Points" in df_purse.columns else ("Points 2026" if "Points 2026" in df_purse.columns else None)
        top12_col = "Top 12 Points" if "Top 12 Points" in df_purse.columns else None
        
        if not df_purse.empty and top12_col and "Team" in df_purse.columns:
            leaderboard = df_purse.sort_values(by=top12_col, ascending=False).reset_index(drop=True)
            
            # Metric blocks at the top matching the new sort criteria
            col1, col2, col3 = st.columns(3)
            col1.metric("Current Leader 🥇", leaderboard.iloc[0]["Team"], f"{leaderboard.iloc[0][top12_col]} pts (Top 12)")
            if len(leaderboard) > 1:
                col2.metric("2nd Place 🥈", leaderboard.iloc[1]["Team"], f"{leaderboard.iloc[1][top12_col]} pts (Top 12)")
            
            # MVP calculation from Draft sheet
            if "Points 2026" in df_draft.columns:
                top_player = df_draft.sort_values(by="Points 2026", ascending=False).iloc[0]
                col3.metric("MVP Player 🔥", top_player["Player Name"], f"{top_player['Points 2026']} pts ({top_player['Sold To']})")

            st.subheader("Rankings Table")
            
            display_cols = ["Team", points_col, top12_col]
            available_cols = [c for c in display_cols if c is not None and c in leaderboard.columns]
            
            st.dataframe(
                leaderboard[available_cols], 
                use_container_width=True, 
                hide_index=True
            )
        else:
            st.warning("Could not find the expected leaderboard metrics columns inside your 'Purse details' sheet tab.")
        
    # ----------------------------------------------------
    # TAB 2: SQUAD DISPLAYS
    # ----------------------------------------------------
    with tab2:
        st.header("Individual Squad Hub")
        
        if "Sold To" in df_draft.columns:
            managers = [m for m in df_draft["Sold To"].unique() if m in VALID_MANAGERS]
            selected_manager = st.selectbox("🎯 Select a Manager to view their Squad:", managers)
            
            if selected_manager:
                squad_df = df_draft[df_draft["Sold To"] == selected_manager].copy()
                total_squad_points = squad_df["Points 2026"].sum()
                player_count = len(squad_df)
                
                s_col1, s_col2 = st.columns(2)
                s_col1.metric(f"{selected_manager}'s Total Points", f"{total_squad_points} pts")
                s_col2.metric("Players Drafted", f"{player_count} / 15")
                
                display_cols = ["Player Name", "Team", "Player Type", "Points 2026"]
                available_cols = [c for c in display_cols if c in squad_df.columns]
                
                st.subheader(f"📋 {selected_manager}'s Roster Breakdown")
                st.dataframe(
                    squad_df[available_cols].sort_values(by="Points 2026", ascending=False), 
                    use_container_width=True, 
                    hide_index=True
                )
                
                # --- VISUALS SECTION ---
                st.markdown("---")
                st.subheader("📊 Squad Performance & Composition Analytics")
                
                g_col1, g_col2, g_col3 = st.columns(3)
                
                # GRAPH 1: Points got from every team
                with g_col1:
                    st.markdown("##### 📈 Total Points Contributed by Country")
                    if "Team" in squad_df.columns and "Points 2026" in squad_df.columns:
                        team_points = squad_df.groupby("Team")["Points 2026"].sum().sort_values(ascending=False)
                        st.bar_chart(team_points, color="#FF4B4B")
                    else:
                        st.info("Missing required team or points columns for calculation.")
                
                # GRAPH 2: Number of players from every team
                with g_col2:
                    st.markdown("##### 👥 Player Share by Country")
                    if "Team" in squad_df.columns:
                        team_counts = squad_df["Team"].value_counts()
                        st.bar_chart(team_counts, color="#00C0F2")
                    else:
                        st.info("Missing 'Team' column to calculate player count.")
                        
                # GRAPH 3: Original Role distribution
                with g_col3:
                    st.markdown("##### 🏏 Roster Breakdown by Position")
                    if "Player Type" in squad_df.columns:
                        role_counts = squad_df["Player Type"].value_counts()
                        st.bar_chart(role_counts, color="#29B5E8")
                    else:
                        st.info("Missing 'Player Type' column to calculate roster distribution.")

    # ----------------------------------------------------
    # TAB 3: DETAILED PLAYER STATS
    # ----------------------------------------------------
    with tab3:
        st.header("📊 Deep-Dive Player Performance Log")
        
        df_points_detail = df_points_detail.dropna(subset=["Player Name"]) if "Player Name" in df_points_detail.columns else df_points_detail
        
        search_query = st.text_input("🔍 Search for any player to see her exact match metrics:")
        if search_query:
            filtered_stats = df_points_detail[df_points_detail["Player Name"].str.contains(search_query, case=False, na=False)]
            st.dataframe(filtered_stats, use_container_width=True, hide_index=True)
        else:
            st.dataframe(df_points_detail, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error handling dashboard data: {e}")