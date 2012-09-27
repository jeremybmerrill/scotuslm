#! /usr/bin/python
# -*- coding: utf-8 -*-

#TODO: turn self.tfidfs into numpy vectors.

import numpy
import codecs
import glob
import os
import nltk
import math

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
    - downcase stuff

  Next steps:
    - From TFIDFs, put each word into N-space. That is, order the words in the TFIDF dict (having been filtered, I guess).
        and vectorize them. Then save that object.
    - Method to calculate lowest cosine similarity for a given word.

  Storage options: (suppose 6.6k words)
    20 most similar words per word. Thus, need to store 132k words. Reasonable, I think.
    Create this vector shit in memory. I guess I've got to do it anyways, so I might as well see how fast it is...
  """

  def __init__(self):
    self.tfidfs = {}
    self.puncts = [",", ".", ";", ":", "!", "?", "-", u"’", "\"", ]
    self.stoplist = open("english.stop.txt").read().split("\n")
    #stoplist via:  http://jmlr.csail.mit.edu/papers/volume5/lewis04a/a11-smart-stop-list/english.stop

  def tf(self, text_path):
    """Construct a dict of term frequencies in the given document. """
    text = codecs.open(text_path, "r", encoding = "utf-8")
    terms_dict = {}
    for line in text.readlines():
      for word in nltk.word_tokenize(line):
        if word not in self.puncts and word not in self.stoplist:
          terms_dict[word] = terms_dict.get(word, 0) + 1
    return terms_dict

  def generate_tfidfs(self, pathglob, lambdaFunc = lambda x: True ):
    tfs = {}
    df = {}
    temp_tfidfs = {}
    document_paths = glob.glob(os.path.join(*pathglob)) #TODO
    number_of_documents = len(document_paths)
    for document_path in document_paths:
      if os.path.basename(document_path) == '.' or os.path.basename(document_path) == '..' or not lambdaFunc(os.path.basename(document_path)):
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
      for word, count in tf.items():
        if key not in temp_tfidfs:
          temp_tfidfs[key] = {}
        key_word_tfidf = float(count) * math.log(float(number_of_documents) / df[word])
        if key_word_tfidf > 40:
          temp_tfidfs[key][word] = key_word_tfidf
    for key, tfidf_dict in temp_tfidfs.items():
      self.tfidfs[key] = numpy.array(sorted(tfidf_dict.items(), key=lambda x:x[1]))

  def load(self, infile="TopicSimilarityDump.dat"):
    """Load from a dump."""

  def dump(self, outfile="TopicSimilarityDump.dat"):
    """Dump the language similarity stuff, so you don't need to regenerate it every time. Maybe via pickle or shelve or something?""" 

global t
t = TopicSimilarity()
t.generate_tfidfs(["/home/merrillj/scotuslm/opinions", "*", "*", "*"], lambda filename: filename == "SCALIA.txt" )
print t.tfidfs[t.tfidfs.keys()[6]]