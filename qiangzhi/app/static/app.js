// -*- mode: js; js-indent-level: 2; -*-

var app = new Vue({
  el: '#wordapp',
  delimiters: ['[[', ']]'],
  data: {
    words: [],
    iword: 0,
    wordsPerPage: 10,
    totalWords: 0,
    activeWords: [],
    message: 'Hello Vue!',
    passed: 0,
    failed: 0,
    points: 0,
    passCurPage: 0,
    totalPoints: 0,
    totalDays: 0,
    totalStudyDays: 0,
    firstDay: 99991231,
    today: 19700101,
    reviewDays: [],
    daily: [],
    nmax: 20,
    bookList: [],
    bookSelected: "",
    skipNewWords: false,
    test_message: "",
  },
  computed: {
    wordList: function() {
      // var iLast = Math.min(this.words.length, this.iword+this.wordsPerPage);
      var i0 = this.iword;
      var i1 = this.iword + this.wordsPerPage;
      return this.filterWords.filter(function (w,i) { return (i >= i0 && i < i1 && !w.skip)});
    },
    iwordLast: function () {
        console.log("the last is:", this.filterWords.length);
	return Math.floor(this.filterWords.length / this.wordsPerPage) * this.wordsPerPage;
    },
    wordInSelectedBook: function () {
      var self = this;
      return this.words.filter(function(w) {
	return (self.bookSelected == "" || w.books.indexOf(self.bookSelected) >= 0); });
    },
    filterWords: function() {
	var self = this;
	return this.wordInSelectedBook.filter(function(w) { return !(self.skipNewWords && ! w.dateStudy); });
    },
  },
  watch: {
    iword: function(val) {
      passCurPage = 0;
    },
  },
  methods: {
    scoreTag: function(w) {
      if (w.score == 0) return '';
      else if (w.score < 0) return 'danger';
      else if (w.score > 0) return 'primary';
    },
    showNextList: function() {
      console.log(this.iword, this.iword + this.wordsPerPage);
      var i0 = this.iword;
      var i1 = this.iword + this.wordsPerPage;
      console.log(this.words.filter(function (w,i) { return (i >= i0 && i < i1)}));

      for(var i = 0; i < this.activeWords.length; ++i) { this.activeWords[i].skip = true; }
      var i = 0;
      var j = 0;
      for(j = 0; j < this.nmax; ++j) {
	while(this.words[i].skip && i < this.words.length) ++i;
	if (i >= this.words.length) break;
	this.activeWords.splice(j, 1, this.words[i++]);
	//j;
	//i;
      }
      var n = 0;
      for (i = 0; i < this.words.length; ++i) { if (this.words[i].skip) ++n; }
      this.totalWords = n;
      // console.log(this.totalWords);
    },
    dateFormat: function(str) {
      if (str) {
	var date = new Date(str);
	return date.getFullYear() + "-" + (1+date.getMonth()) + '-' + date.getDate() + " " + date.getHours() + ":" + Math.floor(date.getMinutes() / 10) + date.getMinutes() % 10;
      } 
      return "";
    },
    markPoints: function(word, score) {
      var dt = new Date();
      console.log("marking ", word.word, "right");
      console.log(dt.toISOString());
      if (score > 0) {
	this.passed += 1;
	this.passCurPage += 1;
	this.points += score > 2 ? 2:1;
      } else {
	this.failed += 1;
	this.points -= 1;
	if (word.score > 30) this.points -= 1;
      }
      this.$set(word, 'score', score);
      this.$set(word, 'dateStudy', dt.toISOString());
      this.saveWords([ word ]);
    },
    skipWord: function(word) { word.skip = true; },
    status: function(word) {
      if (word.score == 0) return 'new';
      else if (word.score < 0) return 'wrong';
      else return 'pass';
    },
    show: function(word) {
      if (word.skip) return false;
      // if (word.score > 0) return false;
      return true;
    },
    saveWords: function(words) {
      var self = this;
      console.log(JSON.stringify({ words: words, points: self.points}));
      $.ajax({
	type: 'POST',
	url: './save',
	contentType:"application/json",
	data: JSON.stringify({ words: words, points: self.points}),
	dataType: 'json',
	success: function(data) {
	    console.log("saved!", data);
	},
	error: function(data) { console.log("ERROR", data); },
      });
    }
  },
  mounted: function() {
    var self = this;
    for (i = 0; i < ALL_WORDS.length; ++i) {
      self.words.push(ALL_WORDS[i]);
    }
    console.log("passed ?");
    this.test_message = "words: " + ALL_WORDS.length;
  },
})
