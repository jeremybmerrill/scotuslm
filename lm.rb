# encoding: utf-8 
require 'linkparser'

class LanguageModel
=begin
What's the best model for a 3LM?

threelm[wordTwoBack][wordBack]
=> {tokencount => 13, {1 => "Jeremy", 2 => "Nate", 3 => "Jeremy", 4 => "Megan"}}
=> {tokencount => 13, [[1, "Jeremy"], [5, "Megan"], [7, "Nate"]]

"backoff" -- if count is less than <10, go to 2LM

=end

  def initialize(pathglob,lambdaFunc)
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

    @linkparser = LinkParser::Dictionary.new
    @complementizer_list = ['AZ', 'TH', 'TS', ]
    @verb_list = ['S']
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

  def checkVerbsAndComplementizers(sentenceSoFar, nextWord, probability = 0.2 )
    #implements "very shallow parsing" on a sentence
    #if the sentence doesn't have N + 1 verbs for every N complementizers, 
    #   then, with some probability, return false if the next word if it doesn't resolve the imbalance.
    #   and return false with higher probability if the next word increases the imbalance
    #   in hopes of finding a word that satisfies the imbalance on the next go-round.

    parsedSentence = @linkparser.parse( (sentenceSoFar + [nextWord]).join(" ") )
    begin 
      linkage = parsedSentence.linkages[-1]
      links = linkage.links
    rescue NoMethodError
      return true #ehh, sentence didn't parse.
    end

    @verb_count = links.select{ |link| @verb_list.include? link[:label].chars.select{ |c| c.match(/[A-Z]/) }.join("") }.size
    @complementizer_count = links.select{ |link| @complementizer_list.include? link[:label].chars.select{ |c| c.match(/[A-Z]/) }.join("") }.size

    lastLinkageLabel = parsedSentence.linkages[-1].links[-1][:label]
    lastLinkagePOS = lastLinkageLabel.chars.select{ |c| c.match(/[A-Z]/) }.join("")
    puts [nextWord, @verb_count, @complementizer_count, lastLinkagePOS].join(" ") #if @debug
    if @complementizer_list.include? lastLinkagePOS
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
    elsif @verb_list.include? lastLinkagePOS
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

  def getPhrase (opts = {})
   o = { #set defaults
      :maxLen => 30,
      :unpathiness => 0.0,
      :wordTwoBack => "",
      :wordBack => "", 
      :debug => false,
      :linkparser => false #TODO: Set to true, see if sentences are more coherent.
   }.merge(opts)
		@unpathiness = o[:unpathiness]
    maxLen = o[:maxLen]
    wordTwoBack = o[:wordTwoBack]
    wordBack = o[:wordBack]
    @debug = o[:debug]
    useLinkparser = o[:linkparser]
    puts "going to use linkparser" if @debug && useLinkparser

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


    soFar = [wordTwoBack, wordBack]
    endOfSentence = false
    while !endOfSentence
      #testthingy = @trigramlm[wordTwoBack]
      #nextWordChoicesStuff = testthingy[wordBack]
      #if ! nextWordChoicesStuff 
      #  puts "falling back to bigram dict" if @debug
      #  nextWordChoicesStuff = @bigramlm[wordBack]
      #end
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

      if nextWord
        if !useLinkparser || checkVerbsAndComplementizers(soFar, nextWord)
          soFar << nextWord
          puts soFar.join(" ") if @debug
          wordTwoBack = wordBack
          wordBack = nextWord
          endOfSentence = true if nextWord == "" || soFar.length >= maxLen
        else
          puts "trying to resolve verb-complementizer imbalance, rejecting \"" + nextWord.to_s + "\"" 
        end
      else
        endOfSentence = true
      end
    end
    soFar.join(" ").strip
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
  def getLinkparser
    @linkparser
  end
  def getVerbCount
    @verb_count
  end
  def getComplementizerCount
    @complementizer_count
  end
end

@n = LanguageModel.new(["/home/merrillj/scotuslm/opinions", "*", "*", "*"], lambda{|filename| filename == "SCALIA.txt"})
puts @n.getPhrase({:debug => true, :linkparser => true})
