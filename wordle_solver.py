import contextlib
import time
import os
import string

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager


class WordleSolver():

    def __init__(self):
        self.options = Options()
        self.options.add_argument('--headless')
        self.options.add_argument('--disable-gpu')
        self.driver = webdriver.Firefox(options=self.options, service=FirefoxService(GeckoDriverManager().install(), log_path=os.devnull))
        self.first_tile_characters = list(string.ascii_lowercase)
        self.second_tile_characters = list(string.ascii_lowercase)
        self.third_tile_characters = list(string.ascii_lowercase)
        self.fourth_tile_characters = list(string.ascii_lowercase)
        self.fifth_tile_characters = list(string.ascii_lowercase)
        self.letter_lists = [self.first_tile_characters, self.second_tile_characters, self.third_tile_characters, self.fourth_tile_characters, self.fifth_tile_characters]
        self.required_letters = []
        self.dead_letters = []
        self.confirmed_letters = []
        self.word_list = []
        self.invalid_guesses =[]
        
        with open('wordlist.txt', 'r') as file:
            lines = file.readlines()        
            for line in lines:
                word = line.replace('\n', '')
                self.word_list.append(word)

        self.selectors = {
            'close_tutorial': 'Modal-module_closeIcon__TcEKb',
            'tiles': 'Tile-module_tile__UWEHN',
            'menu_buttons': 'Welcome-module_button__ZG0Zh',
            'gdpr_consent': 'pz-gdpr-btn-reject'
        }
    
    def prepare_game_page(self):
        """Navigates through the menu and clears all browser pop ups"""
        print("Loading web browser")
        b = self.driver
        b.get('https://nytimes.com/games/wordle/index.html')

        # Clear GDPR consent tracker settings
        b.find_element(By.ID, self.selectors['gdpr_consent']).click()

        # click menu buttons
        menu_buttons = b.find_elements(By.CLASS_NAME, self.selectors['menu_buttons'])
        for menu_button in menu_buttons:
            if 'Play' in menu_button.text:
                menu_button.click()
        print("Browser loaded, attempting first guess.....")
        
        # clear the damnned popups
        b.find_element(By.CLASS_NAME, self.selectors['close_tutorial']).click()

    def send_first_guess(self):
        """Sends the first guess always the control word adieu"""
        b = self.driver
        element =  b.find_element(By.TAG_NAME, 'html')
        time.sleep(2)

        # send characters
        element.send_keys('adieu')

        element.send_keys(Keys.RETURN)
        tiles = b.find_elements(By.CLASS_NAME, self.selectors['tiles'])
        adieu_tiles = tiles[:5]
        while adieu_tiles[4].get_attribute('data-state') == 'tbd':
            time.sleep(1) 

    def process_guess(self, first_tile, last_tile):
        """Grabs a set of tiles and looks at the result"""
        tiles = self.driver.find_elements(By.CLASS_NAME, self.selectors['tiles'])[first_tile:last_tile]
        test_dict = {'correct':[],
                        'present':[],
                        'absent':[],}
        for iteration, tile in enumerate(tiles):
            state = tile.get_attribute('data-state')
            text_entered = tile.text.lower()
            for k, v in test_dict.items():
                if k == state:
                    tile_info = {'letter': text_entered, 'iteration': iteration}
                    v.append(tile_info)
    
        return test_dict

    def update_letter_lists(self, test_dict):
        """Splits out the guess process and the letter updating"""
        for k, v in test_dict.items():
            if k == 'correct':
                self.process_correct_guesses(v)
            elif k == 'present':
                self.process_present_guesses(v)
            elif k == 'absent':
                self.process_absent_guesses(v)

    def process_correct_guesses(self, v):
        """logic for processing the charactes in the correct list
        param v: the value from iterating over the passed dict"""
        for info in v:
            target_list = self.letter_lists[info['iteration']]
            if info['letter'] not in self.confirmed_letters:
                self.confirmed_letters.append(info['letter'])
                if len(target_list) != 1:
                    remove_chars = [letter for letter in target_list if letter != info['letter']]
                    for char in remove_chars:
                        if char in target_list:
                            target_list.remove(char)

    def process_present_guesses(self, v):
        """Logic for processign present letters""" 
        for info in v:
            target_list = self.letter_lists[info['iteration']]
            try:
                target_list.remove(info['letter'])
            except ValueError:
                pass
            else:
                if info['letter'] not in self.required_letters:
                    self.required_letters.append(info['letter'])

    def process_absent_guesses(self, v):
        """"Logic for processign absent letters
        param v: the value of the list in the iteration"""
        for info in v:
            if (info['letter'] not in self.required_letters 
            and info['letter'] not in self.dead_letters 
            and info['letter'] not in self.confirmed_letters):                 
                self.dead_letters.append(info['letter'])
                for ll in self.letter_lists:
                    if len(ll) != 1:
                        with contextlib.suppress(ValueError):
                            ll.remove(info['letter'])
            elif info['letter'] in self.required_letters:
                pass
            elif info['letter'] in self.confirmed_letters:
                for ll in self.letter_lists:
                    if len(ll) !=1:
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
            tiles = b.find_elements(By.CLASS_NAME, self.selectors['tiles'])[start_tile:end_tile]
            time.sleep(2)
            if tiles[0].get_attribute('data-state') != 'tbd':
                while tiles[4].get_attribute('data-state') == 'tbd':
                    time.sleep(1)
                break
            else:
                time.sleep(2)
                print("Invalid guess - Appending to cleanup list")
                self.invalid_guesses.append(guess)
                self.word_list.remove(guess)
                for _ in range(5):
                    element.send_keys(Keys.BACKSPACE)
                
    def check_for_win(self, start_tile, end_tile):
        b = self.driver
        tiles = b.find_elements(By.CLASS_NAME, self.selectors['tiles'])[start_tile:end_tile]
        total = sum(
            tile.get_attribute('data-state') == 'correct' for tile in tiles
        )
        return total == 5

    def print_winning_word(self, start_tile,end_tile):
        b = self.driver
        tiles = b.find_elements(By.CLASS_NAME, self.selectors['tiles'])[start_tile:end_tile]
        winning_word = [tile.text.lower() for tile in tiles]
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

    def handle_failure(self, first_tile, second_tile):
        """exists the program gracefully upon running out of guesses"""
        if first_tile == 25 and second_tile == 30:
            print('Ran out of guesses\n')
            self.remove_invalid_guess()
            self.driver.close()
            os._exit(os.EX_OK)          

    def solve(self):
        first_tile = 0
        second_tile = 5
        
        self.prepare_game_page()
        self.send_first_guess()

        while True:
            test_dict = self.process_guess(first_tile, second_tile)
            self.update_letter_lists(test_dict)
            first_tile += 5
            second_tile += 5
            self.build_guess_list()
            self.try_next_guess(first_tile, second_tile)
            if win := self.check_for_win(first_tile, second_tile):
                print("Win!\n")
                self.print_winning_word(first_tile, second_tile)
                break
            else:
                print("Fail")
                self.handle_failure(first_tile, second_tile)
        

ws=WordleSolver()
ws.solve()
