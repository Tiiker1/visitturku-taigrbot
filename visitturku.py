import discord
import requests
from bs4 import BeautifulSoup
from discord.ext import commands
import hashlib
import os

def setup(client):
    def fetch_articles():
        url = 'https://visitturku.fi/tapahtumat'
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            raise Exception("Failed to fetch article data")

    def parse_articles(articles_data):
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
            
            # Generate a unique identifier for the event
            unique_id = hashlib.sha256((heading + date + link).encode()).hexdigest()
            
            article_info = f"**{heading}**\nDate: {date}\n[Read more]({link})"
            articles.append((unique_id, article_info))
        return articles

    def read_posted_articles(file_path):
        if not os.path.exists(file_path):
            return set()
        with open(file_path, 'r') as file:
            return set(line.strip() for line in file.readlines())

    def write_posted_article(file_path, unique_id):
        with open(file_path, 'a') as file:
            file.write(f"{unique_id}\n")

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

            commit_data_folder = 'commit_data'
            os.makedirs(commit_data_folder, exist_ok=True)
            posted_articles_file = os.path.join(commit_data_folder, 'posted_articles.txt')
            posted_articles = read_posted_articles(posted_articles_file)

            # Send only the articles that haven't been sent before
            unsent_articles = [(unique_id, article_info) for unique_id, article_info in parsed_articles if unique_id not in posted_articles]
            if not unsent_articles:
                await interaction.response.send_message("No new articles found.")
                return

            # Send the first article using interaction response
            first_article_unique_id, first_article_info = unsent_articles.pop(0)
            await interaction.response.send_message(first_article_info)
            write_posted_article(posted_articles_file, first_article_unique_id)

            # Send subsequent articles using follow-up messages
            for unique_id, article_info in unsent_articles:
                await interaction.followup.send(article_info)
                write_posted_article(posted_articles_file, unique_id)

        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message(f"Error: {e}")
            else:
                await interaction.followup.send(f"Error: {e}")
