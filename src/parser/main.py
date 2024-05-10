import logging
from parser import HabrParser


def main():
    logging.getLogger().setLevel(logging.INFO)

    parser = HabrParser()
    text_type = 'news'
    
    parser.parse_articles(text_type=text_type, topic='develop')
    parser.parse_articles(text_type=text_type, topic='admin')
    parser.parse_articles(text_type=text_type, topic='design')
    parser.parse_articles(text_type=text_type, topic='management')
    parser.parse_articles(text_type=text_type, topic='marketing')
    parser.parse_articles(text_type=text_type, topic='popsci')

    parser.save_articles_to_csv(text_type=text_type)


if __name__ == '__main__':
    main()
