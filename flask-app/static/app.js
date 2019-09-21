var app = new Vue({
  el: '#wordapp',
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
    filterWords: function() {
	var self = this;
	return this.words.filter(function(w) { return !(self.skipNewWords && ! w.dateStudy); });
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
	  error: function(data) { alert("ERROR", data); },
      });
    }
  },
  mounted: function() {
    var self = this;
    $.ajax({
      type: 'GET',
      url: "words",
      dataType: 'json',
      success: function(data) {
	console.log(data);
	self.words.splice(0);
	self.totalWords = data.totalWords;
	for (var i = 0; i < data.words.length; ++i) {
	  data.words[i].score = 0;
	  data.words[i].skip = false;
	  // data.words[i].dateStudy = '';
	  self.words.push(data.words[i]);
	  if(self.activeWords.length < self.nmax) self.activeWords.push(self.words[i]);
	}
	self.today = data.today;
	console.log("today: ", data.today);
	console.log("daily: ", data.daily);
	if (data.daily[data.today]) {
	  self.passed = data.daily[data.today][0];
	  self.failed = data.daily[data.today][1];
	  self.points = data.daily[data.today][2];
	}
	self.totalPoints = data.totalPoints;
	self.totalDays = data.totalDays;
	self.totalStudyDays = data.totalStudyDays;
	self.firstDay = data.firstDay;
        self.reviewDays.splice(0);
        self.reviewDays.push(...data.reviewDays);
	self.bookList.splice(0);
	console.log(data.bookList);
	for(var i = 0; i < data.bookList.length; ++i) {
	  self.bookList.splice(i, 1, data.bookList[i]);
	}
	console.log(self.bookList);
      }
    });
    console.log("passed ?");
  },
})
