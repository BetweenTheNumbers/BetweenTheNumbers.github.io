# twitternlp.py
# 2 part process to 1) scrape NHL rosters from Wikipedia, and 2) retrieve tweets mentioning them
#
import GetOldTweets3 as got             
import wikipedia as wiki                
from bs4 import BeautifulSoup as soup   
import datetime
import pandas as pd
from textblob import TextBlob           

#use BeautifulSoup to parse Wikipedia's HTML pages of active NHL rosters
pages = [soup(wiki.WikipediaPage(pageid=20744511).html(), 'html.parser')
         , soup(wiki.WikipediaPage(pageid=20744562).html(), 'html.parser')]
players = []

for p in pages:
    for t in p.find_all('table'):                             # team roster table
        for h in t.find_previous_sibling('h3'):
            if h.text != '[edit]':                            # team name
                tm = h.text
        for r in t.find_all('tr'):                            # rows of players
            r = r.find_all('td')
            for c in r:
                c = c.find_all('span', class_='fn')           # player name
                for a in c:
                    pl = a.find('a').text                     # columns in player row
                    players.append([tm, pl])

nlptweets = pd.DataFrame()
playeravg = pd.DataFrame()
now = datetime.datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
ayearago = (datetime.datetime.now() - datetime.timedelta(days=3 * 365)).strftime("%Y-%m-%d")

#for testing purposes, only select my favorite team
players = [p for p in players if p[0] == 'San Jose Sharks']   
tlimit = 250                                                  
onlytop = False                                               

#retrieve tweets by-player using GetOldTweets3 (deprecated)
for p in players:
    criteria = got.manager.TweetCriteria().setQuerySearch(p[1]).setSince(ayearago)\
        .setMaxTweets(tlimit).setTopTweets(onlytop)
    tweets = got.manager.TweetManager.getTweets(criteria)
    print(p[0], p[1], len(tweets))

    #get all the tweet metrics per-tweet
    for t in tweets:
        s = TextBlob(t.text).sentiment                  
        approval = s.polarity * (1 - s.subjectivity)
        row = pd.DataFrame({'teamname': [p[0]], 'playername': [p[1]], 'dateupdated': [now], 'plink': [t.permalink]
                               , 'tdate': [t.date], 'tweet': [t.text], 'polarity': [round(s.polarity, 3)]
                               , 'subjectivity': [round(s.subjectivity, 3)], 'approval': [round(approval, 3)]
                               , 'numrt': [t.retweets], 'numfav': [t.favorites]})
        nlptweets = nlptweets.append(row, ignore_index=True)

    plset = pd.DataFrame(nlptweets.loc[nlptweets.playername == p[1]])
    plmean = plset.mean()
    plmedian = plset.median()
    #calculate aggregate metrics of tweets and store for later
    pl = pd.DataFrame({'teamname': [p[0]], 'playername': [p[1]], 'dateupdated': [now], 'tweetnum': [len(plset)]
                          , 'toptweetsonly': [onlytop]
                          , 'numrtmean': [round(plmean['numrt'], 3)]
                          , 'numrtmedian': [round(plmedian['numrt'], 3)]
                          , 'numfavmean': [round(plmean['numfav'], 3)]
                          , 'numfavmedian': [round(plmedian['numfav'], 3)]
                          , 'polaritymean': [round(plmean['polarity'], 3)]
                          , 'polaritymedian': [round(plmedian['polarity'], 3)]
                          , 'subjectivitymean': [round(plmean['subjectivity'], 3)]
                          , 'subjectivitymedian': [round(plmedian['subjectivity'], 3)]
                          , 'approvalmean': [round(plmean['approval'], 3)]
                          , 'approvalmedian': [round(plmedian['approval'], 3)]})
    playeravg = playeravg.append(pl, ignore_index=True)

#write the individual tweets to a file, and the aggregated metrics to a separate file
nlptweets.to_csv('nhl_tweets_updated_{}.csv'.format(now), sep=',', index=False, encoding='utf-8')
playeravg.to_csv('nhl_nlp_sentiment_updated_{}.csv'.format(now), sep=',', index=False, encoding='utf-8')
