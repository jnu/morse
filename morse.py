from typing import Generator, Tuple
import re

import click
from wordfreq import word_frequency, iter_wordlist


ALPHABET = {
    'A': '.-',     'B': '-...',   'C': '-.-.',
    'D': '-..',    'E': '.',      'F': '..-.',
    'G': '--.',    'H': '....',   'I': '..',
    'J': '.---',   'K': '-.-',    'L': '.-..',
    'M': '--',     'N': '-.',     'O': '---',
    'P': '.--.',   'Q': '--.-',   'R': '.-.',
    'S': '...',    'T': '-',      'U': '..-',
    'V': '...-',   'W': '.--',    'X': '-..-',
    'Y': '-.--',   'Z': '--..',
    '0': '-----',  '1': '.----',  '2': '..---',
    '3': '...--',  '4': '....-',  '5': '.....',
    '6': '-....',  '7': '--...',  '8': '---..',
    '9': '----.',
}

ONE_LETTER = {'A', 'I'}
TWO_LETTER = {'AN', 'AS', 'AT', 'BE', 'BY', 'DO', 'GO', 'HE', 'HI', 'IF', 'IN', 'IS', 'IT', 'ME', 'MY', 'NO', 'OF', 'ON', 'OR', 'SO', 'TO', 'UP', 'US', 'WE'}
THREE_LETTER = {
        'AND', 'ARE', 'BUT', 'CAN', 'FOR', 'GET', 'GOT', 'HAS', 'HAD', 'HER', 'HIM', 'HIS', 'HOW',
        'ITS', 'LET', 'MAY', 'NOT', 'NOW', 'OUR', 'OUT', 'SAY', 'SEE', 'SHE', 'THE', 'WHO', 'YOU',
        'ALL', 'ANY', 'DAY', 'END', 'EVE', 'EYE', 'FAR', 'FEW', 'FOR', 'GET', 'GOT', 'HAS', 'HER',
        'AXE', 'BEE', 'BOW', 'BOX', 'BUS', 'CAR', 'CAT', 'COW', 'CUT', 'DOG', 'EYE', 'FAR', 'FAX',
        'FLY', 'FOG', 'FOX', 'GUN', 'HAT', 'HEN', 'HOT', 'ICE', 'JET', 'KEY', 'LAW', 'LEG', 'LET',
        'LIE', 'LIP', 'MAP', 'MAY', 'MIX', 'MOM', 'MUD', 'NEW', 'NUT', 'OAK', 'OIL', 'OLD', 'ONE',
        'PAN', 'PEN', 'PIG', 'PIN', 'POP', 'POT', 'PUT', 'RED', 'RIP', 'RUN', 'SAD', 'SAY', 'SEA',
        'SEE', 'SET', 'SHE', 'SIT', 'SKI', 'SKY', 'SUN', 'TAX', 'TEA', 'TEN', 'THE', 'TIE', 'TIN',
        'TOO', 'TOP', 'TWO', 'USE', 'VAN', 'WAX', 'WAY', 'WEB', 'WET', 'WHO', 'WIN', 'YOU', 'ZIP',
        }


def get_word_list() -> set[str]:
    """Get a set of words from Unix dict."""
    return {re.sub(r'[^A-Z]', '', word.upper()) for word in iter_wordlist('en')}


def decode_all_possible(encoded: str) -> Generator[str, None, None]:
    """Decode all possible morse code messages from the given encoded string.

    Args:
        encoded: The encoded morse code message without spaces.

    Returns:
        A generator that yields all possible decoded messages.
    """
    if len(encoded) == 0:
        yield ''
    else:
        for letter, code in ALPHABET.items():
            if encoded.startswith(code):
                for rest in decode_all_possible(encoded[len(code):]):
                    yield letter + rest


def segment_words(wordlist: set[str], message: str) -> Generator[Tuple[str, float], None, None]:
    """Segment a message into words, with its likelihood.

    Args:
        message: The message to segment.

    Returns:
        A generator that yields all possible segmentations of the message
        along with the likelihood of the segmentation.
    """
    if len(message) == 0:
        yield '', 1.0
    else:
        for i in range(1, len(message) + 1):
            word = message[:i]
            # Restrict 1 and 2 letter words to a small set.
            if len(word) == 1 and word not in ONE_LETTER:
                continue
            #if len(word) == 2 and word not in TWO_LETTER:
            #    continue
            #if len(word) == 3 and word not in THREE_LETTER:
            #    continue
            if word in wordlist:
                for rest, likelihood in segment_words(wordlist, message[i:]):
                    yield word + ' ' + rest, likelihood * word_frequency(word, 'en')




@click.command()
@click.argument('encoded')
def main(encoded: str) -> None:
    """Decode a morse code message."""
    wordset = get_word_list()
    max_likelihood = 0.0
    max_segmentation = ''
    for message in decode_all_possible(encoded):
        print(message)
        for segmentation, likelihood in segment_words(wordset, message):
            if likelihood > max_likelihood:
                max_likelihood = likelihood
                max_segmentation = segmentation
                print(segmentation, likelihood)
    print("=== DONE ===")
    print(max_segmentation)
    print(max_likelihood)
        


if __name__ == '__main__':
    main()
