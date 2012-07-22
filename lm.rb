# encoding: utf-8

#Nietzsche trigram language model

class LanguageModel
=begin
What's the best model for a 3LM?

threelm[wordTwoBack][wordBack]
=> {tokencount => 13, {1 => "Jeremy", 2 => "Nate", 3 => "Jeremy", 4 => "Megan"}}
=> {tokencount => 13, [[1, "Jeremy"], [5, "Megan"], [7, "Nate"]]

"backoff" -- if count is less than <10, go to 2LM

=end
  def initialize(pathglob, lambdaFunc)
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

    @wordcount = 0
    files = Dir.glob(File.join(*pathglob))
    files.each do |f|
      next if File.basename(f) == '.' or File.basename(f) == '..' or !lambdaFunc.call(File.basename(f))
      File.open(f).each do |line|
        line.split(/[.?!]|$/).each do |sentence|
          splitSentence = sentence.split(" ")
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

  def getPhrase (opts = {})
   o = {
      :maxLen => 30,
      :unpathiness => 0.0,
      :wordTwoBack => "",
      :wordBack => "", 
      :debug => false
   }.merge(opts)
		@unpathiness = o[:unpathiness]
    maxLen = o[:maxLen]
    wordTwoBack = o[:wordTwoBack]
    wordBack = o[:wordBack]
    @debug = o[:debug]

    #TODO: make sure sentence ending works
    def nextWordBigrams(wordBack)
      nextWordChoicesStuff = @bigramlm[wordBack]
      if rand < @unpathiness / Math.log( nextWordChoicesStuff[:tokencount])
        puts "backing off to unigrams for funzies" if @debug
        nextWordChoicesStuff[:data] = @unigramlm
        nextWordChoicesStuff[:tokencount] = @wordcount
      end
      nextWordChoicesStuff
    end
    def nextWordTrigrams(wordBack, wordTwoBack)
      testthingy = @trigramlm[wordTwoBack]
      nextWordChoicesStuff = testthingy[wordBack] || {:tokencount => 0, :data => []}
      if rand < @unpathiness / Math.log( nextWordChoicesStuff[:tokencount])
        puts "backing off to bigrams for funzies" if @debug
        nextWordChoicesStuff = nextWordBigrams(wordBack)
      elsif ! nextWordChoicesStuff 
        puts "backing off to bigrams, since trigrams returned nothing" if @debug
        nextWordChoicesStuff = nextWordBigrams(wordBack)
      end
      nextWordChoicesStuff
    end


    soFar = [wordTwoBack, wordBack]
    stop = false
    while !stop
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
      puts nextWordChoicesStuff.inspect if @debug
      nextWordChoices = nextWordChoicesStuff[:data].reverse
      tokencount = nextWordChoicesStuff[:tokencount]

      nextWord = nil
      myRand = rand(tokencount) + 1
      puts "rand: #{myRand}, count: #{tokencount}, unpathiness: #{@unpathiness * 100}%" if @debug

      nextWordChoices.each do | val, word |
        if !nextWord && myRand >= val
          nextWord = word
        end
      end
      if nextWord
        soFar << nextWord
        puts soFar.join(" ") if @debug
        wordTwoBack = wordBack
        wordBack = nextWord
        stop = true if nextWord == "" || soFar.length >= maxLen
      else
        stop = true
      end
    end
    soFar.join(" ").strip
  end
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
end

@n = LanguageModel.new(["/home/merrillj/scotuslm/opinions", "*", "*", "*"], lambda{|filename| filename == "SOTOMAYOR.txt"})
puts @n.getPhrase({:debug => true})
