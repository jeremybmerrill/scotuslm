# coding=utf-8

class Syllabizer:
  def __init__(self):
    vowels = ["a", "e", "i", "o", "u"] # Y is dealt with separately
    self.vowels = vowels + map(lambda l: l.upper(), vowels)
    self.consonants = ["b", "c", "d", "f", "g" "h", "j", "k", 'l', 'm', 'n', 'p', 'q', 'r', 's', 't', 'v', 'w', 'x', 'y', 'z']

  def syllabize(self, word):
    letters = list(word)
    previous_letter = None
    syllables = 0
    for index, letter in enumerate(letters):
      if previous_letter not in self.vowels and letter in self.vowels:
        if not ((len(letters)-1) == index and letter == "e"):
          syllables += 1

      #Exceptions, because English says fuck you.
      #TODO phonology:
      #   ua : guarantee vs. ritual
      #   io : trio v. -ation
      if str(previous_letter) + letter in ("eo", "ia", "uo"): 
        syllables += 1
      # Y is a vowel only if surrounded on both sides by non-vowels.
      if letter == "y" and previous_letter not in self.vowels:
        syllables += 1
      if previous_letter == "y" and letter in self.vowels:
        syllables -= 1

      #logic, not an exception :P
      previous_letter = letter
    #more exceptions
    #words ending in "Vble"
    if word[-3:] == "ble":
      syllables += 1
    #[αplace ±voice]e[αplace -voice]
    if word[-2:] in ("ed", "es") and word[-3:] not in ("ted", "ded", "ses", "zes", "ces"):
      syllables -= 1
    return max(syllables, 1)


if __name__ == "__main__":
  s = Syllabizer()
  """
  paragraph = "Depth in and of itself does not guarantee anything it does not guarantee you wont use it in the future and it does not guarantee that that it is not a source of drinking water he saidIf Mexico City search for water seems extreme it is not unusual In aquifers Denver relies on drinking water levels have dropped more than three hundred feet Texas rationed some water use last summer in the midst of a recordbreaking drought And Nevada realizing that the water levels in one of the nations largest reservoirs may soon drop below the intake pipes is building a drain hole to sap every last drop from the bottom Water is limited so they are really hustling to find other types of water said Mark Williams a hydrologist at the University of Colorado at Boulder Its kind of a grim future theres no two ways about it"
  for word in paragraph.split():
    print(word, s.syllabize(word))"""

  tests = {"scouts" : 1, 
           "water" : 2, 
           "scythe": 1, 
           "yvonne": 2,
           "yellow" : 2,
           "aye" : 1,
           "bye" : 1,
           "circulation": 4,
           "syllable" : 3,
           "distressed" : 2,
           "wanted" : 2,
           "eaten" : 2,
           "singed" : 1,
           "diplomacy" : 4,
           "walked": 1,
           "shunted": 2,
           "places" : 2,
           "shoes" : 1,
           "mosses" : 2,
           "adzes": 2,
           "wines" : 1,
           "ritual": 3,
           "guarantee" : 3,
           "assuage": 2
          }
  failures = 0
  for test_word, correct_syllables in tests.items():
    deduced_syllables = s.syllabize(test_word)
    success = deduced_syllables == correct_syllables
    if not success:
      failures += 1
    print(test_word, deduced_syllables, success)
  print str(failures) + " failures"

