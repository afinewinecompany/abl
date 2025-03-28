import streamlit as st
import pandas as pd
import plotly.express as px

def render(standings_data: pd.DataFrame):
    """Render standings section"""
    st.header("League Standings")

    # Sort standings by rank
    standings_data = standings_data.sort_values('rank')

    # Display standings table
    st.dataframe(
        standings_data,
        column_config={
            "team_name": "Team",
            "rank": "Rank",
            "wins": "Wins",
            "losses": "Losses",
            "ties": "Ties",
            "winning_pct": st.column_config.NumberColumn(
                "Winning %",
                format="%.3f"
            ),
            "games_back": st.column_config.NumberColumn(
                "Games Back",
                format="%.1f"
            )
        },
        hide_index=True
    )

    # Create visualization
    st.subheader("Win-Loss Record")
    win_loss_data = standings_data.melt(
        id_vars=['team_name'],
        value_vars=['wins', 'losses', 'ties'],
        var_name='record_type',
        value_name='count'
    )

    fig = px.bar(
        win_loss_data,
        x='team_name',
        y='count',
        color='record_type',
        title='Team Records',
        barmode='group',
        labels={'team_name': 'Team', 'count': 'Games', 'record_type': 'Record Type'}
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    # Create winning percentage visualization
    st.subheader("Team Performance")
    fig2 = px.scatter(
        standings_data,
        x='winning_pct',
        y='games_back',
        text='team_name',
        title='Winning Percentage vs Games Back',
        labels={
            'winning_pct': 'Winning Percentage',
            'games_back': 'Games Back',
            'team_name': 'Team'
        }
    )
    fig2.update_traces(textposition='top center')
    st.plotly_chart(fig2, use_container_width=True)