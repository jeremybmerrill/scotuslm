from syllabizer import Syllabizer
from rhymechecker import RhymeChecker


##



## fix the TODO! things


##



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
    #self.poem_validator = PoemValidator()
    if isinstance(format_name, str) and format_name not in self.formats:
      raise TypeError, "Unknown format specified."
    elif isinstance(format_name, str):
      self.format_name = format_name
    elif isinstance(format_name, dict):
      format = format_name
      format_name = "custom"
      self.format_name = format_name
      #poem_validator.add_format("custom", format)
    self.format = self.formats[format_name]
    if "lines_needed" in self.format:
      self.lines_needed = format["lines_needed"]
    else:
      self.lines_needed = max(len(self.format["syllable_counts"]), len(self.format["rhyme_scheme"])) #TODO: specify a lines_needed param in format.
    self.poems = [ [None] * self.lines_needed ] 
    self.rhyme_checker = RhymeChecker()
    self.rhyme_checker.debug = False
    self.syllabizer = Syllabizer()

  def try_line(self, line):
    #TODO: reorganize the finished output to maximize topicality between adjacent lines.
    if len(self.poems) % 10 == 0:
      print len(self.poems)
    if len(self.poems) % 100 == 0:
      #print sorted(self.poems, key=lambda x: x.count(None))[0:10]
      pass
    for poem_index, temp_poem in enumerate(self.poems):
      for line_index, poem_line in enumerate(temp_poem):
        if poem_line or line in temp_poem:
          continue #don't duplicate a line that's already in the poem
        if self.validate_line(temp_poem, line, line_index):
          if self.debug:
            print("Filled line " + str(line_index) + " with \"" + line + "\"")
          self.poems[poem_index][line_index] = line
          #early return: I don't think this saves much time, so I'm cutting it out for now.
          if len(   filter( lambda x: len(  filter(lambda y: y == None, x)) == len(x), self.poems)   ) == 0:
            self.poems.append([None] * self.lines_needed)
          return False in map(lambda x: None in x, self.poems) # return false until the poem is done. 

    #else, try splitting the line.
    #only do this if the number of syllables in the line is equal to this line plus next line's syllable counts.

      #if we've gotten here, the line doesn't fit by itself.
        if (line_index < (len(temp_poem)-1)): #if we're not trying to fill the last line of the poem 
          line_syllable_counts = map(lambda x: self.syllabizer.syllabize(x), line.split(" "))
          line_syllable_counts_need_to_be = [0,0]
          if isinstance(self.format["syllable_counts"][line_index], int):
            line_syllable_counts_need_to_be[0] += self.format["syllable_counts"][line_index]
            line_syllable_counts_need_to_be[1] += self.format["syllable_counts"][line_index]
          else:
            line_syllable_counts_need_to_be[0] += self.format["syllable_counts"][line_index][0]
            line_syllable_counts_need_to_be[1] += self.format["syllable_counts"][line_index][1]
          if isinstance(self.format["syllable_counts"][line_index + 1], int):
            line_syllable_counts_need_to_be[0] += self.format["syllable_counts"][line_index + 1]
            line_syllable_counts_need_to_be[1] += self.format["syllable_counts"][line_index + 1]
          else:
            line_syllable_counts_need_to_be[0] += self.format["syllable_counts"][line_index + 1][0]
            line_syllable_counts_need_to_be[1] += self.format["syllable_counts"][line_index + 1][1]

          possible_to_split = line_syllable_counts_need_to_be[0] <= sum(line_syllable_counts) and line_syllable_counts_need_to_be[1] >= sum(line_syllable_counts)
          if possible_to_split:
            split_line = self.split_line_at_syllable_count(line, self.format["syllable_counts"][line_index]) 
            if split_line:
              temp_temp_poem = list(temp_poem)
              has_failed_yet = False
              for temp_line_index, temp_line in enumerate(split_line):
                if self.validate_line(temp_temp_poem, temp_line, line_index + temp_line_index):
                  temp_temp_poem[temp_line_index] = temp_line
                else:
                  has_failed_yet = True
              if not has_failed_yet:
                def assign_to_poem(i_and_line):
                  self.poems[poem_index][line_index + i_and_line[0]] = i_and_line[1]
                map(assign_to_poem , enumerate(split_line))
    if len(   filter( lambda x: len(  filter(lambda y: y == None, x)) == len(x), self.poems)   ) == 0:
      self.poems.append([None] * self.lines_needed)
    return False in map(lambda x: None in x, self.poems) # return false until the poem is done. 

  def validate_line(self, poem, line, index):
    """ Return line if given line fits into the format positioned at the given index, false otherwise"""
    #TODO! now: make this return n lines that go into the poem at index, if they do fit.
    #e.g. [line1, line2] is line was split and fits, as split, into two lines.
    #assume a valid format.
    syllable_counts = self.format["syllable_counts"] * (self.lines_needed / len(self.format["syllable_counts"]))
    rhyme_scheme = self.format["rhyme_scheme"] * (self.lines_needed / len(self.format["rhyme_scheme"]))
    #TODO: abstract away formats (like above, make a dict of validator functions
    # and call those iff a given format restrictor is in the format dict)
    valid = True
    valid = valid and self.validate_syllables(line, syllable_counts[index])
    valid = valid and self.validate_rhyme(poem, line, index)
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

  def validate_rhyme(self, poem, line, index):
    """True if this line fits in the rhyme scheme where it is."""
    temp_poem = list(poem) #"copy" the list
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

  def has_poem(self):
    return True in map(lambda x: None not in x, self.poems)

  def get_poem(self):
    self.rhyme_checker.dump_rhyme_cache()
    if self.has_poem():
      return "\n".join( filter(lambda x: None not in x, self.poems)[0] )
    else:
      self.poems.sort(key= lambda x: x.count(None)) #[0:10]
      print self.poems[0:10]
      raise ShitsFuckedException, "No poem could be generated!"

def _test():
  import doctest
  doctest.testmod()

class ShitsFuckedException(Exception):
  pass


#TODO: command line file argument (e.g. find a haiku in this document)
if __name__ == "__main__":
  import re
  lists_of_lines = map(lambda x: x.split(","), open("./opinions/11txt/National Federation of Independent Business v. Sebelius/SCALIA.txt").read().split("\n"))
  lines = [line for line_list in lists_of_lines for line in line_list]
  
  #lines = ["camping is in tents", "my subconscience tries", "between those times I slept none"]
  lines = ["many words in english rhyme with song", "one two three four five six", "a bee see dee word kicks",
  "This is a line that is twenty long and here are ten more ending in wrong", "Jeremy Bee Merrill plays ping pong",
  ]

  p = Poemifier("limerick")
  p.debug = False
  #TODO: make this a do... while (so we quit when we finish a poem)
  for line in lines:
    line = re.sub("[^A-Za-z ']", "", line)
    line = line.strip()
    if p.try_line(line):
      print "Done!"
      break
  print ""
  print p.get_poem()


#TODO: (eventually)
# be a little more recursive, but not all the way, about pairing lines. maybe one loop per rhyming group? (i.e. for "a"s)

#have an array of poems
#try each line in each poem.
#return all the way down when we finally have a real poem


"""
  #TODO! fix this: 
  lines = ["many words in english rhyme with song", "one two three four five six", "a bee see dee word kicks",
  "This is a line that is twenty long and here are ten more ending in wrong", "Jeremy Bee Merrill plays ping pong",
  ]
  the ordering is wrong. if the first line is moved to the end, it works.
  Find a recursive-y way to get the right result here.
"""