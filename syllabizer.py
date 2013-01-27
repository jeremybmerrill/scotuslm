# coding=utf-8

class Syllabizer:
  def __init__(self):
    vowels = ["a", "e", "i", "o", "u"] # Y is dealt with separately
    self.vowels = vowels + map(lambda l: l.upper(), vowels)
    consonants = ["b", "c", "d", "f", "g" "h", "j", "k", 'l', 'm', 'n', 'p', 'q', 'r', 's', 't', 'v', 'w', 'x', 'y', 'z']
    self.consonants = consonants + map(lambda l: l.upper(), consonants)
    self.exceptions = {
      "sometimes" : 2,
      "ritual" : 3,
      "1" : 1,
      "2" : 1,
      "3" : 1,
      "4" : 1,
      "5" : 1,
      "6" : 1,
      "7" : 2,
      "8" : 1,
      "9" : 1,
      "0" : 2
    }


  def syllabize(self, word):
    """ Return the number of syllables in a word.

    Uses some simple phonological rules. Usually right, sometimes wrong.

    >>> s = Syllabizer()
    >>> s.syllabize("scouts")
    1
    >>> s.syllabize("water")
    2
    >>> s.syllabize("scythe")
    1
    >>> s.syllabize("yvonne")
    2
    >>> s.syllabize("yellow")
    2
    >>> s.syllabize("aye")
    1
    >>> s.syllabize("bye")
    1
    >>> s.syllabize("circulation")
    4
    >>> s.syllabize("syllable")
    3
    >>> s.syllabize("distressed")
    2
    >>> s.syllabize("wanted")
    2
    >>> s.syllabize("eaten")
    2
    >>> s.syllabize("singed")
    1
    >>> s.syllabize("diplomacy")
    4
    >>> s.syllabize("walked")
    1
    >>> s.syllabize("shunted")
    2
    >>> s.syllabize("places")
    2
    >>> s.syllabize("shoes")
    1
    >>> s.syllabize("mosses")
    2
    >>> s.syllabize("adzes")
    2
    >>> s.syllabize("wines")
    1
    >>> s.syllabize("ritual")
    3
    >>> s.syllabize("guarantee")
    3
    >>> s.syllabize("assuage")
    2
    >>> s.syllabize("but")
    1
    >>> s.syllabize("sometimes")
    2
    >>> s.syllabize("they")
    1
    >>> s.syllabize("don't")
    1
    >>> s.syllabize("make")
    1
    >>> s.syllabize("sense")
    1
    >>> s.syllabize("laughs")
    1
    """
    if not word:
      return 0
    if word in self.exceptions:
      return self.exceptions[word]

    letters = list(word)
    previous_letter = None
    syllables = 0
    for index, letter in enumerate(letters):
      if previous_letter not in self.vowels and letter in self.vowels:
        if not ((len(letters)-1) == index and letter == "e"):
          syllables += 1

      #Exceptions, because English says fuck you.
      #TODO phonology:
      #   ua : guarantee vs. ritual
      #   io : trio v. -ation
      # oof: sometimes
      if str(previous_letter) + letter in ("eo", "ia", "uo"): 
        syllables += 1
      # Y is a vowel only if surrounded on both sides by non-vowels.
      if letter == "y" and previous_letter not in self.vowels:
        syllables += 1
      if previous_letter == "y" and letter in self.vowels:
        syllables -= 1

      #logic, not an exception :P
      previous_letter = letter
    #more exceptions
    #words ending in "Vble"
    if word[-3:] == "ble":
      syllables += 1
    #[αplace ±voice]e[αplace -voice]
    if word[-2:] in ("ed", "es") and word[-3:] not in ("ted", "ded", "ses", "zes", "ces"):
      syllables -= 1
    return max(syllables, 1)

def _test():
  import doctest
  doctest.testmod()

if __name__ == "__main__":
  _test()