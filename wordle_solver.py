from concurrent.futures import thread
import time
import os
import string

from nltk.corpus import words
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from constants import word_dict


class WordleSolver():

    def __init__(self):
        self.driver = webdriver.Firefox(service_log_path=os.devnull)
        self.first_tile_characters = list(string.ascii_lowercase)
        self.second_tile_characters = list(string.ascii_lowercase)
        self.third_tile_characters = list(string.ascii_lowercase)
        self.fourth_tile_characters = list(string.ascii_lowercase)
        self.fifth_tile_characters = list(string.ascii_lowercase)
        self.letter_lists = [self.first_tile_characters, self.second_tile_characters, self.third_tile_characters, self.fourth_tile_characters, self.fifth_tile_characters]
        self.required_letters = []
        self.dead_letters = []
        self.word_list = []
        raw_words_list = words.words()
        for word in raw_words_list:
            if len(word) == 5:
                self.word_list.append(word)
        

    def send_first_guess(self):
        b = self.driver
        b.get('https://nytimes.com/games/wordle/index.html')
        # clear the damnned popups
        b.find_element(By.ID, 'pz-gdpr-btn-reject').click()
        b.find_element(By.CLASS_NAME, 'Modal-module_closeIcon__b4z74').click()

        element =  b.find_element(By.TAG_NAME, 'html')
            
        # send characters
        element.send_keys('adieu')
        element.send_keys(Keys.RETURN)
        time.sleep(4)

    def process_guess(self, first_tile, last_tile):
        """Grabs a set of tiles and looks at the result"""
        tiles = self.driver.find_elements(By.CLASS_NAME,"Tile-module_tile__3ayIZ")
        first_tiles = tiles[first_tile:last_tile]
        for iteration, tile in enumerate(first_tiles):
            state = tile.get_attribute('data-state')
            text_entered = tile.text
            for k, v in word_dict.items():
                if text_entered.lower() == k:
                    if v['state'] == '':
                        v['state'] = state
                        if state != 'absent':
                            v['position'] = iteration
                    elif v['state'] == 'present':
                        if state == 'correct':
                            v['state'] = state
                            v['position'] = iteration
                        elif state == 'present':
                            v['position'] = iteration
                    elif v['state'] == 'correct':
                        if state == 'absent':
                            for number, letter_list in enumerate(self.letter_lists):
                                if number != v['position']:
                                    try:
                                        letter_list.remove(k)
                                    except ValueError:
                                        pass  
                        elif state == 'present':
                            v['state'] = state
                            v['position'] = iteration
                            v['duplicate'] = True                
                    break

    def update_character_lists(self):
        """Takes an uodated word dict and updates character lists"""
        for k, v in word_dict.items():
            if v['state'] == 'absent':
                if k not in self.dead_letters:
                    self.dead_letters.append(k)
                for letter_list in self.letter_lists:
                    try:
                        letter_list.remove(k)
                    except ValueError:
                        pass
            elif v['state'] == 'present':
                if k not in self.required_letters:
                    self.required_letters.append(k)
                if v['duplicate']:
                    i = 0
                    for rl in self.required_letters:
                        if rl == k:
                            i += 1
                    if i < 2:
                        self.required_letters.append(k)
                num = v['position']
                try:
                    self.letter_lists[num].remove(k)
                except ValueError:
                    pass
            elif v['state'] == 'correct':
                remove_chars = []
                position = v['position']
                for letter in self.letter_lists[position]:
                    if letter != k:
                        remove_chars.append(letter)
                for remove_char in remove_chars:
                    if remove_char in self.letter_lists[position]:
                        self.letter_lists[position].remove(remove_char)                          
            else:
                pass

    def build_guess_list(self):
        """Take the word list and remove words that dont meet the criteria"""
        words_to_remove = []
        for word in self.word_list:
            for n in range(0,5):
                if word[n] not in self.letter_lists[n]:
                    words_to_remove.append(word)
                    break

        for potential_guess in self.word_list:
            for dead_letter in self.dead_letters:
                if dead_letter in potential_guess:
                    words_to_remove.append(potential_guess)
                    break
            
            for required_letter in self.required_letters:
                if required_letter not in potential_guess:
                    words_to_remove.append(potential_guess)
                    break
        
        for word_to_remove in words_to_remove:
            if word_to_remove in self.word_list:
                self.word_list.remove(word_to_remove)
        
    def try_next_guess(self, start_tile, end_tile):
        """Takes the list of guesses and tries for the next one"""
        b = self.driver
        element =  b.find_element(By.TAG_NAME, 'html')
        for guess in self.word_list:
            element.send_keys(guess)
            element.send_keys(Keys.RETURN)
            tiles = b.find_elements(By.CLASS_NAME,"Tile-module_tile__3ayIZ")
            second_tiles = tiles[start_tile:end_tile]
            time.sleep(1)
            if second_tiles[0].get_attribute('data-state') != 'tbd':
                while second_tiles[4].get_attribute('data-state') == 'tbd':
                    time.sleep(1)
                break
            else:
                time.sleep(1)
                for i in range(0,5):
                    element.send_keys(Keys.BACKSPACE)
                
    def check_for_win(self, start_tile, end_tile):
        b = self.driver
        counter = 0
        tiles = b.find_elements(By.CLASS_NAME,"Tile-module_tile__3ayIZ")
        tile_checker = tiles[start_tile:end_tile]
        for tile in tile_checker:
            if tile.get_attribute('data-state') == 'correct':
                counter += 1
        return counter


first_tile = 0
second_tile = 5
ws = WordleSolver()
ws.send_first_guess()

while True:
    ws.process_guess(first_tile, second_tile)
    first_tile += 5
    second_tile +=5
    ws.update_character_lists()
    ws.build_guess_list()
    ws.try_next_guess(first_tile, second_tile)
    win = ws.check_for_win(first_tile, second_tile)
    if win == 5:
        print("Win")
        break
    else:
        print("Fail")



