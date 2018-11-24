import re  
from textblob import TextBlob 
from datetime import date, datetime, timedelta
import twython
from twython import Twython  

class TwitterClient(object): 
	''' 
	Generic Twitter Class for sentiment analysis. 
	'''
	def __init__(self): 
		''' 
		Class constructor or initialization method. 
		'''
		# keys and tokens from the Twitter Dev Console 
		consumer_key = 'yxB1e2ilD3jWtfmq8xaNszGvi'
		consumer_secret = 'qBCvdycFsb5PwSiGSam5PPDOHGwViRrJcrdeUd6PmqS5TDn5up'
		access_token = '490837524-DLccK1bttilXgr5f9lVxDYiHhGvVIenEI3B8WWom'
		access_token_secret = 'gi5VKYBBJp3UUFi7V2knyLwUNR3ZYCe4F95SNdBKSsvja'

		self.Months = {
			"Jan" : 1,
			"Feb" : 2,
			"Mar" : 3,
			"Apr" : 4,
			"May" : 5,
			"Jun" : 6,
			"Jul" : 7,
			"Aug" : 8,
			"Sept" : 9,
			"Oct" : 10,
			"Nov" : 11,
			"Dec" : 12
		}
		try: 
			# Instantiate an object
			self.python_tweets = Twython(consumer_key, consumer_secret)
		except: 
			print("Error: Authentication Failed") 

	def clean_tweet(self, tweet): 
		''' 
		Utility function to clean tweet text by removing links, special characters 
		using simple regex statements. 
		'''
		return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t]) |(\w+:\/\/\S+)", " ", tweet).split()) 

	def get_tweet_sentiment(self, tweet): 
		''' 
		Utility function to classify sentiment of passed tweet 
		using textblob's sentiment method 
		'''
		# create TextBlob object of passed tweet text 
		analysis = TextBlob(self.clean_tweet(tweet)) 
		# set sentiment 
		return analysis.sentiment.polarity * 100 

	def json_serial(self, obj):
		"""JSON serializer for objects not serializable by default json code"""

		if isinstance(obj, (datetime, date)):
			return obj.isoformat()
		raise TypeError ("Type %s not serializable" % type(obj))

	def subtract_hour_from_datetime(self, obj):
		return obj - timedelta(hours=1)
	def get_tweets(self, search_parameters, count = 100): 
		''' 
		Main function to fetch tweets and parse them. 
		'''
		# empty list to store parsed tweets 
		intervals = {} 
		bad_tweets = []
		good_tweets = []
		current_time = datetime.utcnow()
		current_time = current_time.replace(second=0, microsecond=0, minute=0, hour=current_time.hour)
		intervals[self.json_serial(current_time)] = {
				"sentiments": {
					"Very_Bad": 0,
					"Bad": 0,
					"Average": 0,
					"Good": 0,
					"Very_Good": 0,
				}, 
				"average_value": [], 
			}
		for _ in range(168):
			current_time = self.subtract_hour_from_datetime(current_time)
			intervals[self.json_serial(current_time)] = {
				"sentiments": {
					"Very_Bad": 0,
					"Bad": 0,
					"Average": 0,
					"Good": 0,
					"Very_Good": 0,
				}, 
				"average_value": [], 
			}
		try: 
			smallest_id = 9223372036854775807
			run = True
			query = {
				'q': str(search_parameters),  
				'count': 100,
				'lang': 'en'
			}
			while run:
				try:
					# Create our query
					# call twitter api to fetch tweets 
					fetched_tweets = self.python_tweets.search(**query)['statuses']
					# add sentiments to correct bucket in time
					for tweet in fetched_tweets:  
						smallest_id = tweet["id"] if tweet["id"] < smallest_id else smallest_id
						created_at = tweet["created_at"].split()
						created_at = created_at[5] + "-" + str(self.Months[created_at[1]]) + "-" + created_at[2] + "T" + created_at[3][0] + created_at[3][1] + ":00:00"
						sentiment = self.get_tweet_sentiment(tweet["text"]) 
						intervals[created_at]["average_value"].append(sentiment)
						if sentiment >= -100 and sentiment < -60:
							intervals[created_at]["sentiments"]["Very_Bad"] += 1
							bad_tweets.append(tweet["text"])
						elif sentiment >= -60 and sentiment < -20:
							intervals[created_at]["sentiments"]["Bad"] += 1
							bad_tweets.append(tweet["text"])
						elif sentiment >= -20 and sentiment < 20:
							intervals[created_at]["sentiments"]["Average"] += 1
						elif sentiment >= 20 and sentiment < 60:
							intervals[created_at]["sentiments"]["Good"] += 1
							good_tweets.append(tweet["text"])
						elif sentiment >= 60 and sentiment <= 100:
							intervals[created_at]["sentiments"]["Very_Good"] += 1
							good_tweets.append(tweet["text"])
					# call twitter api to fetch tweets 
					query = {
						'q': str(search_parameters),  
						'count': 100,
						'max_id': smallest_id,
						'lang': 'en'
					}
				except Exception:
					run = False
			for _,interval in intervals.items():
				if interval["average_value"]:
					num = len(interval["average_value"])
					total = 0
					for sentiment in interval["average_value"]:
						total += sentiment
					interval["average_value"] = total / num
				else:
					interval["average_value"] = 0
			# frontend has asked for this response shape and so it shall be
			correct_shape = []
			for key,interval in intervals.items():
				correct_shape.append(
					{
						"interval": key,
						"sentiments": {
							"Very Bad": interval["sentiments"]["Very_Bad"],
							"Bad": interval["sentiments"]["Bad"],
							"Average": interval["sentiments"]["Average"],
							"Good": interval["sentiments"]["Good"],
							"Very Good": interval["sentiments"]["Very_Good"],
						}, 
						"average_value": interval["average_value"], 
					}
			) 
			correct_shape = sorted(correct_shape, key=lambda k: k['interval']) 
			return {"sentiments": correct_shape}
			# common_tweets = AUSTIN(bad_tweets, good_tweets)
			# return {"sentiments": correct_shape, "common_tweets": common_tweets} 
			
		except Exception: 
			print("You done fucked up")