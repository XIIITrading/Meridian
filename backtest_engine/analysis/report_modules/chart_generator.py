"""
Chart generator using Plotly
"""
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class ChartGenerator:
    """Generates interactive charts using Plotly"""
    
    def create_confluence_chart(self, confluence_data: Dict) -> str:
        """Create bar chart for confluence performance"""
        if not confluence_data:
            return ""
        
        levels = []
        win_rates = []
        avg_r = []
        trade_counts = []
        
        for level, data in sorted(confluence_data.items()):
            levels.append(level)
            win_rates.append(data.win_rate)
            avg_r.append(data.avg_r_multiple)
            trade_counts.append(data.trade_count)
        
        # Create subplot with 2 y-axes
        fig = make_subplots(
            rows=1, cols=1,
            specs=[[{"secondary_y": True}]]
        )
        
        # Win rate bars
        fig.add_trace(
            go.Bar(
                x=levels,
                y=win_rates,
                name='Win Rate %',
                marker_color='lightblue',
                text=[f"{wr:.1f}%" for wr in win_rates],
                textposition='auto'
            ),
            secondary_y=False
        )
        
        # Avg R line
        fig.add_trace(
            go.Scatter(
                x=levels,
                y=avg_r,
                name='Avg R-Multiple',
                line=dict(color='red', width=2),
                mode='lines+markers+text',
                text=[f"{r:.2f}R" for r in avg_r],
                textposition='top center'
            ),
            secondary_y=True
        )
        
        # Update layout
        fig.update_layout(
            title='Performance by Confluence Level',
            height=400,
            showlegend=True,
            hovermode='x unified'
        )
        
        fig.update_xaxes(title_text='Confluence Level')
        fig.update_yaxes(title_text='Win Rate %', secondary_y=False)
        fig.update_yaxes(title_text='Avg R-Multiple', secondary_y=True)
        
        return fig.to_html(div_id="confluence_chart", include_plotlyjs=False)
    
    def create_r_distribution_chart(self, trades_df: pd.DataFrame) -> str:
        """Create histogram of R-multiple distribution"""
        if trades_df.empty or 'r_multiple' not in trades_df.columns:
            return ""
        
        fig = go.Figure()
        
        # Create histogram
        fig.add_trace(go.Histogram(
            x=trades_df['r_multiple'],
            nbinsx=30,
            name='R-Multiple Distribution',
            marker_color='green',
            opacity=0.7
        ))
        
        # Add vertical line at 0
        fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Break Even")
        
        # Add mean line
        mean_r = trades_df['r_multiple'].mean()
        fig.add_vline(x=mean_r, line_dash="dash", line_color="blue", 
                     annotation_text=f"Mean: {mean_r:.2f}R")
        
        fig.update_layout(
            title='R-Multiple Distribution',
            xaxis_title='R-Multiple',
            yaxis_title='Frequency',
            height=400,
            showlegend=True
        )
        
        return fig.to_html(div_id="r_dist_chart", include_plotlyjs=False)
    
    def create_pattern_chart(self, pattern_results: Dict) -> str:
        """Create chart showing pattern performance"""
        if not pattern_results or 'patterns' not in pattern_results:
            return ""
        
        patterns = pattern_results['patterns'][:10]  # Top 10 patterns
        
        if not patterns:
            return ""
        
        names = []
        confidences = []
        win_rates = []
        
        for pattern in patterns:
            names.append(pattern.definition.name[:30])  # Truncate long names
            confidences.append(pattern.confidence_score)
            win_rates.append(pattern.performance.win_rate)
        
        fig = go.Figure()
        
        # Create scatter plot
        fig.add_trace(go.Scatter(
            x=win_rates,
            y=confidences,
            mode='markers+text',
            marker=dict(
                size=15,
                color=confidences,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Confidence %")
            ),
            text=names,
            textposition="top center",
            hovertemplate='<b>%{text}</b><br>Win Rate: %{x:.1f}%<br>Confidence: %{y:.1f}%'
        ))
        
        fig.update_layout(
            title='Pattern Performance Map',
            xaxis_title='Win Rate %',
            yaxis_title='Confidence %',
            height=500,
            showlegend=False
        )
        
        # Add quadrant lines
        fig.add_hline(y=70, line_dash="dash", line_color="gray", opacity=0.5)
        fig.add_vline(x=50, line_dash="dash", line_color="gray", opacity=0.5)
        
        return fig.to_html(div_id="pattern_chart", include_plotlyjs=False)
    
    def create_pnl_chart(self, trades_df: pd.DataFrame) -> str:
        """Create cumulative P&L chart"""
        if trades_df.empty or 'trade_result' not in trades_df.columns:
            return ""
        
        # Sort by date
        if 'entry_candle_time' in trades_df.columns:
            trades_df = trades_df.sort_values('entry_candle_time')
        
        # Calculate cumulative P&L
        trades_df['cumulative_pnl'] = trades_df['trade_result'].cumsum()
        
        fig = go.Figure()
        
        # Add cumulative P&L line
        fig.add_trace(go.Scatter(
            x=list(range(1, len(trades_df) + 1)),
            y=trades_df['cumulative_pnl'],
            mode='lines',
            name='Cumulative P&L',
            line=dict(color='blue', width=2),
            fill='tozeroy',
            fillcolor='rgba(0, 100, 200, 0.2)'
        ))
        
        # Add individual trade markers
        colors = ['green' if r > 0 else 'red' for r in trades_df['trade_result']]
        fig.add_trace(go.Scatter(
            x=list(range(1, len(trades_df) + 1)),
            y=trades_df['cumulative_pnl'],
            mode='markers',
            marker=dict(color=colors, size=8),
            name='Trades',
            hovertemplate='Trade #%{x}<br>Result: $%{text}<br>Cumulative: $%{y:.2f}',
            text=[f"{r:.2f}" for r in trades_df['trade_result']]
        ))
        
        fig.update_layout(
            title='Cumulative P&L',
            xaxis_title='Trade Number',
            yaxis_title='Cumulative P&L ($)',
            height=400,
            showlegend=True,
            hovermode='x'
        )
        
        # Add zero line
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        
        return fig.to_html(div_id="pnl_chart", include_plotlyjs=False)