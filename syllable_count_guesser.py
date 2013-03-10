# coding=utf-8

class SyllableCountGuesser:
  def __init__(self):
    self.vowels = ["a", "e", "i", "o", "u"] # Y is dealt with separately
    self.consonants = ["b", "c", "d", "f", "g" "h", "j", "k", 'l', 'm', 'n', 'p', 'q', 'r', 's', 't', 'v', 'w', 'x', 'y', 'z']
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
      "0" : 2,
      "our" : 2
    }

  # #TODO: finish.
  # def syllable_at(self, word, index):
  #   """ Return a best guess for the syllable at index in word.
  #   >>> s= Syllabizer()
  #   >>> s.syllable_at("water", -1)
  #   "ter"
  #   >>> s.syllable_at("cheese", -1)
  #   "cheese"

  #   corncob -> ["corn", "cob"]
  #   computer -> ["com", "pu", "ter"]
  #   airplane -> ["air", "plane"]
  #   nicar -> ["ni", "car"]
  #   biter -> ["bi", "ter"]
  #   shimmy -> ["shim", "my"]
  #   shiny -> ["shi", "ny"]
  #   carob -> ["car", "ob"]
  #   garage -> ["ga", "rage"]
  #   monster -> ["mon", "ster"] 
  #   #generalization: English prefers codas to onsets, but <i> is often realized phonologically as /ij/, so any following consonant is likely an onset.
  #   """
  #   if not word:
  #     return None
  #   word = word.lower()
  #   if self.count_syllables(word) == 1:
  #     return word
  #   else:
  #     syllables = []
  #     raise NotYetImplementedError



  def count_syllables(self, word):
    """ Return the number of syllables in a word.

    Uses some simple phonological rules. Usually right, sometimes wrong.

    >>> s = Syllabizer()
    >>> s.count_syllables("scouts")
    1
    >>> s.count_syllables("water")
    2
    >>> s.count_syllables("scythe")
    1
    >>> s.count_syllables("yvonne")
    2
    >>> s.count_syllables("yellow")
    2
    >>> s.count_syllables("aye")
    1
    >>> s.count_syllables("bye")
    1
    >>> s.count_syllables("circulation")
    4
    >>> s.count_syllables("syllable")
    3
    >>> s.count_syllables("distressed")
    2
    >>> s.count_syllables("wanted")
    2
    >>> s.count_syllables("eaten")
    2
    >>> s.count_syllables("singed")
    1
    >>> s.count_syllables("diplomacy")
    4
    >>> s.count_syllables("walked")
    1
    >>> s.count_syllables("shunted")
    2
    >>> s.count_syllables("places")
    2
    >>> s.count_syllables("shoes")
    1
    >>> s.count_syllables("mosses")
    2
    >>> s.count_syllables("adzes")
    2
    >>> s.count_syllables("wines")
    1
    >>> s.count_syllables("ritual")
    3
    >>> s.count_syllables("guarantee")
    3
    >>> s.count_syllables("assuage")
    2
    >>> s.count_syllables("but")
    1
    >>> s.count_syllables("sometimes")
    2
    >>> s.count_syllables("they")
    1
    >>> s.count_syllables("don't")
    1
    >>> s.count_syllables("make")
    1
    >>> s.count_syllables("sense")
    1
    >>> s.count_syllables("laughs")
    1
    """
    if not word:
      return 0
    if word in self.exceptions:
      return self.exceptions[word]

    word = word.lower()

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
  s = Syllabizer()
  print s.count_syllables("and")
  print s.count_syllables("JUSTICE")
  print s.count_syllables("alito")