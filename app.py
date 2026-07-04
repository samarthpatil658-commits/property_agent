import streamlit as st
import time
import html
from typing import Dict, Any, Optional, List

from agent import HomeFinderAgent, run_agent
from charts import show_price_comparison, show_rating_chart
from display import show_property_card
from ui_state import (
    ensure_ui_state,
    find_property_item,
    selected_items,
    set_selected_property,
    toggle_property_id,
)


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="NestFind - Find Your Dream Home",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
def format_money(value: Optional[float]) -> str:
    """Format money value with proper currency display."""
    if value is None:
        return "Not set"
    try:
        if value >= 10_000_000:
            return f"₹ {value / 10_000_000:.2f} Cr"
        return f"₹ {value / 100_000:.0f} L"
    except (TypeError, ValueError):
        return "Not set"


def profile_value(value: Any) -> str:
    """Format profile values with proper display."""
    if value in (None, "", [], {}):
        return "—"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, list):
        return ", ".join(str(v) for v in value) if value else "—"
    return str(value)


# ============================================================================
# STATE MANAGEMENT
# ============================================================================
def ensure_state():
    """Initialize all session state variables."""
    ensure_ui_state(st.session_state)
    
    if "agent" not in st.session_state:
        st.session_state.agent = HomeFinderAgent()
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "last_result" not in st.session_state:
        st.session_state.last_result = None
    
    if "shortlist" not in st.session_state:
        st.session_state.shortlist = []
    
    if "compare" not in st.session_state:
        st.session_state.compare = []
    
    if "selected_property_id" not in st.session_state:
        st.session_state.selected_property_id = None
    
    if "show_tool_trace" not in st.session_state:
        st.session_state.show_tool_trace = False
    
    if "run_count" not in st.session_state:
        st.session_state.run_count = 0


def reset_demo_state():
    """Reset all session state to initial values."""
    st.session_state.messages = []
    st.session_state.last_result = None
    st.session_state.shortlist = []
    st.session_state.compare = []
    st.session_state.selected_property_id = None
    st.session_state.agent = HomeFinderAgent()
    st.session_state.run_count = 0


def handle_property_actions(actions: Dict[str, Any]) -> None:
    """Handle property card action buttons."""
    if not actions:
        return

    property_id = actions.get("property_id")
    if not property_id:
        return
    
    if actions.get("details"):
        set_selected_property(st.session_state, property_id)
        st.toast("📋 Property details opened", icon="📋")
    
    if actions.get("compare"):
        added = toggle_property_id(st.session_state, "compare", property_id, limit=3)
        if added:
            st.toast("➕ Added to comparison", icon="➕")
        else:
            st.toast("➖ Removed from comparison", icon="➖")
    
    if actions.get("shortlist"):
        added = toggle_property_id(st.session_state, "shortlist", property_id)
        if added:
            st.toast("⭐ Added to shortlist", icon="⭐")
        else:
            st.toast("🗑️ Removed from shortlist", icon="🗑️")


# ============================================================================
# CSS STYLING
# ============================================================================
def inject_css():
    """Inject custom CSS for the application."""
    st.markdown(
        """
        <style>
        /* Hide sidebar completely */
        [data-testid="stSidebar"] {
            display: none !important;
        }
        
        [data-testid="collapsedControl"] {
            display: none !important;
        }
        
        /* Main container */
        .stApp {
            background: radial-gradient(circle at 20% 0%, rgba(100, 210, 255, 0.08), transparent 40rem),
                        linear-gradient(180deg, #07090f 0%, #0b0f18 100%);
            color: #f7f8fb;
        }

        .block-container {
            max-width: 1300px;
            padding-top: 1.5rem;
            padding-bottom: 3rem;
        }

        /* Hero Section */
        .hero {
            background: linear-gradient(135deg, 
                rgba(17, 21, 32, 0.8) 0%, 
                rgba(25, 31, 46, 0.6) 50%,
                rgba(17, 21, 32, 0.8) 100%
            );
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 20px;
            padding: 3rem 3.5rem;
            margin-bottom: 2rem;
            backdrop-filter: blur(12px);
            position: relative;
            overflow: hidden;
        }

        .hero::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -20%;
            width: 60%;
            height: 200%;
            background: radial-gradient(ellipse, rgba(100, 210, 255, 0.05), transparent 70%);
            pointer-events: none;
        }

        .hero .logo {
            font-size: 3rem;
            font-weight: 800;
            background: linear-gradient(135deg, #64d2ff 0%, #9ae6b4 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: inline-block;
            letter-spacing: -0.5px;
        }

        .hero .tagline {
            color: #64d2ff;
            font-size: 1.1rem;
            font-weight: 500;
            letter-spacing: 0.3px;
            opacity: 0.9;
            margin-top: 0.5rem;
        }

        .hero h1 {
            font-size: clamp(2.2rem, 4vw, 3.5rem);
            font-weight: 700;
            margin: 0.2rem 0 0.5rem;
            color: #f7f8fb;
            letter-spacing: -0.5px;
            line-height: 1.1;
        }

        .hero-copy {
            color: #c9d1dc;
            font-size: 1.05rem;
            line-height: 1.7;
            margin-top: 0.2rem;
            max-width: 600px;
            opacity: 0.9;
        }

        .hero-pills {
            display: flex;
            flex-wrap: wrap;
            gap: 0.6rem;
            margin-top: 1.2rem;
        }

        .pill {
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 999px;
            padding: 0.35rem 1rem;
            color: #dbe4ef;
            background: rgba(255, 255, 255, 0.04);
            font-size: 0.8rem;
            transition: all 0.3s ease;
        }

        .pill:hover {
            background: rgba(100, 210, 255, 0.08);
            border-color: rgba(100, 210, 255, 0.2);
            transform: translateY(-1px);
        }

        /* Prompt suggestion box */
        .prompt-box {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 14px;
            padding: 0.8rem 1.2rem;
            margin-bottom: 1.5rem;
            transition: border-color 0.3s ease;
        }

        .prompt-box:hover {
            border-color: rgba(100, 210, 255, 0.2);
        }

        .prompt-box .label {
            color: #9aa4b2;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .prompt-box .text {
            color: #dbe4ef;
            font-family: monospace;
            font-size: 0.85rem;
            margin-top: 0.2rem;
            padding: 0.4rem 0.6rem;
            background: rgba(0,0,0,0.3);
            border-radius: 6px;
            border-left: 3px solid #64d2ff;
        }

        /* Tabs */
        .tabs-container {
            background: rgba(17, 21, 32, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 14px;
            padding: 0.5rem;
            margin-bottom: 1.5rem;
            backdrop-filter: blur(12px);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.2rem;
            background: transparent;
            padding: 0;
            border: none;
            flex-wrap: wrap;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 10px;
            padding: 0.7rem 1.4rem;
            background: transparent;
            color: #9aa4b2;
            font-weight: 500;
            font-size: 0.85rem;
            transition: all 0.3s ease;
            border: none;
            letter-spacing: 0.3px;
            position: relative;
        }

        .stTabs [data-baseweb="tab"]:hover {
            color: #f7f8fb;
            background: rgba(255, 255, 255, 0.05);
            transform: translateY(-1px);
        }

        .stTabs [aria-selected="true"] {
            background: rgba(100, 210, 255, 0.15);
            color: #f7f8fb;
            border: 1px solid rgba(100, 210, 255, 0.25);
            box-shadow: 0 4px 15px rgba(100, 210, 255, 0.15);
            font-weight: 600;
        }

        .stTabs [aria-selected="true"]::after {
            content: '';
            position: absolute;
            bottom: -1px;
            left: 20%;
            right: 20%;
            height: 2px;
            background: linear-gradient(90deg, #64d2ff, #9ae6b4);
            border-radius: 2px;
        }

        .stTabs [data-baseweb="tab-panel"] {
            padding-top: 1rem;
        }

        /* Chat */
        .chat-shell {
            background: rgba(17, 21, 32, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 14px;
            padding: 1.5rem;
            min-height: 30rem;
            max-height: 38rem;
            overflow-y: auto;
            backdrop-filter: blur(12px);
            margin-bottom: 0.5rem;
        }

        .chat-shell::-webkit-scrollbar {
            width: 5px;
        }

        .chat-shell::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.02);
            border-radius: 10px;
        }

        .chat-shell::-webkit-scrollbar-thumb {
            background: rgba(100, 210, 255, 0.3);
            border-radius: 10px;
        }

        .chat-message {
            padding: 0.9rem 1.2rem;
            border-radius: 14px;
            margin-bottom: 0.8rem;
            max-width: 85%;
            animation: fadeIn 0.4s ease;
            line-height: 1.6;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .chat-message.user {
            background: linear-gradient(135deg, rgba(100, 210, 255, 0.15), rgba(100, 210, 255, 0.05));
            border: 1px solid rgba(100, 210, 255, 0.2);
            margin-left: auto;
            color: #f7f8fb;
            border-bottom-right-radius: 4px;
        }

        .chat-message.assistant {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
            margin-right: auto;
            color: #f7f8fb;
            border-bottom-left-radius: 4px;
        }

        .chat-role {
            font-size: 0.65rem;
            font-weight: 700;
            text-transform: uppercase;
            color: #9aa4b2;
            margin-bottom: 0.3rem;
            letter-spacing: 0.5px;
        }

        .chat-role.user-role {
            color: #64d2ff;
        }

        .chat-role.assistant-role {
            color: #9ae6b4;
        }

        /* Fixed chat input */
        div[data-testid="stChatInput"] {
            position: sticky;
            bottom: 0;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            background: rgba(17, 21, 32, 0.9);
            backdrop-filter: blur(12px);
            padding: 0.3rem;
            margin-top: 0.5rem;
            z-index: 10;
        }

        div[data-testid="stChatInput"] > div {
            background: transparent;
            border-radius: 10px;
        }

        div[data-testid="stChatInput"] textarea {
            color: #f7f8fb;
            font-size: 0.95rem;
        }

        /* Buttons */
        .stButton > button {
            border-radius: 12px !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            background: rgba(255, 255, 255, 0.04) !important;
            color: #f7f8fb !important;
            padding: 0.5rem 1.5rem !important;
            transition: all 0.3s ease !important;
            font-size: 0.85rem !important;
            font-weight: 500 !important;
            letter-spacing: 0.3px !important;
        }

        .stButton > button:hover {
            background: rgba(255, 255, 255, 0.08) !important;
            border-color: rgba(255, 255, 255, 0.15) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
        }

        /* Analytics Metrics */
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            margin: 1rem 0;
        }

        .metric-box {
            background: rgba(17, 21, 32, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 14px;
            padding: 1.5rem;
            text-align: center;
            backdrop-filter: blur(8px);
            transition: all 0.3s ease;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }

        .metric-box:hover {
            transform: translateY(-2px);
            border-color: rgba(100, 210, 255, 0.15);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
        }

        .metric-box .number {
            font-size: 2.2rem;
            font-weight: 700;
            color: #f7f8fb;
            letter-spacing: -0.5px;
        }

        .metric-box .label {
            color: #9aa4b2;
            font-size: 0.8rem;
            font-weight: 500;
            margin-top: 0.3rem;
        }

        /* Responsive */
        @media (max-width: 860px) {
            .chat-message {
                max-width: 95%;
            }
            .hero {
                padding: 1.5rem;
            }
            .hero .logo {
                font-size: 2.2rem;
            }
            .metric-grid {
                grid-template-columns: 1fr;
            }
            .stTabs [data-baseweb="tab"] {
                padding: 0.4rem 0.8rem;
                font-size: 0.75rem;
            }
            .chat-shell {
                min-height: 20rem;
                max-height: 25rem;
            }
        }

        @media (max-width: 480px) {
            .block-container {
                padding: 0.5rem;
            }
            .hero .logo {
                font-size: 1.8rem;
            }
            .hero {
                padding: 1rem;
            }
            .stTabs [data-baseweb="tab"] {
                padding: 0.3rem 0.5rem;
                font-size: 0.7rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================================
# RENDER FUNCTIONS
# ============================================================================
def render_hero():
    """Render the hero section with logo only."""
    st.markdown(
        """
        <div class="hero">
            <div class="logo">NestFind</div>
            <div class="tagline">AI-Powered Real Estate Consultant</div>
            <h1>Find Your Dream Home</h1>
            <p class="hero-copy">
                Build your buyer profile, search listings, check neighbourhoods, 
                schools, commute, and price history — all in one conversation.
            </p>
            <div class="hero-pills">
                <span class="pill">📍 Bangalore</span>
                <span class="pill">🤖 AI Assistant</span>
                <span class="pill">📊 Smart Ranking</span>
                <span class="pill">💡 Investment Insights</span>
                <span class="pill">🏫 School Ratings</span>
                <span class="pill">🚗 Commute Analysis</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_prompt_suggestion():
    """Render the prompt suggestion box."""
    st.markdown(
        """
        <div class="prompt-box">
            <div class="label">💡 Try saying</div>
            <div class="text">"I need a 3 BHK apartment in Electronic City under 90 lakh with schools nearby"</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chat() -> None:
    """Render the chat interface."""
    st.markdown('<div class="chat-shell">', unsafe_allow_html=True)
    
    if not st.session_state.messages:
        st.markdown(
            """
            <div class="chat-message assistant">
                <div class="chat-role assistant-role">🏠 NestFind</div>
                Tell me what you're looking for in Bangalore.<br>
                <span style="color: #9aa4b2; font-size: 0.85rem;">
                    Example: "3 BHK near Electronic City under 90 lakh with schools nearby"
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    for message in st.session_state.messages:
        role_class = "user" if message["role"] == "user" else "assistant"
        role_label = "You" if message["role"] == "user" else "NestFind"
        role_style = "user-role" if message["role"] == "user" else "assistant-role"
        
        st.markdown(
            f"""
            <div class="chat-message {role_class}">
                <div class="chat-role {role_style}">{role_label}</div>
                {message["content"]}
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    st.markdown("</div>", unsafe_allow_html=True)


def render_results(result: Optional[Dict[str, Any]]) -> None:
    """Render property results."""
    if not result or result.get("type") != "recommendation":
        st.info("Start a conversation to see property recommendations.")
        return

    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: center; margin: 0.5rem 0 1rem;">
            <div>
                <h2 style="font-size: 1.2rem; margin: 0; color: #f7f8fb;">🏠 Property Results</h2>
                <p style="color: #9aa4b2; margin: 0; font-size: 0.85rem;">Ranked recommendations with confidence scores</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    results = result.get("results", [])
    if not results:
        st.warning("No properties matched. Try adjusting your criteria.")
        return

    st.caption(
        f"⭐ Shortlisted: {len(st.session_state.shortlist)} | "
        f"⚖️ Comparing: {len(st.session_state.compare)}/3"
    )

    for rank, item in enumerate(results, start=1):
        actions = show_property_card(item, rank=rank, key_prefix="results")
        handle_property_actions(actions)


def render_property_details(result: Optional[Dict[str, Any]]) -> None:
    """Render property details view."""
    results = result.get("results", []) if result else []
    if not results:
        st.info("Search for properties to see details.")
        return

    item = find_property_item(result, st.session_state.selected_property_id) or results[0]
    
    col1, col2 = st.columns([1, 1])
    with col1:
        actions = show_property_card(item, rank=1, key_prefix="details")
        handle_property_actions(actions)
    with col2:
        st.markdown("""
        <div style="background: rgba(17,21,32,0.6); border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; padding: 1.5rem; backdrop-filter: blur(12px);">
            <h3 style="color: #f7f8fb; margin-bottom: 0.5rem;">📋 Property Details</h3>
            <hr style="border-color: rgba(255,255,255,0.06); margin: 0.5rem 0 1rem;">
        """, unsafe_allow_html=True)
        
        prop = item.get("property", {})
        st.markdown(f"""
        <div style="margin-bottom: 1rem;">
            <p style="color: #9aa4b2; font-size: 0.8rem; margin: 0;">📍 Location</p>
            <p style="color: #f7f8fb; font-size: 1.1rem; font-weight: 600; margin: 0;">{prop.get('location', 'N/A')}</p>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem; margin-bottom: 1rem;">
            <div>
                <p style="color: #9aa4b2; font-size: 0.8rem; margin: 0;">💰 Price</p>
                <p style="color: #64d2ff; font-size: 1.1rem; font-weight: 600; margin: 0;">{format_money(prop.get('price'))}</p>
            </div>
            <div>
                <p style="color: #9aa4b2; font-size: 0.8rem; margin: 0;">🏠 BHK</p>
                <p style="color: #f7f8fb; font-size: 1.1rem; font-weight: 600; margin: 0;">{prop.get('bhk', 'N/A')}</p>
            </div>
            <div>
                <p style="color: #9aa4b2; font-size: 0.8rem; margin: 0;">📐 Area</p>
                <p style="color: #f7f8fb; font-size: 1.1rem; font-weight: 600; margin: 0;">{prop.get('area_sqft', 'N/A')} sqft</p>
            </div>
            <div>
                <p style="color: #9aa4b2; font-size: 0.8rem; margin: 0;">⭐ Rating</p>
                <p style="color: #9ae6b4; font-size: 1.1rem; font-weight: 600; margin: 0;">{prop.get('rating', 'N/A')}/5</p>
            </div>
        </div>
        <hr style="border-color: rgba(255,255,255,0.06); margin: 0.5rem 0 1rem;">
        """, unsafe_allow_html=True)
        
        st.markdown('<h4 style="color: #9ae6b4; margin-top: 0.5rem;">✅ Strengths</h4>', unsafe_allow_html=True)
        for value in item.get("pros", []) or ["None listed"]:
            st.success(value)
        
        st.markdown('<h4 style="color: #facc15; margin-top: 1rem;">⚠️ Trade-offs</h4>', unsafe_allow_html=True)
        for value in item.get("tradeoffs", []) or ["None listed"]:
            st.info(value)
        
        st.markdown('<h4 style="color: #fb7185; margin-top: 1rem;">🔴 Watch-outs</h4>', unsafe_allow_html=True)
        for value in item.get("cons", []) or ["None listed"]:
            st.warning(value)
        
        st.markdown('<h4 style="color: #9aa4b2; margin-top: 1rem;">🔧 Tools Used</h4>', unsafe_allow_html=True)
        tools_used = item.get("tools_used", [])
        if tools_used:
            st.write(", ".join(tools_used))
        else:
            st.write("No tools recorded.")
        
        st.markdown("</div>", unsafe_allow_html=True)


def render_comparison(result: Optional[Dict[str, Any]]) -> None:
    """Render property comparison view."""
    results = result.get("results", []) if result else []
    selected = selected_items(result, st.session_state.compare)
    items = selected or results[:3]
    
    st.markdown(
        """
        <div style="margin: 0.5rem 0 1rem;">
            <h2 style="font-size: 1.2rem; margin: 0; color: #f7f8fb;">⚖️ Compare Properties</h2>
            <p style="color: #9aa4b2; margin: 0; font-size: 0.85rem;">Side-by-side comparison of selected properties</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    if not items:
        st.info("Select properties to compare using the compare button on property cards.")
        return

    rows = []
    for item in items[:5]:
        prop = item.get("property", {})
        rows.append({
            "Property": prop.get("name", "N/A"),
            "Location": prop.get("location", "N/A"),
            "Price": format_money(prop.get("price")),
            "BHK": prop.get("bhk", "N/A"),
            "Rating": f"{prop.get('rating', 0):.1f}",
            "ROI": f"{prop.get('roi', 0)}%",
            "Match": item.get("match", "N/A"),
            "Confidence": f"{item.get('confidence', 0)}%",
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)


def render_analytics(result: Optional[Dict[str, Any]]) -> None:
    """Render analytics view."""
    results = result.get("results", []) if result else []
    
    st.markdown(
        """
        <div style="margin: 0.5rem 0 1rem;">
            <h2 style="font-size: 1.2rem; margin: 0; color: #f7f8fb;">📊 Analytics</h2>
            <p style="color: #9aa4b2; margin: 0; font-size: 0.85rem;">Market intelligence from your search results</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    if not results:
        st.info("Analytics available after search.")
        return

    properties = [item.get("property", {}) for item in results if item.get("property")]
    if not properties:
        st.info("No property data available for analytics.")
        return
    
    avg_price = sum(p.get("price", 0) for p in properties) / len(properties)
    avg_rating = sum(p.get("rating", 0) for p in properties) / len(properties)
    avg_roi = sum(p.get("roi", 0) for p in properties) / len(properties)
    
    st.markdown(f"""
    <div class="metric-grid">
        <div class="metric-box">
            <div class="number">{len(properties)}</div>
            <div class="label">Properties Found</div>
        </div>
        <div class="metric-box">
            <div class="number">{format_money(avg_price)}</div>
            <div class="label">Average Price</div>
        </div>
        <div class="metric-box">
            <div class="number">{avg_rating:.1f}</div>
            <div class="label">Average Rating</div>
        </div>
        <div class="metric-box">
            <div class="number">{avg_roi:.1f}%</div>
            <div class="label">Average ROI</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        show_rating_chart(properties)
    with col2:
        show_price_comparison(properties)


def render_shortlist(result: Optional[Dict[str, Any]]) -> None:
    """Render shortlist view."""
    st.markdown(
        """
        <div style="margin: 0.5rem 0 1rem;">
            <h2 style="font-size: 1.2rem; margin: 0; color: #f7f8fb;">⭐ Shortlist</h2>
            <p style="color: #9aa4b2; margin: 0; font-size: 0.85rem;">Your saved properties</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    items = selected_items(result, st.session_state.shortlist)
    if not items:
        st.info("Use the shortlist button on property cards to save properties here.")
        return

    rows = []
    for item in items:
        prop = item.get("property", {})
        rows.append({
            "Property": prop.get("name", "N/A"),
            "Location": prop.get("location", "N/A"),
            "Price": format_money(prop.get("price")),
            "Match": item.get("match", "N/A"),
            "Confidence": f"{item.get('confidence', 0)}%",
            "Rating": f"{prop.get('rating', 0):.1f}",
            "ROI": f"{prop.get('roi', 0)}%",
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)


def render_settings() -> None:
    """Render settings view."""
    st.markdown(
        """
        <div style="margin: 0.5rem 0 1rem;">
            <h2 style="font-size: 1.2rem; margin: 0; color: #f7f8fb;">⚙️ Settings</h2>
            <p style="color: #9aa4b2; margin: 0; font-size: 0.85rem;">Manage your session and preferences</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 New Conversation", use_container_width=True):
            reset_demo_state()
            st.rerun()
    with col2:
        st.markdown("""
        <div style="background: rgba(17,21,32,0.6); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 0.8rem 1rem; backdrop-filter: blur(8px);">
            <div style="color: #9aa4b2; font-size: 0.7rem;">Session Status</div>
            <div style="color: #9ae6b4; font-size: 0.8rem; font-weight: 600;">● Active</div>
        </div>
        """, unsafe_allow_html=True)


# ============================================================================
# MAIN APPLICATION
# ============================================================================
def main():
    """Main application entry point."""
    ensure_state()
    inject_css()
    
    render_hero()
    render_prompt_suggestion()
    
    st.markdown('<div class="tabs-container">', unsafe_allow_html=True)
    tabs = st.tabs([
        "💬 Chat",
        "🏠 Results",
        "📄 Details",
        "⚖️ Compare",
        "📊 Analytics",
        "⭐ Shortlist",
        "⚙️ Settings"
    ])
    st.markdown('</div>', unsafe_allow_html=True)
    
    last_result = st.session_state.last_result
    
    with tabs[0]:
        render_chat()
    
    with tabs[1]:
        render_results(last_result)
    
    with tabs[2]:
        render_property_details(last_result)
    
    with tabs[3]:
        render_comparison(last_result)
    
    with tabs[4]:
        render_analytics(last_result)
    
    with tabs[5]:
        render_shortlist(last_result)
    
    with tabs[6]:
        render_settings()
    
    prompt = st.chat_input("💬 Describe what you're looking for...")
    
    if prompt:
        st.session_state.run_count += 1
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.status("🔍 Searching...", expanded=True) as status:
            st.write("🧠 Understanding buyer intent")
            st.write("📋 Planning tool calls")
            st.write("🔎 Searching and enriching properties")
            
            try:
                result = run_agent(prompt, agent=st.session_state.agent)
                status.update(label="✅ Done", state="complete", expanded=False)
            except Exception as e:
                st.error(f"Error: {str(e)}")
                status.update(label="❌ Failed", state="error", expanded=False)
                return
        
        st.session_state.last_result = result
        
        if result.get("type") == "question":
            assistant_text = result.get("message", "I need more information to help you.")
        else:
            count = len(result.get("results", []))
            explanation = result.get("explanation", "")
            assistant_text = explanation or f"I found {count} matching properties."
        
        st.session_state.messages.append({"role": "assistant", "content": assistant_text})
        st.rerun()


if __name__ == "__main__":
    main()