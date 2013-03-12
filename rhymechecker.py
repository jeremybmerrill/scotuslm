import urllib2, urllib
import pickle
import json
import sys
from syllabizer import Syllabizer
import re
import os.path
from syllable_count_guesser import SyllableCountGuesser

#assumes rhyme involves only rime of last syllable; this is incomplete.
#for paroxytones (ha! words with penultimate stress, let's include the onset
# of the last syllable and rime of the penultimate)

#OMG: this has stress?!?!?! so much fun.
#TODO: make phoneme class with is_vowel(); etc.
class RhymeChecker:
  def __init__(self, syllabizer=None):
    self.syllabizer = syllabizer or Syllabizer()
    RhymeChecker.vowels = []
    self.symbols = {}
    self.pronunciations = {}
    self.syllabifications = {}
    self.syllable_count_guesser = SyllableCountGuesser()
    #self.consonants = [] #unimplemented
    for line in open(os.path.abspath(os.path.join("./lib/cmudict/cmudict.0.7a.phones")) ,"r"):
      symbol, manner = line.strip().split("\t")
      if manner == "vowel":
        RhymeChecker.vowels.append(symbol)
      self.symbols[symbol] = manner
    for index, line in enumerate(open(os.path.abspath(os.path.join("./lib/cmudict/cmudict.0.7a")), "r")):
      if line.strip()[0] in [";", "#"]:
        continue
      # if index % 1000 == 0 and index > 0:
      #   print("indexed " + str(index) + " words.")
      word_and_pronunciation = line.strip().split("  ")
      if len(word_and_pronunciation) > 1:
        word = word_and_pronunciation[0]
        pronunciation = word_and_pronunciation[1]
      else:
        print line
      if "(" in word:
        continue #not yet implemented
      pronunciation = re.sub("[0-9]", "", pronunciation).split(" ") #ignore stress for now. for now. :P
      self.pronunciations[word] = RhymeChecker.Pronunciation(pronunciation)
      #self.syllabifications[word] = self.syllabify_pron(pronunciation)

  def count_syllables(self, word):
    """ Return the number of syllables in word. 

      #TODO: if the word is unknown, guess using algo from syllabizer.py
    """
    if word.upper() in self.syllabifications:
      return len(self.syllabifications[word.upper()].syllables)
    else:
      return self.syllable_count_guesser.count_syllables(word.lower())

  def syllabify(self, word):
    """ Divide a word directly into its constituent syllables. 

    >>> r = RhymeChecker()
    >>> map(lambda syll: syll.phonemes, r.syllabify("shoe").syllables)
    [['SH', 'UW']]
    """
    return self.syllabify_pron(self.pronunciations[word.upper()])

  def get_rime(self, word):
    """
    Return this word's rime. 

    #TODO: for words with penultimate or antepenultimate stress, return 
      penultimate syllable's rime and ultimate syllable.
      (e.g. syllable rhymes with killable, but not edible.)
    """
    try:
      return self.syllabify(word).syllables[-1].rime()
    except KeyError:
      return []

  def syllabify_pron(self, pronunciation):
    """
    Divide a word's Pronunciation into syllables.

    Returns a syllabification object.

    >>> r = RhymeChecker()
    >>> map(lambda syll: syll.phonemes, r.syllabify_pron(RhymeChecker.Pronunciation(["SH", "UW"])).syllables)
    [['SH', 'UW']]
    >>> map(lambda syll: syll.phonemes, r.syllabify_pron(RhymeChecker.Pronunciation(["L", "AY1", "N"])).syllables)
    [['L', 'AY1', 'N']]
    >>> map(lambda syll: syll.phonemes, r.syllabify_pron(RhymeChecker.Pronunciation(['W', 'IH1', 'N'])).syllables)
    [['W', 'IH1', 'N']]
    >>> map(lambda syll: syll.phonemes, r.syllabify_pron(RhymeChecker.Pronunciation(['T', 'W', 'IH1', 'N'])).syllables)
    [['T', 'W', 'IH1', 'N']]
    >>> map(lambda syll: syll.phonemes, r.syllabify_pron(RhymeChecker.Pronunciation(['M', 'AY1', 'N', 'Z'])).syllables)
    [['M', 'AY1', 'N', 'Z']]
    """
    #one consonant? prefer onset
    #three consonants? prefer one coda, two onsets
    #TODO: write now 
    array_of_arrays_of_phonemes = []
    for phoneme in pronunciation.phonemes:
      #if it's a vowel, start a new syllable and take all but one of the trailing consonants in the prev syll.
      #print phoneme
      if not array_of_arrays_of_phonemes:
        array_of_arrays_of_phonemes.append([])
      if phoneme in RhymeChecker.vowels:
        if array_of_arrays_of_phonemes:
          previous_syllable = array_of_arrays_of_phonemes[-1]
          vowels_in_syllable = map(lambda x: x in RhymeChecker.vowels, previous_syllable)
          if True in vowels_in_syllable:
            onset_location = map(lambda x: x in RhymeChecker.vowels, previous_syllable).index(True)
            consonants_to_pop = len(array_of_arrays_of_phonemes[-1][onset_location:])/2
            onset = []
            if consonants_to_pop > 0:
              for index in range(consonants_to_pop):
                onset.append(array_of_arrays_of_phonemes[-1].pop())
            else:
              array_of_arrays_of_phonemes.append([])
            #print "moved " + str(consonants_to_pop) + " consonants to the onset of the next syllable"
          else:
            array_of_arrays_of_phonemes[-1].append(phoneme)
            continue
        if onset and len(onset) > 0:
          onset.reverse()
          array_of_arrays_of_phonemes.append([] + onset)
        array_of_arrays_of_phonemes[-1].append(phoneme)
      else: #phoneme is not a vowel
        array_of_arrays_of_phonemes[-1].append(phoneme)
    return RhymeChecker.Syllabification(map(lambda array_of_phonemes: RhymeChecker.Syllable(array_of_phonemes), array_of_arrays_of_phonemes))

  def rhymes_with(self, word1, word2):
    """ Returns whether word1 rhymes with word2.
    >>> r = RhymeChecker()
    >>> r.rhymes_with("hand", "sand")
    True
    >>> r.rhymes_with("pound", "hound")
    True
    >>> r.rhymes_with("pound", "sand")
    False
    >>> r.rhymes_with("candy", "sand")
    False
    """
    if word1.upper() in self.syllabifications:
      syllables1 = self.syllabifications[word1.upper()]
      syllables2 = self.syllabifications[word2.upper()]
    else:
      syllables1 = self.syllabify_pron(self.pronunciations[word1.upper()]).syllables
      syllables2 = self.syllabify_pron(self.pronunciations[word2.upper()]).syllables
    word1_last_syllable = syllables1[-1]
    word2_last_syllable = syllables2[-1]
    return word1_last_syllable.rime() == word2_last_syllable.rime()
    # word1_nucleus = word1_last_syllable.nucleus()
    # word2_nucleus = word2_last_syllable.nucleus()
    # word1_coda = word1_last_syllable.coda()
    # word2_coda = word2_last_syllable.coda()
    # return word1_nucleus == word2_nucleus and word1_coda == word2_coda

  class Pronunciation:
    def __init__(self, phonemes_array):
      self.phonemes = phonemes_array

  class Syllabification:
    def __init__(self, array_of_syllables):
      self.syllables = array_of_syllables

  class Syllable:
    def __init__(self, phoneme_array):
      self.phonemes = phoneme_array
      self._nucleus_end_location = None #set later, if needed
      self._nucleus_start_location = None #set later, if needed

    def nucleus(self):
      return filter(lambda x: x in RhymeChecker.vowels, self.phonemes)
    def _nucleus_start(self):
      if not self._nucleus_start_location:
        self._nucleus_start_location = map(lambda x: x in RhymeChecker.vowels, self.phonemes).index(True)
      return self._nucleus_start_location

    #TODO fix.
    def _nucleus_end(self):
      if not self._nucleus_end_location:
        self._nucleus_end_location = map(lambda x: x in RhymeChecker.vowels, self.phonemes).index(True)
      return self._nucleus_end_location

    def coda(self):
      return self.phonemes[self._nucleus_end():]
    def rime(self):
      return self.nucleus() + self.coda()
    def onset(self):
      return self.phonemes[:self._nucleus_start()]

  def test_stuff(self, word):
    pron = self.pronunciations[word.upper()]
    print map(lambda s: s, pron.phonemes)
    print map(lambda s: s.phonemes, self.syllabify_pron(pron))


  #TODO: stress.
  # class Phone:
  #   def __init__(self, phone_string):
  #     self.phone = phone_string
  #   def isVowel(self):



def _test():
  import doctest
  doctest.testmod()

if __name__ == "__main__":
  # r = RhymeChecker()
  # r.test_stuff("anthropology")
  _test()