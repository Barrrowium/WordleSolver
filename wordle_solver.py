import contextlib
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
        #self.options.add_argument('--headless')
        #self.options.add_argument('--disable-gpu')
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
        self.invalid_guesses =[]
        with open('wordlist.txt', 'r') as file:
            lines = file.readlines()        
            for line in lines:
                word = line.replace('\n', '')
                self.word_list.append(word)
        self.selectors = {
            'reject_cookies': 'pz-gdpr-btn-reject',

        }

    def send_first_guess(self):
        # added coment
        b = self.driver
        b.get('https://nytimes.com/games/wordle/index.html')
        # clear the damnned popups
        b.find_element(By.ID, self.selectors['reject_cookies']).click()
        b.find_element(By.CLASS_NAME, 'Modal-module_closeIcon__b4z74').click()

        element =  b.find_element(By.TAG_NAME, 'html')
        time.sleep(2)

        # send characters
        element.send_keys('adieu')

        element.send_keys(Keys.RETURN)
        tiles = b.find_elements(By.CLASS_NAME,"Tile-module_tile__3ayIZ")
        adieu_tiles = tiles[:5]
        while adieu_tiles[4].get_attribute('data-state') == 'tbd':
                    time.sleep(1) 

    

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
                    if len(target_list) != 1:
                        remove_chars = [letter for letter in target_list if letter != info['letter']]
                        for char in remove_chars:
                            if char in target_list:
                                target_list.remove(char)
            if k == 'present':
                for info in v:
                    target_list = self.letter_lists[info['iteration']]
                    try:
                        target_list.remove(info['letter'])
                    except ValueError:
                        pass
                    else:
                        if info['letter'] not in self.required_letters:
                            self.required_letters.append(info['letter'])

            if k == 'absent':
                for info in v:
                    if (info['letter'] not in self.required_letters
                        and info['letter'] not in self.dead_letters):
                        self.dead_letters.append(info['letter'])

                        for ll in self.letter_lists:
                            if len(ll) != 1:
                                with contextlib.suppress(ValueError):
                                    ll.remove(info['letter'])
                
    def build_guess_list(self):
        """Take the word list and remove words that dont meet the criteria"""
        words_to_remove = []
        for word in self.word_list:
            for n in range(5):
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
            print(f"\nAttempting guess: {guess}")
            element.send_keys(guess)
            element.send_keys(Keys.RETURN)
            tiles = b.find_elements(By.CLASS_NAME,"Tile-module_tile__3ayIZ")
            second_tiles = tiles[start_tile:end_tile]
            time.sleep(2)
            if second_tiles[0].get_attribute('data-state') != 'tbd':
                while second_tiles[4].get_attribute('data-state') == 'tbd':
                    time.sleep(1)
                break
            else:
                time.sleep(1)
                print("Invalid guess - Appending to cleanup list")
                self.invalid_guesses.append(guess)
                self.word_list.remove(guess)
                for _ in range(5):
                    element.send_keys(Keys.BACKSPACE)
                
    def check_for_win(self, start_tile, end_tile):
        b = self.driver
        tiles = b.find_elements(By.CLASS_NAME,"Tile-module_tile__3ayIZ")
        tile_checker = tiles[start_tile:end_tile]
        return sum(
            tile.get_attribute('data-state') == 'correct' for tile in tile_checker
        )

    def print_winning_word(self, start_tile,end_tile):
        b = self.driver
        tiles = b.find_elements(By.CLASS_NAME,"Tile-module_tile__3ayIZ")
        tile_checker = tiles[start_tile:end_tile]
        winning_word = [tile.text.lower() for tile in tile_checker]
        print('The winning word was:')
        print("\t" + ''.join(winning_word))
        self.remove_invalid_guess()
        b.close()

    
    def remove_invalid_guess(self):
        """Remove any invalid words found whilst guessing from the wordlist file
        :param invalid_word: string value of the word to be removed"""
        if len(self.invalid_guesses) > 0:
            print('\nCleaning up word file')
            with open('wordlist.txt', 'r') as readFile:
                lines = readFile.readlines()

            for line in lines:
                word = line.replace('\n','')
                if word in self.invalid_guesses:
                    lines.remove(line)
            
            with open('wordlist.txt', 'w') as writeFile:
                writeFile.writelines(lines)
            print(f'Clean up finished removed {len(self.invalid_guesses)} words!')
        else:
            print("\nNo words to remove")

    def check_word_list_not_empty(self):
        """Check the wordlist to ensure it is not empty - end the session if it is"""
        if len(self.word_list) == 0:
            self.driver.close()
            print("Guess list was wiped, debug for more info")
            raise AssertionError



first_tile = 0
second_tile = 5
ws = WordleSolver()
ws.send_first_guess()

while True:
    ws.process_guess(first_tile, second_tile)
    first_tile += 5
    second_tile += 5
    ws.build_guess_list()
    ws.check_word_list_not_empty()
    ws.try_next_guess(first_tile, second_tile)
    win = ws.check_for_win(first_tile, second_tile)
    if win == 5:
        print("Win!\n")
        ws.print_winning_word(first_tile, second_tile)
        break
    else:
        print("Fail")
