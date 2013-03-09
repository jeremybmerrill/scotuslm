import urllib2, urllib
import pickle
import json
import sys
from syllabizer import Syllabizer
import re
import os.path

#   are rhymebrain scores symmetical? is score(a, b) = score(b, a)
# lol turns out yes.

#TODO: rewrite using CMU pronouncing dictionary. rewrite syllabizer too?
# compare rime + coda of last syllable
#TODO: should I refactor everything into a word object that has rhymes_with methods, etc.?
#OMG: this has stress?!?!?! eustress, you could say. so much fun.

#TODO: make phoneme class with is_vowel(); etc.
class RhymeChecker:
  def __init__(self, syllabizer=None):
    self.syllabizer = syllabizer or Syllabizer()
    self.vowels = []
    self.symbols = {}
    self.pronunciations = {}
    self.syllabifications = {}
    #self.consonants = [] #unimplemented
    for line in open(os.path.abspath(os.path.join("./lib/cmudict/cmudict.0.7a.phones")) ,"r"):
      symbol, manner = line.strip().split("\t")
      if manner == "vowel":
        self.vowels.append(symbol)
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
      self.pronunciations[word] = pronunciation
      #self.syllabifications[word] = self.syllabify_pron(pronunciation)

  def syllabify(self, word):
    """ Divide a word directly into its constituent syllables. 

    # >>> r = RhymeChecker2()
    # >>> r.syllabify("shoe")
    # [['SH', 'UW']]
    """
    return self.syllabify_pron(self.pronunciations[word.upper()])

  def syllabify_pron(self, pronunciation):
    """
    Divide a word's pronunciation into syllables.

    >>> r = RhymeChecker2()
    >>> r.syllabify_pron(["SH", "UW"])
    [['SH', 'UW']]
    >>> r.syllabify_pron(["L", "AY1", "N"])
    [['L', 'AY1', 'N']]
    >>> r.syllabify_pron(['W', 'IH1', 'N'])
    [['W', 'IH1', 'N']]
    >>> r.syllabify_pron(['T', 'W', 'IH1', 'N'])
    [['T', 'W', 'IH1', 'N']]
    >>> r.syllabify_pron(['M', 'AY1', 'N', 'Z'])
    [['M', 'AY1', 'N', 'Z']]
    """
    #one consonant? prefer onset
    #three consonants? prefer one coda, two onsets
    #TODO: write now 
    syllables = []
    for phoneme in pronunciation:
      #if it's a vowel, start a new syllable and take all but one of the trailing consonants in the prev syll.
      #print phoneme
      if not syllables:
        syllables.append([])
      if phoneme in self.vowels:
        if syllables:
          previous_syllable = syllables[-1]
          vowels_in_syllable = map(lambda x: x in self.vowels, previous_syllable)
          if True in vowels_in_syllable:
            onset_location = map(lambda x: x in self.vowels, previous_syllable).index(True)
            consonants_to_pop = len(syllables[-1][onset_location:])/2
            onset = []
            if consonants_to_pop > 0:
              for index in range(consonants_to_pop):
                onset.append(syllables[-1].pop())
            else:
              syllables.append([])
            #print "moved " + str(consonants_to_pop) + " consonants to the onset of the next syllable"
          else:
            syllables[-1].append(phoneme)
            continue
        if onset and len(onset) > 0:
          onset.reverse()
          syllables.append([] + onset)
        syllables[-1].append(phoneme)
      else: #phoneme is not a vowel
        syllables[-1].append(phoneme)
    return syllables

  def rhymes_with(self, word1, word2):
    syllables1 = self.syllabify_pron(self.pronunciations[word1.upper()])
    syllables2 = self.syllabify_pron(self.pronunciations[word2.upper()])
    word1_last_syllable = syllables1.pop()
    word2_last_syllable = syllables2.pop()
    word1_rime = filter(lambda x: x in self.vowels, word1_last_syllable)
    word2_rime = filter(lambda x: x in self.vowels, word2_last_syllable)
    word1_coda = word1_last_syllable[word1_last_syllable.index(word1_rime[-1]):]
    word2_coda = word2_last_syllable[word2_last_syllable.index(word2_rime[-1]):]
    return word1_rime == word2_rime and word1_coda == word2_coda





# class RhymeChecker:
#   def __init__(self, rhyme_cache_filename="rhymecache.dat"):
#     self.debug = False
#     self.rhyme_cache_filename = rhyme_cache_filename
#     try:
#       rhyme_cache = pickle.load(open(self.rhyme_cache_filename, 'r'))
#       if self.debug:
#         sys.stderr.write("loaded " + str(len(rhyme_cache)) + " rhymes from cache.")
#     except EOFError:
#       print "rhyme cache could not be loaded!"
#       rhyme_cache = {}
#     rhyme_extras = [ ("anatomical", "economical") ]
#     rhyme_exclusions = [] #TODO implement

#     processed_rhyme_extras = []
#     for extra in rhyme_extras:
#       processed_rhyme_extras.append( (extra[0], [{"word" : extra[1], "score" : 300 }])  )
#     self.rhyme_threshold = 156
#     self.rhyme_cache = dict(rhyme_cache.items() + processed_rhyme_extras)


#   def dump_rhyme_cache(self):
#     pickle.dump(self.rhyme_cache, open(self.rhyme_cache_filename, 'w'))

#   def rhymes_with(self, word1, word2, recurse=True):
#     """ Returns whether word1 rhymes with word2.

#         Rhymebrain is rate limited, so this function caches results.
#         These caches are pickled and saved on the hard drive, so they persist
#         even across runs.

#         I don't know quite how Rhymebrain's API works. Is it possible that
#         word1 is in word2's list of rhymes but word2 is not in word1's list?
#         If so, might have to make two requests per non-rhyme.

#         >>> r = RhymeChecker()
#         >>> r.rhymes_with("hand", "and")
#         True
#         >>> r.rhymes_with("sand", "band")
#         True
#         >>> r.rhymes_with("IV", "No")
#         False
#         >>> r.rhymes_with("No", "ed")
#         False
#     """
#     word1 = word1.lower()
#     word2 = word2.lower()

#     if word1 in self.rhyme_cache:
#       data = self.rhyme_cache[word1]
#     elif word2 in self.rhyme_cache:
#       return self.rhymes_with(word2, word1, False)
#     else:
#       base_url = "http://rhymebrain.com/talk?function=getRhymes&word="
#       full_url = base_url + urllib.quote_plus(word1)
#       if self.debug:
#         print "Didn't have cache data; requesting \"" + word1 + "\" from RhymeBrain"
#       data_json = urllib2.urlopen(full_url).read()
#       data = json.loads(data_json) #a list of dicts, each of which has a word key.
#       self.rhyme_cache[word1] = data
#       if len(self.rhyme_cache) % 10 == 0:
#         self.dump_rhyme_cache()
#     words_that_rhyme = [word_dict["word"] for word_dict in data if word_dict["score"] >= self.rhyme_threshold] #allows hand to rhyme with and.
#     # if word2 in words_that_rhyme:
#     #   if word1 in self.rhyme_cache and word2 in self.rhyme_cache and word1 in [ word_dict["word"] for word_dict in self.rhyme_cache[word2] ]:
#     #     print word1 + "'s score wrt " + word2 + " = " + str([ word_dict["score"] for word_dict in self.rhyme_cache[word1] if word_dict["word"] == word2 ][0])
#     #     print word2 + "'s score wrt " + word1 + " = " + str([ word_dict["score"] for word_dict in self.rhyme_cache[word2] if word_dict["word"] == word1 ][0])
#     return word2 in words_that_rhyme or (recurse and self.rhymes_with(word2, word1, False))

def _test():
  import doctest
  doctest.testmod()

if __name__ == "__main__":
  r = RhymeChecker()
  print r.rhymes_with("hand", "sand")
  print r.rhymes_with("pound", "sand")
  print r.rhymes_with("candy", "sand")
  print r.rhymes_with("pound", "hound")

  #_test()