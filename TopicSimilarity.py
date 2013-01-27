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
from operator import itemgetter

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
    self.tfidfs = {} #for word similarity, map of words to vector of TFIDF per document
    self.tfidfs_by_document = {} #for document similarity/topic modeling, map of documents to vector of tfidf per word
    self.puncts = [",", ".", ";", ":", "!", "?", "-", u"’", "\"", ]
    self.stoplist = open("english.stop.txt").read().split("\n")
    self.tfs = {}
    self.cached_file_stats = {}

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
    """Construct a dict of term frequencies in the given document. 

      Also side-effectily populates file-size dict
    """
    text = codecs.open(text_path, "r", encoding = "utf-8")
    terms_dict = {}    
    for line in text.readlines():
      for word in nltk.word_tokenize(line):
        word = word.lower()
        if word not in self.puncts and word not in self.stoplist:
          terms_dict[word] = terms_dict.get(word, 0) + 1
    return terms_dict

  #damnit python. If it looks like a duck, but doesn't act like a duck, it's not a goddamn duck typed language.
  #def file_stats(self):
  #  """Let's totally just imitate an array, Ruby-style."""
  #  return self.cached_file_stats

  def topical_words(self, document_path, count = 10):
    minimal_topicality = 0.0
    topic_words = []
    for word, val in self.tfidfs_by_document[document_path].iteritems():
      if val > minimal_topicality:
        if len(topic_words) >= count:
          topic_words.pop()
        topic_words.append((word, val))
        get_val = lambda x: x[1]
        minimal_topicality = min( map(lambda x: x[1], topic_words) )
        topic_words = sorted(topic_words, key=itemgetter(1), reverse=True)
    return topic_words #map(lambda x: x[0], topic_words)



  def file_stats(self, filename):
    def shellquote(s):
      return "'" + s.replace("'", "'\\''") + "'"
    stats = os.popen("wc " + shellquote(filename)).read().strip().split(" ")
    if filename not in self.cached_file_stats:
      self.cached_file_stats[filename] = {}
      #self.cached_file_stats[filename]["lines"] = stats[0]
      self.cached_file_stats[filename]["unique words"] = len(self.tfs[filename].keys())
      self.cached_file_stats[filename]["words"] = stats[2]
    return self.cached_file_stats[filename]


  def generate_tfidfs(self, pathglob, filesFilter = lambda x: True ):
    """ For words in documents specified in pathglob and filesFilter, construct TFIDF vectors.

    Each word's TFIDF vector contains its TFIDF for a given document. 

    The correspondence between a document's index in a word's TFIDF vector and its name is not consistent, but it does remain
      constant within calls of this method. Thus, words with similar TFIDFs for a given index in the vector share some similarity.

    This method is side-effecty; self.tfidfs contains the TFIDF vectors. This method doens't return anything.
    """
    df = {}
    temp_tfidfs = {}
    document_paths = glob.glob(os.path.join(*pathglob)) #TODO
    number_of_documents = len(document_paths)
    for document_path in document_paths:
      if os.path.basename(document_path) == '.' or os.path.basename(document_path) == '..' or not filesFilter(os.path.basename(document_path)):
        continue
      self.tfs[document_path] = self.tf(document_path)
    #Lots of possibilities for creating DF dict.
    # 1. Create it side-effectily in tf() <-- Gross, but more efficient.
    # 2. Create it on-the-fly when tf() returns a dict. <-- as inefficient as (3).
    # 3. Create it all at once from tfs dict. <-- I chose this one.
    for tf in self.tfs.values():
      for word in tf.keys():
        df[word] = df.get(word, 0) + 1 #document frequency.
    for document_path, tf in self.tfs.items():
      temp_tfidfs[document_path] = {}
      for word, tf_of_word in tf.items():
        #N.B. on the line below, I'm normalizing TF by unique word count in documents.     total word count: float( self.file_stats(document_path)["words"] )
        filepath_word_tfidf = (float(tf_of_word) / len(tf.keys())) * math.log(float(number_of_documents) / df[word])
    #     if filepath_word_tfidf > 40:
    #       temp_tfidfs[document_path][word] = filepath_word_tfidf
    # for document_path, tfidf_dict in temp_tfidfs.items():
    #   self.tfidfs[document_path] = numpy.array(sorted(tfidf_dict.items(), document_path=lambda x:x[1]))
        temp_tfidfs[document_path][word] = filepath_word_tfidf
      #need to pivot documents to be {word : ordered_vector_of_tfidf_by_document}
    for index, docs_to_tfidfs in enumerate(temp_tfidfs.items()):
      filename, tfidfs = docs_to_tfidfs #I don't care what document a TFIDF came from, as long as its consistent.
      for word, tfidf in tfidfs.items():
        if filename not in self.tfidfs_by_document:
          self.tfidfs_by_document[filename] = {}
        self.tfidfs_by_document[filename][word] = tfidf
        self.tfidfs[word] = self.tfidfs.get(word, numpy.zeros( len(temp_tfidfs)))
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

  def document_tfidf_vectors(self):
    """map of filenames to vectors of consistently ordered tfidf values

      algorithm choice: How do I normalize these? My current results correlate very highly with document size.
        1. Divide each value by the highest TFIDF in any document.
        2. Divide each value by the highest TFIDF in the given document.
        3. Divide each value by the highest TFIDF for the given word.
        4. Same type of things, but where there's 1 point of mass per document. 
    """
    filenames_to_tfidf_vectors = {}
    word_count = len(self.tfidfs.keys())
    print word_count
    for document, words_to_tfidfs in self.tfidfs_by_document.iteritems():
      filenames_to_tfidf_vectors[document] = numpy.zeros(word_count )

    for index, word in enumerate(self.tfidfs.keys()):
      for document, words_to_tfidfs in self.tfidfs_by_document.iteritems():
        if word in words_to_tfidfs:
          print index
          filenames_to_tfidf_vectors[document][index] = words_to_tfidfs[word]
    return filenames_to_tfidf_vectors

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
#t = TopicSimilarity(glob = ["/home/merrillj/code/scotuslm/opinions", "*", "*", "*"] ) #337.698110104secs
#t = TopicSimilarity(glob = ["/home/merrillj/code/scotuslm/opinions", "*", "*", "*"], filesFilter= lambda filename: filename == "SCALIA.txt" ) #crappy results, 6.03190803528secs
print str(time.time() - before) + "secs"
print time.localtime()

print t.similar_words("habeas")[0:10]
"""


#t = TopicSimilarity() # 103.504664898secs
#t = TopicSimilarity(glob = ["/home/merrillj/code/scotuslm/opinions", "*", "*", "*"], filesFilter= lambda filename: filename == "SCALIA.txt" )
t = TopicSimilarity(glob = ["/home/merrillj/code/scotuslm/opinions", "11txt", "*", "*"], filesFilter= lambda filename: filename == "SCALIA.txt" )

print t.document_tfidf_vectors()


from hcluster import pdist, linkage, dendrogram
from os.path import basename


document_tfidf_vectors = t.document_tfidf_vectors()

for index, filename in enumerate(document_tfidf_vectors.keys()):
  print str(index) + ": " + filename.split("/")[-2] + ": " + str(t.file_stats(filename)["words"])

pdist_of_tfidfs = pdist(document_tfidf_vectors.values())
asdf = linkage(pdist_of_tfidfs)
dendrogram(asdf)

#1,8,0,11,2,7,4,6,5,10,9,3,12,13
