#!/usr/bin/env python
# coding: utf-8

# # Trexquant Interview Project (The Hangman Game)
# 
# * Copyright Trexquant Investment LP. All Rights Reserved. 
# * Redistribution of this question without written consent from Trexquant is prohibited

# ## Instruction:
# For this coding test, your mission is to write an algorithm that plays the game of Hangman through our API server. 
# 
# When a user plays Hangman, the server first selects a secret word at random from a list. The server then returns a row of underscores (space separated)—one for each letter in the secret word—and asks the user to guess a letter. If the user guesses a letter that is in the word, the word is redisplayed with all instances of that letter shown in the correct positions, along with any letters correctly guessed on previous turns. If the letter does not appear in the word, the user is charged with an incorrect guess. The user keeps guessing letters until either (1) the user has correctly guessed all the letters in the word
# or (2) the user has made six incorrect guesses.
# 
# You are required to write a "guess" function that takes current word (with underscores) as input and returns a guess letter. You will use the API codes below to play 1,000 Hangman games. You have the opportunity to practice before you want to start recording your game results.
# 
# Your algorithm is permitted to use a training set of approximately 250,000 dictionary words. Your algorithm will be tested on an entirely disjoint set of 250,000 dictionary words. Please note that this means the words that you will ultimately be tested on do NOT appear in the dictionary that you are given. You are not permitted to use any dictionary other than the training dictionary we provided. This requirement will be strictly enforced by code review.
# 
# You are provided with a basic, working algorithm. This algorithm will match the provided masked string (e.g. a _ _ l e) to all possible words in the dictionary, tabulate the frequency of letters appearing in these possible words, and then guess the letter with the highest frequency of appearence that has not already been guessed. If there are no remaining words that match then it will default back to the character frequency distribution of the entire dictionary.
# 
# This benchmark strategy is successful approximately 18% of the time. Your task is to design an algorithm that significantly outperforms this benchmark.

# In[1]:


import json
import requests
import random
import string
import secrets
import time
import re
import collections
try:
    from urllib.parse import parse_qs, urlencode, urlparse
except ImportError:
    from urlparse import parse_qs, urlparse
    from urllib import urlencode


# In[2]:


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# In[3]:


# googled the top six frequently occored letters
top_six_letters = ['a', 'e', 'i', 'o', 'n','t']

# ratio of top six to length of word
def top_six(word):
    count = 0
    for i in word:
        if i in top_six_letters:
            count = count+1.0
    return count/len(word)

# import the train set to a list
word_library = open("words_250000_train.txt", "r")
word_list = []
for word in word_library:
    word_list.append(word)
    
# brute force the list and replace the "\n" to "" for further use
for i in range(len(word_list)):
    word_list[i] = word_list[i].replace("\n", "")

    
# list the ration of top six to length of word of the words in the dictionary
top_six_ratio=[]
for words in word_list:
    top_six_ratio.append(top_six(words))
top_six_ratio = pd.Series(top_six_ratio)
top_six_ratio.describe()


# In[4]:


bins = np.arange(0.0, 1.0, 0.01)
plt.hist(x = top_six_ratio, bins = bins)


# ### From the above plot we can stastically say that if the number of top six in it are greater than 0.67 times of its lenght than guessing a letter in top six will not be a good choice.

# In[5]:


# find the maximum length of the words
max_length = 0
for words in word_list:
    if(len(words) > max_length):
        max_length = len(words)


# In[6]:


# construct a substring dictionary with length greater or equal to 3
substring_dictionary = {i:[] for i in range(3,max_length + 1)}
sub_length = 3
for sub_length in range (3,max_length + 1):
    for words in word_list:
        if(len(words) >= sub_length):
            for i in range(len(words) - sub_length + 1):
                substring_dictionary[sub_length].append(words[i:i + sub_length]) 


# In[7]:


# function to find number of times a letter come in whole dictionary, keeping count of letter 1 if it comes in a word else 0
def frequency_in_whole_dictionary(new_dictionary):
    dictx = collections.Counter()
    for words in new_dictionary:
        temp = collections.Counter(words)
        for i in temp:
            temp[i] = 1
            dictx = dictx + temp
    return dictx


# In[8]:


# function to generate a list of words which are substring in the original dictionary and of same length as clean word
def match_with_starting_letter(substring_dictionary, clean_word):
    new_dictionary = []
    l = len(clean_word)
    for dict_word in substring_dictionary[l]:
        if re.match(clean_word,dict_word):
            new_dictionary.append(dict_word)
    return new_dictionary


# In[9]:


HANGMAN_URL = "https://www.trexsim.com/trexsim/hangman"

class HangmanAPI(object):
    def __init__(self, access_token=None, session=None, timeout=None):
        self.access_token = access_token
        self.session = session or requests.Session()
        self.timeout = timeout
        self.guessed_letters = []
        
        full_dictionary_location = "words_250000_train.txt"
        self.full_dictionary = self.build_dictionary(full_dictionary_location)        
        self.full_dictionary_common_letter_sorted = collections.Counter("".join(self.full_dictionary)).most_common()
        
        self.current_dictionary = []
        
    

    
        
    def guess(self, word): # word input example: "_ p p _ e "
        ###############################################
        # Replace with your own "guess" function here #
        ###############################################

        # clean the word so that we strip away the space characters
        # replace "_" with "." as "." indicates any character in regular expressions
        clean_word = word[::2].replace("_",".")
        
        # find length of passed word
        len_word = len(clean_word)
        
        # grab current dictionary of possible words from self object, initialize new possible words dictionary to empty
        current_dictionary = self.current_dictionary
        new_dictionary = []
        
        # iterate through all of the words in the old plausible dictionary
        for dict_word in current_dictionary:
            # continue if the word is not of the appropriate length
            if len(dict_word) != len_word:
                continue
                
            # if dictionary word is a possible match then add it to the current dictionary
            if re.match(clean_word,dict_word):
                new_dictionary.append(dict_word)
        
        # overwrite old possible words dictionary with updated version
        self.current_dictionary = new_dictionary   
        
        
        # update the letter frequency count of the new dictionary
        sorted_letter_count = frequency_in_whole_dictionary(new_dictionary).most_common()                   
        
        guess_letter = None
        
        # return most frequently occurring letter in all possible words that hasn't been guessed yet
        for letter,curr_count in sorted_letter_count:
            if letter not in self.guessed_letters:
                if letter in top_six_letters and top_six(clean_word) > 0.67:
                    self.guessed_letters.append(letter)
                    continue
                guess_letter = letter
                break
        
        # return most frequently occurring letter in the substrings dictionary
        if not guess_letter:
            new_dictionary = match_with_starting_letter(substring_dictionary, clean_word)
            sorted_letter_count = frequency_in_whole_dictionary(new_dictionary).most_common()
            if sorted_letter_count:
                for letter,curr_count in sorted_letter_count:
                    if letter not in self.guessed_letters:
                        if letter in top_six_letters and top_six(clean_word) > 0.67:
                            self.guessed_letters.append(letter)
                            continue
                        guess_letter = letter
                        break
                    
        # use the substrings of the clean word to return the most frequent letter in the substrings dictionary, cut the clean words into substrings form 2 to 10    
        def substring_guess(guess_letter,clean_word,k,substring_dictionary):
            c = collections.Counter()
            for i in range(len(clean_word) - len(clean_word)//k + 1):
                substring_clean_word = clean_word[i:i + len(clean_word)//k]
                new_dictionary = match_with_starting_letter(substring_dictionary, substring_clean_word)
                temp = frequency_in_whole_dictionary(new_dictionary)
                c = c + temp
            sorted_letter_count = c.most_common()
            for letter, curr_count in sorted_letter_count:
                if letter not in self.guessed_letters:
                    guess_letter = letter
                    break
            return guess_letter
        
        if not guess_letter:
            for k in range(2, 11):
                guess_letter = substring_guess(guess_letter,clean_word, k, substring_dictionary)
                if guess_letter:
                    break 
                else:
                    # This block will be executed if the loop completes without finding a non-None guess_letter
                    guess_letter = None
        guess_letter = guess_letter
            
            
        # if no word matches in training dictionary, default back to ordering of full dictionary
        if not guess_letter:
            sorted_letter_count = self.full_dictionary_common_letter_sorted
            for letter,curr_count in sorted_letter_count:
                if letter not in self.guessed_letters:
                    if letter in top_six_letters and top_six(clean_word) > 0.67:
                        self.guessed_letters.append(letter)
                        continue
                    guess_letter = letter
                    break            
        
        return guess_letter

    


    ##########################################################
    # You'll likely not need to modify any of the code below #
    ##########################################################
    
    def build_dictionary(self, dictionary_file_location):
        text_file = open(dictionary_file_location,"r")
        full_dictionary = text_file.read().splitlines()
        text_file.close()
        return full_dictionary
                
    def start_game(self, practice=True, verbose=True):
        # reset guessed letters to empty set and current plausible dictionary to the full dictionary
        self.guessed_letters = []
        self.current_dictionary = self.full_dictionary
                         
        response = self.request("/new_game", {"practice":practice})
        if response.get('status')=="approved":
            game_id = response.get('game_id')
            word = response.get('word')
            tries_remains = response.get('tries_remains')
            if verbose:
                print("Successfully start a new game! Game ID: {0}. # of tries remaining: {1}. Word: {2}.".format(game_id, tries_remains, word))
            while tries_remains>0:
                # get guessed letter from user code
                guess_letter = self.guess(word)
                    
                # append guessed letter to guessed letters field in hangman object
                self.guessed_letters.append(guess_letter)
                if verbose:
                    print("Guessing letter: {0}".format(guess_letter))
                    
                try:    
                    res = self.request("/guess_letter", {"request":"guess_letter", "game_id":game_id, "letter":guess_letter})
                except HangmanAPIError:
                    print('HangmanAPIError exception caught on request.')
                    continue
                except Exception as e:
                    print('Other exception caught on request.')
                    raise e
               
                if verbose:
                    print("Sever response: {0}".format(res))
                status = res.get('status')
                tries_remains = res.get('tries_remains')
                if status=="success":
                    if verbose:
                        print("Successfully finished game: {0}".format(game_id))
                    return True
                elif status=="failed":
                    reason = res.get('reason', '# of tries exceeded!')
                    if verbose:
                        print("Failed game: {0}. Because of: {1}".format(game_id, reason))
                    return False
                elif status=="ongoing":
                    word = res.get('word')
        else:
            if verbose:
                print("Failed to start a new game")
        return status=="success"
        
    def my_status(self):
        return self.request("/my_status", {})
    
    def request(
            self, path, args=None, post_args=None, method=None):
        if args is None:
            args = dict()
        if post_args is not None:
            method = "POST"

        # Add `access_token` to post_args or args if it has not already been
        # included.
        if self.access_token:
            # If post_args exists, we assume that args either does not exists
            # or it does not need `access_token`.
            if post_args and "access_token" not in post_args:
                post_args["access_token"] = self.access_token
            elif "access_token" not in args:
                args["access_token"] = self.access_token

        try:
            # response = self.session.request(
            response = requests.request(
                method or "GET",
                HANGMAN_URL + path,
                timeout=self.timeout,
                params=args,
                data=post_args)
        except requests.HTTPError as e:
            response = json.loads(e.read())
            raise HangmanAPIError(response)

        headers = response.headers
        if 'json' in headers['content-type']:
            result = response.json()
        elif "access_token" in parse_qs(response.text):
            query_str = parse_qs(response.text)
            if "access_token" in query_str:
                result = {"access_token": query_str["access_token"][0]}
                if "expires" in query_str:
                    result["expires"] = query_str["expires"][0]
            else:
                raise HangmanAPIError(response.json())
        else:
            raise HangmanAPIError('Maintype was not text, or querystring')

        if result and isinstance(result, dict) and result.get("error"):
            raise HangmanAPIError(result)
        return result
    
class HangmanAPIError(Exception):
    def __init__(self, result):
        self.result = result
        self.code = None
        try:
            self.type = result["error_code"]
        except (KeyError, TypeError):
            self.type = ""

        try:
            self.message = result["error_description"]
        except (KeyError, TypeError):
            try:
                self.message = result["error"]["message"]
                self.code = result["error"].get("code")
                if not self.type:
                    self.type = result["error"].get("type", "")
            except (KeyError, TypeError):
                try:
                    self.message = result["error_msg"]
                except (KeyError, TypeError):
                    self.message = result

        Exception.__init__(self, self.message)


# # API Usage Examples

# ## To start a new game:
# 1. Make sure you have implemented your own "guess" method.
# 2. Use the access_token that we sent you to create your HangmanAPI object. 
# 3. Start a game by calling "start_game" method.
# 4. If you wish to test your function without being recorded, set "practice" parameter to 1.
# 5. Note: You have a rate limit of 20 new games per minute. DO NOT start more than 20 new games within one minute.

# In[10]:


api = HangmanAPI(access_token="9557335ce3acf17960764778772f30", timeout=2000)


# ## Playing practice games:
# You can use the command below to play up to 100,000 practice games.

# In[15]:


k = 0
while k <= 30:

    api.start_game(practice=1,verbose=True)
    [total_practice_runs,total_recorded_runs,total_recorded_successes,total_practice_successes] = api.my_status() # Get my game stats: (# of tries, # of wins)
    practice_success_rate = total_practice_successes / total_practice_runs
    print('run %d practice games out of an allotted 100,000. practice success rate so far = %.3f' % (total_practice_runs, practice_success_rate))
    k += 1


# ## Playing recorded games:
# Please finalize your code prior to running the cell below. Once this code executes once successfully your submission will be finalized. Our system will not allow you to rerun any additional games.
# 
# Please note that it is expected that after you successfully run this block of code that subsequent runs will result in the error message "Your account has been deactivated".
# 
# Once you've run this section of the code your submission is complete. Please send us your source code via email.

# In[ ]:





# In[13]:


for i in range(1000):
    print('Playing ', i, ' th game')
    # Uncomment the following line to execute your final runs. Do not do this until you are satisfied with your submission
    
    api.start_game(practice=0,verbose=False)
    
    # DO NOT REMOVE as otherwise the server may lock you out for too high frequency of requests
    time.sleep(0.5)


# ## To check your game statistics
# 1. Simply use "my_status" method.
# 2. Returns your total number of games, and number of wins.

# In[14]:


[total_practice_runs,total_recorded_runs,total_recorded_successes,total_practice_successes] = api.my_status() # Get my game stats: (# of tries, # of wins)
success_rate = total_recorded_successes/total_recorded_runs
print('overall success rate = %.3f' % success_rate)


# In[ ]:




