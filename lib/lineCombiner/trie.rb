class Trie
  @subtrie = {} # "a" => Trie, {"n" => nil}

  def initialize(word = nil)
    @subtrie = {}
  end

  def [](elem)
    @subtrie.fetch(elem, nil)
  end

  def addAWord(word)
    if word.nil?
      nil
    else
      if ! @subtrie.include? word[0]
        @subtrie[word[0]] = Trie.new.addAWord(word[1..-1])
      else
        @subtrie[word[0]] = @subtrie[word[0]].addAWord(word[1..-1])
      end
      self
    end
  end

  def subtrie
    @subtrie
  end

  def include?(word)
    @subtrie.include?(word[0]) && (word[1..-1] == "" || @subtrie[word[0]].include?(word[1..-1]) )
  end
end