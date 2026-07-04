import html

import streamlit as st


PROPERTY_VISUALS = [
    ("#172033", "#2f80ed", "#9ae6b4"),
    ("#1d2233", "#a855f7", "#64d2ff"),
    ("#16251f", "#22c55e", "#facc15"),
    ("#241d2b", "#fb7185", "#38bdf8"),
    ("#202033", "#818cf8", "#f8fafc"),
]


def _money(value):
    if value is None:
        return "N/A"
    if value >= 10_000_000:
        return f"Rs {value / 10_000_000:.2f} Cr"
    return f"Rs {value / 100_000:.0f} L"


def _list_items(items):
    if not items:
        return "<li>Recommendation generated from available market signals.</li>"
    return "".join(f"<li>{html.escape(str(item))}</li>" for item in items)


def show_property_card(item, rank=None, key_prefix="property"):
    """Render a premium property recommendation card and return button clicks."""

    property_data = item["property"]
    score = item.get("score", 0)
    match = item.get("match", f"{score}%")
    confidence = item.get("confidence", 90)
    reasons = item.get("reason", [])
    cons = item.get("cons", [])
    tradeoffs = item.get("tradeoffs", [])
    affordability = item.get("affordability", {})
    commute = item.get("commute", {})
    schools = item.get("schools", [])
    neighbourhood = item.get("neighbourhood", {})
    ai_summary = item.get("ai_summary", "AI summary will appear after ranking completes.")

    price_per_sqft = property_data["price"] / property_data["area_sqft"]
    affordable = affordability.get("affordable")
    budget_text = (
        f"Within budget, {_money(affordability.get('remaining_budget'))} buffer"
        if affordable
        else f"{_money(affordability.get('shortfall'))} shortfall"
    )

    commute_text = commute.get("time_min", "N/A")
    if commute_text != "N/A":
        commute_text = f"{commute_text} min"

    safety = neighbourhood.get("safety", property_data.get("crime_score", "N/A"))
    metro = "Yes" if neighbourhood.get("metro") else f"{property_data.get('metro_distance', 'N/A')} m"
    title_prefix = f"#{rank} " if rank else ""
    visual = PROPERTY_VISUALS[property_data["id"] % len(PROPERTY_VISUALS)]

    st.markdown(
        f"""
        <article class="property-card">
            <div class="property-visual" style="background: linear-gradient(135deg, {visual[0]}, {visual[1]} 56%, {visual[2]});">
                <div class="property-visual-overlay">
                    <span>{html.escape(property_data["location"])}</span>
                    <strong>{property_data["bhk"]} BHK</strong>
                </div>
            </div>
            <div class="property-top">
                <div>
                    <p class="property-name">{title_prefix}{html.escape(property_data["name"])}</p>
                    <div class="property-location">{html.escape(property_data["location"])} | {property_data["bhk"]} BHK | {property_data["area_sqft"]} sqft</div>
                </div>
                <div class="score-badge">{match}</div>
            </div>
            <div class="card-metrics">
                <div class="card-metric"><small>Price</small><strong>{_money(property_data["price"])}</strong></div>
                <div class="card-metric"><small>Confidence</small><strong>{confidence}%</strong></div>
                <div class="card-metric"><small>Rating</small><strong>{property_data["rating"]}/5</strong></div>
                <div class="card-metric"><small>Price / sqft</small><strong>Rs {price_per_sqft:,.0f}</strong></div>
                <div class="card-metric"><small>Metro</small><strong>{metro}</strong></div>
                <div class="card-metric"><small>Commute</small><strong>{commute_text}</strong></div>
                <div class="card-metric"><small>Safety</small><strong>{safety}</strong></div>
                <div class="card-metric"><small>ROI</small><strong>{property_data.get("roi", "N/A")}%</strong></div>
            </div>
            <div class="pill-row">
                {"".join(f'<span class="pill">{html.escape(str(a))}</span>' for a in property_data.get("amenities", []))}
            </div>
            <ul class="reason-list">{_list_items(reasons)}</ul>
            <div class="pill-row">
                <span class="pill">{budget_text}</span>
                <span class="pill">Schools: {len(schools) if schools else property_data.get("school_rating", "N/A")}</span>
                <span class="pill">Growth: {property_data.get("price_growth", "N/A")}%</span>
            </div>
            <div class="pill-row">
                {"".join(f'<span class="pill">Trade-off: {html.escape(str(t))}</span>' for t in tradeoffs[:2])}
                {"".join(f'<span class="pill">Watch: {html.escape(str(c))}</span>' for c in cons[:2])}
            </div>
            <div class="ai-summary">
                <small>AI Summary</small>
                <p>{html.escape(ai_summary)}</p>
            </div>
        </article>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    prop_id = property_data["id"]
    return {
        "property_id": prop_id,
        "details": c1.button("Details", key=f"{key_prefix}_view_{prop_id}", use_container_width=True),
        "compare": c2.button("Compare", key=f"{key_prefix}_compare_{prop_id}", use_container_width=True),
        "shortlist": c3.button("Shortlist", key=f"{key_prefix}_save_{prop_id}", use_container_width=True),
    }
