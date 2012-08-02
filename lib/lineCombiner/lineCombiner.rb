require_relative './trie.rb'

class LineCombiner
  def initialize(words = "/usr/share/dict/words")
    puts "creating a new LineCombiner"
    f = File.open(words)
    @t = Trie.new
    f.each_line{ |line| @t.addAWord(line.chomp) }
  end

  def safeToCombine?(w1, w2)
    @t.include?(w1 + w2) && !(@t.include?(w1) && @t.include?(w2))
  end

  def strictSafeToCombine?(w1, w2)
    @t.include?(w1 + w2) && !(@t.include?(w1) || @t.include?(w2))
  end

  def safeToSplit(w1, w2)
    @t.include?(w1) && @t.include?(w2) && !@t.include?(w1 + w2)
  end
end