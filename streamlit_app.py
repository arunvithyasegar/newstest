import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
import json
from datetime import datetime
import re
from textblob import TextBlob
import time
import plotly.express as px
import plotly.graph_objects as go
from streamlit_lottie import st_lottie

# Set page configuration
st.set_page_config(
    page_title="Guidance Tamil Nadu Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Function to load Lottie animations
def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# Function to extract country mentions from text
def extract_country(text):
    # List of common countries that might be mentioned in business news
    countries = ["India", "USA", "China", "Japan", "Germany", "UK", "France", 
                 "South Korea", "Taiwan", "Malaysia", "Vietnam", "Singapore", 
                 "Thailand", "Indonesia", "Philippines", "Europe", "Tamil Nadu"]
    
    found_countries = []
    for country in countries:
        if re.search(r'\b' + re.escape(country) + r'\b', text, re.IGNORECASE):
            found_countries.append(country)
    
    if found_countries:
        return ", ".join(found_countries)
    return "Global"

# Function to perform sentiment analysis
def analyze_sentiment(text):
    analysis = TextBlob(text)
    polarity = analysis.sentiment.polarity
    
    if polarity > 0.1:
        return "Positive"
    elif polarity < -0.1:
        return "Negative"
    else:
        return "Neutral"

# Function to fetch news
def fetch_news(api_key, query="electronics OR semiconductors OR manufacturing", language="en", page_size=20):
    url = f"https://newsapi.org/v2/everything?q={query}&language={language}&pageSize={page_size}&apiKey={api_key}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if data.get("status") != "ok":
            st.error(f"Error fetching news: {data.get('message', 'Unknown error')}")
            return None
            
        articles = data.get("articles", [])
        
        # Process the articles to extract relevant information
        processed_articles = []
        for article in articles:
            title = article.get("title", "No title")
            url = article.get("url", "#")
            published_at = article.get("publishedAt", "")
            
            # Format the timestamp
            if published_at:
                try:
                    published_date = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
                    formatted_date = published_date.strftime("%Y-%m-%d %H:%M")
                except:
                    formatted_date = published_at
            else:
                formatted_date = "Unknown"
            
            # Extract country mentions
            content = article.get("description", "") + " " + title
            country = extract_country(content)
            
            # Perform sentiment analysis
            sentiment = analyze_sentiment(title)
            
            processed_articles.append({
                "title": title,
                "url": url,
                "timestamp": formatted_date,
                "country": country,
                "sentiment": sentiment
            })
        
        return processed_articles
    except Exception as e:
        st.error(f"Error fetching news: {str(e)}")
        return None

# Define the app layout and functionality
def main():
    # Sidebar
    st.sidebar.title("Guidance Tamil Nadu")
    
    # Add Lottie animation to sidebar
    lottie_factory = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_qp1q7mct.json")
    if lottie_factory:
        st_lottie(lottie_factory, height=200, key="factory")
    
    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Navigation",
        ["Dashboard", "News Analysis", "About"]
    )
    
    # Set a default API key
    DEFAULT_API_KEY = "8357a2cfb61d426abe449df18e7d86e1"

    # Modify the API Key input to use the default key if no input is provided
    api_key = st.sidebar.text_input("Enter NewsAPI Key", type="password", value=DEFAULT_API_KEY)
    
    # Search parameters
    if page == "News Analysis":
        st.sidebar.subheader("Search Parameters")
        query = st.sidebar.text_input("Search Query", "electronics OR semiconductors OR manufacturing")
        language = st.sidebar.selectbox("Language", ["en", "ta", "hi"], index=0)
        news_count = st.sidebar.slider("Number of Headlines", min_value=5, max_value=50, value=20)
    else:
        query = "electronics OR semiconductors OR manufacturing"
        language = "en"
        news_count = 20
    
    # Main content
    if page == "Dashboard":
        st.title("📊 Industrial Insights Dashboard")
        
        # Display sections in columns
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.header("Recent Industry News")
            if api_key:
                # Fetch news
                news_data = fetch_news(api_key, query, language, news_count)
                
                if news_data:
                    # Display news in an interactive table
                    df = pd.DataFrame(news_data)
                    
                    # Add clickable links
                    def make_clickable(url, title):
                        return f'<a href="{url}" target="_blank">{title}</a>'
                    
                    df['clickable_title'] = df.apply(lambda row: make_clickable(row['url'], row['title']), axis=1)
                    
                    # Apply styling based on sentiment
                    def style_sentiment(val):
                        if val == "Positive":
                            return 'background-color: rgba(0, 255, 0, 0.2)'
                        elif val == "Negative":
                            return 'background-color: rgba(255, 0, 0, 0.2)'
                        else:
                            return 'background-color: rgba(255, 255, 0, 0.1)'
                    
                    styled_df = df[['clickable_title', 'timestamp', 'country', 'sentiment']]
                    styled_df = styled_df.style.applymap(style_sentiment, subset=['sentiment'])
                    
                    st.write(styled_df.to_html(escape=False), unsafe_allow_html=True)
                else:
                    st.info("Enter a valid API key to fetch news")
            else:
                st.info("Enter your NewsAPI key in the sidebar to fetch news")
        
        with col2:
            st.header("Quick Stats")
            if api_key and 'df' in locals():
                # Calculate sentiment distribution
                sentiment_counts = df['sentiment'].value_counts()
                
                # Create a pie chart for sentiment distribution
                fig = px.pie(
                    values=sentiment_counts.values,
                    names=sentiment_counts.index,
                    title="Sentiment Distribution",
                    color=sentiment_counts.index,
                    color_discrete_map={
                        'Positive': 'green',
                        'Neutral': 'gold',
                        'Negative': 'red'
                    }
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig)
                
                # Create a bar chart for country distribution
                country_counts = df['country'].str.split(', ').explode().value_counts().head(10)
                fig2 = px.bar(
                    x=country_counts.index,
                    y=country_counts.values,
                    title="Top Countries Mentioned",
                    labels={'x': 'Country', 'y': 'Count'},
                    color=country_counts.index
                )
                st.plotly_chart(fig2)
    
    elif page == "News Analysis":
        st.title("📰 News Sentiment Analysis")
        
        if api_key:
            with st.spinner("Fetching and analyzing news..."):
                news_data = fetch_news(api_key, query, language, news_count)
                
                if news_data:
                    df = pd.DataFrame(news_data)
                    
                    # Display detailed sentiment analysis
                    st.subheader("Sentiment Analysis Results")
                    
                    # Create tabs for different views
                    tab1, tab2, tab3 = st.tabs(["Overview", "Detailed Analysis", "Data Table"])
                    
                    with tab1:
                        # Summary metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            positive_count = (df['sentiment'] == 'Positive').sum()
                            st.metric("Positive Headlines", positive_count, delta=None)
                        
                        with col2:
                            neutral_count = (df['sentiment'] == 'Neutral').sum() 
                            st.metric("Neutral Headlines", neutral_count, delta=None)
                        
                        with col3:
                            negative_count = (df['sentiment'] == 'Negative').sum()
                            st.metric("Negative Headlines", negative_count, delta=None)
                        
                        # Sentiment bar chart
                        sentiment_data = df['sentiment'].value_counts().reset_index()
                        sentiment_data.columns = ['Sentiment', 'Count']
                        
                        fig = px.bar(
                            sentiment_data,
                            x='Sentiment',
                            y='Count',
                            color='Sentiment',
                            color_discrete_map={
                                'Positive': 'green',
                                'Neutral': 'gold',
                                'Negative': 'red'
                            },
                            title="Distribution of Sentiments Across Headlines"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with tab2:
                        # Country-wise sentiment analysis
                        st.subheader("Country-wise Sentiment Analysis")
                        
                        # Split countries and create a new dataframe with one country per row
                        country_df = df.copy()
                        country_df['country'] = country_df['country'].str.split(', ')
                        country_df = country_df.explode('country')
                        
                        # Group by country and sentiment
                        country_sentiment = country_df.groupby(['country', 'sentiment']).size().reset_index(name='count')
                        
                        # Filter for countries with at least 2 mentions
                        country_counts = country_df['country'].value_counts()
                        relevant_countries = country_counts[country_counts >= 2].index.tolist()
                        
                        if relevant_countries:
                            filtered_country_sentiment = country_sentiment[country_sentiment['country'].isin(relevant_countries)]
                            
                            # Create a grouped bar chart
                            fig = px.bar(
                                filtered_country_sentiment, 
                                x='country', 
                                y='count', 
                                color='sentiment',
                                barmode='group',
                                color_discrete_map={
                                    'Positive': 'green',
                                    'Neutral': 'gold',
                                    'Negative': 'red'
                                },
                                title="Sentiment Distribution by Country"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("Not enough country data to analyze trends")
                    
                    with tab3:
                        # Show the raw data
                        st.subheader("Headlines Data")
                        st.dataframe(df)
                        
                        # Allow download of data
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="Download Data as CSV",
                            data=csv,
                            file_name="news_sentiment_data.csv",
                            mime="text/csv",
                        )
                else:
                    st.error("Failed to fetch news data. Please check your API key and try again.")
        else:
            st.info("Enter your NewsAPI key in the sidebar to perform news analysis")
    
    elif page == "About":
        st.title("ℹ️ About Guidance Tamil Nadu Assessment")
        
        st.markdown("""
        ## Project Overview
        
        This dashboard was created as part of an assessment for Guidance Tamil Nadu. It demonstrates:
        
        1. **Web Scraping**: Fetching real-time news headlines related to electronics, semiconductors, and manufacturing.
        
        2. **Sentiment Analysis**: Using TextBlob to classify news headlines as positive, neutral, or negative.
        
        3. **Data Visualization**: Creating interactive charts to visualize sentiment distribution and geographical trends.
        
        ## Technologies Used
        
        - **Streamlit**: For creating the interactive web application
        - **NewsAPI**: For fetching current news headlines
        - **TextBlob**: For sentiment analysis
        - **Plotly**: For interactive data visualizations
        - **Pandas**: For data manipulation and analysis
        
        ## How to Use
        
        1. Enter your NewsAPI key in the sidebar
        2. Navigate between different sections using the sidebar menu
        3. Customize search parameters to focus on specific news topics
        4. Explore the sentiment analysis and visualizations
        
        ## Contact
        
        For any queries regarding this assessment, please contact Guidance Tamil Nadu.
        """)

# Run the app
if __name__ == "__main__":
    main()