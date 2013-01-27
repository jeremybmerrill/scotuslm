require_relative './trie.rb'

class LineCombiner
  def initialize(words = "/usr/share/dict/words")
    puts "creating a new LineCombiner"
    f = File.open(words)
    @t = Trie.new
    f.each_line{ |line| @t.addAWord(line.chomp) }
  end

  def safe_to_combine?(w1, w2)
    @t.include?(w1 + w2) && !(@t.include?(w1) && @t.include?(w2))
  end

  def strict_safe_to_cmbine?(w1, w2)
    @t.include?(w1 + w2) && !(@t.include?(w1) || @t.include?(w2))
  end

  def safe_to_split(w1, w2)
    @t.include?(w1) && @t.include?(w2) && !@t.include?(w1 + w2)
  end
end