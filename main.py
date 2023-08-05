import os

from pythorhead import Lemmy

username = os.environ['LEMMY_USERNAME']
password = os.environ['LEMMY_PASSWORD']
instance_url = 'https://lemmy.ca'

lemmy = Lemmy(instance_url)
lemmy.log_in(username, password)

community_id = lemmy.discover_community('bot_testing_ground')

lemmy.post.create(community_id, "Hello Lemmy!")