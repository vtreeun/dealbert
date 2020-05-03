import secrets
import os

import tweepy
import pymongo 

# Mongo 
client = pymongo.MongoClient('localhost', 27017)
deals = client.dealbert.deals


# Twitter
# keys
consumer_key = os.getenv('TWITTER_CONSUMER')
consumer_key_secret = os.getenv('TWITTER_CONSUMER_SECRET')

access_token = os.getenv('TWITTER_ACCESS_TOKEN')
access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

keyword_mention = os.getenv('TWITTER_KEYWORD_MENTION')
account_mention = os.getenv('TWITTER_ACCOUNT_MENTION')

account_id = os.getenv('TWITTER_ACCOUNT_ID')

# Authorization
authorization = tweepy.OAuthHandler(consumer_key, consumer_key_secret)
authorization.set_access_token(access_token, access_token_secret)

# API
twitter = tweepy.API(authorization)


# Stream
class Dealbert(tweepy.StreamListener):
    def on_status(self, status):

        friendship, _ = twitter.show_friendship(target_id=status.user.id)

        if not friendship.followed_by:
            return super().on_status(status)

        if keyword_mention in status.text:

            has_mentions = mentions = status.entities.get('user_mentions', [])
            has_an_account_mention = any(mention.get('screen_name') == account_mention for mention in mentions)
            if has_mentions and has_an_account_mention:

                count = deals.estimated_document_count()
                if count > 100:
                    message = 'Sorry, we already gave 100 codes'

                has_code_already = deals.find_one({ "user.id": status.user.id }) 
                if has_code_already:
                    message = 'Sorry, we already gave you a code'

                else:
                    deal_code = secrets.token_urlsafe()
                    deal_user = {
                        'id': status.user.id,
                        'name': status.user.name,
                        'account': status.user.screen_name
                    }
                    deal = {
                        'user': deal_user,
                        'code': deal_code
                    }
                    deals.insert_one(deal)
                    message = 'Hello, here is your discount code ' + deal_code
                
                twitter.send_direct_message(status.user.id, message)
        return super().on_status(status)

    def on_error(self, status_code):
        print(status_code)
        if status_code == 420:
            return False 
        
        return True


dealbert = Dealbert()
dealbert_stream = tweepy.Stream(twitter.auth, dealbert)
dealbert_stream.filter(track=[account_mention], is_async=True)
