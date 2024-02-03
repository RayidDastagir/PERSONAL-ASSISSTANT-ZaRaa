import requests
import speech_recognition as sr
from transformers import pipeline, Conversation
from gtts import gTTS
import tempfile
import os
import re
import time
import spacy  # python -m spacy download en_core_web_sm
from playsound import playsound
import pymongo
from pymongo import MongoClient
import threading
import pygame
import tkinter as tk
from tkinter import ttk, scrolledtext, font as tkFont
from tkinter import scrolledtext
import threading
import time
import hashlib
user_input_text = ""
ai_response_text = ""

# API keys for OpenWeatherMap and NewsAPI
OPENWEATHER_API_KEY = 'apikey'
NEWSAPI_API_KEY = 'apikey'

class MySoulDatabase:
		def __init__(self):
			# Connect to the local MongoDB database
			self.client = MongoClient('mongodb://localhost:27017/')
			self.db = self.client.mySoulDB
			self.interactions = self.db.interactions


		def log_interaction(self, interaction):
			# Store the interaction in the database
			self.interactions.insert_one(interaction)

		def get_all_interactions(self):
			# Retrieve all interactions from the database
			return list(self.interactions.find({}, {'_id': 0}))
			
class MySoul:
			def __init__(self):
				self.desktop_voice_folder = os.path.join(os.path.expanduser("~\\Desktop"), "voice")  # Define the voice folder path
				print("Initializing MySoul...")
				self.text_to_speech("starting my soul 3 2 1")
				try:
					self.chatbot = pipeline("conversational", model="facebook/blenderbot-400M-distill")
					self.conversation = Conversation()
					self.nlp = spacy.load("en_core_web_sm")
					self.audio_file_counter = 0  # Initialize the audio file counter
					self.desktop_voice_folder = os.path.join(os.path.expanduser("~\\Desktop"), "voice")  # Define the voice folder path
					if not os.path.exists(self.desktop_voice_folder):
						os.makedirs(self.desktop_voice_folder)  # Create the folder if it doesn't exist
					print("Initialization successful")
					self.text_to_speech("Initialization successful.")
				except Exception as e:
					print(f"Error during initialization: {e}")

			def listen_for_wake_word(self):
				"""
				Listen continuously for the wake word.
				"""
				recognizer = sr.Recognizer()
				with sr.Microphone() as source:
					recognizer.adjust_for_ambient_noise(source)
					while True:
						print("Listening for 'the secret word'...")
						self.text_to_speech("Listening for 'the secret word'...")
						audio = recognizer.listen(source, phrase_time_limit=10)
						try:
							speech_as_text = recognizer.recognize_google(audio).lower()
							if 'hey zara' in speech_as_text:
								print("Wake word heard, starting interaction...")
								self.text_to_speech("secret word heard, starting interaction...")
								return 'continue'
							if 'shut down' in speech_as_text:
								print("Shutting down...")
								return 'shutdown'
						except sr.UnknownValueError:
							pass  # Ignore if the speech is not understood
						except sr.RequestError:
							print("Could not request results;")


			
			def voice_to_text(self):
					recognizer = sr.Recognizer()
					with sr.Microphone() as source:
							recognizer.adjust_for_ambient_noise(source)
							try:
								# Listen for the first 10 seconds
								audio = recognizer.listen(source, phrase_time_limit=10)
								return recognizer.recognize_google(audio).lower()
							except Exception as e:
								return "false"
					


			def handle_reminder(self, user_input):
				duration_in_seconds = self.extract_number(user_input)
				if duration_in_seconds:
					self.text_to_speech("Timer set for" + duration_in_seconds)
					self.set_timer(duration_in_seconds, "Your reminder time is up.")
				else:
					self.text_to_speech("I couldn't find a time in your request.")

			def extract_number(self, text):
				numbers = re.findall(r'\d+', text)
				return int(numbers[0]) if numbers else None

			def set_timer(self, duration_in_seconds, message):
				def timer_thread():
					print(f"Timer set for {duration_in_seconds} seconds.")
					time.sleep(duration_in_seconds)
					self.text_to_speech(message)

				threading.Thread(target=timer_thread).start()


			def text_to_speech(self, text):
				# Create a hash of the text to ensure a unique and short filename
				hash_object = hashlib.md5(text.encode())
				filename_hash = hash_object.hexdigest()
				
				# Generate the filename using the hash and current timestamp to ensure uniqueness
				filename = f"audio_{filename_hash[:8]}_{int(time.time())}.mp3"
				file_path = os.path.join(self.desktop_voice_folder, filename)
				
				# Generate the speech
				tts = gTTS(text)
				tts.save(file_path)
				
				# Play the sound file
				playsound(file_path)
			
			def log_interaction(self, user_input, response):
				self.db.log_interaction({"user_input": user_input, "response": response})

			def extract_entity(self, text, entity_type):
				doc = self.nlp(text)
				entities = [ent.text for ent in doc.ents if ent.label_ == entity_type]
				return entities

			def extract_news_topic(self, text):
				print(text)
				doc = self.nlp(text)
				topics = [ent.text for ent in doc.ents if ent.label_ in ["GPE","LOC","ORG", "PERSON", "NORP", "EVENT"]]
				return ' '.join(topics) if topics else None

			def extract_location(self, text):
				print(text)
				doc = self.nlp(text)
				locations = [ent.text for ent in doc.ents if ent.label_ in ["GPE","LOC"]]
				return locations[0] if locations else None

			def fetch_weather(self, location):
				if not location:
					return "Please specify a location for weather information."
				url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={OPENWEATHER_API_KEY}&units=metric"
				response = requests.get(url)
				if response.status_code == 200:
					weather_data = response.json()
					weather = weather_data['weather'][0]['description']
					temp = weather_data['main']['temp']
					return f"Weather in {location}: {weather}, {temp}°C."
				else:
					error_message = f"Failed to fetch weather data: {response.json().get('message', 'Unknown error')}"
				print(error_message)
				return error_message

			def fetch_news(self, topic):
				if not topic:
					topic = "general"
				url = f"https://newsapi.org/v2/everything?q={topic}&apiKey={NEWSAPI_API_KEY}"
				response = requests.get(url)
				if response.status_code == 200:
					news_data = response.json()
					headlines = news_data['articles'][:5]
					news_report = "\n".join([f"{i+1}. {article['title']} - {article['source']['name']}" for i, article in enumerate(headlines)])
					return news_report if news_report else "No news found on this topic."
				else:
					return "Unable to fetch news data."

			def interact(self, user_input):
				print(user_input)
				try:
					conversation = Conversation(user_input)
					response = self.chatbot(conversation)
					# Extract the latest response from the assistant
					if response and response.generated_responses:
						chat_response = response.generated_responses[-1]
						print(f"Chatbot response: {chat_response}")
						return chat_response
					else:
						print("Warning: Unexpected response format or empty response.")
						return "Sorry, I didn't understand that."
				except Exception as e:
					print(f"Interaction error: {e}")
					return "An error occurred during interaction."
				

			def handle_user_input(self):
				global user_input_text, ai_response_text
				user_input = self.voice_to_text().lower()
				user_input_text = user_input
				if user_input == "false":
					print(user_input)
					self.text_to_speech("I didn't catch that. Could you please repeat?")
					return True
				
				elif user_input == "shut down":
					print(user_input)
					self.text_to_speech("shutting down mySoul. bye bye")
					return False
				
				elif 'weather' in user_input:
					location = self.extract_location(user_input)
					weather_info = self.fetch_weather(location) if location else "Please specify a location for weather information."
					self.text_to_speech(weather_info)
					ai_response_text = weather_info
					return True

				elif 'news' in user_input:
					topic = self.extract_news_topic(user_input)
					news_info = self.fetch_news(topic) if topic else "Please specify a topic for news."
					self.text_to_speech(news_info)
					ai_response_text = news_info
					return True

				
				elif 'reminder' in user_input:
					self.handle_reminder(user_input)
					return True


				else:
					response = self.interact(user_input)
					self.text_to_speech(response)
					ai_response_text = response
					return True


my_soul = MySoul()
action = my_soul.listen_for_wake_word()
if action == 'shutdown':
    print("bye-bye")
elif action == 'continue':
	my_soul.text_to_speech("Start speaking 3 2 1 ")
	while(True):
		print("Start speaking 3...2...1...")
		success = my_soul.handle_user_input()
		if not success:
			break
