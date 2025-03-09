
import os
import sys
import time
from datetime import datetime
import random

from instagrapi import Client
from instagrapi.exceptions import ClientError

class InstagramMonitor:
    def __init__(self, username, password):
        self.client = Client()
        self.username = username
        self.password = password
        self.users_cache = {}
        self.last_message_id = None
            
        self.client.login(self.username, self.password)
        self.threads = self.client.direct_threads()
        
    def logout(self):
        self.client.logout()
        
    def print_threads(self):
        # Print thread IDs and names
        for thread in self.threads:
            thread_id = thread.id
            thread_name = thread.thread_title if thread.thread_title else "No Name"
            participants = [user.username for user in thread.users]

            print(f"Thread ID: {thread_id}")
            print(f"Thread Name: {thread_name}")
            print(f"Participants: {', '.join(participants)}")
            print("-" * 40)
            
    def get_thread_id(self, thread_name):
        # Get thread ID by name
        for thread in self.threads:
            if thread.thread_title == thread_name:
                return thread.id
        print(f"Thread '{thread_name}' not found")
        return None

    def get_time_ago(self, timestamp):
        """Improved time formatting with plural handling"""
        now = datetime.now(timestamp.tzinfo) if timestamp.tzinfo else datetime.now()
        delta = now - timestamp
        total_seconds = delta.total_seconds()
        
        hours = int(total_seconds // 3600)
        if hours >= 1:
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        
        minutes = int(total_seconds // 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"

    def get_username(self, user_id):
        """Get username with error handling and retries"""
        try:
            if user_id in self.users_cache:
                return self.users_cache[user_id]
            
            # Try multiple methods to get username
            try:
                user = self.client.user_info(user_id)
            except ClientError:
                user = self.client.user_short(user_id)
            
            username = user.username
            self.users_cache[user_id] = username
            return username
        except Exception as e:
            print(f"Error getting username for {user_id}: {e}")
            return f"unknown_user_{user_id}"

    # def format_messages(self, messages, id_to_name):
    #     """Format messages with error handling"""
    #     formatted = []
    #     for msg in messages:
    #         try:
    #             # username = self.get_username(msg.user_id)
    #             full_name = id_to_name.get(msg.user_id, "Unknown")
    #             user = full_name.split(" ")[0]
    #             time_ago = self.get_time_ago(msg.timestamp)
    #             formatted.append(f"<{user}> ({time_ago}): {msg.text}")
    #         except Exception as e:
    #             print(f"Error formatting message {msg.id}: {e}")
    #     return '\n'.join(formatted)

    def monitor_thread(self, thread_id, poll_interval=15):
        """Safer monitoring with increased interval"""
        thread = self.client.direct_thread(thread_id)
        id_to_name = {user.pk: user.full_name for user in thread.users}
        
        while True:
            try:
                thread = self.client.direct_thread(thread_id)
                if not thread.messages:
                    time.sleep(poll_interval)
                    continue

                last_10_messages = thread.messages[-10::-1] if len(thread.messages) >= 10 else thread.messages[::-1]
                latest_message = last_10_messages[-1]
                
                if latest_message.id != self.last_message_id:
                    self.last_message_id = latest_message.id
                    formatted = self.format_messages(last_10_messages, id_to_name)
                    print('\n' + formatted + '\n')
                
                time.sleep(poll_interval)
                
            except Exception as e:
                print(f"Critical error: {e}")
                print("Retrying in 60 seconds...")
                time.sleep(60)
        
                
    def activate_instapersona(self, thread_id, poll_interval=15):
        """Safer monitoring with increased interval"""
        thread = self.client.direct_thread(thread_id)
        id_to_name = {user.pk: user.full_name for user in thread.users}
        
        while True:
            try:
                thread = self.client.direct_thread(thread_id)
                if not thread.messages:
                    time.sleep(poll_interval)
                    continue

                last_10_messages = thread.messages[-10::-1] if len(thread.messages) >= 10 else thread.messages[::-1]
                latest_message = last_10_messages[-1]
                
                if latest_message.id != self.last_message_id:
                    self.last_message_id = latest_message.id
                    formatted = '\n'.join([f"<{id_to_name.get(msg.user_id, 'Unknown')}> ({self.get_time_ago(msg.timestamp)}): {msg.text}" for msg in last_10_messages])
                    print('\n' + formatted + '\n')
                    response = model_response(formatted)
                    print(f"Response: {response}")
                    reply_probability = REPLY_PROBABILITIES[datetime.now().hour]
                    print(f"Reply probability: {reply_probability}")
                    if random.random() < reply_probability:
                        self.client.direct_send(response, [thread_id])
                        print(f'Replied successfully with: {response}')
                
                time.sleep(poll_interval)
                
            except Exception as e:
                print(f"Critical error: {e}")
                print("Retrying in 60 seconds...")
                time.sleep(60)

from instapersona import model_response
from setup import IG_USERNAME, IG_PASSWORD, HF_READ_TOKEN, HF_WRITE_TOKEN, TARGET_NAME, MODEL_NAME

import json 
with open("{TARGET_NAME}_reply_probabilities.json", "r") as file:
    REPLY_PROBABILITIES = json.load(file)
# reply probabilities include the probability of the response at a hour (0-23) for a given message

# Usage example
if __name__ == "__main__":
    # Initialize with your Instagram credentials
    monitor = InstagramMonitor(IG_USERNAME, IG_PASSWORD)
    
    # Print threads
    monitor.print_threads()
    
    # Get thread ID by name
    thread_id = monitor.get_thread_id("Thread Name")
    
    # Start monitoring a specific thread (replace with actual thread ID)
    if thread_id:
        try:
            monitor.monitor_thread(thread_id)
        except KeyboardInterrupt:
            print("Monitoring stopped")
            monitor.logout()