import discord
import requests
from bs4 import BeautifulSoup
from discord.ext import commands
from discord import app_commands

def setup(client):
    def fetch_articles():
        # Fetch the HTML content from the Visit Turku website
        url = 'https://visitturku.fi/tapahtumat'
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            raise Exception("Failed to fetch article data")

    def parse_articles(articles_data):
        # Parse the HTML content to extract articles
        soup = BeautifulSoup(articles_data, 'html.parser')
        article_elements = soup.find_all('article')
        articles = []
        for article in article_elements:
            heading_element = article.find('h2')
            heading = heading_element.get_text(strip=True) if heading_element else 'No title available'
            
            date_element = article.find('time', class_='event-date')
            date = date_element.get_text(strip=True) if date_element else 'No date available'
            
            link_element = article.find('a', href=True)
            link = f"https://visitturku.fi{link_element['href']}" if link_element else 'No link available'
            
            article_info = f"**{heading}**\nDate: {date}\n[Read more]({link})"
            articles.append(article_info)
        return articles

    @client.tree.command(name='visitturku', description='Get ongoing week events in Turku')
    async def events_command(interaction: discord.Interaction):
        try:
            # Fetch article data
            articles_data = fetch_articles()

            # Parse article data
            parsed_articles = parse_articles(articles_data)

            # Check if there are articles
            if not parsed_articles:
                await interaction.response.send_message("No articles found.")
                return

            # Send the first article using interaction response
            first_article = parsed_articles.pop(0)
            await interaction.response.send_message(first_article)

            # Send subsequent articles using follow-up messages
            for article_info in parsed_articles:
                if article_info:  # Ensure the article info is not empty
                    await interaction.followup.send(article_info)

        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message(f"Error: {e}")
            else:
                await interaction.followup.send(f"Error: {e}")
