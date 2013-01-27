from syllabizer import Syllabizer
from rhymechecker import RhymeChecker

class PoemValidator:
  """ Validates whether a given poem fits a given format.

  e.g. a haiku is an unrhyming poem of three lines of 5,7,5 syllables.
  This class includes methods to define those formats.
  """
  #TODO: stress: http://www.speech.cs.cmu.edu/cgi-bin/cmudict
  def __init__(self):
    self.formats = {
        #TODO: add lines_needed element
        "haiku" : {"syllable_counts" : [5,7,5],
                   "rhyme_scheme" : "abc"},
        "limerick" : {"syllable_counts" : [(9,11),(9, 11),6,6,(9, 11)], 
                       "rhyme_scheme" : "aabba"},
        "sonnet" : {"syllable_counts" : [10],
                      "rhyme_scheme" :  "ababcdcdefefgg"}
      }
    self.debug = False
    self.syllabizer = Syllabizer()
    self.rhyme_checker = RhymeChecker()
    #pairs of words that rhyme but aren't shown as rhymes in rhymebrain.
    # k,v has the same effect as v,k
    #TODO: allow extras to be specified as k,v and transform that to k, [{"word" : v}]

  def clean_poem(self, poem):
    """ Transform a string into a list of (non-empty) lines."""
    return filter(lambda x: x, map(lambda x: x.strip(), poem.split("\n")))

  def add_format(self, format_name, format):
    #TODO validate format (e.g. ensuring that for the shortest of lines_needed, syllable_counts and rhyme_scheme,
    # all the others are a multiple of that length.)
    #TODO: normalize format -- ensure that syllable_counts and rhyme_scheme are both there, as long as_lines_needed
    self.formats[format_name] = format

  def validate(self, format_name, raw_poem):
    """
    For a given poem (a newline-separated string), return True if it fits the given format

    Formats are specified by name, but can be added to the validator via add_format()

    >>> p = PoemValidator()
    >>> haiku = "Haikus are easy\\nBut sometimes they don't make sense\\nrefrigerator"
    >>> p.validate("haiku", haiku)
    True
    >>> limerick = "The lim\'rick packs laughs anatomical\\nIn space that is quite economical\\nBut the good ones I've seen\\nWell, so seldom are clean\\nAnd the clean ones so seldom are comical"
    >>> p.validate("limerick", limerick)
    True
    """

    validators = {
      "syllable_counts": self.validate_syllables,
      "rhyme_scheme" : self.validate_rhyme
    }
    poem = self.clean_poem(raw_poem)
    poem = map(lambda x: x.strip(), poem)
    #TODO: return validation info on every attribute, not just first to fail.
    validate_okay = [True] * len(self.formats[format_name])
    for index, format_stuff in enumerate(self.formats[format_name].items()):
      format_item_name, format_item = format_stuff
      if not validators[format_item_name](format_item, poem):
        if self.debug: 
          print(format_item_name + " didn't validate!")
        validate_okay[index] = False
    if False not in validate_okay:
      if self.debug: 
        print "Go show 'em your poem. It's valid!"
    else:
      if self.debug: 
        print "Uh oh. Your poem's either invalid or transgressively postmodern."
    return False not in validate_okay

  def validate_syllables(self, syllable_counts, poem):
    """For a given list of syllable counts, find if the given poem fits it"""
    #normalize the length of the syllable_counts array to one count per line.
    if len(syllable_counts) != len(poem):
      if float(len(poem)) % len(syllable_counts) != 0.0:
        raise ShitsFuckedException
      else:
        syllable_counts = syllable_counts * (len(poem) / len(syllable_counts))

    if len(syllable_counts) != len(poem):
      raise ShitsFuckedException, "Your poem length " + str(len(poem)) + " isn't a multiple of specified syllable length!"

    syllables_okay = [False] * len(syllable_counts)
    for index, line_and_syllable_count in enumerate(zip(poem, syllable_counts)):
      line, syllable_count = line_and_syllable_count
      syllable_count_on_this_line = 0
      for dirty_word in line.split(" "):
        word = dirty_word.strip(",.:?!")
        syllable_count_on_this_line += self.syllabizer.syllabize(word)
      if self.debug: 
        print line + ": " + str(syllable_count_on_this_line)
      if isinstance(syllable_count, int):
        if syllable_count_on_this_line != syllable_count:
          if self.debug: 
            print "Line " + str(index + 1) + " has the wrong number of syllables! Should be " + str(syllable_count)
          syllables_okay[index] = False
        else:
          syllables_okay[index] = True
      elif isinstance(syllable_count, tuple):
        if not syllable_count_on_this_line >= syllable_count[0] and syllable_count_on_this_line <= syllable_count[1]:
          if self.debug: 
            print "Line " + str(index + 1) + " has the wrong number of syllables! Should be " + str(syllable_count)
          syllables_okay[index] = False
        else:
          syllables_okay[index] = True
      else: #TODO: move format validation out of app logic. (assume format is valid.)
        raise TypeError, "Each element of syllable_count must be an int or a tuple!"

    return False not in syllables_okay

  def validate_rhyme(self, rhyme_scheme, poem):
    #normalize the length of the rhyme scheme array to one rhyme letter per line.
    if len(rhyme_scheme) != len(poem):
      if float(len(poem)) % len(rhyme_scheme) != 0.0:
        raise ShitsFuckedException
      else:
        rhyme_scheme = rhyme_scheme * (len(poem) / len(rhyme_scheme))

    rhyme_okay = [False] * len(rhyme_scheme)
    for index, line_symbol in enumerate(zip(poem,rhyme_scheme)):
      line, symbol = line_symbol
      #if line is first of its rhyme scheme symbol,there's nothing to compare to, so it's okay.
      if symbol not in rhyme_scheme[:index]:
        rhyme_okay[index] = True
        continue
      #if line isn't, check if it rhymes with any previous words with its rhyme scheme symbol
      dirty_last_word = line.split(" ")[-1]
      last_word = dirty_last_word #TODO: clean.
      indices_to_rhyme_with = [i for i, same_symbol in enumerate(rhyme_scheme[:index]) if same_symbol == symbol]
      needs_to_rhyme_with = [poem[inx].split(" ")[-1] for inx in indices_to_rhyme_with]
      #print str(index) + ": " + str(needs_to_rhyme_with)
      for word_to_rhyme_with in needs_to_rhyme_with:
        if rhyme_okay[index]:
          continue
        if self.rhyme_checker.rhymes_with(last_word, word_to_rhyme_with):
          rhyme_okay[index] = True
          if self.debug: 
            print "Does " + last_word + " rhyme with " + word_to_rhyme_with + "? " + "Yes!"
          continue
        if self.debug: 
          print "Does " + last_word + " rhyme with " + word_to_rhyme_with + "? " + "No?! Uh oh..."
        rhyme_okay[index] = False
      #print ""
    for index, okayness in enumerate(rhyme_okay):
      if not okayness:
        if self.debug: 
          print "Line " + str(index + 1) + " (\"" + poem[index] + "\") does not rhyme."
    return False not in rhyme_okay



class ShitsFuckedException(Exception):
  pass

class Poemifier:
  def __init__(self, format_name):
    """Specify the name of a known format or specify a fully-defined format."""
    #TODO specify a name (req) and optionally the format specification
    self.formats = {
        "haiku" : {"syllable_counts" : [5,7,5],
                   "rhyme_scheme" : "abc"},
        "limerick" : {"syllable_counts" : [(9,11),(9, 11),6,6,(9, 11)], 
                       "rhyme_scheme" : "aabba"},
        "sonnet" : {"syllable_counts" : [10],
                      "rhyme_scheme" :  "ababcdcdefefgg"}
      }
    self.debug = False
    self.poem_complete = False
    self.poem_validator = PoemValidator()
    if isinstance(format_name, str) and format_name not in self.formats:
      raise TypeError, "Unknown format specified."
    elif isinstance(format_name, str):
      self.format_name = format_name
    elif isinstance(format_name, dict):
      format = format_name
      format_name = "custom"
      self.format_name = format_name
      poem_validator.add_format("custom", format)
    self.format = self.formats[format_name]
    if "lines_needed" in self.format:
      self.lines_needed = format["lines_needed"]
    else:
      self.lines_needed = max(len(self.format["syllable_counts"]), len(self.format["rhyme_scheme"])) #TODO: specify a lines_needed param in format.
    self.poem = [None] * self.lines_needed
    self.rhyme_checker = RhymeChecker()
    self.syllabizer = Syllabizer()

  def try_line(self, line):
    #TODO: reorganize the finished output to maximize topicality between adjacent lines.
    for index, poem_line in enumerate(self.poem):
      if poem_line or line in self.poem:
        continue #don't put something into a line that already has something in it.
      if self.validate_line(index, line):
        if self.debug:
          print "Filled line " + str(index)
        self.poem[index] = line
        break
    return None not in self.poem # return false until the poem is done. 

  def validate_line(self, index, line):
    """ True if given line fits into the format positioned at the given index."""
    #assume a valid format.
    syllable_counts = self.format["syllable_counts"] * (self.lines_needed / len(self.format["syllable_counts"]))
    rhyme_scheme = self.format["rhyme_scheme"] * (self.lines_needed / len(self.format["rhyme_scheme"]))
    #TODO: abstract away formats (like above, make a dict of validator functions
    # and call those iff a given format restrictor is in the format dict)
    status = True
    status = status and self.validate_syllables(line, syllable_counts[index])
    status = status and self.validate_rhyme(index, line)
    return status 

  def validate_rhyme(self, index, line):
    """True if this line fits in the rhyme scheme where it is."""
    temp_poem = self.poem 
    temp_poem[index] = line

    last_word = line.split(" ")[-1]
    last_word.strip(".,?!:;\" ")
    #does it fit where it is.
    rhyme_symbol = self.format["rhyme_scheme"][index]
    lines_to_compare_to = [temp_poem[i] for i, symbol in enumerate(self.format["rhyme_scheme"]) if symbol == rhyme_symbol and temp_poem[i]]
    words_to_compare_to = map(lambda x: x.split(" ")[-1], lines_to_compare_to )
    return True in map(lambda x: self.rhyme_checker.rhymes_with(last_word, x), words_to_compare_to)

  def validate_syllables(self, line, syllable_count):
    """True if line has the number of syllables specified in syllable_count."""
    syllable_count_on_this_line = 0
    for dirty_word in line.split(" "):
      word = dirty_word.strip(",.:?!")
      syllable_count_on_this_line += self.syllabizer.syllabize(word)
    #if self.debug: #leads to huge amounts of output
    #  print line + ": " + str(syllable_count_on_this_line)
    if isinstance(syllable_count, int):
      return syllable_count_on_this_line == syllable_count
    elif isinstance(syllable_count, tuple):
      return syllable_count_on_this_line >= syllable_count[0] and syllable_count_on_this_line <= syllable_count[1]

  def get_poem(self):
    if None in self.poem:
      raise ShitsFuckedException, "No poem could be generated!"
    else:
      return "\n".join(self.poem)


  # p = PoemGenerator("haiku")
  # for line in lines:
  #   p.try(line)

def _test():
  import doctest
  doctest.testmod()

#TODO: command line file argument (e.g. find a haiku in this document)
if __name__ == "__main__":
  import re
  lines = open("./opinions/11txt/National Federation of Independent Business v. Sebelius/SCALIA.txt").read().split("\n")
  p = Poemifier("limerick")
  p.debug = True
  for line in lines:
    line = re.sub("[^A-Za-z ']", "", line)
    p.try_line(line)
  print ""
  print p.get_poem()
