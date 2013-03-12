from rhymechecker import RhymeChecker
from random import random

"""
#TODO:
Architecture changes:
  1. Give poemifier the whole document. (Eventually: chunks of document, with reprocessing at each chunk.)
  2. Create two "hash" dicts, one for rhymes and one for syllable length.
    a. Each dict is of the form: hash_value -> [line1, line2, line3]
    b. each hash_value is computed by hash(line) where the syllable_hash function returns syllable length of the line and rhyme_hash returns the rime (i.e. nucleus + coda) of the final syllable of the line.
  3. Discard or ignore all syllable_hash_dict entries whose syllable counts are not in the format.
  3.5: Optionally, pair stuff, e.g. rhyming pairs or triplets (or n-lets where n is the greatest amount of rhyming lines needed in the format, e.g. 3 for a limerick, , but only 2 for a sonnet.) and, if necessary, of the right syllable length.
  3.75 From these pairs, assemble a poem.
  4. iterate over each line of the right syllable length to see if anything rhymes with it (i.e. has the same rhyme_hash value) and if so, insert into the poem. (with the same tricks to keep options open in self.poems)
"""

class Poemifier:
  def __init__(self, format_name, format=None):
    """Specify the name of a known format or specify a fully-defined format."""
    #TODO specify a name (req) and optionally the format specification
    self.formats = {
        "haiku" : {"syllable_structure" : [5,7,5],
                   "rhyme_scheme" : "abc"},
        "limerick" : {"syllable_structure" : [(9,11),(9, 11),6,6,(9, 11)], 
                       "rhyme_scheme" : "aabba"},
        "sonnet" : {"syllable_structure" : [10],
                      "rhyme_scheme" :  "ababcdcdefefgg"}
      }
    self.debug = False
    #self.poem_complete = False #dunno what this is.
    #self.poem_validator = PoemValidator()
    if not format:
      self.format_name = format_name
    else:
      self.format_name = format_name
      self.formats[format_name] = format #potentially temporarily overwriting a predefined format. That's okay.
    self.format = self._fill_out_format(self.formats[format_name])
    self.lines_needed = self.format["lines_needed"]

    #self.poems = [ [None] * self.lines_needed ] 

    self.rhyme_checker = RhymeChecker()
    self.rhyme_checker.debug = False

    #TODO abstract away hash types.
    self.rhyme_dict = {}
    self.syllable_count_dict = {}

  def _fill_out_format(self, format):
    if "lines_needed" not in format:
      format["lines_needed"] = max(len(format["syllable_structure"]), len(format["rhyme_scheme"]))
      lines_needed = format["lines_needed"]
    rhyme_scheme = format["rhyme_scheme"] * (lines_needed / len(format["rhyme_scheme"]))
    if len(format["syllable_structure"]) < lines_needed:
      multiple = float(lines_needed) / len(format["syllable_structure"])
      if multiple % 1.0 != 0.0:
        raise TypeError, "Invalid poem format :("
      format["syllable_structure"] = int(multiple) * format["syllable_structure"]
    if len(format["rhyme_scheme"]) < lines_needed:
      multiple = float(lines_needed) / len(format["rhyme_scheme"])
      if multiple % 1.0 != 0.0:
        raise TypeError, "Invalid poem format :("
      format["rhyme_scheme"] = int(multiple) * format["rhyme_scheme"]
    format["syllable_counts_needed"] = []
    for syllable_count_item in format["syllable_structure"]:
      if isinstance(syllable_count_item, int) and syllable_count_item not in format["syllable_counts_needed"]:
         format["syllable_counts_needed"].append(syllable_count_item)
      else:
        for num in range([line_index][0],[line_index][1]+1):
          if num not in format["syllable_counts_needed"]:
            format["syllable_counts_needed"].append(num)
    return format

  def _rime(self, line):
    #return this line's last word's rime to use as key to this value in the rhyme hash.
    #TODO integrate with rhymechecker's stress stuff to sometimes return penultimate syllable's rime + last syllable.
    return tuple(self.rhyme_checker.get_rime(line.split(" ")[-1]))

  def _syllable_count(self, line):
    #return this line's syllable count to use as key to this value in the syllable_count hash.
    return sum(map(self.rhyme_checker.count_syllables, line.split(" ")))

  def try_line(self, line):
    """ Add a line, then return True if, given that line, a poem can be created."""
    #TODO: add line to all hashes.
    self.add_line(line)
    #TODO: split line here.
    #TODO: do any intermediate processing (e.g. pairing rhyming lines)
    return self.get_poem() #False or a poem.

  def add_line(self, line):
    """
    Adds a line to the format hash dicts. Return False if the line cannot be used.
    """
    #TODO: abstract away format stuff
    # format_items = [[self._rime, self.rhyme_dict], [self._syllable_count, self.syllable_count_dict]]
    # for hashFunc, format_hash_dict in format_items:
    syll_count = self._syllable_count(line)
    if syll_count in self.format["syllable_counts_needed"]: #TODO: obviously, abstract this.
      rime = self._rime(line)
      if rime not in self.rhyme_dict:
        self.rhyme_dict[rime] = []
      self.rhyme_dict[rime].append(line)
      if syll_count not in self.syllable_count_dict:
        self.syllable_count_dict[syll_count] = []
      self.syllable_count_dict[syll_count].append(line)
      return True
    else:
      return False

  # def old_try_line(self, line):
  #   #TODO: reorganize the finished output to maximize topicality between adjacent lines.
  #   if self.debug:
  #     if len(self.poems) % 10 == 0:
  #       print len(self.poems)
  #     if len(self.poems) % 10 == 0:
  #       print self.poems.sort(key= lambda x: x.count(None))
  #   extra_poems = []
  #   for poem_index, temp_poem in enumerate(self.poems):
  #     for line_index, poem_line in enumerate(temp_poem):
  #       if poem_line or line in temp_poem:
  #         continue #don't duplicate a line that's already in the poem
  #       if self.validate_line(temp_poem, line, line_index):
  #         if self.debug:
  #           print("Filled line " + str(line_index) + " with \"" + line + "\"")
  #         if self.poems[poem_index] != ([None] * self.lines_needed):
  #           extra_poems.append(list(self.poems[poem_index])) #append in a copy of the same poem, without the new line
  #         self.poems[poem_index][line_index] = line
  #         #early return: I don't think this saves much time, so I'm cutting it out for now.
  #         # if len(   filter( lambda x: len(  filter(lambda y: y == None, x)) == len(x), self.poems)   ) == 0:
  #         #   self.poems.append([None] * self.lines_needed)
  #         # if len(extra_poems) > 0:
  #         #   print "Added: " + str(len(extra_poems))
  #         #   self.poems.extend(extra_poems)

  #         # #TODO: don't early return just because the line fits well.
  #         # return False in map(lambda x: None in x, self.poems) # return false until the poem is done. 

  #   #else, try splitting the line.
  #   #only do this if the number of syllables in the line is equal to this line plus next line's syllable counts.

  #     #if we've gotten here, the line doesn't fit by itself.
  #       if (line_index < (len(temp_poem)-1)): #if we're not trying to fill the last line of the poem 
  #         line_syllable_counts = map(lambda x: self.rhyme_checker.count_syllables(x), line.split(" "))
  #         line_syllable_counts_need_to_be = [0,0]
  #         if isinstance(self.format["syllable_structure"][line_index], int):
  #           line_syllable_counts_need_to_be[0] += self.format["syllable_structure"][line_index]
  #           line_syllable_counts_need_to_be[1] += self.format["syllable_structure"][line_index]
  #         else:
  #           line_syllable_counts_need_to_be[0] += self.format["syllable_structure"][line_index][0]
  #           line_syllable_counts_need_to_be[1] += self.format["syllable_structure"][line_index][1]
  #         if (line_index < (len(temp_poem)-2)):
  #           if isinstance(self.format["syllable_structure"][line_index + 1], int):
  #             line_syllable_counts_need_to_be[0] += self.format["syllable_structure"][line_index + 1]
  #             line_syllable_counts_need_to_be[1] += self.format["syllable_structure"][line_index + 1]
  #           else:
  #             line_syllable_counts_need_to_be[0] += self.format["syllable_structure"][line_index + 1][0]
  #             line_syllable_counts_need_to_be[1] += self.format["syllable_structure"][line_index + 1][1]

  #         possible_to_split = line_syllable_counts_need_to_be[0] <= sum(line_syllable_counts) and line_syllable_counts_need_to_be[1] >= sum(line_syllable_counts)
  #         if possible_to_split:
  #           split_lines = self.split_line_at_syllable_count(line, self.format["syllable_structure"][line_index]) 
  #           if split_lines:
  #             for split_line in split_lines:
  #               temp_temp_poem = list(temp_poem)
  #               has_failed_yet = False
  #               for temp_line_index, temp_line in enumerate(split_line):
  #                 if self.validate_line(temp_temp_poem, temp_line, line_index + temp_line_index):
  #                   temp_temp_poem[line_index + temp_line_index] = temp_line
  #                 else:
  #                   has_failed_yet = True
  #                   break
  #               if not has_failed_yet:
  #                 def assign_to_poem(i_and_line):
  #                   self.poems[poem_index][line_index + i_and_line[0]] = i_and_line[1]
  #                 if (self.poems[poem_index] != [None] * self.lines_needed):
  #                   extra_poems.append(list(self.poems[poem_index])) #append in a copy of the same poem, without the new line
  #                 map(assign_to_poem , enumerate(split_line))
  #   #add a new poem if there isn't a blank one in the list of poems.
  #   if len(   filter( lambda x: len(  filter(lambda y: y == None, x)) == len(x), self.poems)   ) == 0:
  #     self.poems.append([None] * self.lines_needed)
  #   if len(extra_poems) > 0:
  #     if self.debug:
  #       print "Added: " + str(len(extra_poems))
  #     self.poems.extend(extra_poems)
  #   return False in map(lambda x: None in x, self.poems) # return false until the poem is done. 

  def validate_line(self, poem, line, index):
    """ Return line if given line fits into the format positioned at the given index, false otherwise"""
    #TODO! now: make this return n lines that go into the poem at index, if they do fit.
    #e.g. [line1, line2] is line was split and fits, as split, into two lines.
    syllable_counts = self.format["syllable_structure"]
    rhyme_scheme = self.format["rhyme_scheme"]

    #TODO: abstract away formats (like above, make a dict of validator functions
    # and call those iff a given format restrictor is in the format dict)
    valid = True
    valid = valid and self.validate_syllables(line, syllable_counts[index])
    valid = valid and self.validate_rhyme(poem, line, index)
    return valid

  def split_line_at_syllable_count(self, line, syllable_count):
    """Returns a line split at the given number of syllables. False if split is inside a word.

    #TODO: Should this return a list of possible splits? Yes.
    E.g. for sentence "a man a plan" and range 1,3, 
    Should this return [["a", "man a plan"], ["a man", "a plan"], ["a man a", "plan"]]?

    >>> p = Poemifier("haiku")
    >>> p.split_line_at_syllable_count("There once was banana man from the beach", 4)
    False
    >>> p.split_line_at_syllable_count("There once was a man from the beach", 4)
    [['There once was a', 'man from the beach']]
    >>> p.split_line_at_syllable_count("There once was a man from the beach banana", 4)
    [['There once was a', 'man from the beach banana']]
    >>> p.split_line_at_syllable_count("There once was banana people from the beach", (5,7))
    [['There once was banana', 'people from the beach']]
    >>> p.split_line_at_syllable_count("There once was banana man from the beach Anna", (5,7))
    [['There once was banana', 'man from the beach Anna'], ['There once was banana man', 'from the beach Anna']]
    """

    if isinstance(syllable_count, int):
      splits = [self._split_line_at_syllable_count_helper(line, syllable_count)]
    elif isinstance(syllable_count, tuple):
      splits = map(lambda s: self._split_line_at_syllable_count_helper(line, s), range(syllable_count[0], syllable_count[1]+1))
    return filter(lambda x: x is not False, splits) or False

  def _split_line_at_syllable_count_helper(self, line, syllable_count):
    split_line = line.strip().split(" ")
    if "" in split_line:
      return False
    if syllable_count == 0:
      return ["", line]
    elif syllable_count > 0:
      word = split_line[0]
      this_word_syllables = self.rhyme_checker.count_syllables(word)
      next_return =  self._split_line_at_syllable_count_helper(" ".join(split_line[1:]), syllable_count - this_word_syllables)
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
      if self.debug:
        print "nothing to compare " + last_word + " to. " 
      return True
    words_to_compare_to = map(lambda x: x.split(" ")[-1], lines_to_compare_to )
    return True in map(lambda x: self.rhyme_checker.rhymes_with(last_word, x), words_to_compare_to)

  # def validate_syllables(self, line, syllable_count):
  #   """True if line has the number of syllables specified in syllable_count."""
  #   syllable_count_on_this_line = 0
  #   split_line = line.split(" ")

  #   #exclude lines with abbreviations
  #   if True in map(lambda x: len(x) == 1 and x not in ["a", "A", "I"], split_line):
  #     return False

  #   for dirty_word in split_line:
  #     word = dirty_word.strip(",.:?!")
  #     syllable_count_on_this_line += self.rhyme_checker.count_syllables(word)
  #   if self.debug: #leads to huge amounts of output
  #     print line + ": " + str(syllable_count_on_this_line)
  #   if isinstance(syllable_count, int):
  #     return syllable_count_on_this_line == syllable_count
  #   elif isinstance(syllable_count, tuple):
  #     return syllable_count_on_this_line >= syllable_count[0] and syllable_count_on_this_line <= syllable_count[1]

  # def has_poem(self):
  #   return True in map(lambda x: None not in x, self.poems)

  def get_poem(self, random=False):
    """ Return False or a poem. """
    #TODO: again, abstraction!
    poem = self.lines_needed * [None]
    if self.format["syllable_structure"]:
      #TODO: delete all the hash entries that don't fit anything in the syllable structure
      for index, syllable_count in enumerate(self.format["syllable_structure"]):
        if syllable_count not in self.syllable_count_dict:
          return False 
        candidate_lines = filter(lambda l: l not in poem, self.syllable_count_dict[syllable_count])
        if not candidate_lines:
          return False
        if random:
          next_line_index = random(len(candidate_lines))
        else:
          next_line_index = 0
        next_line = candidate_lines[next_line_index] #TODO: if random, pick one randomly.
        poem[index] = next_line
      return poem

  # def old_get_poem(self):
  #   #print "Created " + str(len(self.poems)) + " partial poems."
  #   if self.has_poem():
  #     return "\n".join( filter(lambda x: None not in x, self.poems)[0] )
  #   else:
  #     self.poems.sort(key= lambda x: x.count(None)) #[0:10]
  #     print self.poems[0:10]
  #     raise ShitsFuckedException, "No poem could be generated!"

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
  
  #lines = ["camping is in tents", "my tree table tries", "between those times I slept none"]
  # lines = ["many words in english rhyme with song", "one two three four five six", "a bee see dee word kicks",
  # "This is a line that is twenty long and here are ten more ending in wrong", "Jeremy Bee Merrill plays ping pong",
  # ]

  p = Poemifier("haiku")
  p.debug = True
  #TODO: make this a do... while (so we quit when we finish a poem)
  for line in lines:
    line = re.sub("[^A-Za-z ']", "", line)
    line = line.strip()
    if re.search("\s[BCDEFGHJKLMNOPQRSTUVWXYZ]\s", line):
      continue
    if p.try_line(line):
      if p.debug: 
        print "Done!"
      break
    print p.syllable_count_dict
  print ""
  print p.get_poem()


#TODO: (eventually)
# Done? be a little more recursive, but not all the way, about pairing lines. maybe one loop per rhyming group? (i.e. for "a"s)
# Allow multiple poems to be requested (only break when the number of complete poems in self.poems = the number requested)

"""
  #TODO! fix this: 
  lines = ["many words in english rhyme with song", "one two three four five six", "a bee see dee word kicks",
  "This is a line that is twenty long and here are ten more ending in wrong", "Jeremy Bee Merrill plays ping pong",
  ]
  the ordering is wrong. if the first line is moved to the end, it works.
  Find a recursive-y way to get the right result here.
"""