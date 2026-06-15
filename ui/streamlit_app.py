# ui/streamlit_app.py
"""Streamlit web interface for Finance Agentic Chatbot"""

import sys
import os
import json
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.finance_agent import create_finance_agent
from config.settings import get_settings
from data import DataManager

# Page configuration
st.set_page_config(
    page_title="Finance Agentic Chatbot",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)


class FinanceAgentWebUI:
    """Streamlit web interface for Finance Agent"""
    
    def __init__(self):
        self.settings = get_settings()
        self.data_manager = DataManager()
        
        # Initialize session state
        self.init_session_state()
    
    def init_session_state(self):
        """Initialize session state variables"""
        if "agent" not in st.session_state:
            st.session_state.agent = create_finance_agent()
        
        if "user_id" not in st.session_state:
            st.session_state.user_id = "web_user_001"
        
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        if "transaction_history" not in st.session_state:
            st.session_state.transaction_history = []
        
        if "risk_alerts" not in st.session_state:
            st.session_state.risk_alerts = []
    
    def run(self):
        """Main UI render method"""
        # Sidebar
        self.render_sidebar()
        
        # Main content
        self.render_main()
    
    def render_sidebar(self):
        """Render sidebar with controls and info"""
        with st.sidebar:
            st.image("https://img.icons8.com/color/96/bank-building.png", width=80)
            st.title(" Finance Agent")
            st.markdown(f"**Version:** {self.settings.app_version}")
            st.markdown(f"**Environment:** {self.settings.app_env}")
            st.markdown("---")
            
            # User info
            st.subheader("👤 User Information")
            user_id = st.text_input("User ID", value=st.session_state.user_id)
            if user_id != st.session_state.user_id:
                st.session_state.user_id = user_id
                st.session_state.messages = []
                st.rerun()
            
            # Get user profile
            user_profile = self.data_manager.get_user(st.session_state.user_id)
            if user_profile:
                st.markdown(f"**Name:** {user_profile.get('full_name', 'N/A')}")
                st.markdown(f"**Tier:** {user_profile.get('user_tier', 'basic').upper()}")
                st.markdown(f"**Verified:** {'✅' if user_profile.get('verified_account') else '❌'}")
                st.markdown(f"**Daily Limit:** ${user_profile.get('daily_transfer_limit', 0):,.2f}")
            
            st.markdown("---")
            
            # Controls
            st.subheader("Controls")
            if st.button("Reset Conversation"):
                st.session_state.agent.reset_state(st.session_state.user_id)
                st.session_state.messages = []
                st.success("Conversation reset!")
            
            if st.button(" Show Metrics"):
                metrics = st.session_state.agent.get_agent_metrics()
                st.json(metrics)
            
            st.markdown("---")
            
            # Quick actions
            st.subheader("⚡ Quick Actions")
            quick_actions = [
                "What's my balance?",
                "Transfer $100 to savings",
                "Show my recent transactions",
                "What's Apple stock price?",
                "Check my credit score"
            ]
            
            for action in quick_actions:
                if st.button(action, key=action):
                    self.send_message(action)
            
            st.markdown("---")
            
            # Risk metrics
            st.subheader(" Risk Dashboard")
            risk_score = st.session_state.agent.get_state(st.session_state.user_id)
            if risk_score:
                current_risk = risk_score.get("risk_score", 0)
                
                # Risk gauge
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=current_risk,
                    title={"text": "Current Risk Score"},
                    domain={"x": [0, 1], "y": [0, 1]},
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar": {"color": "darkred" if current_risk > 70 else "orange" if current_risk > 30 else "green"},
                        "steps": [
                            {"range": [0, 30], "color": "lightgreen"},
                            {"range": [30, 70], "color": "lightyellow"},
                            {"range": [70, 100], "color": "salmon"}
                        ],
                        "threshold": {
                            "line": {"color": "red", "width": 4},
                            "thickness": 0.75,
                            "value": current_risk
                        }
                    }
                ))
                st.plotly_chart(fig, use_container_width=True)
    
    def render_main(self):
        """Render main chat interface"""
        st.title("Finance Agentic Chatbot")
        st.markdown("*Your intelligent banking assistant*")
        st.markdown("---")
        
        # Chat history
        chat_container = st.container()
        
        with chat_container:
            for message in st.session_state.messages:
                if message["role"] == "user":
                    st.markdown(
                        f'<div style="display: flex; justify-content: flex-end; margin-bottom: 10px;">'
                        f'<div style="background-color: #007bff; color: white; padding: 10px 15px; '
                        f'border-radius: 15px; max-width: 70%;">'
                        f'<strong>You:</strong> {message["content"]}</div></div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f'<div style="display: flex; justify-content: flex-start; margin-bottom: 10px;">'
                        f'<div style="background-color: #f1f1f1; color: #333; padding: 10px 15px; '
                        f'border-radius: 15px; max-width: 70%;">'
                        f'<strong> Agent:</strong> {message["content"]}</div></div>',
                        unsafe_allow_html=True
                    )
                    
                    # Show additional info if available
                    if message.get("risk_score", 0) > 50:
                        st.warning(f"Risk Score: {message['risk_score']}/100")
                    
                    if message.get("needs_human_review"):
                        st.error("This transaction requires human review")
        
        # Chat input
        st.markdown("---")
        col1, col2 = st.columns([6, 1])
        
        with col1:
            user_input = st.text_input(
                "Type your message:",
                key="user_input",
                placeholder="e.g., What's my balance? or Transfer $500 to savings..."
            )
        
        with col2:
            send_button = st.button("Send", use_container_width=True)
        
        if send_button and user_input:
            self.send_message(user_input)
        
        # Transaction history table
        self.render_transaction_table()
        
        # Risk alerts
        self.render_risk_alerts()
    
    def send_message(self, message: str):
        """Send a message to the agent"""
        # Add user message to chat
        st.session_state.messages.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Process through agent
        with st.spinner("Processing..."):
            result = st.session_state.agent.process(message, st.session_state.user_id)
        
        # Add agent response
        st.session_state.messages.append({
            "role": "assistant",
            "content": result["response"],
            "risk_score": result.get("risk_score", 0),
            "needs_human_review": result.get("needs_human_review", False),
            "timestamp": datetime.now().isoformat()
        })
        
        # Add to transaction history if it was a transaction
        if "transfer" in message.lower() or "send" in message.lower():
            st.session_state.transaction_history.append({
                "timestamp": datetime.now().isoformat(),
                "user_id": st.session_state.user_id,
                "query": message,
                "response": result["response"],
                "risk_score": result.get("risk_score", 0)
            })
        
        # Add risk alert if high risk
        if result.get("risk_score", 0) > 70:
            st.session_state.risk_alerts.append({
                "timestamp": datetime.now().isoformat(),
                "user_id": st.session_state.user_id,
                "query": message,
                "risk_score": result["risk_score"]
            })
        
        # Rerun to update UI
        st.rerun()
    
    def render_transaction_table(self):
        """Render transaction history table"""
        if st.session_state.transaction_history:
            st.markdown("---")
            st.subheader(" Recent Transactions")
            
            df = pd.DataFrame(st.session_state.transaction_history[-10:])
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df["timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%d %H:%M")
            
            st.dataframe(
                df[["timestamp", "query", "response", "risk_score"]],
                use_container_width=True,
                hide_index=True
            )
    
    def render_risk_alerts(self):
        """Render risk alerts"""
        if st.session_state.risk_alerts:
            st.markdown("---")
            st.subheader(" Risk Alerts")
            
            for alert in st.session_state.risk_alerts[-5:]:
                with st.expander(f"Alert: {alert['timestamp'][:16]} - Score: {alert['risk_score']}"):
                    st.write(f"**User:** {alert['user_id']}")
                    st.write(f"**Query:** {alert['query']}")
                    st.write(f"**Risk Score:** {alert['risk_score']}/100")


def main():
    """Entry point for Streamlit app"""
    ui = FinanceAgentWebUI()
    ui.run()


if __name__ == "__main__":
    main()