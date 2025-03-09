import re
import json
import matplotlib.pyplot as plt
from datetime import datetime
from collections import Counter, deque

from tqdm import tqdm
import random
random.seed(1)

from helper import get_file_dir_with_ext, get_file_dir_from_dir, transcoder

class Content:
        def __init__(self, json_message):
            self.text = transcoder(json_message['content']) if 'content' in json_message else None
            self.photos = json_message['photos'] if 'photos' in json_message else None
            self.share = json_message['share'] if 'share' in json_message else None
            self.links = self.share['link'] if self.share and 'link' in self.share else None
            self.is_message = True if isinstance(self.text, str) and not self.photos and not self.share else False

class Message:
    def __init__(self, json_message):
        self.sender_name = transcoder(json_message['sender_name'])
        self.epoch_time = json_message['timestamp_ms']/1000
        self.datetime = datetime.fromtimestamp(self.epoch_time)
        self.content = Content(json_message)
        
        self.is_attachment_message = True
        self.is_reaction_message = False
        self.is_action_message = False
        
        if self.content.text:
            self.is_attachment_message = self._is_attachment_message(self.content.text)
            self.is_reaction_message = self._is_reaction_message(self.content.text)
            self.is_action_message = self._is_action_message(self.content.text)
        
    def _is_attachment_message(self, content):
        patterns = [
            re.compile(r'.*sent an attachment.'),
        ]
        if any([pattern.match(content) for pattern in patterns]):
            return True
        return False
        
    def _is_reaction_message(self, content):
        # Exclude messages like "user_name reacted \u00e2\u0098\u00a0\u00ef\u00b8\u008f to your message " and "Reacted 🧡 to your message "        
        patterns = [
            re.compile(r'.* reacted.*to your message '),
            re.compile(r'Reacted.*to your message '),
            re.compile(r'.*liked a message'),
            re.compile(r'Liked by .*'),
        ]
        if any([pattern.match(content) for pattern in patterns]):
            return True
        return False
    
    def _is_action_message(self, content):
        # Katherine created the group.
        patterns = [
            re.compile(r'.* started an audio call'),
            re.compile(r'You missed an audio call'),
            re.compile(r'.* started a video chat'),
            re.compile(r'You missed a video chat'),
            re.compile(r'.* created the group'),            
        ]
        if any([pattern.match(content) for pattern in patterns]):
            return True
        return False
    
    def get_string(self, base_time=None):
        if not base_time:
            return f'{self.sender_name}: {self.content.text}'
        time_passed = base_time - self.epoch_time
        return f'{self.sender_name} ({round(time_passed)}s): {self.content.text}'
    
    def __repr__(self):
        return f'''{self.sender_name} ({self.datetime.strftime('%Y-%m-%d %H:%M:%S')}): {self.content.text}\n'''
        

class DirectMessages:
    def __init__(self, dm_dir):
        self.dm_dir = dm_dir
        self.dm_json_files = get_file_dir_with_ext(self.dm_dir, 'json')
        self.title = None
        self.participants = None
        self.is_gc = None
        self.messages = deque()
        
    def _message_filter_default(self, message):
        return message
        
    def init_dm_processing(self, message_filer=_message_filter_default):
        for i, json_path in tqdm(enumerate(self.dm_json_files), desc='Processing JSON files', leave=False):
            with open(json_path, 'r') as file:
                json_data = json.load(file)  
                
            for json_message in json_data['messages']:
                message = Message(json_message)
                if message_filer(message):
                    self.messages.appendleft(message)
            
            if i == 0:
                self.title = transcoder(json_data['title'])
                self.participants = [transcoder(participant['name']) for participant in json_data['participants']]
                self.is_gc = len(self.participants) > 2
                
    def __repr__(self):
        return f'{self.title} ({self.participants})'

class Inbox:
    def __init__(self, inbox_dir):
        self.inbox_dir = inbox_dir
        self.dm_dirs = get_file_dir_from_dir(inbox_dir)
        self.dms = {}
        self.all_participants = set()
        
    def _dm_default_filer(self, dm):
        return dm
    
    def init_inbox_processing(self, dm_filter=_dm_default_filer, message_filter=None):
        for dm_dir in tqdm(self.dm_dirs, desc='Processing Inbox', leave=True):
            dm = DirectMessages(dm_dir)
            dm.init_dm_processing(message_filter) if message_filter else dm.init_dm_processing()
            if dm_filter(dm):
                self.dms[dm.title] = dm
                self.all_participants.update(dm.participants)
                
    def __repr__(self):
        return f'{self.dms.keys()}'
            
    def _common_words_from_partipant(self, participant):
        def normalize_text(text):
            return re.sub(r'\W+', ' ', text.lower()).strip()
            # return re.sub(r'[^a-zA-Z0-9 ]', '', text).lower()
        
        participant_messages = []
        for dm in self.dms.values():
            if participant not in dm.participants:
                continue
            
            for message in dm.messages:
                if message.sender_name == participant:
                    participant_messages.append(normalize_text(message.content.text))
                    
        return Counter(participant_messages)
    
    def _default_message_format(self, message: Message, ref_datetime: datetime) -> str:
        return str(message)
    
    def _save_dataset(self, dataset, file_path):        
        with open(file_path, 'w') as file:
            json.dump(dataset, file)
    
    def create_chat_dataset(self, target_participant, context_size=10, message_format=None):
        if message_format is None:
            message_format = self._default_message_format
            
        dataset = []
        for dm in tqdm(self.dms.values(), desc='Creating Chat Dataset', leave=True):
            if target_participant not in dm.participants:
                continue
            
            for i, message in tqdm(enumerate(dm.messages), desc=f'Processing {dm.title} Messages', leave=False):
                if message.sender_name == target_participant:
                    response = message.content.text
                    curr_time = message.datetime
                    
                    context = deque(maxlen=context_size)
                    for j in range(i-1, i-context_size-1, -1):
                        if j < 0:
                            break
                        context.appendleft(message_format(dm.messages[j], curr_time))
                    
                    data_point = {
                        'context': "\n".join(list(context)),
                        'response': response
                    }
                    dataset.append(data_point)
                    
                    
        self._save_dataset(dataset, f'{target_participant}_dataset.json')
        
        return dataset
    
    def create_timing_dataset(self, target_participant, context_size=10, message_format=None):
        
        high_density_chat_windows = []
        for dm in tqdm(self.dms.values(), desc='Creating Timing Dataset', leave=True):
            if target_participant not in dm.participants:
                continue
            
            messages = list(dm.messages)
            
            chat_window = []
            sender_indices = []
            ref_i = None
            for i, message in enumerate(messages):
                if ref_i == None and message.sender_name == target_participant:
                    start_i = i-context_size if i-context_size >= 0 else 0
                    chat_window.extend(messages[start_i:i])   
                    sender_indices.append(len(chat_window)-1)
                    ref_i = i
                    
                if ref_i != None:
                    if i - ref_i <= context_size:
                        chat_window.append(message)
                        if message.sender_name == target_participant:
                            ref_i = i
                            sender_indices.append(len(chat_window)-1)
                    else:
                        high_density_chat_windows.append((chat_window, sender_indices))
                        chat_window = []
                        sender_indices = []
                        ref_i = None
                        
        # High density chat windows are the chat windows where the target participant is active
        # From high density chat windows, extract  
        
        dataset = []
        for chat_window, sender_indices in high_density_chat_windows:
            num_target_messages = len(sender_indices)
            avail_indices = set(range(context_size+1, len(chat_window)))
            avail_indices -= set(sender_indices)
            
            if num_target_messages > len(avail_indices):
                continue
            
            selected_indices = random.sample(list(avail_indices), num_target_messages)
            for i in selected_indices:
                start_i = i-context_size if i-context_size >= 0 else 0
                context = [message_format(message, chat_window[i].datetime) for message in chat_window[start_i:i]]
                label = 0
                
                data_point = {
                    'context': '\n'.join(context),
                    'label': label
                }
                dataset.append(data_point)
                
            for i in sender_indices:
                start_i = i-context_size if i-context_size >= 0 else 0
                context = [message_format(message, chat_window[i].datetime) for message in chat_window[start_i:i]]
                label = 1
                
                data_point = {
                    'context': '\n'.join(context),
                    'label': label
                }
                dataset.append(data_point)
                
        self._save_dataset(dataset, f'{target_participant}_timing_dataset.json')
        
        return dataset
    
    def plot_active_hours(self, target_participant):
        """
        Graphs the active times of the target participant throughout the day.
        The function creates a histogram of message counts by hour (0-23).
        """
        hours = []
        
        for dm in tqdm(self.dms.values(), desc='Active Analysis', leave=True):
            if target_participant not in dm.participants:
                continue
            
            for message in dm.messages:
                if message.sender_name == target_participant and message.content.text:
                    hours.append(message.datetime.hour)
        
        if not hours:
            print(f"No messages found for {target_participant}")
            return
        
        plt.figure(figsize=(10, 6))
        plt.hist(hours, bins=24, range=(0, 24), edgecolor='black')
        plt.title(f"Active Times of {target_participant} Throughout the Day")
        plt.xlabel("Hour of Day")
        plt.ylabel("Number of Messages")
        plt.xticks(range(0, 25))
        plt.show()
        
    def plot_reply_probability(self, target_participant):
        """
        Plots the probability at each hour of day that the target participant replies to a comment.
        For each message not sent by the target, if the next message is from the target, it is considered a reply.
        """
        reply_counts = {hour: 0 for hour in range(24)}
        total_counts = {hour: 0 for hour in range(24)}
        
        for dm in self.dms.values():
            if target_participant not in dm.participants:
                continue
            
            messages = list(dm.messages)
            for i in range(len(messages) - 1):
                current_msg = messages[i]
                next_msg = messages[i+1]
                # Only consider messages not from the target as potential comments
                if current_msg.sender_name != target_participant:
                    hour = current_msg.datetime.hour
                    total_counts[hour] += 1
                    if next_msg.sender_name == target_participant:
                        reply_counts[hour] += 1
        
        # Calculate reply probabilities for each hour (0-23)
        hours = list(range(24))
        probabilities = []
        for hour in hours:
            if total_counts[hour] > 0:
                probabilities.append(reply_counts[hour] / total_counts[hour])
            else:
                probabilities.append(0)
        
        # Plot the probabilities per hour
        plt.figure(figsize=(10, 6))
        plt.bar(hours, probabilities, color='skyblue', edgecolor='black')
        plt.xlabel('Hour of Day')
        plt.ylabel('Reply Probability')
        plt.title(f"Reply Probability of {target_participant} by Hour of Day")
        plt.xticks(hours)
        plt.ylim(0, 1)
        plt.show()
        
        # Save the probabilities to a JSON file
        with open(f'{target_participant}_reply_probabilities.json', 'w') as file:
            json.dump(probabilities, file)
            