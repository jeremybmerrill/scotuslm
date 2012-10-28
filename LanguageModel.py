#! /usr/bin/python
# -*- coding: utf-8 -*-

import os
import copy
import math
import random
import glob
import re
import nltk
import codecs
from operator import itemgetter

class LanguageModel:
  """
  Trigram language model.

  threelm[word_two_back][word_back]
  => {tokencount => 13, {1 => "Jeremy", 2 => "Nate", 3 => "Jeremy", 4 => "Megan"}}
  => {tokencount => 13, [[1, "Jeremy"], [5, "Megan"], [7, "Nate"]]

  "backoff" -- if count is less than <10, go to 2LM

  """


  def __init__(self, pathglob, filesFilter = lambda x: True ):
    trigram_counts = dict()
    unigram_counts = dict()
    bigram_counts = dict() #e.g. {San => {Francisco => 50, Jose => 20} }
    self.word_count = 0
    self.unpathiness = 0.2


    self.debug = False


    files = glob.glob(os.path.join(*pathglob)) #TODO
    for f in files:
      if os.path.basename(f) == '.' or os.path.basename(f) == '..' or not filesFilter(os.path.basename(f)):
        continue
      for sentence in codecs.open(f, "r", encoding = "utf-8"): #files are pre-split into sentences
        #line = line.split(/[.?!]|$/) 
        split_sentence = nltk.word_tokenize(sentence.strip())
        word_two_back = ""
        word_back = ""
        for word in split_sentence:
          #word.replace("—", "")
          word = re.sub(re.compile("[_\(\),]"), "", word.lower() ) #—
          self.word_count += 1

          unigram_counts[word] = unigram_counts.get(word, 0) + 1
          bigram_inner_dict = copy.copy(bigram_counts.get( word_back, dict()))
          bigram_inner_dict[word] = bigram_inner_dict.get(word, 0) +1
          bigram_counts[word_back] = bigram_inner_dict
          #trigram_counts[word_two_back][word_back][word] += 1
          trigram_one_step_inside = copy.copy(trigram_counts.get(word_two_back, dict()))
          trigram_two_steps_inside = copy.copy( trigram_one_step_inside.get(word_back, dict()) )
          trigram_two_steps_inside[word] = trigram_two_steps_inside.get(word, 0) + 1
          trigram_one_step_inside[word_back] = trigram_two_steps_inside
          trigram_counts[word_two_back] = trigram_one_step_inside
          
          word_two_back = word_back
          word_back = word

    self.trigramlm = dict()
    self.bigramlm = dict()
    self.unigramlm = []

    for word_two_back, trigram_counts_one_step_inside in trigram_counts.iteritems():
      trigram_LM_one_step_inside = dict()
      outerCount = 0
      for word_back, trigram_counts_two_steps_inside in trigram_counts_one_step_inside.iteritems():
        outerCount += 1
        count = 0
        trigram_LM_two_steps_inside = []
        for word, myCount in trigram_counts_two_steps_inside.iteritems():
          count += myCount
          trigram_LM_two_steps_inside.append([count, word])
        trigram_LM_one_step_inside[word_back] = dict()
        trigram_LM_one_step_inside[word_back]["tokencount"] = count
        trigram_LM_one_step_inside[word_back]["data"] = trigram_LM_two_steps_inside
      self.trigramlm[word_two_back] = trigram_LM_one_step_inside

    if self.debug:
      print(bigram_counts)
    for word_back, inner_hash in bigram_counts.iteritems():
      count = 0
      innerLM = []
      for word, myCount in inner_hash.iteritems():
        count += myCount
        innerLM.append([count, word])
      self.bigramlm[word_back] = dict()
      self.bigramlm[word_back]["tokencount"] = count
      self.bigramlm[word_back]["data"] = innerLM

    count = 0
    for word, myCount in unigram_counts.iteritems():
      count += myCount
      self.unigramlm.append([count, word])
    if self.debug:
      print("done generating hashes")

  def next_word_bigrams(self,word_back):
    next_word_candidates = self.bigramlm.get(word_back, dict({"tokencount" : 0, "data" : []}))
    logthis = float("inf") if next_word_candidates.get("tokencount", 0) <= 1 else next_word_candidates["tokencount"]
    
    #backoff
    if random.random() < self.unpathiness / math.log( logthis ):
      if self.debug: 
        print("backing off to unigrams.")
      next_word_candidates["data"] = self.unigramlm
      next_word_candidates["tokencount"] = self.word_count
    return next_word_candidates

  def next_word_trigrams(self, word_back, word_two_back):
    word_back_and_next_word_candidates = self.trigramlm.get(word_two_back, dict({"tokencount" : 0, "data" : []}) )
    next_word_candidates = word_back_and_next_word_candidates.get(word_back, dict({"tokencount" : 0, "data" : []}))

    #backoff. 
    logthis = float("inf") if next_word_candidates.get("tokencount", 0) <= 1 else next_word_candidates["tokencount"]
    if random.random() < self.unpathiness / math.log( logthis ):
      if self.debug:
        print("backing off to bigrams, aka smoothing.")
      next_word_candidates = self.next_word_bigrams(word_back)
    elif not next_word_candidates :
      if self.debug:
        print("backing off to bigrams, since trigrams returned nothing")
      next_word_candidates = self.next_word_bigrams(word_back)
    return next_word_candidates

  def trigram_children(self, word_back, word_two_back, max=20):
    word_back_and_next_word_candidates = self.trigramlm.get(word_two_back, dict({"tokencount" : 0, "data" : []}) )
    next_word_candidates = word_back_and_next_word_candidates.get(word_back, dict({"tokencount" : 0, "data" : []}))
    return map(lambda x: x[1], sorted(next_word_candidates["data"], key=itemgetter(0), reverse=True)[0:max])

  def bigram_children(self, word_back, max=20): 
    next_word_candidates = self.bigramlm.get(word_back, dict({"tokencount" : 0, "data" : []}))
    return map(lambda x: x[1], sorted(next_word_candidates["data"], key=itemgetter(0), reverse=True)[0:max])


"""
myLM = LanguageModel(["/home/merrillj/scotuslm/opinions", "*", "*", "*"], lambda filename: filename == "SCALIA.txt" )
opts = dict({"debug" : True, "veryShallowParse" : True, "max_sentence_length" : 50, "paragraph_length" : 10, 
  'topic':'congress', 'random_weight': 1, 'topicality_weight':3, 'very_shallow_parse_weight':3})
print(myLM.get_phrase( **opts )).encode("utf-8")
"""