# UniHack-2018
UniHack 2018 - Symphony Flask API

This is the API for my group's UniHack 2018 submission, Symphony.
Eddie Yao and Jord Gui contributed to the backend code and Jacob Wisniewski and Ahbi Balreddygari were on the team working on the frontend.  
The following text was taken from our Devpost post after the hack...

## Inspiration
We've all been in a situation at a party or gathering where the a music playlist has just been a great struggle to get going. Not everyone likes the songs in it and it's a big hassle to ask for song requests all the time. From this situation, the idea arose to create a dynamic geo-location based collaborative playlist, powered by Spotify, which takes everyone's tastes into consideration when generating a playlist.

## What it does
When a user creates a Gig their location is recorded and Symphony generates a playlist from their top songs and displays it to them. From this, if another user within a 50 meter radius clicks join, they can see the created Gigs in their area and connect with them. Once connected, Symphony uses it's playlist generation algorithm to dynamically update the Gig's playlist.

## Algorithm Explanation
Symphony pools the top 15 songs of each person in the Gig and from that pool it randomly selects 5 songs for each person in the gig. From each sample we use Spotify's recommendation algorithm to find songs that are similar in taste and we add these songs to the Gig's playlist. So, as each person joins, the whole playlist is dynamically updated and replaced with one that is more suited to everyone's tastes.
In addition, we have also added some fine-tuning options when a user firsts creates a Gig to help guide the seeding algorithm as to better fit the mood of the situation. These parameters include energy, danceability, valence and instrumentalness.

## How we built it
Back-end:
The back-end RESTful API is built with a Flask in Python which makes the calls to the Spotify API to handle authentication, playlist generation and playlist modification. Geopy also is used to group users in a nearby location and handle the Gig's users. The API and the PostgreSQL database are both hosted in the cloud using Heroku and are always running.

Front-end: 
The front-end is built with React.js, and is primarily used to handle the creation and interaction with Gigs. Built for desktop and mobile applications the front-end is robust and was designed from the ground up with no templates. 
The front-end interacts with the API using a series of calls whenever the user creates a Gig, joins a Gig or leaves. Another function of the front-end is that it handles the first part of user authentication with OAuth2. The front-end is hosted using Google's Firebase service which is also able to run 24/7.

## Challenges We ran into
In terms of challenges, some of the issues we ran into were unavoidable from our design and some stemmed from our inexperience with front-end development. 
Firstly the GPS location services on laptops were quite inaccurate so our preliminary tests were failing to show Gigs in our area properly so we had to tweak some variables in our back-end to accommodate. The JavaScript use of arrow functions and promises for fetch requests also stumped our team for a while but we managed to resolve it after some testing.

## Accomplishments that we're proud of
Our team was very proud of reaching the top 8 teams in UniHack whilst only consisting of first year CS students. It was very exciting being able to create a working application that was almost ready for production. Symphony was able to grab the attention of the audience and we were able to introduce new users to our service.

## What's next for Symphony
Symphony has a lot of potentials to become a full-fledged application currently, it's at a working build that performs all needed functions. Future improvements would include admin controls for hosts, and an option for more private Gigs that would use room codes. 
If the project gains enough users, the large amount of data on user playlists could be used to create our own recommendation system through the use of a clustering algorithm and some machine learning but this goal is still far off. 

## Disclaimer
The code found in this repository was all written in 24 hours and probably contains bugs.  
For more info see https://devpost.com/software/symphony-65i8u9
