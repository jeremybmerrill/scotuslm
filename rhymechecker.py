import urllib2, urllib
import pickle
import json
import sys

class RhymeChecker:
  def __init__(self, rhyme_cache_filename="rhymecache.dat"):
    self.debug = False
    self.rhyme_cache_filename = rhyme_cache_filename
    try:
      rhyme_cache = pickle.load(open(self.rhyme_cache_filename, 'r'))
      if self.debug:
        sys.stderr.write("loaded " + str(len(rhyme_cache)) + " rhymes from cache.")
    except IOError:
      rhyme_cache = {}
    rhyme_extras = [ ("anatomical", "economical") ]

    processed_rhyme_extras = []
    for extra in rhyme_extras:
      processed_rhyme_extras.append( (extra[0], [{"word" : extra[1], "score" : 300 }])  )

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
      self.dump_rhyme_cache()
    words_that_rhyme = [word_dict["word"] for word_dict in data if word_dict["score"] >= 156] #allows hand to rhyme with and.
    return word2 in words_that_rhyme or (recurse and self.rhymes_with(word2, word1, False))

def _test():
  import doctest
  doctest.testmod()

if __name__ == "__main__":
  _test()