import pandas as pd
import plotly.express as px
import streamlit as st


CHART_TEMPLATE = "plotly_dark"
CHART_LAYOUT = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"color": "#e8edf5"},
    "margin": {"l": 20, "r": 20, "t": 58, "b": 30},
}


def _show(fig):
    fig.update_layout(**CHART_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)


def show_price_history(price_data):
    """Display property price history as an interactive line chart."""

    if not price_data:
        st.warning("No price history available.")
        return

    if isinstance(price_data[0], (int, float)):
        df = pd.DataFrame(
            {
                "Year": list(range(2021, 2021 + len(price_data))),
                "Price": price_data,
            }
        )
    else:
        df = pd.DataFrame(price_data).rename(columns={"year": "Year", "price": "Price"})

    fig = px.line(
        df,
        x="Year",
        y="Price",
        markers=True,
        title="Price trend",
        labels={"Price": "Average price / sqft"},
        template=CHART_TEMPLATE,
    )
    _show(fig)


def show_budget_comparison(budget, property_price):
    """Compare buyer budget against a property price."""

    df = pd.DataFrame(
        {
            "Category": ["Budget", "Property Price"],
            "Amount": [budget, property_price],
        }
    )
    fig = px.bar(
        df,
        x="Category",
        y="Amount",
        text="Amount",
        title="Budget comparison",
        template=CHART_TEMPLATE,
        color="Category",
        color_discrete_sequence=["#64d2ff", "#9ae6b4"],
    )
    fig.update_traces(texttemplate="Rs %{text:,}", textposition="outside")
    _show(fig)


def show_rating_chart(properties):
    """Display property ratings."""

    if not properties:
        return

    df = pd.DataFrame(
        [{"Property": p["name"], "Rating": p["rating"]} for p in properties]
    )
    fig = px.bar(
        df,
        x="Property",
        y="Rating",
        text="Rating",
        title="Property ratings",
        template=CHART_TEMPLATE,
        color="Rating",
        color_continuous_scale=["#64d2ff", "#9ae6b4"],
    )
    fig.update_layout(yaxis_range=[0, 5])
    _show(fig)


def show_price_comparison(properties):
    """Compare property prices."""

    if not properties:
        return

    df = pd.DataFrame(
        [{"Property": p["name"], "Price": p["price"]} for p in properties]
    )
    fig = px.bar(
        df,
        x="Property",
        y="Price",
        text="Price",
        title="Price comparison",
        template=CHART_TEMPLATE,
        color="Price",
        color_continuous_scale=["#64d2ff", "#9ae6b4"],
    )
    fig.update_traces(texttemplate="Rs %{text:,}", textposition="outside")
    _show(fig)
