import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import HttpResponse, HttpResponseRedirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
# from .web_scraper import *
import time
import multiprocessing

import requests
from bs4 import BeautifulSoup
import webbrowser
from collections import Counter
from string import punctuation
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS as stop_words
import concurrent.futures

class News():
    """Given a chosen news category, find top 5 articles
    Article titles and summarise them"""

    def __init__(self, category):
        self.category = category
        self.titles = []
        self.urls = []
        self.final_urls = []
        self.summaries = []
        self.content = None
        self.article_contents = []

    def get_content(self):
        """Fetch webpage content of news category"""
        result = requests.get(f'https://www.bbc.co.uk/news/{self.category}/')
        src = result.content
        soup = BeautifulSoup(src,'lxml')

        links = soup.find_all('a', class_ = 'gs-c-promo-heading gs-o-faux-block-link__overlay-link gel-pica-bold nw-o-link-split__anchor')
        promo_story = soup.find('a', class_ ='gs-c-promo-heading gs-o-faux-block-link__overlay-link gel-paragon-bold gs-u-mt+ nw-o-link-split__anchor')
        links.insert(0, promo_story)
        self.content = links

    def findURLs(self):
        """Find all of the links to articles and add them to self.urls array"""
        for link in self.content:
            if len(self.urls) >= 10:
                break
            try:
                url = 'https://www.bbc.co.uk' + link.attrs['href']
                if url not in self.urls and url.startswith('https://www.bbc.co.uk/news/') and ("/live/" not in url):
                    self.urls.append(url)
            except:
                pass

    def findTitles(self):
        """Find title for each article"""
        for url in self.urls:
            if len(self.titles) >= 5:
                break
            try:
                article = BeautifulSoup(requests.get(url).content,'lxml')
                self.article_contents.append(article)
                article_title = article.find('h1', {"id":"main-heading"}).text
                self.titles.append(article_title)
                self.final_urls.append(url)
            except AttributeError:
                try:
                    article = BeautifulSoup(requests.get(url).content,'lxml')
                    self.article_contents.append(article)
                    article_title = article.find('h1', class_ = 'vxp-media__headline').text
                    self.titles.append(article_title)
                    #print(article_title)
                except AttributeError:
                    pass

    def tokenizer(self, s):
        tokens = []
        for word in s.split(' '):
            tokens.append(word.strip().lower())
        return tokens

    def sent_tokenizer(self, s):
        sents = []
        for sent in s.split('.'):
            sents.append(sent.strip())
        return sents

    #Count word occurences in document
    def count_words(self, tokens):
        word_counts = {}
        for token in tokens:
            if token not in stop_words and token not in punctuation:
                if token not in word_counts.keys():
                    word_counts[token] = 1
                else:
                    word_counts[token] += 1
        return word_counts

    #Count frequency of words
    def word_freq_distribution(self, word_counts):
        freq_dist = {}
        max_freq = max(word_counts.values())
        for word in word_counts.keys():
            freq_dist[word] = (word_counts[word]/max_freq)
        return freq_dist

    #Score sentences
    def score_sentences(self, sents, freq_dist, max_len=40):
        sent_scores = {}
        for sent in sents:
            words = sent.split(' ')
            for word in words:
                if word.lower() in freq_dist.keys():
                    if len(words) < max_len:
                        if sent not in sent_scores.keys():
                            sent_scores[sent] = freq_dist[word.lower()]
                        else:
                            sent_scores[sent] += freq_dist[word.lower()]
        return sent_scores

    #Summarize using scores:
    def summarize(self, sent_scores, k):
        top_sents = Counter(sent_scores)
        summary = ''
        scores = []

        top = top_sents.most_common(k)
        for t in top:
            summary += t[0].strip()+'. '
            scores.append((t[1], t[0]))
        return summary[:-1], scores

    def find_summaries(self):
        for article in self.article_contents:
            try:
                paragraphs = article.find_all('p')
                string_concat = ''
                #Concatenate text into one string!
                for paragraph in paragraphs:
                    string = paragraph.text
                    string_concat += string + ' '
                text = string_concat
                text = text.replace("Share this withEmailFacebookMessengerMessengerTwitterPinterestWhatsAppLinkedInCopy this linkThese are external links and will open in a new window", "")
                text = text.replace("The BBC is not responsible for the content of external sites. Read about our approach to external linking.", "")
                text = text.replace("Share this with Email Facebook Messenger Messenger Twitter Pinterest WhatsApp LinkedIn", "")
                text = text.replace("Copy this link These are external links and will open in a new window", "")

                #Tokenise
                tokens = self.tokenizer(text)
                sents = self.sent_tokenizer(text)
                word_counts = self.count_words(tokens)
                freq_dist = self.word_freq_distribution(word_counts)
                sent_scores = self.score_sentences(sents, freq_dist)

                #Generate summary
                summary, summary_sent_scores = self.summarize(sent_scores, 3)
                #print(titles[number-1] + '\n')
                #print(summary)
                self.summaries.append(summary)
            except IndexError:
                pass


# UK = News("uk")
# UK.get_content()
# UK.findURLs()
# UK.findTitles()
# UK.summarise()
# print(len(UK.summaries))
#print(UK.urls)
#print(UK.titles)