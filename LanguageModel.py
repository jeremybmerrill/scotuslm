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

class LanguageModel:
  """What's the best model for a 3LM?

  threelm[word_two_back][word_back]
  => {tokencount => 13, {1 => "Jeremy", 2 => "Nate", 3 => "Jeremy", 4 => "Megan"}}
  => {tokencount => 13, [[1, "Jeremy"], [5, "Megan"], [7, "Nate"]]

  "backoff" -- if count is less than <10, go to 2LM

  """


  def __init__(self, pathglob, filesFilter = lambda x: True ):
    trigram_counts = dict()
    unigram_counts = dict()
    bigram_counts = dict() #e.g. {San => {Francisco => 50, Jose => 20} }

    #complementizer_list = ['AZ', 'TH', 'TS', ]
    #verb_list = ['S']
    self.complementizer_list = ["WP", "WPS," "WDT", "WRB"] #also, "in", dealt with separately
    #actual_IN_complementizers = ["that", "although", "after", "although", "if", "unless", "as", "inasmuch", "until", "when", "whenever", "since", "while", "because", "before", "though"]
    self.verb_list = ["VB", "VBD", "VBP", "VBZ",] #, "vbg", "vbn" #participles, which I don't really want.
    #complementizer_count = 0
    #verb_count = 0
    self.makes_things_worse_adjustment = 3 #if the selected part of speech would make things worse, multiply this by probability to make it harder to add the selected word
    self.unpathiness = 0
    self.debug = False

    word_count = 0
    files = glob.glob(os.path.join(*pathglob)) #TODO
    for f in files:
      if os.path.basename(f) == '.' or os.path.basename(f) == '..' or not filesFilter(os.path.basename(f)):
        continue
      for sentence in codecs.open(f, "r", "utf-8"): #files are pre-split into sentences
        #line = line.split(/[.?!]|$/) 
        split_sentence = nltk.word_tokenize(sentence.strip())
        word_two_back = ""
        word_back = ""
        for word in split_sentence:
          #word.replace("—", "")
          word = re.sub(re.compile("[_\(\),]"), "", word.lower() ) #—
          word_count += 1

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

  def check_verbs_and_complementizers(self, sentence_so_far, next_word, probability = 0.3 ):
    #implements "very shallow parsing" on a sentence
    #if the sentence doesn't have N + 1 verbs for every N complementizers, 
    #   then, with some probability, return False if the next word if it doesn't resolve the imbalance.
    #   and return False with higher probability if the next word increases the imbalance
    #   in hopes of finding a word that satisfies the imbalance on the next go-round.

    #TODO: rewrite to return a probability of rejection.

    tagged_sentence_so_far = nltk.pos_tag(nltk.word_tokenize( " ".join(sentence_so_far) ))
    tagged_sentence_with_next_word =  nltk.pos_tag(nltk.word_tokenize( " ".join(sentence_so_far + [next_word]) ))
    next_word_POS = tagged_sentence_with_next_word[-1][1] #the next word's tag is the second element of the final element of the list of words in the sentence.
    print(str(tagged_sentence_with_next_word ))
    #TODO: what if the sentence didn't get tagged successfully?
    verb_count = len([pos for word, pos in tagged_sentence_so_far if pos in self.verb_list])
    complementizer_count = len([pos for word, pos in tagged_sentence_so_far if pos in self.complementizer_list]) #TODO: some complementizers are BS.

    if self.debug:
      print(". ".join(map(str, [next_word, verb_count, complementizer_count, next_word_POS])).encode("utf-8"))

    if verb_count == 0 and complementizer_count == 0:
      return True

    if next_word_POS in self.complementizer_list:
      if verb_count == complementizer_count + 1: #balance
        return True
      elif verb_count > complementizer_count + 1: #imbalance -- complementizer needed
        #accept, this fixes the imbalance!
        return True
      elif random.random() > probability * self.makes_things_worse_adjustment: #verb needed, reject with high probability; allowing this word would increase the imbalance
        #oh well, keep it.
        return True
      else:
        return False
    elif next_word_POS in self.verb_list:
      if verb_count == complementizer_count: #balance, feel free to take me out of balance verbly. :)
        return True
      elif verb_count < complementizer_count:  #imbalance -- verb needed
        #accept, this fixes the imbalance!
        return True
      elif random.random() > probability * self.makes_things_worse_adjustment: #complementizer needed, reject with high probability; allowing this word would increase the imbalance
        #oh well, keep it.
        return True
      else:
        return False
    else:
      if verb_count == complementizer_count + 1: #balance
        return True
      elif random.random() > probability: #selected word doesn't fix the imbalance.
        #oh well, keep it.
        return True
      else:
        #rejected!
        return False

  def next_word_bigrams(self,word_back):
    get_stuff = self.bigramlm.get(word_back, dict({"tokencount" : 0, "data" : []}))
    logthis = float("inf") if get_stuff.get("tokencount", 0) <= 1 else get_stuff["tokencount"]
    if random.random() < self.unpathiness / Math.log( logthis ):
      if self.debug: 
        print("backing off to unigrams.")
      get_stuff["data"] = unigramlm
      get_stuff["tokencount"] = word_count
    return get_stuff

  def next_word_trigrams(self, word_back, word_two_back):
    testthingy = self.trigramlm.get(word_two_back, dict({"tokencount" : 0, "data" : []}) )
    get_stuff = testthingy.get(word_back, dict({"tokencount" : 0, "data" : []}))

    logthis = float("inf") if get_stuff.get("tokencount", 0) <= 1 else get_stuff["tokencount"]
    if random.random() < self.unpathiness / math.log( logthis ):
      if self.debug:
        print("backing off to bigrams, aka smoothing.")
      get_stuff = self.next_word_bigrams(word_back)
    elif not get_stuff :
      if self.debug:
        print("backing off to bigrams, since trigrams returned nothing")
      get_stuff = self.next_word_bigrams(word_back)
    return get_stuff

  def get_next_word(self, word_back, word_two_back):
    #returns the next word based on the word_back and word_two_back
    #  dumb wrapper around next_word_bigrams, !!Trigrams functions.
    #  i.e. doesn't do any parsing or anything.
    get_stuff = self.next_word_trigrams(word_back, word_two_back)
    if not get_stuff:
      if self.debug:
        print("backing off to bigrams, since trigrams returned nothing")
      get_stuff = self.next_word_bigrams(word_back)
    next_word_choices = get_stuff["data"]

    next_word_choices.sort()
    next_word_choices.reverse()
    tokencount = get_stuff["tokencount"]

    next_word = None
    myRand = random.randint(0, tokencount)  #TODO, double check output here.
    if self.debug:
      print(next_word_choices)
      print("rand: " + str(myRand) + ", count: " + str(tokencount) + ", unpathiness: "+ str(self.unpathiness * 100))

    most_recent_word = None
    for index, valword in enumerate(next_word_choices):
      val, word = valword
      if (myRand == val):
        next_word = word
        break
      elif (myRand > val):
        next_word = most_recent_word 
        break     
      elif index == len(next_word_choices) - 1: #if its the last one in the list
        next_word = word
        break
      most_recent_word = word
    return next_word

  def get_phrase (self, **kwargs):
    #defaults
    self.unpathiness = kwargs.get("unpathiness", 0.0)
    maxLen = kwargs.get("maxLen", 30)  # if you set maxLen to 0, there is no maxLen
    word_two_back = kwargs.get("word_two_back", "")
    word_back = kwargs.get("word_back", "")
    self.debug = kwargs.get("debug", False)
    useShallowParsing = kwargs.get("veryShallowParse", False)
    only_parseable_sentences = kwargs.get("guaranteeParse", False)  #should we return only parse-able sentences?
    similar_words = kwargs.get("similar_words", None)

    if self.debug and useShallowParsing:
      print("going to use very shallow parsing")

    so_far = [word_two_back, word_back]
    endOfSentence = False

    while 1:
      next_word = self.get_next_word(word_back, word_two_back)
      if next_word:
        # conditions under which we reject a word and go back to picking another one.
        #TODO: rewrite topics and very-shallow-parsing to each return a "how much we want/don't-want this word", to be run over a handful of words.
        if useShallowParsing and not self.check_verbs_and_complementizers(so_far, next_word):
          if self.debug: 
            print("trying to resolve verb-complementizer imbalance, rejecting \"" + next_word + "\"" )
        elif False: #if the word is off topic
          #given a topic, 
          #check if an "on topic" word could come next -- with 10% chance, choose it.     
          pass     
        else:
          so_far.append(next_word)
          if self.debug: 
            print(" ".join(so_far))
          word_two_back = word_back
          word_back = next_word
          if next_word == "" or (maxLen != 0 and len(so_far) >= maxLen):
            break 
      """
      candidate_next_words = []
      for i in range(10):
        random_factor = .5
        candidate_next_words.append([self.get_next_word(word_back, word_two_back), random.random() * random_factor])
        for word in candidate_next_words:
          #adjust scores based on topicality and veryShallowParse results.
        #pick the highest ranked one
      """
      else:
        break
    sentence = " ".join(so_far).strip()

    if not only_parseable_sentences:
      return sentence
    else:
      raise NotImplementedError
      """ #TODO
      require 'linkparser'
      sentence = so_far.join(" ").strip()
      linkparser = LinkParser::Dictionary.new
      result = linkparser.parse(sentence)
      if result.linkages != []
        return sentence
      else
        print("ehhhhh, sentence didn't parse, trying again!" if debug)
        return get_phrase(opts) #if the sentence doesn't parse, throw it out and start again.
      """

  def get_paragraph(self, length = 10, **kwargs):
    paragraph = []
    opts = kwargs
    if "topic" in kwargs:
      print "building topic similarity engine..."
      import TopicSimilarity
      if not self.topic_similarity:
        self.topic_similarity = TopicSimilarity.TopicSimilarity(glob = ["/home/merrillj/scotuslm/opinions", "*", "*", "*"])
      similar_words = self.topic_similarity.similar_to(kwargs["topic"], max=20)
      opts["similar_words"] = similar_words
    for i in range(length):
      paragraph.append(self.get_phrase(**opts))
    return " ".join(paragraph)

myLM = LanguageModel(["/home/merrillj/scotuslm/opinions", "*", "*", "*"], lambda filename: filename == "SCALIA.txt" )
opts = dict({"debug" : True, "veryShallowParse" : True, "maxLen" : 50})
print(myLM.get_phrase( opts ))
