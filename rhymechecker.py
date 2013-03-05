import urllib2, urllib
import pickle
import json
import sys
from syllabizer import Syllabizer
import re

#   are rhymebrain scores symmetical? is score(a, b) = score(b, a)
# lol turns out yes.

#TODO: rewrite using CMU pronouncing dictionary. rewrite syllabizer too?
# compare rime + coda of last syllable

#TODO: should I refactor everything into a word object that has rhymes_with methods, etc.?
class RhymeChecker2:
  def __init__(self, syllabizer=None):
    self.syllabizer = syllabizer or Syllabizer()

  def rhymes_with(self, word1, word2):
    word1_last_syllable = self.syllabizer.syllable_at(word1, -1)
    word2_last_syllable = self.syllabizer.syllable_at(word2, -1)
    word1_rime = re.search("[aeiou]+", word1_last_syllable).group(0) #first contiguous stretch of vowels
    word2_rime = re.search("[aeiou]+", word2_last_syllable).group(0)
    word1_coda = re.search("[aeiou]+([^aeiou]+)", word1_last_syllable).group(1)
    word2_coda = re.search("[aeiou]+([^aeiou]+)", word1_last_syllable).group(1)
    return word1_rime == word2_rime and word1_coda == word2_coda



class RhymeChecker:
  def __init__(self, rhyme_cache_filename="rhymecache.dat"):
    self.debug = False
    self.rhyme_cache_filename = rhyme_cache_filename
    try:
      rhyme_cache = pickle.load(open(self.rhyme_cache_filename, 'r'))
      if self.debug:
        sys.stderr.write("loaded " + str(len(rhyme_cache)) + " rhymes from cache.")
    except EOFError:
      print "rhyme cache could not be loaded!"
      rhyme_cache = {}
    rhyme_extras = [ ("anatomical", "economical") ]
    rhyme_exclusions = [] #TODO implement

    processed_rhyme_extras = []
    for extra in rhyme_extras:
      processed_rhyme_extras.append( (extra[0], [{"word" : extra[1], "score" : 300 }])  )
    self.rhyme_threshold = 156
    self.rhyme_cache = dict(rhyme_cache.items() + processed_rhyme_extras)


  def dump_rhyme_cache(self):
    pickle.dump(self.rhyme_cache, open(self.rhyme_cache_filename, 'w'))

  def rhymes_with(self, word1, word2, recurse=True):
    """ Returns whether word1 rhymes with word2.

        Rhymebrain is rate limited, so this function caches results.
        These caches are pickled and saved on the hard drive, so they persist
        even across runs.

        I don't know quite how Rhymebrain's API works. Is it possible that
        word1 is in word2's list of rhymes but word2 is not in word1's list?
        If so, might have to make two requests per non-rhyme.

        >>> r = RhymeChecker()
        >>> r.rhymes_with("hand", "and")
        True
        >>> r.rhymes_with("sand", "band")
        True
        >>> r.rhymes_with("IV", "No")
        False
        >>> r.rhymes_with("No", "ed")
        False
    """
    word1 = word1.lower()
    word2 = word2.lower()

    if word1 in self.rhyme_cache:
      data = self.rhyme_cache[word1]
    elif word2 in self.rhyme_cache:
      return self.rhymes_with(word2, word1, False)
    else:
      base_url = "http://rhymebrain.com/talk?function=getRhymes&word="
      full_url = base_url + urllib.quote_plus(word1)
      if self.debug:
        print "Didn't have cache data; requesting \"" + word1 + "\" from RhymeBrain"
      data_json = urllib2.urlopen(full_url).read()
      data = json.loads(data_json) #a list of dicts, each of which has a word key.
      self.rhyme_cache[word1] = data
      if len(self.rhyme_cache) % 10 == 0:
        self.dump_rhyme_cache()
    words_that_rhyme = [word_dict["word"] for word_dict in data if word_dict["score"] >= self.rhyme_threshold] #allows hand to rhyme with and.
    # if word2 in words_that_rhyme:
    #   if word1 in self.rhyme_cache and word2 in self.rhyme_cache and word1 in [ word_dict["word"] for word_dict in self.rhyme_cache[word2] ]:
    #     print word1 + "'s score wrt " + word2 + " = " + str([ word_dict["score"] for word_dict in self.rhyme_cache[word1] if word_dict["word"] == word2 ][0])
    #     print word2 + "'s score wrt " + word1 + " = " + str([ word_dict["score"] for word_dict in self.rhyme_cache[word2] if word_dict["word"] == word1 ][0])
    return word2 in words_that_rhyme or (recurse and self.rhymes_with(word2, word1, False))

def _test():
  import doctest
  doctest.testmod()

if __name__ == "__main__":
  _test()