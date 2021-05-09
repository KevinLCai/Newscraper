import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import HttpResponse, HttpResponseRedirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from .webscraper import News
import time
import multiprocessing
from threading import Thread

import requests
from bs4 import BeautifulSoup
import webbrowser
from collections import Counter
from string import punctuation
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS as stop_words
import concurrent.futures

def index(request):
    return render(request, "newscraper/index.html")

def return_page(request, category):
    topic = News(f"{category}")
    topic.get_content()
    topic.findURLs()
    topic.findTitles()
    topic.find_summaries()

    # #Multiprocessing to speed up scraping and summarising
    # with concurrent.futures.ProcessPoolExecutor() as executor:

    # pool = multiprocessing.Pool()
    # summaries = [pool.map(finalise, urls)]
    # pool.close()
    # pool.join()
    # summaries = summaries[0]

    return render(request, "newscraper/category.html", {
        'catagory' : category.title(),
        'title1' : topic.titles[0],
        'title2' : topic.titles[1],
        'title3' : topic.titles[2],
        'title4' : topic.titles[3],
        'title5' : topic.titles[4],
        'summary1' : topic.summaries[0],
        'summary2' : topic.summaries[1],
        'summary3' : topic.summaries[2],
        'summary4' : topic.summaries[3],
        'summary5' : topic.summaries[4],
    })