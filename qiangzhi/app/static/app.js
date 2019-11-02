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
    num_thumbs_up: 0,
    cur_xpoints: 0,
    tot_xpoints: 0,
    passCurPage: 0,
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
	this.cur_xpoints += score;
	word.num_pass += 1;
      } else if (score < 0) {
	this.failed += 1;
	this.cur_xpoints -= 1;
	word.num_fail += 1;
      }
      word.cur_xpoints += score;
      this.$set(word, 'xpoints', score);
      this.$set(word, 'dateStudy', dt.toISOString());
      this.saveWords([ word ]);
    },
    skipWord: function(word) { word.skip = true; },
    status: function(word) {
      if (word.cur_xpoints == 0) return 'new';
      else if (word.cur_xpoints < 0) return 'fail';
      else return 'pass';
    },
    show: function(word) {
      if (word.skip) return false;
      // if (word.score > 0) return false;
      return true;
    },
    saveWords: function(words) {
      var self = this;
      console.log(JSON.stringify({ words: words, points: self.cur_xpoints}));
      $.ajax({
	type: 'POST',
	url: './save',
	contentType:"application/json",
	data: JSON.stringify({ words: words, points: self.cur_xpoints}),
	dataType: 'json',
	success: function(data) {
	  console.log("saved!", data);
	  for(i = 0; i < data.length; ++i) {
	    var w = data[i];
	    var wc = self.words[w.iword];
	    wc.streak = w.streak;
	    wc.tot_xpoints = w.tot_xpoints;
	    wc.study_date = w.study_date;
	  }
	  for (i = 0; i < words.length; ++i) {
	    self.cur_xpoints += words[i].xpoints;
	    self.tot_xpoints += words[i].xpoints;
	  }
	},
	error: function(data) { console.log("ERROR", data); },
      });
    }
  },
  mounted: function() {
    var self = this;
    for (i = 0; i < ALL_WORDS.length; ++i) {
      self.words.push(ALL_WORDS[i]);
      self.words[i].iword = i;
    }
    self.cur_xpoints = CUR_XPOINTS;
    self.tot_xpoints = TOT_XPOINTS;
    console.log("passed ?");
  },
})
