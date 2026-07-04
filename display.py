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
    property_data = item["property"]

    score = item.get("score", 0)
    match = item.get("match", f"{score}%")
    confidence = item.get("confidence", 90)

    reasons = item.get("reason", [])
    cons = item.get("cons", [])
    tradeoffs = item.get("tradeoffs", [])

    affordability = item.get("affordability", {})
    commute = item.get("commute", {})
    neighbourhood = item.get("neighbourhood", {})
    schools = item.get("schools", [])

    price_per_sqft = property_data["price"] / property_data["area_sqft"]

    budget_text = (
        f"Within Budget • {_money(affordability.get('remaining_budget'))} left"
        if affordability.get("affordable")
        else f"Short by {_money(affordability.get('shortfall'))}"
    )

    commute_text = commute.get("time_min", "N/A")
    if commute_text != "N/A":
        commute_text = f"{commute_text} min"

    metro = (
        "Nearby"
        if neighbourhood.get("metro")
        else f"{property_data.get('metro_distance','N/A')} m"
    )

    with st.container(border=True):

        c1, c2 = st.columns([5,1])

        with c1:
            st.subheader(
                f"{'#'+str(rank)+' ' if rank else ''}{property_data['name']}"
            )

            st.caption(
                f"📍 {property_data['location']} • "
                f"{property_data['bhk']} BHK • "
                f"{property_data['area_sqft']} sqft"
            )

        with c2:
            st.metric("Match", match)

        m1, m2, m3, m4 = st.columns(4)

        m1.metric("Price", _money(property_data["price"]))
        m2.metric("Rating", f"{property_data['rating']}/5")
        m3.metric("Confidence", f"{confidence}%")
        m4.metric("ROI", f"{property_data.get('roi','N/A')}%")

        m5, m6, m7, m8 = st.columns(4)

        m5.metric("Price/sqft", f"₹ {price_per_sqft:,.0f}")
        m6.metric("Metro", metro)
        m7.metric("Commute", commute_text)
        m8.metric(
            "Safety",
            neighbourhood.get(
                "safety",
                property_data.get("crime_score","N/A")
            )
        )

        st.write("### Amenities")
        st.write(" • ".join(property_data.get("amenities", [])))

        st.write("### Why this property?")

        for reason in reasons:
            st.success(reason)

        col1, col2 = st.columns(2)

        with col1:
            st.info(f"💰 {budget_text}")
            st.info(
                f"🏫 Schools: "
                f"{len(schools) if schools else property_data.get('school_rating','N/A')}"
            )

        with col2:
            st.info(
                f"📈 Growth: "
                f"{property_data.get('price_growth','N/A')}%"
            )

        if tradeoffs:
            st.write("### Trade-offs")
            for t in tradeoffs:
                st.warning(t)

        if cons:
            st.write("### Things to Watch")
            for c in cons:
                st.error(c)

    c1, c2, c3 = st.columns(3)

    pid = property_data["id"]

    return {
        "property_id": pid,
        "details": c1.button(
            "📄 Details",
            key=f"{key_prefix}_view_{pid}",
            use_container_width=True,
        ),
        "compare": c2.button(
            "⚖ Compare",
            key=f"{key_prefix}_compare_{pid}",
            use_container_width=True,
        ),
        "shortlist": c3.button(
            "⭐ Shortlist",
            key=f"{key_prefix}_save_{pid}",
            use_container_width=True,
        ),
    }