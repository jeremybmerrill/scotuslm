
import random
import nltk

import LanguageModel

class SentenceGenerator:
  """ Generates sentences. """
  def __init__(self):
    self.lm = LanguageModel.LanguageModel(["/home/merrillj/scotuslm/opinions", "*", "*", "*"], lambda filename: filename == "SCALIA.txt" )
    self.topic_similarity = None

    #if a word is in the wordlist, don't capitalize it.
    self.wordlist = set()
    for word in open("/usr/share/dict/words"):
      self.wordlist.add(word)

    #complementizer_list = ['AZ', 'TH', 'TS', ]
    #verb_list = ['S']
    self.complementizer_list = ["WP", "WPS," "WDT", "WRB"] #also, "in", dealt with separately
    self.actual_IN_complementizers = ["that", "although", "after", "although", "if", "unless", "as", "inasmuch", "until", "when", "whenever", "since", "while", "because", "before", "though"]
    self.verb_list = ["VB", "VBD", "VBP", "VBZ",] #, "vbg", "vbn" #participles, which I don't really want.
    #complementizer_count = 0
    #verb_count = 0
    self.makes_things_worse_adjustment = 3 #if the selected part of speech would make things worse, multiply this by probability to make it harder to add the selected word
    self.debug = False
    self.RANDOM_WEIGHT = 1
    self.TOPICALITY_WEIGHT = 1
    self.VERY_SHALLOW_PARSE_WEIGHT = 1


  def get_next_word(self, word_back, word_two_back):
    #returns the next word based on the word_back and word_two_back
    #  dumb wrapper around next_word_bigrams, next_word_trigrams functions.
    #  i.e. doesn't do any parsing or anything.
    get_stuff = self.lm.next_word_trigrams(word_back, word_two_back)
    if not get_stuff:
      if self.debug:
        print("backing off to bigrams, since trigrams returned nothing")
      get_stuff = self.lm.next_word_bigrams(word_back)
    next_word_choices = get_stuff["data"]

    next_word_choices.sort()
    next_word_choices.reverse()
    tokencount = get_stuff["tokencount"]

    next_word = None
    myRand = random.randint(0, tokencount)  #TODO, double check output here.
    # if self.debug:
    #   print(next_word_choices)
    #   print("rand: " + str(myRand) + ", count: " + str(tokencount) + ", unpathiness: "+ str(self.unpathiness * 100))

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

  def very_shallow_parse_score(self, sentence_so_far, next_word):
    """ return a value representing whether it will make the sentence more or less coherent via "very shallow parsing"

    Return: integer 0 < x < 1. 1 represents that the word makes the much sentence more coherent, 0 that it makes it much worse.

    if the sentence doesn't have N + 1 verbs for every N complementizers, 
      then, return a low score if the next word doesn't resolve the imbalance.
      and return an even lower score if the next word increases the imbalance
      in hopes of prioritizing words that will cause the sentence to be more
      coherent.
    """
    tagged_sentence_so_far = nltk.pos_tag(nltk.word_tokenize( " ".join(sentence_so_far) )) 
    tagged_sentence_with_next_word =  nltk.pos_tag(nltk.word_tokenize( " ".join(sentence_so_far + [next_word]) ))
    next_word_POS = tagged_sentence_with_next_word[-1][1] #the next word's tag is the second element of the final element of the list of words in the sentence.
    print(str(tagged_sentence_with_next_word ))
    #TODO: what if the sentence didn't get tagged successfully?
    verb_count = len([pos for word, pos in tagged_sentence_so_far if pos in self.verb_list])
    complementizer_count = len([pos for word, pos in tagged_sentence_so_far if pos in self.complementizer_list]) and word in self.actual_IN_complementizers #TODO: some complementizers are BS.

    RESOLVES_IMBALANCE = 1.0
    FURTHERS_IMBALANCE = 0.0
    BALANCE = 1.0
    IMBALANCE_NOT_A_VERB_OR_COMPLEMENTIZER = 0.7

    if self.debug:
      try:
        print(". ".join(map(unicode, [next_word, verb_count, complementizer_count, next_word_POS])).encode("utf-8"))
      except UnicodeEncodeError:
        print "eh, tried to print, but error. :("

    if verb_count == 0 and complementizer_count == 0:
      return BALANCE #anything's fine, whatever. #TODO: constantize these magic-number values.

    #Complementizer
    if next_word_POS in self.complementizer_list and next_word in self.actual_IN_complementizers:
      if verb_count == complementizer_count + 1: #balance
        return BALANCE
      elif verb_count > complementizer_count + 1: #imbalance -- complementizer needed
        #accept, this fixes the imbalance!
        return RESOLVES_IMBALANCE
      else:  #verb needed, this word would increase the imbalance
        return FURTHERS_IMBALANCE
    #Verb
    elif next_word_POS in self.verb_list:
      if verb_count == complementizer_count: #balance, feel free to take me out of balance verbly. :)
        return BALANCE
      elif verb_count < complementizer_count:  #imbalance -- verb needed
        #accept, this fixes the imbalance!
        return RESOLVES_IMBALANCE
      else: #complementizer needed, this word would increase the imbalance
        return FURTHERS_IMBALANCE
    #Something else
    else: #if it's some other word (e.g. a noun)
      if verb_count == complementizer_count + 1: #balance
        return BALANCE
      else: #imbalance, this word doesn't help or make things worse.
        return IMBALANCE_NOT_A_VERB_OR_COMPLEMENTIZER


  def get_phrase (self, **kwargs):
    #TODO: pass unpathiness through to LanguageModel.
    max_sentence_length = kwargs.get("max_sentence_length", 30)  # if you set max_sentence_length to 0, there is no max_sentence_length
    word_two_back = kwargs.get("word_two_back", "")
    word_back = kwargs.get("word_back", "")
    self.debug = kwargs.get("debug", False)
    use_topic = kwargs.get("topic", False)
    use_very_shallow_parsing = kwargs.get("veryShallowParse", False) 
    only_parseable_sentences = kwargs.get("guaranteeParse", False)  #should we return only parse-able sentences? NotImplementedYet

    if self.debug and use_very_shallow_parsing:
      print("going to use very shallow parsing")

    if "topic" in kwargs:
      print "building topic similarity engine..."
      import TopicSimilarity
      if not self.topic_similarity:
        self.topic_similarity = TopicSimilarity.TopicSimilarity(glob = ["/home/merrillj/scotuslm/opinions", "*", "*", "*"])

    so_far = [word_two_back, word_back]
    endOfSentence = False

    while 1:
      candidate_next_words = {}
      for i in range(10):
        #N.B.: The absolute values of the weights don't matter, what matters is the ratio between the three.
        random_weight = kwargs.get("random_weight", self.RANDOM_WEIGHT)
        topicality_weight = kwargs.get("topicality_weight", self.TOPICALITY_WEIGHT)
        very_shallow_parse_weight = kwargs.get("very_shallow_parse_weight", self.VERY_SHALLOW_PARSE_WEIGHT)
        #TODO: make these into settleable parameters.

        word = self.get_next_word(word_back, word_two_back)

        word_score = random.random() * random_weight
        if word:
          if use_topic and self.topic_similarity:
            word_score += ( self.topic_similarity.similar_to(kwargs["topic"], word) ) * topicality_weight
            #TODO: look at the "children" of _word_, if they include high-topicality words, favor _word_; 
          if use_very_shallow_parsing:
            word_score += self.very_shallow_parse_score(so_far, word) * very_shallow_parse_weight
        candidate_next_words[word] = word_score
        #TODO: This weights (unnecessarily) towards continuing a sntence, rather than ending it. Fix this.

      next_word = ""
      max_word_score = 0.0
      for word, word_score in candidate_next_words.items():
        if word_score > max_word_score:
          print " ".join([u'"' + unicode(word) + u'"', "superseding", u'"' + unicode(next_word) + u'"', u"with a score of", str(word_score)]).encode('utf-8')
          next_word = word
          max_word_score = word_score
      if not next_word:
        next_word = ""
      so_far.append(next_word)
      if self.debug: 
        print so_far
        print(" ".join(so_far))
      word_two_back = word_back
      word_back = next_word
      if next_word == "" or (max_sentence_length != 0 and len(so_far) >= max_sentence_length):
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

  def get_paragraph(self, **kwargs):
    paragraph = []
    length = kwargs.get("paragraph_length", 10)
    if "paragraph_length" in kwargs:
      del kwargs["paragraph_length"]

    opts = kwargs

    for i in range(length):
      next_sentence = self.get_phrase(**opts)
      if next_sentence:
        #cleanup
        if next_sentence[-1] == ".":
          next_sentence = next_sentence[0:-1]
        if next_sentence[-1] == " ":
          next_sentence = next_sentence[0:-1]
        paragraph.append(next_sentence.capitalize())
    return u".\n ".join(paragraph)

  def stylize_sentence(self, sent):
    split_sent = sent.split(" ")
    for word, index in enumerate(split_sent):
      word = word.strip()
      if word not in self.wordlist:
        split_sent[index] = word.capitalize()
    sent = (" ".join(split_sent)).strip()
    if sent[-1] not in [".", "?", "!"]:
      sent = sent + "."
    return sent


  def stylize_paragraph(self, paragraph):
    """ TK """
    return paragraph

  def do_stuff(self):
    opts = dict({"debug" : True, "veryShallowParse" : True, "max_sentence_length" : 50, "paragraph_length" : 10, #'topic': 'congress',
       'random_weight': 1, 'topicality_weight':3, 'very_shallow_parse_weight':3})
    print(self.get_phrase( **opts )).encode("utf-8")


if __name__ == "__main__":
  s = SentenceGenerator()
  s.do_stuff()