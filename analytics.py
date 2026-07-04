def build_analytics_summary(results):
    """Build a comprehensive analytics summary from results."""
    items = _items(results)
    if not items:
        return {
            "properties": 0,
            "average_price": 0,
            "average_rating": 0,
            "average_roi": 0,
            "metro_coverage": 0,
            "best_match": "N/A",
            "price_range": {"min": 0, "max": 0},
            "top_amenities": [],
        }

    props = [item["property"] for item in items]
    metro_ready = [
        prop
        for prop in props
        if prop.get("metro_distance", 99999) <= 500
        or item_has_neighbourhood_metro(items, prop["id"])
    ]
    
    # Calculate price range
    prices = [prop["price"] for prop in props]
    
    # Get top amenities
    all_amenities = []
    for prop in props:
        all_amenities.extend(prop.get("amenities", []))
    from collections import Counter
    top_amenities = [a for a, _ in Counter(all_amenities).most_common(5)]
    
    return {
        "properties": len(props),
        "average_price": round(sum(prop["price"] for prop in props) / len(props)),
        "average_rating": round(sum(prop.get("rating", 0) for prop in props) / len(props), 2),
        "average_roi": round(sum(prop.get("roi", 0) for prop in props) / len(props), 1),
        "metro_coverage": round((len(metro_ready) / len(props)) * 100) if props else 0,
        "best_match": items[0].get("match", "N/A") if items else "N/A",
        "price_range": {
            "min": min(prices) if prices else 0,
            "max": max(prices) if prices else 0,
        },
        "top_amenities": top_amenities,
    }


def build_heatmap_rows(results):
    """Build heatmap data for property comparison."""
    rows = []
    for item in _items(results):
        prop = item["property"]
        commute = _commute_score(item)
        rows.append(
            {
                "Property": prop["name"],
                "Budget": 100 if item.get("affordability", {}).get("affordable") else 35,
                "Commute": commute,
                "Schools": _scale(prop.get("school_rating", 0), 10),
                "Metro": _metro_score(prop, item),
                "Safety": _scale(_safety_value(prop, item), 10),
                "Investment": investment_score(item),
                "Overall": item.get("score", 0),
            }
        )
    return rows


def build_locality_rows(results):
    """Build locality-based aggregation for market analysis."""
    grouped = {}
    for item in _items(results):
        prop = item["property"]
        location = prop["location"]
        
        if location not in grouped:
            grouped[location] = {
                "Locality": location,
                "Properties": 0,
                "Average Price": 0,
                "Average Rating": 0,
                "Average ROI": 0,
                "Metro Coverage": 0,
                "School Rating": 0,
                "Total Score": 0,
            }
        
        row = grouped[location]
        row["Properties"] += 1
        row["Average Price"] += prop["price"]
        row["Average Rating"] += prop.get("rating", 0)
        row["Average ROI"] += prop.get("roi", 0)
        row["School Rating"] += prop.get("school_rating", 0)
        row["Total Score"] += item.get("score", 0)
        
        # Check metro coverage
        if prop.get("metro_distance", 99999) <= 500 or item_has_neighbourhood_metro(items, prop["id"]):
            row["Metro Coverage"] += 1
    
    # Calculate averages
    result_rows = []
    for location, data in grouped.items():
        count = data["Properties"]
        result_rows.append({
            "Locality": location,
            "Properties": count,
            "Average Price": round(data["Average Price"] / count),
            "Average Rating": round(data["Average Rating"] / count, 1),
            "Average ROI": round(data["Average ROI"] / count, 1),
            "Metro Coverage": round((data["Metro Coverage"] / count) * 100),
            "School Rating": round(data["School Rating"] / count, 1),
            "Total Score": round(data["Total Score"] / count, 1),
        })
    
    # Sort by total score
    return sorted(result_rows, key=lambda x: x["Total Score"], reverse=True)


def build_price_distribution(results):
    """Build price distribution data for histogram."""
    items = _items(results)
    if not items:
        return {"bins": [], "counts": [], "labels": []}
    
    prices = [item["property"]["price"] for item in items]
    
    # Create bins
    min_price = min(prices)
    max_price = max(prices)
    if min_price == max_price:
        return {"bins": [min_price], "counts": [len(prices)], "labels": [f"₹{min_price/100000:.0f}L"]}
    
    bin_size = (max_price - min_price) / 5
    bins = []
    counts = []
    labels = []
    
    for i in range(5):
        low = min_price + (i * bin_size)
        high = min_price + ((i + 1) * bin_size)
        if i == 4:
            high = max_price + 1
        count = sum(1 for p in prices if low <= p < high)
        bins.append((low + high) / 2)
        counts.append(count)
        labels.append(f"₹{low/100000:.0f}L-₹{high/100000:.0f}L")
    
    return {"bins": bins, "counts": counts, "labels": labels}


def build_rating_distribution(results):
    """Build rating distribution data."""
    items = _items(results)
    if not items:
        return {"ratings": [], "counts": []}
    
    ratings = [item["property"].get("rating", 0) for item in items]
    
    # Group by rating
    rating_groups = {}
    for r in ratings:
        key = round(r)
        rating_groups[key] = rating_groups.get(key, 0) + 1
    
    return {
        "ratings": sorted(rating_groups.keys()),
        "counts": [rating_groups[k] for k in sorted(rating_groups.keys())],
    }


def build_amenity_analysis(results):
    """Build amenity analysis data."""
    items = _items(results)
    if not items:
        return {"amenities": [], "counts": []}
    
    from collections import Counter
    
    all_amenities = []
    for item in items:
        all_amenities.extend(item["property"].get("amenities", []))
    
    amenity_counts = Counter(all_amenities)
    return {
        "amenities": [a for a, _ in amenity_counts.most_common(10)],
        "counts": [c for _, c in amenity_counts.most_common(10)],
    }


def build_commute_analysis(results, office_location=None):
    """Build commute time analysis."""
    items = _items(results)
    if not items:
        return {"properties": [], "times": [], "labels": []}
    
    properties = []
    times = []
    labels = []
    
    for item in items:
        prop = item["property"]
        commute = item.get("commute", {})
        commute_time = commute.get("time_min", "N/A")
        
        if commute_time != "N/A":
            properties.append(prop["name"])
            times.append(commute_time)
            labels.append(f"{commute_time} min")
    
    return {
        "properties": properties,
        "times": times,
        "labels": labels,
        "average": round(sum(times) / len(times), 1) if times else 0,
        "min": min(times) if times else 0,
        "max": max(times) if times else 0,
    }


def build_investment_analysis(results):
    """Build investment potential analysis."""
    items = _items(results)
    if not items:
        return {"properties": [], "roi": [], "growth": [], "overall": []}
    
    investment_data = []
    for item in items:
        prop = item["property"]
        investment_data.append({
            "property": prop["name"],
            "roi": prop.get("roi", 0),
            "growth": prop.get("price_growth", 0),
            "score": investment_score(item),
        })
    
    # Sort by investment score
    investment_data.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "properties": [d["property"] for d in investment_data],
        "roi": [d["roi"] for d in investment_data],
        "growth": [d["growth"] for d in investment_data],
        "overall": [d["score"] for d in investment_data],
        "best_investment": investment_data[0]["property"] if investment_data else "N/A",
    }


def build_market_trends(results):
    """Build market trend analysis."""
    items = _items(results)
    if not items:
        return {"locations": [], "prices": [], "trends": []}
    
    # Group by location
    location_data = {}
    for item in items:
        prop = item["property"]
        location = prop["location"]
        if location not in location_data:
            location_data[location] = {
                "prices": [],
                "ratings": [],
                "rois": [],
            }
        location_data[location]["prices"].append(prop["price"])
        location_data[location]["ratings"].append(prop.get("rating", 0))
        location_data[location]["rois"].append(prop.get("roi", 0))
    
    trends = []
    for location, data in location_data.items():
        avg_price = sum(data["prices"]) / len(data["prices"])
        avg_rating = sum(data["ratings"]) / len(data["ratings"])
        avg_roi = sum(data["rois"]) / len(data["rois"])
        
        trends.append({
            "location": location,
            "avg_price": avg_price,
            "avg_rating": avg_rating,
            "avg_roi": avg_roi,
            "count": len(data["prices"]),
            "price_trend": "up" if len(data["prices"]) > 1 and data["prices"][-1] > data["prices"][0] else "stable",
        })
    
    return sorted(trends, key=lambda x: x["avg_rating"], reverse=True)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _items(results):
    """Extract items from results."""
    if not results:
        return []
    return results.get("results", [])


def _commute_score(item):
    """Calculate commute score (0-100)."""
    commute = item.get("commute", {})
    time_min = commute.get("time_min")
    if time_min is None:
        return 50  # Default middle score
    
    # Score: 100 for <15 min, 0 for >60 min
    if time_min <= 15:
        return 100
    elif time_min >= 60:
        return 0
    else:
        return int(100 - ((time_min - 15) / 45) * 100)


def _metro_score(prop, item):
    """Calculate metro accessibility score."""
    # Check direct metro distance
    metro_dist = prop.get("metro_distance", 99999)
    if metro_dist <= 200:
        return 100
    elif metro_dist <= 500:
        return 70
    elif metro_dist <= 1000:
        return 40
    else:
        # Check neighbourhood data
        if item_has_neighbourhood_metro([item], prop["id"]):
            return 60
        return 10


def _safety_value(prop, item):
    """Get safety score."""
    neighbourhood = item.get("neighbourhood", {})
    safety = neighbourhood.get("safety")
    if safety is not None:
        return safety
    
    crime_score = prop.get("crime_score")
    if crime_score is not None:
        return 10 - crime_score  # Invert crime score (0-10 scale)
    
    return 5  # Default


def _scale(value, max_val):
    """Scale a value to 0-100 range."""
    if value is None:
        return 50
    try:
        return min(100, max(0, int((value / max_val) * 100)))
    except (TypeError, ZeroDivisionError):
        return 50


def investment_score(item):
    """Calculate investment potential score."""
    prop = item["property"]
    score = 0
    
    # ROI contribution (max 40 points)
    roi = prop.get("roi", 0)
    if roi >= 15:
        score += 40
    elif roi >= 10:
        score += 30
    elif roi >= 5:
        score += 20
    else:
        score += 10
    
    # Price growth contribution (max 30 points)
    growth = prop.get("price_growth", 0)
    if growth >= 10:
        score += 30
    elif growth >= 5:
        score += 20
    else:
        score += 10
    
    # Rating contribution (max 30 points)
    rating = prop.get("rating", 0)
    score += int((rating / 5) * 30)
    
    return min(100, score)


def item_has_neighbourhood_metro(items, prop_id):
    """Check if a property has metro access from neighbourhood data."""
    for item in items:
        if item["property"]["id"] == prop_id:
            neighbourhood = item.get("neighbourhood", {})
            return neighbourhood.get("metro", False)
    return False


# ============================================================================
# RENDER FUNCTIONS FOR ANALYTICS
# ============================================================================

def render_analytics_dashboard(result):
    """Render a comprehensive analytics dashboard."""
    if not result or result.get("type") != "recommendation":
        st.info("Run a search to see analytics.")
        return
    
    # Build all analytics data
    summary = build_analytics_summary(result)
    locality_data = build_locality_rows(result)
    price_dist = build_price_distribution(result)
    rating_dist = build_rating_distribution(result)
    amenity_data = build_amenity_analysis(result)
    commute_data = build_commute_analysis(result)
    investment_data = build_investment_analysis(result)
    market_trends = build_market_trends(result)
    
    # Display summary metrics
    st.markdown("### 📊 Market Summary")
    cols = st.columns(5)
    cols[0].metric("Properties", summary["properties"])
    cols[1].metric("Avg Price", format_money(summary["average_price"]))
    cols[2].metric("Avg Rating", f"{summary['average_rating']}/5")
    cols[3].metric("Avg ROI", f"{summary['average_roi']}%")
    cols[4].metric("Metro Coverage", f"{summary['metro_coverage']}%")
    
    # Display locality breakdown
    if locality_data:
        st.markdown("### 📍 Locality Breakdown")
        st.dataframe(locality_data, use_container_width=True, hide_index=True)
    
    # Display price distribution
    if price_dist.get("counts"):
        st.markdown("### 💰 Price Distribution")
        import plotly.express as px
        fig = px.bar(
            x=price_dist["labels"],
            y=price_dist["counts"],
            title="Property Price Distribution",
            labels={"x": "Price Range", "y": "Number of Properties"},
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#f7f8fb",
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Display amenity analysis
    if amenity_data.get("amenities"):
        st.markdown("### 🏷️ Top Amenities")
        cols = st.columns(5)
        for idx, (amenity, count) in enumerate(zip(amenity_data["amenities"][:5], amenity_data["counts"][:5])):
            with cols[idx]:
                st.metric(amenity, count)
    
    # Display investment analysis
    if investment_data.get("properties"):
        st.markdown("### 📈 Investment Analysis")
        cols = st.columns(3)
        cols[0].metric("Top Investment", investment_data["best_investment"])
        cols[1].metric("Avg ROI", f"{sum(investment_data['roi']) / len(investment_data['roi']):.1f}%")
        cols[2].metric("Avg Growth", f"{sum(investment_data['growth']) / len(investment_data['growth']):.1f}%")
        
        # Investment comparison chart
        fig = px.bar(
            x=investment_data["properties"][:5],
            y=investment_data["overall"][:5],
            title="Top 5 Investment Options",
            labels={"x": "Property", "y": "Investment Score"},
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#f7f8fb",
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Display market trends
    if market_trends:
        st.markdown("### 📊 Market Trends by Location")
        trend_df = pd.DataFrame(market_trends)
        st.dataframe(trend_df, use_container_width=True, hide_index=True)

        