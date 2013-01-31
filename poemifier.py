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
  #TODO: be recursive, so that if an unrhyming line is chosen, the whole poem isn't lost.
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
    self.rhyme_checker.debug = True
    self.syllabizer = Syllabizer()

  def try_line(self, line):
    #TODO: reorganize the finished output to maximize topicality between adjacent lines.
    for index, poem_line in enumerate(self.poem):
      if poem_line or line in self.poem:
        continue #don't put something into a line that already has something in it.
      if self.validate_line(index, line):
        if self.debug:
          print("Filled line " + str(index) + " with " + line)
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
    valid = True
    valid = valid and self.validate_syllables(line, syllable_counts[index])
    valid = valid and self.validate_rhyme(index, line)

    #only do this if the number of syllables in the line is equal to this line plus next line's syllable counts.

    if not valid and (index < (len(self.poem)-1)): 
      line_syllable_counts = map(lambda x: self.syllabizer.syllabize(x), line.split(" "))
      line_syllable_counts_need_to_be = [0,0]
      """
      if isinstance(syllable_counts[index], int):
        line_syllable_counts_need_to_be[0] += syllable_counts[index]
        line_syllable_counts_need_to_be[1] += syllable_counts[index]
      else:
        line_syllable_counts_need_to_be[0] += syllable_counts[index][0]
        line_syllable_counts_need_to_be[1] += syllable_counts[index][1]
      if isinstance(syllable_counts[index + 1], int):
        line_syllable_counts_need_to_be[0] += syllable_counts[index + 1]
        line_syllable_counts_need_to_be[1] += syllable_counts[index + 1]
      else:
        line_syllable_counts_need_to_be[0] += syllable_counts[index + 1][0]
        line_syllable_counts_need_to_be[1] += syllable_counts[index + 1][1]

      possible_to_split = line_syllable_counts_need_to_be[0] <= sum(line_syllable_counts) and line_syllable_counts_need_to_be[1] >= line_syllable_counts
      """
      possible_to_split = True
      if possible_to_split:
      #              #if not last line
        split_line = self.split_line_at_syllable_count(line, syllable_counts[index]) #loop over these possibilities
        #TODO: refactor, this is suuuuuuuuper ugly.
        if split_line and self.validate_line(index, split_line[0]) and self.validate_line(index+1, split_line[1]):
          self.poem[index] = split_line[0]
          self.poem[index+1] = split_line[1]
          return False
    return valid

  def split_line_at_syllable_count(self, line, syllable_count ):
    """Returns a line split at the given number of syllables. False if split is inside a word.

    #TODO: Should this return a list of possible splits? Yes.
    E.g. for sentence "a man a plan" and range 1,3, 
    Should this return [["a", "man a plan"], ["a man", "a plan"], ["a man a", "plan"]]?

    >>> p = Poemifier("haiku")
    >>> p.split_line_at_syllable_count("There once was banana man from the beach", 4)
    False
    >>> p.split_line_at_syllable_count("There once was a man from the beach", 4)
    ['There once was a', 'man from the beach']
    >>> p.split_line_at_syllable_count("There once was a man from the beach banana", 4)
    ['There once was a', 'man from the beach banana']
    >>> p.split_line_at_syllable_count("There once was banana man from the beach banana", (5,7))
    ['There once was banana', 'man from the beach banana']
    """
    split_line = line.strip().split(" ")

    if "" in split_line:
      return False
    if isinstance(syllable_count, int):
      if syllable_count == 0:
        return ["", line]
      elif syllable_count > 0:
        word = split_line[0]
        this_word_syllables = self.syllabizer.syllabize(word)
        next_return =  self.split_line_at_syllable_count(" ".join(split_line[1:]), syllable_count - this_word_syllables)
        if next_return:
          next_return[0] = " ".join([word] + filter(lambda x: x != "", next_return[0].split(" ")))
          return next_return
        else:
          return False
      else:
        return False
    elif isinstance(syllable_count, tuple):
      if syllable_count[0] == 0 or syllable_count[0] < 0 and syllable_count[1] >= 0:
        return ["", line]
      elif syllable_count[0] > 0:
        word = split_line[0]
        this_word_syllables = self.syllabizer.syllabize(word)
        next_syllable_count = (syllable_count[0] - this_word_syllables, syllable_count[1] - this_word_syllables)
        next_return =  self.split_line_at_syllable_count(" ".join(split_line[1:]), next_syllable_count)
        if next_return:
          next_return[0] = " ".join([word] + filter(lambda x: x != "", next_return[0].split(" ")))
          return next_return
        else:
          return False
      else:
        return False

  def validate_rhyme(self, index, line):
    """True if this line fits in the rhyme scheme where it is."""
    temp_poem = list(self.poem) #"copy" the list
    temp_poem[index] = line

    last_word = line.split(" ")[-1]
    last_word.strip(".,?!:;\" ")
    #does it fit where it is.
    rhyme_symbol = self.format["rhyme_scheme"][index]
    lines_to_compare_to = [temp_poem[i] for i, symbol in enumerate(self.format["rhyme_scheme"]) if symbol == rhyme_symbol and temp_poem[i] and i != index]
    if not lines_to_compare_to:
      return True
    words_to_compare_to = map(lambda x: x.split(" ")[-1], lines_to_compare_to )
    return True in map(lambda x: self.rhyme_checker.rhymes_with(last_word, x), words_to_compare_to)

  def validate_syllables(self, line, syllable_count):
    """True if line has the number of syllables specified in syllable_count."""
    syllable_count_on_this_line = 0
    split_line = line.split(" ")

    #exclude lines with abbreviations
    if True in map(lambda x: len(x) == 1 and x not in ["a", "A", "I"], split_line):
      return False

    for dirty_word in split_line:
      word = dirty_word.strip(",.:?!")
      syllable_count_on_this_line += self.syllabizer.syllabize(word)
    if self.debug: #leads to huge amounts of output
      print line + ": " + str(syllable_count_on_this_line)
    if isinstance(syllable_count, int):
      return syllable_count_on_this_line == syllable_count
    elif isinstance(syllable_count, tuple):
      return syllable_count_on_this_line >= syllable_count[0] and syllable_count_on_this_line <= syllable_count[1]

  def get_poem(self):
    if None in self.poem:
      print self.poem
      raise ShitsFuckedException, "No poem could be generated!"
    else:
      return "\n".join(self.poem)

def _test():
  import doctest
  doctest.testmod()

#TODO: command line file argument (e.g. find a haiku in this document)
if __name__ == "__main__":
  import re
  lists_of_lines = map(lambda x: x.split(","), open("./opinions/11txt/National Federation of Independent Business v. Sebelius/SCALIA.txt").read().split("\n"))
  lines = [line for line_list in lists_of_lines for line in line_list]
  
  #lines = ["camping is in tents", "my subconscience tries", "between those times I slept none"]
  lines = ["one two three four five six", "a bee see dee eff licks",  
  "This is a line that is twenty long and here is ten more ending in thong", "Jeremy Bee Merrill plays ping pong",
  ]
  p = Poemifier("limerick")
  p.debug = False
  for line in lines:
    line = re.sub("[^A-Za-z ']", "", line)
    p.try_line(line)
  print ""
  print p.get_poem()


#TODO:
# be a little more recursive, but not all the way, about pairing lines. maybe one loop per rhyming group? (i.e. for "a"s)
# Find shorter lines to consider, e.g. breaking sentences into pieces