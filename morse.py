from typing import Generator, Tuple
import re

import click
from wordfreq import word_frequency, iter_wordlist
from unidecode import unidecode
import wordsegment
from countries import countries


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
#    '0': '-----',  '1': '.----',  '2': '..---',
#    '3': '...--',  '4': '....-',  '5': '.....',
#    '6': '-....',  '7': '--...',  '8': '---..',
#    '9': '----.',
}

STATES = [
        "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
        "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
        "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
        "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
        "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
        "New Hampshire", "New Jersey", "New Mexico", "New York",
        "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
        "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
        "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
        "West Virginia", "Wisconsin", "Wyoming",
        ]
STATE_CAPITALS = [
        "Montgomery", "Juneau", "Phoenix", "Little Rock", "Sacramento",
        "Denver", "Hartford", "Dover", "Tallahassee", "Atlanta", "Honolulu",
        "Boise", "Springfield", "Indianapolis", "Des Moines", "Topeka",
        "Frankfort", "Baton Rouge", "Augusta", "Annapolis", "Boston",
        "Lansing", "Saint Paul", "Jackson", "Jefferson City", "Helena",
        "Lincoln", "Carson City", "Concord", "Trenton", "Santa Fe",
        "Albany", "Raleigh", "Bismarck", "Columbus", "Oklahoma City",
        "Salem", "Harrisburg", "Providence", "Columbia", "Pierre",
        "Nashville", "Austin", "Salt Lake City", "Montpelier", "Richmond",
        "Olympia", "Charleston", "Madison", "Cheyenne",
        ]
CONTINENTS = [
        "Africa", "Antarctica", "Asia", "Australia", "Europe", "North America",
        "South America",
        ]
        

ONE_LETTER = {'A', 'I'}


def encode(message: str, spaces: bool = True) -> str:
    """Encode a message into morse code.

    Args:
        message: The message to encode.

    Returns:
        The encoded morse code message.
    """
    sep = ' ' if spaces else ''
    return sep.join(ALPHABET[unidecode(letter)] for letter in message.upper())


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
            # Restrict one letter words to "words"
            if len(word) == 1 and word not in ONE_LETTER:
                continue
            if word in wordlist:
                for rest, likelihood in segment_words(wordlist, message[i:]):
                    yield word + ' ' + rest, likelihood * word_frequency(word, 'en')


@click.group()
def cli():
    pass

@cli.command("decode")
@click.option('--segmenter', default='freq', type=click.Choice(['freq', 'wordsegment']))
def decode(segmenter) -> None:
    """Decode a morse code message."""
    # Read encoded from stdin:
    encoded = click.prompt('Enter encoded message', type=str)
    encoded = re.sub(r'[^.-]', '', encoded)
    wordsegment.load()
    wordset = get_word_list()
    max_likelihood = 0.0
    max_segmentation = ''
    i = 0
    s = 0
    for message in decode_all_possible(encoded):
        i += 1
        if segmenter == 'freq':
            for segmentation, likelihood in segment_words(wordset, message):
                s += 1
                if likelihood > max_likelihood:
                    max_likelihood = likelihood
                    max_segmentation = segmentation
                    print(segmentation, likelihood)
        else:
            segments = wordsegment.segment(message)
            s += 1
            freq = 1.0
            for segment in segments:
                freq *= word_frequency(segment, 'en')
            if freq > max_likelihood:
                max_likelihood = freq
                max_segmentation = ' '.join(segments)
                print(max_segmentation, freq)
    print("\n=== DONE ===")
    print("Best match:")
    print(max_segmentation)
    print("Likelihood:", max_likelihood)
    print("Total number of possibilities:", i)
    print("Directly evaluated segmentations:", s)


@cli.command("reparse")
@click.argument('segment', type=str)
def reparse(segment) -> None:
    """Convert segment to morse code without spaces and find all possible decodings."""
    segment = re.sub(r'[^A-Z]', '', segment.upper())
    encoded = encode(segment, spaces=False)
    worset = get_word_list()
    print("Encoded:", encoded)
    print("Decoded:")
    for message in decode_all_possible(encoded):
        for segmentation, likelihood in segment_words(worset, message):
            print(segmentation, likelihood)


@cli.command("country")
def country() -> None:
    # Find countries that have the same encoding
    names = [country['name'].decode('utf-8') for country in countries]
    names += [country['capital'].decode('utf-8') for country in countries]
    names += STATES
    names += STATE_CAPITALS
    names += CONTINENTS
    clean = {n: encode(re.sub(r'[^A-Z]', '', n.upper()), spaces=False) for n in names}
    encodings: dict[str, list[str]] = {}
    for country, encoding in clean.items():
        encodings.setdefault(encoding, []).append(country)
    for encoding, cts in encodings.items():
        #print(encoding, cts)
        if len(cts) > 1:
            print("WINNER!!!")
            print(encoding, cts)


if __name__ == '__main__':
    cli()
