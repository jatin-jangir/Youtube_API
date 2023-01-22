import json
from youtube_transcript_api import YouTubeTranscriptApi
from pytube import YouTube
#import cv2
import os
import time
import pytesseract
from pytesseract import Output
from PIL import Image
from apiclient.discovery import build
import argparse
import unidecode
import pandas as pd
import urllib
from flask import Flask, jsonify, request
pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe' 

import jellyfish
import nltk.corpus
from nltk.corpus import stopwords
import math
import re
from collections import Counter
import numpy as np

def scrape_comments_with_replies(ID):
    try:
        api_key = "AIzaSyAfFM-ZlbVD-E5392Yd5jcO2CBZbkvzo2g" 
        youtube = build('youtube', 'v3', developerKey=api_key)
        box=[]
        data = youtube.commentThreads().list(part='snippet', videoId=ID, maxResults='100', textFormat="plainText").execute()

        for i in data["items"]:
            comment = i["snippet"]['topLevelComment']["snippet"]["textDisplay"]

            box.append(comment)
            
        while ("nextPageToken" in data):

            data = youtube.commentThreads().list(part='snippet', videoId=ID, pageToken=data["nextPageToken"],
                                                maxResults='100', textFormat="plainText").execute()

            for i in data["items"]:
                comment = i["snippet"]['topLevelComment']["snippet"]["textDisplay"]

                box.append(comment)      
        if(box == None):
            return []
        return box
    except Exception:
        return []



WORD = re.compile(r"\w+")
def get_cosine(vec1, vec2):
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])

    sum1 = sum([vec1[x] ** 2 for x in list(vec1.keys())])
    sum2 = sum([vec2[x] ** 2 for x in list(vec2.keys())])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    if not denominator:
        return 0.0
    else:
        return float(numerator) / denominator

def text_to_vector(text):
    words = WORD.findall(text)
    return Counter(words)
def remove_token(text):
    text = re.sub(r"(@\[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)|^rt|http.+?", "", text)
    stop = stopwords.words('english')
    text = " ".join([word for word in text.split() if word not in (stop)])
    return text

def give_mathching_score(tags,text):
    text=remove_token(text)

    jaro_distance=jellyfish.jaro_distance(tags,text)
    vector1 = text_to_vector(tags)
    vector2 = text_to_vector(text)

    cosine = get_cosine(vector1, vector2)
    return (jaro_distance+cosine)/2

def get_relative_score(tags,video_data,captions):
    # if(int(video_data["viewCount"])!=0):
    # like_ratio=(int(video_data["likeCount"])/int(video_data["viewCount"]))*100
    # comment_ratio=(int(video_data["commentCount"])/int(video_data["viewCount"]))*100
    similarity_caption=give_mathching_score(tags,captions)
    similarity_title=give_mathching_score(tags,video_data['Title'])
    similarity_description=give_mathching_score(tags,video_data['Description'])
    final_similarity=(similarity_caption)+(similarity_description * 2)+(similarity_title * 3)
    final_similarity=final_similarity/6
    return 100*final_similarity



DEVELOPER_KEY="AIzaSyAfFM-ZlbVD-E5392Yd5jcO2CBZbkvzo2g"
YOUTUBE_API_SERVICES_NAME="youtube"
YOUTUBE_API_VERSION="v3"
titles=[]
PublishTime=[]
videoIds=[]
channelTitles=[]
channelId=[]
video_descriptions=[]
viewCounts=[]
likeCounts=[]
dislikeCounts=[]
commentCounts=[]
duration=[]
favoritesCounts=[]
URLS=[]
Audience_Response=[]

def getCaptions(url):
  try:
    srt = YouTubeTranscriptApi.get_transcript(url,languages=['en'])
    ans=""
    for i in srt:
      ans=ans+" "+i['text']
    return ans
  except Exception:
    return ""


def getVideo(URL):
    try: 
        yt = YouTube(URL)
        #print(yt)
        stream = yt.streams.get_highest_resolution()
        #print(stream)
        srt=stream.download()
        #print(srt)
        #print("Download completed!!")
        return srt
    except Exception:
        return ""

def getDuration(URL):
    YT_KEY="AIzaSyAfFM-ZlbVD-E5392Yd5jcO2CBZbkvzo2g"# API key
    search_url = f'https://www.googleapis.com/youtube/v3/videos?id={URL}&key={YT_KEY}&part=contentDetails'
    req = urllib.request.Request(search_url)
    response = urllib.request.urlopen(req).read().decode('utf-8')
    data = json.loads(response)
    all_data = data['items']
    duration = all_data[0]['contentDetails']['duration']
    #print(duration)
    minutes=0
    if('H' in duration):
        minutes = int(duration[2:].split('H')[0])*60
        duration=duration[0:2]+duration.split('H')[1]
        #print(duration)
    if('M' in duration):
        minutes =minutes+ int(duration[2:].split('M')[0])
        return minutes
    return 0
'''
def get_frames(URL,step,count):

  # Input:
  #   URL - url of video
  #   outputFolder - name and path of the folder to save the results
  #   step - time lapse between each step (in seconds)
  #   count - number of screenshots
  # Output:
  #   'count' number of screenshots that are 'step' seconds apart created from video 'inputFile' and stored in folder 'outputFolder'
  # Function Call:
  #   get_frames("test.mp4", 'data', 10, 10)
  inputFile=getVideo(URL)
  if(inputFile==""):
    return ""
  #initializing local variables
  step = step
  frames_count = count

  currentframe = 0
  frames_captured = 0

  #creating a folder
  try:  
      # creating a folder named data 
      if not os.path.exists("/data/"): 
          os.makedirs("/data/") 
    
  #if not created then raise error 
  except OSError: 
      print ('Error! Could not create a directory') 
      return
  
  cam = cv2.VideoCapture(inputFile)
  #reading the number of frames at that particular second
  frame_per_second = cam.get(cv2.CAP_PROP_FPS)
  words =""
  while (True):
      ret, frame = cam.read()
      if ret:
          if currentframe > (step*frame_per_second):  
              currentframe = 0
              #saving the frames (screenshots)
              #name = './data/frame' + str(frames_captured) + '.jpg'
              #print ('Creating...' + name) 
              #cv2_imshow(frame)  

              #print ('getting text...' + name) 
              # pytessercat
              text = pytesseract.image_to_string(frame)
              #print(text)
              words=words+" "+text

              #cv2.imwrite(name, frame)       
              frames_captured+=1
              
              #breaking the loop when count achieved
              if frames_captured > frames_count-1:
                ret = False
          currentframe += 1           
      if ret == False:
          break
  cam.release()
  os.remove(inputFile)
  special_characters = ['!','#','$','%', '&','@','[',']',' ',']','_','-','=','+','?','|','\n','\x0c']
  words = ''.join(filter(lambda i:i not in special_characters, words))

  return words
'''
def youtube_mobie_review(x,max_Results):
    youtube=build(YOUTUBE_API_SERVICES_NAME,YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)
    #print("get connection")
    #print(youtube)
    iterator=0
    token=""
    while(iterator< max_Results ):
      iterator=iterator+50
      search_response=youtube.search().list(q=x, part="id,snippet",maxResults=max_Results,pageToken=token).execute()
      #print("get search results")
      #print(search_response)
      token=search_response["nextPageToken"]
      df=pd.DataFrame()
      count=0
      for search_result in search_response.get("items",[]):
          count=count+1
          #print(count)
          if search_result["id"]["kind"]=="youtube#video":
              #print(search_result["snippet"])
              title=search_result["snippet"]["title"]
              title=unidecode.unidecode(title)
              titles.append(title.lower())
              #print("Title : "+title)
              
              publishedAt=search_result["snippet"]["publishedAt"]
              PublishTime.append(publishedAt)
              #print("publishedAt : "+str(publishedAt))
              
              channelTitle=search_result["snippet"]["channelTitle"]
              channelTitles.append(channelTitle)
              #print("channel name : "+str(channelTitle))
              Channel_Id=search_result["snippet"]["channelId"]
              channelId.append(Channel_Id)
              
              videoId=search_result["id"]["videoId"]
              videoIds.append(videoId)
              #print("videoId : "+str(videoId))
              
              url="https://www.youtube.com/watch?v="+videoId
              URLS.append(url)
              
              video_description=search_result["snippet"]["description"]
              video_descriptions.append(video_description.lower())
              #print("Description : "+str(video_description))
              
              video_response=youtube.videos().list(id=videoId,part="statistics").execute()
              
              for video_result in video_response.get("items",[]):
                  viewCount=video_result["statistics"]["viewCount"]
                  viewCounts.append(viewCount)
                  
                  if 'likeCount' not in video_result['statistics']:
                      likeCount=0
                  else:
                      likeCount=video_result["statistics"]["likeCount"]
                  likeCounts.append(likeCount)
                  
                  if 'commentCount' not in video_result['statistics']:
                      commentCount=0
                  else:
                      commentCount=video_result["statistics"]["commentCount"]
                  commentCounts.append(commentCount)
              duration.append(getDuration(videoId))
              
              dict1={"Title":titles,"PublishTime":PublishTime,"URL":URLS,"Channel_Name":channelTitles,'Channel_Id':channelId,"Description":video_descriptions,"viewCount":viewCounts,"commentCount":commentCounts,"likeCount":likeCounts,"Duration":duration}
              
              df=pd.DataFrame.from_dict(dict1,orient='index')
              df=df.transpose()
              df.columns=['Title','PublishTime','URL','Channel_Name','Channel_Id','Description','viewCount','commentCount','likeCount',"Duration"]
            
            
    #print(count)
    return df

def key_words(x,max_Result):
    print("getting new data from api....")
    youtube_response_df=youtube_mobie_review(x,max_Result)
    youtube_response_df=youtube_response_df.dropna()
    youtube_response_df['relative_score']=0
    #youtube_response_df['video_text']=''
    for i in range(youtube_response_df.shape[0]):
        print(str(i))
        URL = youtube_response_df.at[i, "URL"]
        URL=URL[URL.index("=")+1:]
        # print(URL)
        youtube_response_df.at[i, "relative_score"]= get_relative_score(x,youtube_response_df.loc[i], getCaptions(URL).lower() )  # audio
        #youtube_response_df.at[i, "video_text"]= get_frames(youtube_response_df.at[i, "URL"],3,100)   # video
    youtube_response_df.sort_values(by=['relative_score'], ascending=False)
    print("we sorted the data ..... ")
    return youtube_response_df[:50].to_dict()


from flask import Flask, jsonify, request
  
# creating a Flask app
app = Flask(__name__)

# A simple function to calculate the square of a number
# the number to be squared is sent in the URL when we use GET
# on the terminal type: curl http://127.0.0.1:5000 / home / {user_query} (use  "_" instead of space)
# this returns top 50 relevant vidoes
@app.route('/tags/<string:tags>', methods = ['GET'])
def disp(tags):
    user_query=tags.replace('_',' ')
    return key_words(user_query,200)
  
@app.route("/")
def hello_world():
    return '''<p>Hello, you are in youtube search improvement api service !</p>
    <h1>
    # Youtube_API
    </h1>
    <p>
The  API for getting information about any topic from youtube.
</br>
This API is build on flask 
</br>
We are using YouTube V3 api services to build our API
</br>
To run this service you have to </br>
1. clone this repository</br>
2. create a virtual environment</br>
      virtualenv ~environment-name~</br>
3. start environment</br>
        ~environment-name~\Scripts\activate</br>
4.install reqired libraries</br>
        pip install -m requirements.txt</br>
5. paste you google developer api where YT_API is required</br>
6. run the code </br>
        python api.py</br>
7. now you will able to get top50 youtube videos according to your need.</br>

</br>
to use api service on localhost use </br>

url ----->   "http://127.0.0.1:5000/tags/user_query_words_seperated_by_underscroll"
</br>
this will return most of the required informations .</br>

This is just simple python,</br>
You can modify this according to your need......</br>
    </p>'''

# driver function
if __name__ == '__main__':
  
    app.run(debug = True)
