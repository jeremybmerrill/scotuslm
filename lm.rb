# encoding: utf-8 
require 'engtagger'
require 'nokogiri'

class LanguageModel
=begin
What's the best model for a 3LM?

threelm[wordTwoBack][wordBack]
=> {tokencount => 13, {1 => "Jeremy", 2 => "Nate", 3 => "Jeremy", 4 => "Megan"}}
=> {tokencount => 13, [[1, "Jeremy"], [5, "Megan"], [7, "Nate"]]

"backoff" -- if count is less than <10, go to 2LM

=end

  def initialize(pathglob,lambdaFunc = lambda{|a| a } )
    trigramcounts = {}
    unigramcounts = {}
    unigramcounts.default = 0

    bigramcountsmember = {}
    bigramcountsmember.default = 0
    bigramcounts = {} #e.g. {San => {Francisco => 50, Jose => 20} }
    bigramcounts.default = bigramcountsmember

    trigramcountsmember = {}
    trigramcountsmember.default = bigramcountsmember
    trigramcounts.default = trigramcountsmember

    @engtagger = EngTagger.new
    #@complementizer_list = ['AZ', 'TH', 'TS', ]
    #@verb_list = ['S']
    @complementizer_list = ["wp", "wps," "wdt", "wrb"] #also, "in", dealt with separately
    @actual_IN_complementizers = ["that", "although", "after", "although", "if", "unless", "as", "inasmuch", "until", "when", "whenever", "since", "while", "because", "before", "though"]
    @verb_list = ["vb", "vbd", "vbp", "vbz",] #, "vbg", "vbn" #participles, which I don't really want.
    @complementizer_count = 0
    @verb_count = 0
    @makes_things_worse_adjustment = 3 #if the selected part of speech would make things worse, multiply this by probability to make it harder to add the selected word



    @wordcount = 0
    files = Dir.glob(File.join(*pathglob))
    files.each do |f|
      next if File.basename(f) == '.' or File.basename(f) == '..' or !lambdaFunc.call(File.basename(f))
      File.open(f).each do |line|
        #line = line.split(/[.?!]|$/) 
        [line].each do |sentence|
          splitSentence = sentence.strip().split(" ")
          wordTwoBack = ""
          wordBack = ""
          splitSentence.each do |word|
            word.gsub("—", "")
            word = word.downcase.gsub(/[_\(\),]/, "") #—
            @wordcount += 1

            unigramcounts[word] += 1
            bigramInnerDict = bigramcounts[wordBack].clone
            bigramInnerDict[word] = bigramInnerDict[word] +1
            bigramcounts[wordBack] = bigramInnerDict
            #trigramcounts[wordTwoBack][wordBack][word] += 1
            trigramOneStepInside = trigramcounts[wordTwoBack].clone
            trigramTwoStepsInside = trigramOneStepInside[wordBack].clone
            trigramTwoStepsInside[word] += 1
            trigramOneStepInside[wordBack] = trigramTwoStepsInside
            trigramcounts[wordTwoBack] = trigramOneStepInside
            
            wordTwoBack = wordBack
            wordBack = word
          end
        end
      end
    end

    @trigramlm = {}
    @bigramlm = {}
    @bigramlm.default = {:tokencount => 0, :data => []}
    @trigramlm.default = @bigramlm
    @unigramlm = []

    trigramcounts.each do |wordTwoBack, trigramCountsOneStepInside|
      trigramLMOneStepInside = {}
      outerCount = 0
      trigramCountsOneStepInside.each do |wordBack, trigramCountsTwoStepsInside|
        outerCount += 1
        count = 0
        trigramLMTwoStepsInside = []
        trigramCountsTwoStepsInside.each do |word, myCount|
          count += myCount
          trigramLMTwoStepsInside << [count, word]
        end
        trigramLMOneStepInside[wordBack] = {}
        trigramLMOneStepInside[wordBack].default = {:tokencount => 0, :data => []}
        trigramLMOneStepInside[wordBack][:tokencount] = count
        trigramLMOneStepInside[wordBack][:data] = trigramLMTwoStepsInside
      end
      @trigramlm[wordTwoBack] = trigramLMOneStepInside
    end

    bigramcounts.each do |wordBack, innerHash|
      count = 0
      innerLM = []
      innerHash.each do |word, myCount|
        count += myCount
        innerLM << [count, word]
      end
      @bigramlm[wordBack] = {}
      @bigramlm[wordBack].default = {:tokencount => 0, :data => []}
      @bigramlm[wordBack][:tokencount] = count
      @bigramlm[wordBack][:data] = innerLM
    end

    count = 0
    unigramcounts.each do |word, myCount|
      count += myCount
      @unigramlm << [count, word]
    end
    puts "done generating hashes"
    true
  end

  def checkVerbsAndComplementizers(sentenceSoFar, nextWord, probability = 0.3 )
    #implements "very shallow parsing" on a sentence
    #if the sentence doesn't have N + 1 verbs for every N complementizers, 
    #   then, with some probability, return false if the next word if it doesn't resolve the imbalance.
    #   and return false with higher probability if the next word increases the imbalance
    #   in hopes of finding a word that satisfies the imbalance on the next go-round.

    tagged_sentence = @engtagger.add_tags( sentenceSoFar.join(" ") )
    tagged_sentence_with_next_word = @engtagger.add_tags( (sentenceSoFar + [nextWord]).join(" ") )
    last_word_tag_stuff = tagged_sentence_with_next_word.split("> <")[-1].gsub(/^</, "").gsub(/>$/, "")
    last_word_POS = last_word_tag_stuff[0...last_word_tag_stuff.index(">")]
    last_word_content = last_word_tag_stuff[last_word_tag_stuff.index(">")+1 ... last_word_tag_stuff.index("<")]
    if tagged_sentence
      @verb_count = tagged_sentence.split("> <").select{ |e| @verb_list.include? e[0...e.index(">")] }.count
      @complementizer_count = tagged_sentence.split("> <").select{ |e| @complementizer_list.include?(e[0...e.index(">")]) || (e[0...e.index(">")] == "in" && @actual_IN_complementizers.include?(last_word_content) )}.count
    end
    #@verb_count = links.select{ |link| @verb_list.include? link[:label].chars.select{ |c| c.match(/[A-Z]/) }.join("") }.size
    #@complementizer_count = links.select{ |link| @complementizer_list.include? link[:label].chars.select{ |c| c.match(/[A-Z]/) }.join("") }.size

    if @verb_count == 0 && @complementizer_count == 0
      return true
    end

    puts [nextWord, @verb_count, @complementizer_count, last_word_POS].join(" ") if @debug
    if @complementizer_list.include? last_word_POS
      if @verb_count == @complementizer_count + 1 #balance
        true
      elsif @verb_count > @complementizer_count + 1  #imbalance -- complementizer needed
        #accept, this fixes the imbalance!
        true
      elsif rand > probability * @makes_things_worse_adjustment #verb needed, reject with high probability; allowing this word would increase the imbalance
        #oh well, keep it.
        true
      else 
        false
      end
    elsif @verb_list.include? last_word_POS
      if @verb_count == @complementizer_count + 1 #balance
        true
      elsif @verb_count < @complementizer_count + 1  #imbalance -- verb needed
        #accept, this fixes the imbalance!
        true
      elsif rand > probability * @makes_things_worse_adjustment #complementizer needed, reject with high probability; allowing this word would increase the imbalance
        #oh well, keep it.
        true
      else 
        false
      end
    else
      if @verb_count == @complementizer_count + 1 #balance
        true
      elsif rand > probability #selected word doesn't fix the imbalance.
        #oh well, keep it.
        true
      else 
        #rejected!
        false
      end
    end
  end

  def nextWordBigrams(wordBack)
    nextWordChoicesStuff = @bigramlm[wordBack]
    if rand < @unpathiness / Math.log( nextWordChoicesStuff[:tokencount])
      puts "backing off to unigrams." if @debug
      nextWordChoicesStuff[:data] = @unigramlm
      nextWordChoicesStuff[:tokencount] = @wordcount
    end
    nextWordChoicesStuff
  end
  def nextWordTrigrams(wordBack, wordTwoBack)
    testthingy = @trigramlm[wordTwoBack]
    nextWordChoicesStuff = testthingy[wordBack] || {:tokencount => 0, :data => []}
    if rand < @unpathiness / Math.log( nextWordChoicesStuff[:tokencount])
      puts "backing off to bigrams, aka smoothing." if @debug
      nextWordChoicesStuff = nextWordBigrams(wordBack)
    elsif ! nextWordChoicesStuff 
      puts "backing off to bigrams, since trigrams returned nothing" if @debug
      nextWordChoicesStuff = nextWordBigrams(wordBack)
    end
    nextWordChoicesStuff
  end


  def getNextWord(wordBack, wordTwoBack)
    #returns the next word based on the wordBack and wordTwoBack
    #  dumb wrapper around nextWordBigrams, !!Trigrams functions.
    #  i.e. doesn't do any parsing or anything.
    nextWordChoicesStuff = nextWordTrigrams(wordBack, wordTwoBack)
    if ! nextWordChoicesStuff 
      puts "backing off to bigrams, since trigrams returned nothing" if @debug
      nextWordChoicesStuff = nextWordBigrams(wordBack)
    end
    nextWordChoices = nextWordChoicesStuff[:data].reverse
    tokencount = nextWordChoicesStuff[:tokencount]

    nextWord = nil
    myRand = rand(tokencount) + 1
    puts nextWordChoices.inspect if @debug
    puts "rand: #{myRand}, count: #{tokencount}, unpathiness: #{@unpathiness * 100}%" if @debug

    mostRecentWord = nil
    nextWordChoices.each_with_index do | valword, index |
      val,word = valword
      if (myRand == val) 
        nextWord = word
        break
      elsif (myRand > val) 
        nextWord = mostRecentWord 
        break     
      elsif index == (nextWordChoices.size) - 1
        nextWord = word
        break
      end
      mostRecentWord = word
    end
    nextWord
  end

  def getPhrase (opts = {})
   o = { #set defaults
      :maxLen => 30, # if you set maxLen to 0, there is no maxLen
      :unpathiness => 0.0, #TODO: Remember what this does.
      :wordTwoBack => "",
      :wordBack => "", 
      :debug => false,
      :engtagger => false, #TODO: Set to true, see if sentences are more coherent.
      :guaranteeParse => false,
   }.merge(opts)
		@unpathiness = o[:unpathiness]
    maxLen = o[:maxLen]
    wordTwoBack = o[:wordTwoBack]
    wordBack = o[:wordBack]
    @debug = o[:debug]
    useEngtagger = o[:engtagger]
    uselinkParserToValidateSentences = o[:guaranteeParse]  #should we return only parse-able sentences?
    puts "going to use engtagger" if @debug && useEngtagger

    soFar = [wordTwoBack, wordBack]
    endOfSentence = false

    loop do
      nextWord = getNextWord(wordBack, wordTwoBack)
      if nextWord
        # conditions under which we reject a word and go back to picking another one.
        if useEngtagger && ! checkVerbsAndComplementizers(soFar, nextWord)
          puts "trying to resolve verb-complementizer imbalance, rejecting \"" + nextWord.to_s + "\"" if @debug
        elsif false #if the word is off topic
          #given a topic, 
          #check if an "on topic" word could come next -- with 10% chance, choose it.          
          
        else
          soFar << nextWord
          puts soFar.join(" ") if @debug
          wordTwoBack = wordBack
          wordBack = nextWord
          break if nextWord == "" || (maxLen != 0 && soFar.length >= maxLen) 
        end
      else
        break
      end
    end
    sentence = soFar.join(" ").strip

    if !uselinkParserToValidateSentences
      sentence
    else
      require 'linkparser'
      sentence = soFar.join(" ").strip
      @linkparser = LinkParser::Dictionary.new
      result = @linkparser.parse(sentence)
      if result.linkages != []
        sentence
      else
        puts "ehhhhh, sentence didn't parse, trying again!" if @debug
        getPhrase(opts) #if the sentence doesn't parse, throw it out and start again.
      end
    end
  end

  #accessor methods for debugging, etc.
  def getDict (word)
    @trigramlm[word]
  end
  def getBigramDict (word)
    @bigramlm[word]
  end
  def getWholeBigramDict
    @bigramlm
  end
  def getWholeDict
    @trigramlm
  end
  def getEngtagger
    @engtagger
  end
  def getVerbCount
    @verb_count
  end
  def getComplementizerCount
    @complementizer_count
  end
end

@n = LanguageModel.new(["/home/merrillj/scotuslm/opinions", "*", "*", "*"], lambda{|filename| filename == "SCALIA.txt"})
puts @n.getPhrase({:debug => true, :engtagger => true})
