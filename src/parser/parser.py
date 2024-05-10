from bs4 import BeautifulSoup
from datetime import datetime
import logging
import pandas as pd
import re
import requests
import time
from typing import Optional


MAX_PAGES = 50
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                         '(KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36'}

TEXT_TYPES = (
    'articles',
    'news',
)

TOPICS = (
    'develop', 
    'admin', 
    'design', 
    'management', 
    'marketing', 
    'popsci',
)


class HabrArticle:
    """
    Class for Habr article
    """
    def __init__(self, name: str, publication_date: datetime, text: str, link: str, 
                 author: str, tags: list[str], topic: str):
        self._name = name
        self._publication_date = publication_date
        self._text = text
        self._link = link
        self._author = author
        self._tags = tags
        self._topic = topic

    @staticmethod
    def get_article_by_page(page: str, topic: str) -> Optional['HabrArticle']:
        """
        Get link to the page with article from Habr and return HabrArticle object
        """
        response = requests.get(page, headers=HEADERS)

        attempt = 0
        max_attempts = 5
        while not response.ok:
            if attempt >= max_attempts:
                logging.error('Unable to get article')
                return None

            response = requests.get(page, headers=HEADERS)
            attempt += 1
            logging.info(f'Try {attempt} / {max_attempts} attempt')

        soup = BeautifulSoup(response.text, 'lxml')
        name = soup.find('h1', class_='tm-title tm-title_h1').text.strip().replace('\xa0', ' ')

        publication_date = soup.find('span', class_='tm-article-datetime-published').find('time')['title']
        publication_date = datetime.strptime(publication_date.replace(',', ''), '%Y-%m-%d %H:%M')

        try:
            text = soup.find(
                'div', class_='article-formatted-body article-formatted-body article-formatted-body_version-1'
            ).text
        except AttributeError:
            text = soup.find(
                'div', class_='article-formatted-body article-formatted-body article-formatted-body_version-2'
            ).text
        text = re.sub(r'\s+', ' ', text).replace('\xa0', ' ').strip()

        author = soup.find('a', class_='tm-user-info__username')
        author = author.text.strip() if author else None

        tags = soup.find('div', class_='tm-publication-hubs')
        tags = [tag.text.strip(' *')
                for tag in tags.find_all('span', class_='tm-publication-hub__link-container') if tag]

        return HabrArticle(
            name=name,
            publication_date=publication_date,
            text=text,
            link=page,
            author=author,
            tags=tags,
            topic=topic,
        )

    def transform_article_to_dict(self) -> dict:
        """
        Transform HabrArticle to dict
        """
        return {attribute[1:]: value for attribute, value in self.__dict__.items()}


class HabrParser:
    """
    Class for parsing Habr articles
    """
    def __init__(self):
        self._main_page = 'https://habr.com'
        self._articles = []

    def parse_articles(self, text_type: str, topic: str):
        """
        Get Habr articles by topic
        """
        if text_type not in TEXT_TYPES:
            raise ValueError(f'Text type "{text_type}" not in {str(TEXT_TYPES)}')

        if topic not in TOPICS:
            raise ValueError(f'Topic "{topic}" not in {str(TOPICS)}')

        logging.info(f'==========Topic {topic}==========')
        for i in range(MAX_PAGES):
            logging.info(f'Parse page number {i + 1} / {MAX_PAGES}...')
            links = self.__get_links_by_page(f'{self._main_page}/ru/flows/{topic}/{text_type}/page{i + 1}')
            self.__parse_articles_by_pages(links, topic)
            
    def get_articles(self) -> pd.DataFrame:
        """
        Get parsed articles in pandas.DataFrame
        """
        articles = []

        for article in self._articles:
            article_dict = article.transform_article_to_dict()
            if article_dict not in articles:
                articles.append(article_dict)

        return pd.DataFrame(articles)

    def save_articles_to_csv(self, text_type: str):
        """
        Save articles to csv file
        """
        articles_df = self.get_articles()
        articles_df.to_csv(f'../../data/{text_type}.csv', index=False)


    def __get_links_by_page(self, page: str) -> list[str]:
        """
        Get list of links with articles from Habr page
        """
        response = requests.get(page, headers=HEADERS)
        soup = BeautifulSoup(response.content, 'lxml')
        links_list = []

        for element in soup.find_all('a', class_='tm-article-snippet__readmore'):
            if element.has_attr('href'):
                links_list.append(self._main_page + element['href'])

        return links_list


    def __parse_articles_by_pages(self, links: list[str], topic: str) -> bool:
        """
        Update self._articles by articles from pages
        """
        cnt_pages = len(links)
        for i, page in enumerate(links):
            logging.info(f'Parsing page {i + 1} / {cnt_pages}: {page}')
            try:
                article = HabrArticle.get_article_by_page(page, topic)
            except Exception as error:
                logging.error(str(error))
            else:
                if article:
                    self._articles.append(article)
                    logging.info('Successfully add to list')

        return True
