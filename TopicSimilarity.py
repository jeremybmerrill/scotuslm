#! /usr/bin/python
# -*- coding: utf-8 -*-

#TODO: turn self.tfidfs into numpy sparse vectors.
#TODO: when dumping, record glob and filesFilter in a separate "manifest" file, so when the same glob and filesFilter are supplied, we don't need to regenerate.
#TODO: Explore other methods of TFIDF (e.g. normalized)

import numpy
import codecs
import glob
import os
import nltk
import math
from scipy.spatial.distance import cosine

class TopicSimilarity:
  """ 
    From a corpus of input documents, discover which words are 'topic words' and which topic words are similar to one another.

    When supplied with a topic word, return a list of words and their similarities to the argument word.

    Similarity: Words with high similarity have low cosine distance to other words in N-space where N is each document and values in N-space are TFIDF per document.
    Alternative measure (not implemented): clustering somehow

    How to compute similarity: 
      TFIDF in a document, ignore below a certain TFIDF. (40!)
      Cosine similarity across TFIDF'd words.
  """

  """
  TODO: 
    - profile to check efficiency of side-effecty or add'l iteration for DF.

  Next steps:
    - From TFIDFs, put each word into N-space. That is, order the words in the TFIDF dict (having been filtered, I guess).
        and vectorize them. Then save that object.
    - Method to calculate lowest cosine similarity for a given word.

  Storage options: (suppose 6.6k words)
    20 most similar words per word. Thus, need to store 132k words. Reasonable, I think.
    Create this vector shit in memory. I guess I've got to do it anyways, so I might as well see how fast it is...
  """

  default_dump_path = "TopicSimilarityDump.dat"

  def __init__(self, **kwargs):
    self.tfidfs = {}
    self.puncts = [",", ".", ";", ":", "!", "?", "-", u"’", "\"", ]
    self.stoplist = open("english.stop.txt").read().split("\n")
    if "infile" in kwargs:
      self.load(kwargs["infile"])
    elif "glob" in kwargs:
      if "filesFilter" in kwargs:
        self.generate_tfidfs(kwargs["glob"], kwargs["filesFilter"])
      else:
        self.generate_tfidfs(kwargs["glob"])
    elif os.path.exists("TopicSimilarityDump.dat"):
      print "loading from default dump path."
      self.load("TopicSimilarityDump.dat")
    else:
      raise TypeError('Required keyword argument infile or glob not found.')

    #stoplist via:  http://jmlr.csail.mit.edu/papers/volume5/lewis04a/a11-smart-stop-list/english.stop

  def tf(self, text_path):
    """Construct a dict of term frequencies in the given document. """
    text = codecs.open(text_path, "r", encoding = "utf-8")
    terms_dict = {}
    for line in text.readlines():
      for word in nltk.word_tokenize(line):
        word = word.lower()
        if word not in self.puncts and word not in self.stoplist:
          terms_dict[word] = terms_dict.get(word, 0) + 1
    return terms_dict

  def generate_tfidfs(self, pathglob, filesFilter = lambda x: True ):
    """ For words in documents specified in pathglob and filesFilter, construct TFIDF vectors.

    Each word's TFIDF vector contains its TFIDF for a given document. 

    The correspondence between a document's index in a word's TFIDF vector and its name is not consistent, but it does remain
      constant within calls of this method. Thus, words with similar TFIDFs for a given index in the vector share some similarity.

    This method is side-effecty; self.tfidfs contains the TFIDF vectors. This method doens't return anything.
    """
    tfs = {}
    df = {}
    temp_tfidfs = {}
    document_paths = glob.glob(os.path.join(*pathglob)) #TODO
    number_of_documents = len(document_paths)
    for document_path in document_paths:
      if os.path.basename(document_path) == '.' or os.path.basename(document_path) == '..' or not filesFilter(os.path.basename(document_path)):
        continue
      tfs[document_path] = self.tf(document_path)
    #Lots of possibilities for creating DF dict.
    # 1. Create it side-effectily in tf() <-- Gross, but more efficient.
    # 2. Create it on-the-fly when tf() returns a dict. <-- as inefficient as (3).
    # 3. Create it all at once from tfs dict. <-- I chose this one.
    for tf in tfs.values():
      for word in tf.keys():
        df[word] = df.get(word, 0) + 1 #document frequency.
    for key, tf in tfs.items():
      temp_tfidfs[key] = {}
      for word, count in tf.items():         
        filepath_word_tfidf = float(count) * math.log(float(number_of_documents) / df[word])
    #     if filepath_word_tfidf > 40:
    #       temp_tfidfs[key][word] = filepath_word_tfidf
    # for key, tfidf_dict in temp_tfidfs.items():
    #   self.tfidfs[key] = numpy.array(sorted(tfidf_dict.items(), key=lambda x:x[1]))
        temp_tfidfs[key][word] = filepath_word_tfidf
      #need to pivot documents to be {word : ordered_vector_of_tfidf_by_document}
    for index, docs_to_tfidfs in enumerate(temp_tfidfs.items()):
      filename, tfidfs = docs_to_tfidfs #I don't care what document a TFIDF came from, as long as its consistent.
      for word, tfidf in tfidfs.items():
        self.tfidfs[word] = self.tfidfs.get(word, numpy.zeros( (1, len(temp_tfidfs)))[0])
        self.tfidfs[word][index] = tfidf

  def similar_words(self, word, max=None):
    """ Returns *max* tuples of similarities (0 to 1), words similar to *word*. """
    similarity = []
    for candidate_word, tfidfs in self.tfidfs.items():
      if candidate_word == word: #words don't count as similar to themselves
        continue
      try:
        distance = cosine_distance(self.tfidfs.get(word.lower()), self.tfidfs[candidate_word])
      except KeyError:
        distance = float('inf')

      similarity.append((distance, candidate_word)) 
      #TODO: remove the word itself.
    if max:
      return sorted(filter(lambda x: x[0] > 0.2, similarity), reverse=True)[0:max]
    else:
      return sorted(filter(lambda x: x[0] > 0.2, similarity), reverse=True)

  def similar_to(self, word1, word2):
    """Returns w2's similarity to w1 as float, 0 < n < 1. """
    if word1 in self.stoplist or word2 in self.stoplist or word1 not in self.tfidfs or word2 not in self.tfidfs:
      return 0.01 #why? I dunno. 
    else:
      return cosine_distance(self.tfidfs[word1.lower()], self.tfidfs[word2.lower()])

  def load(self, infile="TopicSimilarityDump.dat"):
    """Load from a dump."""
    import cPickle
    self.tfidfs = cPickle.load(open(infile))


  def dump(self, outfile="TopicSimilarityDump.dat"):
    """Dump the language similarity data.""" 
    import cPickle
    cPickle.dump(self.tfidfs, open(outfile))

def cosine_distance(u, v):
  """
  Returns the cosine of the angle between vectors v and u. This is equal to
  u.v / |u||v|.

  via: http://stackoverflow.com/questions/2380394/simple-implementation-of-n-gram-tf-idf-and-cosine-similarity-in-python
  """
  return numpy.dot(u, v) / (math.sqrt(numpy.dot(u, u)) * math.sqrt(numpy.dot(v, v))) 

"""
#NB: only for profiling
import time

before = time.time()
print time.localtime(before)
t = TopicSimilarity() # 103.504664898secs
#t = TopicSimilarity(glob = ["/home/merrillj/scotuslm/opinions", "*", "*", "*"] ) #337.698110104secs
#t = TopicSimilarity(glob = ["/home/merrillj/scotuslm/opinions", "*", "*", "*"], filesFilter= lambda filename: filename == "SCALIA.txt" ) #crappy results, 6.03190803528secs
print str(time.time() - before) + "secs"
print time.localtime()

print t.similar_words("habeas")[0:10]
"""