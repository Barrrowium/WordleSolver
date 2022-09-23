from multiprocessing.sharedctypes import Value
from optparse import Option
import time
import os
import string


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options


class WordleSolver():

    def __init__(self):
        self.options = Options()
        self.options.add_argument('--headless')
        self.options.add_argument('--disable-gpu')
        self.driver = webdriver.Firefox(options=self.options, service_log_path=os.devnull)
        self.first_tile_characters = list(string.ascii_lowercase)
        self.second_tile_characters = list(string.ascii_lowercase)
        self.third_tile_characters = list(string.ascii_lowercase)
        self.fourth_tile_characters = list(string.ascii_lowercase)
        self.fifth_tile_characters = list(string.ascii_lowercase)
        self.letter_lists = [self.first_tile_characters, self.second_tile_characters, self.third_tile_characters, self.fourth_tile_characters, self.fifth_tile_characters]
        self.required_letters = []
        self.dead_letters = []
        self.word_list = []
        with open('wordlist.txt', 'r') as file:
            lines = file.readlines()        
            for line in lines:
                word = line.replace('\n', '')
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
        test_dict = {'correct':[],
                        'present':[],
                        'absent':[],}
        for iteration, tile in enumerate(first_tiles):
            state = tile.get_attribute('data-state')
            text_entered = tile.text.lower()
            for k, v in test_dict.items():
                if k == state:
                    tile_info = {'letter': text_entered, 'iteration': iteration}
                    v.append(tile_info)

        for k, v in test_dict.items():
            if k == 'correct':
                for info in v:
                    target_list = self.letter_lists[info['iteration']]
                    remove_chars = []
                    if len(target_list) != 1:
                        for letter in target_list:
                            if letter != info['letter']:
                                remove_chars.append(letter)
                        for char in remove_chars:
                            if char in target_list:
                                target_list.remove(char)
                    else:
                        pass

            if k == 'present':
                for info in v:
                    target_list = self.letter_lists[info['iteration']]
                    try:
                        target_list.remove(info['letter'])
                    except ValueError:
                        pass
                    else:
                        self.required_letters.append(info['letter'])
            
            if k == 'absent':
                for info in v:
                    for ll in self.letter_lists:
                        if len(ll) != 1:
                            try:
                                ll.remove(info['letter'])
                            except ValueError:
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

    def print_winning_word(self, start_tile,end_tile):
        b = self.driver
        tiles = b.find_elements(By.CLASS_NAME,"Tile-module_tile__3ayIZ")
        tile_checker = tiles[start_tile:end_tile]
        winning_word = []
        for tile in tile_checker:
            winning_word.append(tile.text.lower())
        print('The winning word was:')
        print(''.join(winning_word))
        b.close()


first_tile = 0
second_tile = 5
ws = WordleSolver()
ws.send_first_guess()

while True:
    ws.process_guess(first_tile, second_tile)
    first_tile += 5
    second_tile +=5
    ws.build_guess_list()
    ws.try_next_guess(first_tile, second_tile)
    win = ws.check_for_win(first_tile, second_tile)
    if win == 5:
        print("Win")
        ws.print_winning_word(first_tile, second_tile)
        break
    else:
        print("Fail")
